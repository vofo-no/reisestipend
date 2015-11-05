#!/usr/bin/env python

import datetime
import myapp

from google.appengine.ext import ndb

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
    application_year = ndb.IntegerProperty(required=True, default=myapp.APPLICATION_YEAR)
    priority =      ndb.IntegerProperty(choices=range(11))
    remark =        ndb.TextProperty()
    learning_association_name = ndb.ComputedProperty(lambda self: self.learning_association.get().name)

class Otp(ndb.Model):
    """Model for storing OTP tokens."""
    learning_association = ndb.KeyProperty(kind=LearningAssociation)
    token = ndb.StringProperty()
    is_signed_in = ndb.BooleanProperty(default=False)
    valid_from = ndb.DateTimeProperty(auto_now=True)
    valid_until = ndb.ComputedProperty(lambda self: self.valid_from + datetime.timedelta(minutes=62))
