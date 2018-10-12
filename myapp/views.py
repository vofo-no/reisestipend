#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

reload(sys)
sys.setdefaultencoding('utf8')

import os
import time
import datetime
import string
import random
import re

from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

from Crypto.Hash import SHA256

import myapp
from models import *

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/../templates/'),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class MainHandler(webapp2.RequestHandler):
    __locked = True
    __grace_locked = True

    def dispatch(self):
        self.__locked = myapp.time_locked(11, 20, 5)
        self.__grace_locked = myapp.time_locked(11, 20, 7)
        super(MainHandler, self).dispatch()

    def render_form(self, grants_application, errors={}):
        learning_associations = LearningAssociation.query().order(LearningAssociation.name).fetch(50)

        while (len(grants_application.previous_grants) < 3):
            grants_application.previous_grants.append(PreviousGrants())

        while (len(grants_application.other_grants) < 3):
            grants_application.other_grants.append(OtherGrants())

        template_values = {
            'application_year': myapp.APPLICATION_YEAR,
            'learning_associations': learning_associations,
            'grants_application': grants_application,
            'errors': errors,
            'is_locked': self.__locked
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
        if self.__grace_locked:
            self.abort(403)
        else:
            grants_application = TravelGrantsApplication(parent=ndb.Key('Year', myapp.APPLICATION_YEAR))
            errors = {}

            for item in ['name', 'address', 'postal_code', 'postal_city', 'phone', 'email', 'organization', 'location', 'time_span', 'expenses', 'purpose', 'study_program']:
                setattr(grants_application, item, self.request.POST.get(item))
                if not getattr(grants_application, item):
                    errors[item] = 'missing'
                elif item == 'email':
                    if not re.match(r"[^@]+@[^@]+\.[^@]+", grants_application.email):
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

                application_text = myapp.application_text(grants_application)
                mail.send_mail(sender="Voksenopplæringsforbundet <mg@vofo.no>",
                               to="%s <%s>" % (learning_association.name, learning_association.email),
                               subject="Reisestipendsøknad fra %s" % (grants_application.name),
                               body="""
Hei

Det har kommet en ny søknad om reisestipend til deres studieforbund.

Søknaden er fra %s (%s) og gjelder studiereise til %s i tidsrommet %s.

Gå til %sprioriter for å lese og prioritere søknader fra deres studieforbund.

Husk at fristen for å prioritere søknader er 30. november.

--
Hilsen Voksenopplæringsforbundet
""" % (grants_application.name,
       grants_application.organization,
       grants_application.location,
       grants_application.time_span,
       myapp.APPLICATION_URL))

                mail.send_mail(sender="Voksenopplæringsforbundet <mg@vofo.no>",
                               to="%s <%s>" % (grants_application.name, grants_application.email),
                               subject="Reisestipendsøknad til %s" % (learning_association.name),
                               body="""
Hei %s

Du har sendt søknad om reisestipend til %s.

%s

Ta kontakt med studieforbundet på %s hvis du har spørsmål.

--
Hilsen Voksenopplæringsforbundet
""" % (grants_application.name, grants_application.learning_association_name, application_text, learning_association.email))

                template_values = {
                    'application_year': myapp.APPLICATION_YEAR,
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
            'application_year': myapp.APPLICATION_YEAR,
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


def get_otp_by_token(token, fresh=False):
    q = Otp.query(ndb.AND(Otp.token == token, Otp.valid_until > datetime.datetime.now()))
    if fresh:
        q = q.filter(Otp.is_signed_in == False)
    return q.get()

class PrioritizeHandler(webapp2.RequestHandler):
    __scope = None
    __locked = True

    def dispatch(self):
        self.__scope = None
        auth_token = self.request.cookies.get('auth_token')
        if users.is_current_user_admin():
            self.__locked = False
            if self.request.get('logg_ut') == 'true':
                self.redirect(users.create_logout_url('/prioriter'))
            else:
                self.__scope = TravelGrantsApplication.query(TravelGrantsApplication.application_year == myapp.APPLICATION_YEAR)
        elif auth_token:
            self.__locked = myapp.time_locked(12, 1, 5)
            auth_token = SHA256.new(auth_token).hexdigest()
            if self.request.get('logg_ut') == 'true':
                ndb.delete_multi_async(Otp.query(ndb.OR(Otp.token==auth_token, Otp.valid_until<datetime.datetime.now())).fetch(options=ndb.QueryOptions(keys_only=True)))
                self.response.delete_cookie('auth_token')
                self.redirect('/prioriter')
            else:
                otp = get_otp_by_token(auth_token)
                if otp:
                    self.__scope = TravelGrantsApplication.query(ndb.AND(TravelGrantsApplication.learning_association == otp.learning_association, TravelGrantsApplication.application_year == myapp.APPLICATION_YEAR))
                    otp.put() # Refresh expiration

        super(PrioritizeHandler, self).dispatch()

    def get(self):
        if self.__scope:
            prioritized_grants_applications = self.__scope.filter(TravelGrantsApplication.priority > 0).order(TravelGrantsApplication.priority).fetch()
            grants_applications = self.__scope.filter(TravelGrantsApplication.priority < 1).order(TravelGrantsApplication.priority, TravelGrantsApplication.sent_at).fetch()

            template_values = {
                'application_year': myapp.APPLICATION_YEAR,
                'grants_applications': grants_applications,
                'prioritized_grants_applications': prioritized_grants_applications,
                'TZONE': myapp.TZONE,
                'UTC': myapp.UTC,
                'is_admin': users.is_current_user_admin(),
                'is_locked': self.__locked
            }

            if self.request.get('print') == 'true':
                template = JINJA_ENVIRONMENT.get_template('prints.html')
            else:
                template = JINJA_ENVIRONMENT.get_template('prioritize.html')

            self.response.write(template.render(template_values))
        else:
            template_values = {
                'application_year': myapp.APPLICATION_YEAR,
                'learning_associations': LearningAssociation.query().order(LearningAssociation.name).fetch(50)
            }

            template = JINJA_ENVIRONMENT.get_template('login.html')
            self.response.write(template.render(template_values))


    def post(self):
        if self.__locked:
            self.abort(403)
        else:
            item = self.__scope.filter(TravelGrantsApplication.key==ndb.Key(urlsafe=self.request.POST.get('grants_application'))).get()
            if item:
                if self.request.POST.get('priority').isdigit():
                    item.priority = int(self.request.POST.get('priority'))
                elif self.request.POST.get('priority') == 'nil':
                    del item.priority
                else:
                    self.abort(400)
                item.put()
                time.sleep(0.3)
                self.redirect('/prioriter')
            else:
                self.abort(403)

class OtpHandler(webapp2.RequestHandler):
    def post(self):
        otp = Otp()
        otp.learning_association = ndb.Key(urlsafe=self.request.POST.get('sf'))
        otp_token = SHA256.new(str(otp.learning_association.id()) + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(30))).hexdigest()
        otp.token = SHA256.new(otp_token).hexdigest()
        learning_association = otp.learning_association.get()
        if learning_association:
            otp.put()
            mail.send_mail(sender="Voksenopplæringsforbundet <mg@vofo.no>",
            to="%s <%s>" % (learning_association.name, learning_association.email),
            subject="Engangspassord til reisestipendsøknader",
            body="""
Hei

For å logge inn til reisestipendsøknadene, bruk denne lenken:

%sotp/%s

Lenken er gyldig i en time.

Hilsen Voksenopplæringsforbundet
""" % (myapp.APPLICATION_URL, otp_token))

            template_values = {
                'application_year': myapp.APPLICATION_YEAR,
                'learning_association': learning_association
            }

            template = JINJA_ENVIRONMENT.get_template('login_sent.html')
            self.response.write(template.render(template_values))

        else:
            self.abort(400)

    def get(self, token):
        auth_token = SHA256.new(token).hexdigest()
        otp = get_otp_by_token(auth_token, fresh=True)
        if otp:
            otp.is_signed_in = True
            otp.put()
            self.response.set_cookie('auth_token', token, expires=datetime.datetime.now() + datetime.timedelta(hours=6), secure=True)
            self.redirect('/prioriter')
        else:
            template_values = {
                'application_year': myapp.APPLICATION_YEAR
            }

            template = JINJA_ENVIRONMENT.get_template('login_failed.html')
            self.response.write(template.render(template_values))
