#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

reload(sys)
sys.setdefaultencoding('utf8')

import os
import logging
import time
import datetime
import string
import random

from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

from Crypto.Hash import SHA256

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

APPLICATION_YEAR = 2016

class LearningAssociation(ndb.Model):
    """Main model for representing learning associations."""
    name = ndb.StringProperty(required=True, default="")
    email = ndb.StringProperty(required=True, default="")
    active = ndb.BooleanProperty(required=True, default=True)

class PreviousGrants(ndb.Model):
    """Sub model for previous grants."""
    year = ndb.StringProperty('y', required=True, default="")
    location = ndb.StringProperty('l', required=True, default="")

class OtherGrants(ndb.Model):
    """Sub model for other grants applications."""
    provider = ndb.StringProperty('p', required=True, default="")
    amount = ndb.StringProperty('a', required=True, default="")

class TravelGrantsApplication(ndb.Model):
    """Main model for representing a travel grants application."""
    name =          ndb.StringProperty(required=True, default="")
    address =       ndb.StringProperty(required=True, default="")
    postal_code =   ndb.StringProperty(required=True, default="")
    postal_city =   ndb.StringProperty(required=True, default="")
    phone =         ndb.StringProperty(required=True, default="")
    email =         ndb.StringProperty(required=True, default="")
    organization =  ndb.StringProperty(required=True, default="")
    learning_association = ndb.KeyProperty(kind=LearningAssociation, required=True)
    previous_grants = ndb.StructuredProperty(PreviousGrants, repeated=True)
    location =      ndb.StringProperty(required=True, default="")
    time_span =     ndb.StringProperty(required=True, default="")
    expenses =      ndb.StringProperty(required=True, default="")
    other_grants =  ndb.StructuredProperty(OtherGrants, repeated=True)
    purpose =       ndb.TextProperty(required=True, default="")
    study_program = ndb.TextProperty(required=True, default="")
    sent_at =       ndb.DateTimeProperty(required=True)
    application_year = ndb.IntegerProperty(required=True, default=APPLICATION_YEAR)
    priority =      ndb.IntegerProperty(choices=range(11))
    remark =        ndb.TextProperty()
    learning_association_name = ndb.ComputedProperty(lambda self: self.learning_association.get().name)

class Otp(ndb.Model):
    """Model for storing OTP tokens."""
    learning_association = ndb.KeyProperty(kind=LearningAssociation)
    token = ndb.StringProperty()
    valid_from = ndb.DateTimeProperty(auto_now=True)
    valid_until = ndb.ComputedProperty(lambda self: self.valid_from + datetime.timedelta(minutes=30))

class MainHandler(webapp2.RequestHandler):
    def render_form(self, grants_application, errors={}):
        learning_associations = LearningAssociation.query().order(LearningAssociation.name).fetch(50)

        while (len(grants_application.previous_grants) < 3):
            grants_application.previous_grants.append(PreviousGrants())

        while (len(grants_application.other_grants) < 3):
            grants_application.other_grants.append(OtherGrants())

        template_values = {
            'application_year': APPLICATION_YEAR,
            'learning_associations': learning_associations,
            'grants_application': grants_application,
            'errors': errors
        }

        template = JINJA_ENVIRONMENT.get_template('application_form.html')
        self.response.write(template.render(template_values))

    def enum_params(self, class_name, params, target):
        classes = {
            'previous_grants': PreviousGrants,
            'other_grants': OtherGrants
        }
        for i, item in enumerate(self.request.POST.getall('_'.join([class_name,params[0]]))):
            model = classes[class_name]()
            setattr(model, params[0], item)
            setattr(model, params[1], self.request.POST.getall('_'.join([class_name,params[1]]))[i])
            if not model == classes[class_name]():
                target.append(model)

    def get(self):
        grants_application = TravelGrantsApplication()

        self.render_form(grants_application)

    def post(self):
        grants_application = TravelGrantsApplication(parent=ndb.Key('Year', APPLICATION_YEAR))
        errors = {}

        for item in ['name', 'address', 'postal_code', 'postal_city', 'phone', 'email', 'organization', 'location', 'time_span', 'expenses', 'purpose', 'study_program']:
            setattr(grants_application, item, self.request.POST.get(item))
            if not getattr(grants_application, item):
                errors[item] = 'missing'
            elif item == 'email':
                if not mail.is_email_valid(grants_application.email):
                    errors[item] = 'invalid'

        grants_application.learning_association = ndb.Key(urlsafe=self.request.POST.get('learning_association'))
        learning_association = grants_application.learning_association.get()
        if not learning_association:
            errors['learning_association'] = 'missing'

        self.enum_params('previous_grants', ['year','location'], grants_application.previous_grants)
        self.enum_params('other_grants', ['provider','amount'], grants_application.other_grants)

        if (len(errors) > 0):
            self.render_form(grants_application, errors)
        else:
            grants_application.sent_at = datetime.datetime.now()
            grants_application.put()

            previous_grants_text = []
            if len(grants_application.previous_grants) > 0:
                for item in grants_application.previous_grants:
                    previous_grants_text.append("- År: %s\n- Sted (land): %s\n" % (item.year, item.location))
            else:
                previous_grants_text.append("[ingen]")

            other_grants_text = []
            if len(grants_application.other_grants) > 0:
                for item in grants_application.other_grants:
                    other_grants_text.append("- Fra: %s\n- Beløp: %s\n" % (item.provider, item.amount))
            else:
                other_grants_text.append("[ingen]")

            application_text = """
SØKER:
%s
%s
%s %s

Telefon (dagtid): %s
Epostadresse:     %s

Organisasjon/arbeidsfelt/funksjon:
%s

Studieforbund:
%s

Tidligere tildelt stipend fra KD/VOFO:
%s

PLAN FOR REISEN:
Sted (land): %s
Tidsrom:     %s
Antatte totale reisekostnader: %s

Formål med studiereisen:
%s

Program for studieoppholdet:
%s

Andre offentlige tilskudd det søkes om til samme studiereise:
%s

Søknad sendt %s.
""" % (grants_application.name, grants_application.address, grants_application.postal_code,
grants_application.postal_city, grants_application.phone, grants_application.email,
grants_application.organization, learning_association.name, "\n".join(previous_grants_text), grants_application.location,
grants_application.time_span, grants_application.expenses, grants_application.purpose,
grants_application.study_program, "\n".join(other_grants_text), grants_application.sent_at.strftime("%d.%m.%y %H:%M"))
            mail.send_mail(sender="Voksenopplæringsforbundet <vofo@vofo.no>",
                           to="%s <%s>" % (learning_association.name, learning_association.email),
                           subject="Reisestipendsøknad fra %s" % (grants_application.name),
                           body="""
Hei

Det har kommet en ny søknad om reisestipend til deres studieforbund.

%s

--
Hilsen Voksenopplæringsforbundet
""" % (application_text))

            mail.send_mail(sender="Voksenopplæringsforbundet <vofo@vofo.no>",
                           to="%s <%s>" % (grants_application.name, grants_application.email),
                           subject="Reisestipendsøknad til %s" % (learning_association.name),
                           body="""
Hei %s

Du har nettopp sendt søknad om reisestipend til %s.

%s

--
Hilsen Voksenopplæringsforbundet
""" % (grants_application.name, grants_application.email, application_text))

            template_values = {
                'application_year': APPLICATION_YEAR,
                'grants_application': grants_application,
                'learning_association': learning_association
            }

            template = JINJA_ENVIRONMENT.get_template('hooray.html')
            self.response.write(template.render(template_values))


class AdminHandler(webapp2.RequestHandler):
    def dispatch(self):
        """This handler requires the current_user to be admin."""
        if users.is_current_user_admin():
            super(AdminHandler, self).dispatch()
        else:
            if users.get_current_user():
                self.abort(403)
            else:
                self.redirect(users.create_login_url(self.request.uri))

    def get_params(self):
        return (self.request.get('sf') == 'new'), (self.request.get('sf').isdigit() and int(self.request.get('sf')) or self.request.get('sf'))

    def get(self):
        if self.request.get('sf'):
            is_new, sf_id = self.get_params()
            learning_association = is_new and LearningAssociation() or LearningAssociation.get_by_id(sf_id)
            learning_associations = None
        else:
            learning_association = None
            learning_associations = LearningAssociation.query().order(LearningAssociation.name).fetch(50)

        template_values = {
            'application_year': APPLICATION_YEAR,
            'learning_association': learning_association,
            'learning_associations': learning_associations
        }

        template = JINJA_ENVIRONMENT.get_template('admin_form.html')
        self.response.write(template.render(template_values))

    def post(self):
        if self.request.get('sf'):
            is_new, sf_id = self.get_params()
            learning_association = is_new and LearningAssociation() or LearningAssociation.get_by_id(sf_id)
            if learning_association:
                learning_association.name = self.request.get('name')
                learning_association.email = self.request.get('email')
                learning_association.active = self.request.get('active') == 'true'
                learning_association.put()
        self.redirect('/admin')

class PrioritizeHandler(webapp2.RequestHandler):
    __scope = None

    def dispatch(self):
        self.__scope = None
        auth_token = self.request.cookies.get('auth_token')
        if users.is_current_user_admin():
            if self.request.get('logg_ut') == 'true':
                self.redirect(users.create_logout_url('/prioriter'))
            else:
                self.__scope = TravelGrantsApplication.query()
        elif auth_token:
            auth_token = SHA256.new(auth_token).hexdigest()
            if self.request.get('logg_ut') == 'true':
                ndb.delete_multi_async(Otp.query(ndb.OR(Otp.token==auth_token, Otp.valid_until<datetime.datetime.now())).fetch(options=ndb.QueryOptions(keys_only=True)))
                self.response.delete_cookie('auth_token')
                self.redirect('/prioriter')
            else:
                otp = Otp.query(ndb.AND(Otp.token==auth_token, Otp.valid_until>datetime.datetime.now())).get()
                if otp:
                    self.__scope = TravelGrantsApplication.query(TravelGrantsApplication.learning_association == otp.learning_association)
                    otp.put() # Refresh expiration

        super(PrioritizeHandler, self).dispatch()

    def get(self):
        if self.__scope:
            prioritized_grants_applications = self.__scope.filter(TravelGrantsApplication.priority > 0).order(TravelGrantsApplication.priority).fetch()
            grants_applications = self.__scope.filter(TravelGrantsApplication.priority < 1).order(TravelGrantsApplication.priority, TravelGrantsApplication.sent_at).fetch()

            template_values = {
                'application_year': APPLICATION_YEAR,
                'grants_applications': grants_applications,
                'prioritized_grants_applications': prioritized_grants_applications
            }

            template = JINJA_ENVIRONMENT.get_template('prioritize.html')
            self.response.write(template.render(template_values))
        else:
            template_values = {
                'application_year': APPLICATION_YEAR,
                'learning_associations': LearningAssociation.query().order(LearningAssociation.name).fetch(50)
            }

            template = JINJA_ENVIRONMENT.get_template('login.html')
            self.response.write(template.render(template_values))


    def post(self):
        item = self.__scope.filter(TravelGrantsApplication.key==ndb.Key(urlsafe=self.request.POST.get('grants_application'))).get()
        if item:
            item.priority = int(self.request.POST.get('priority'))
            item.put()
            time.sleep(0.3)
            self.redirect('/prioriter')
        else:
            self.abort(403)

class OtpHandler(webapp2.RequestHandler):
    def post(self):
        otp = Otp()
        otp_token = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(30))
        logging.info(otp_token)
        otp.token = SHA256.new(otp_token).hexdigest()
        otp.learning_association = ndb.Key(urlsafe=self.request.POST.get('sf'))
        learning_association = otp.learning_association.get()
        if learning_association:
            otp.put()
            mail.send_mail(sender="Voksenopplæringsforbundet <vofo@vofo.no>",
            to="%s <%s>" % (learning_association.name, learning_association.email),
            subject="Engangspassord til reisestipendsøknader",
            body="""
Hei

For å logge inn til reisestipendsøknadene, bruk denne lenken:

https://???/otp/%s

Lenken er gyldig i en time.

Hilsen Voksenopplæringsforbundet
""" % (otp_token))

            template_values = {
                'application_year': APPLICATION_YEAR,
                'learning_association': learning_association
            }

            template = JINJA_ENVIRONMENT.get_template('login_sent.html')
            self.response.write(template.render(template_values))

        else:
            self.abort(400)

    def get(self, token):
        self.response.set_cookie('auth_token', token, expires=datetime.datetime.now() + datetime.timedelta(hours=6)) #TODO: Secure
        self.redirect('/prioriter')


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/admin', AdminHandler),
    ('/prioriter', PrioritizeHandler),
    ('/otp', OtpHandler),
    (r'/otp/(.+)', OtpHandler)
], debug=True)
