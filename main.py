#!/usr/bin/env python
import os

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class LearningAssociation(ndb.Model):
    """Main model for representing learning associations."""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    active = ndb.BooleanProperty(required=True, default=False)

class Address(ndb.Model):
    """Sub model for address."""
    street = ndb.StringProperty()
    postal_code = ndb.StringProperty()
    postal_city = ndb.StringProperty()

class PreviousGrants(ndb.Model):
    """Sub model for previous grants."""
    year = ndb.StringProperty(required=True)
    location = ndb.StringProperty(required=True)

class OtherGrants(ndb.Model):
    """Sub model for other grants applications."""
    provider = ndb.StringProperty(required=True)
    ammount = ndb.FloatProperty(required=True)

class TravelGrantsApplication(ndb.Model):
    """Main model for representing a travel grants application."""
    name =          ndb.StringProperty(required=True)
    address =       ndb.StructuredProperty(Address, required=True)
    phone_number =  ndb.StringProperty(required=True)
    email =         ndb.StringProperty(required=True)
    organization =  ndb.StringProperty(required=True)
    previous_grants = ndb.StructuredProperty(PreviousGrants, repeated=True)
    location =      ndb.StringProperty(required=True)
    time_span =     ndb.StringProperty(required=True)
    expenses =      ndb.FloatProperty(required=True)
    other_grants =  ndb.StructuredProperty(OtherGrants, repeated=True)
    purpose =       ndb.StringProperty(required=True)
    study_program = ndb.StringProperty(required=True)
    sent_at =       ndb.DateTimeProperty(required=True)

class MainHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {}

        template = JINJA_ENVIRONMENT.get_template('application_form.html')
        self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)
