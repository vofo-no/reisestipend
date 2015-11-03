#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

reload(sys)
sys.setdefaultencoding('utf8')

import os
import logging

from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import ndb
from datetime import datetime

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

APPLICATION_YEAR = 2016

def admin_required(handler):
    if users.is_current_user_admin():
        return True
    else:
        if users.get_current_user():
            handler.abort(403)
        else:
            handler.redirect(users.create_login_url(handler.request.uri))
        return False

class LearningAssociation(ndb.Model):
    """Main model for representing learning associations."""
    name = ndb.StringProperty(required=True, default="")
    email = ndb.StringProperty(required=True, default="")
    active = ndb.BooleanProperty(required=True, default=True)

class PreviousGrants(ndb.Model):
    """Sub model for previous grants."""
    year = ndb.StringProperty('y', required=True)
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
    previous_grants = ndb.StructuredProperty(PreviousGrants, repeated=True)
    location =      ndb.StringProperty(required=True, default="")
    time_span =     ndb.StringProperty(required=True, default="")
    expenses =      ndb.StringProperty(required=True, default="")
    other_grants =  ndb.StructuredProperty(OtherGrants, repeated=True)
    purpose =       ndb.TextProperty(required=True, default="")
    study_program = ndb.TextProperty(required=True, default="")
    sent_at =       ndb.DateTimeProperty(required=True)
    application_year = ndb.IntegerProperty(required=True, default=APPLICATION_YEAR)
    priority =      ndb.IntegerProperty(choices=range(1,10))
    remark =        ndb.TextProperty()

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

    def get(self):
        grants_application = TravelGrantsApplication()

        self.render_form(grants_application)

    def post(self):
        grants_application = TravelGrantsApplication(parent=ndb.Key('Year', APPLICATION_YEAR))
        errors = {}

        for item in ['name', 'address', 'postal_code', 'postal_city', 'phone', 'email', 'organization', 'learning_association', 'location', 'time_span', 'expenses', 'purpose', 'study_program']:
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

        for i, item in enumerate(self.request.POST.getall('previous_grants_year')):
            previous_grants = PreviousGrants()
            previous_grants.year = item
            previous_grants.location = self.request.POST.getall('previous_grants_location')[i]
            grants_application.previous_grants.append(previous_grants)

        for i, item in enumerate(self.request.POST.getall('other_grants_provider')):
            other_grants = OtherGrants()
            other_grants.provider = item
            other_grants.amount = self.request.POST.getall('other_grants_amount')[i]
            grants_application.other_grants.append(other_grants)

        if (len(errors) > 0):
            self.render_form(grants_application, errors)
        else:
            grants_application.sent_at = datetime.now()
            grants_application.put()

            previous_grants_text = []
            if len(grants_application.previous_grants) > 0:
                for item in grants_application.previous_grants:
                    previous_grants_text.append("- År: %s\n- Sted (land): %s\n" % (item.year, item.location))
            else:
                previous_grants_text.append = "[ingen]"

            other_grants_text = []
            if len(grants_application.other_grants) > 0:
                for item in grants_application.other_grants:
                    other_grants_text.append("- Fra: %s\n- Beløp: %s\n" % (item.provider, item.amount))
            else:
                other_grants_text.append = "[ingen]"

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
    def get(self):
        if admin_required(self):
            if self.request.get('sf'):
                is_new = self.request.get('sf') == 'new'
                sf_id = self.request.get('sf').isdigit() and int(self.request.get('sf')) or self.request.get('sf')
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
        if admin_required(self) and self.request.get('sf'):
            is_new = self.request.get('sf') == 'new'
            sf_id = self.request.get('sf').isdigit() and int(self.request.get('sf')) or self.request.get('sf')
            learning_association = is_new and LearningAssociation() or LearningAssociation.get_by_id(sf_id)
            if learning_association:
                learning_association.name = self.request.get('name')
                learning_association.email = self.request.get('email')
                learning_association.active = self.request.get('active') == 'true'
                learning_association.put()
        self.redirect('/admin')


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/admin', AdminHandler)
], debug=True)
