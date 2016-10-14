#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from dateutil import tz

APPLICATION_YEAR = 2017
APPLICATION_URL = "https://www.voforeisestipend.no/"
TZONE = tz.gettz('Europe/Oslo')
UTC = tz.gettz('UTC')

def enum_to_list(items, target_string, props):
    outlist = []
    if len(items) > 0:
        for item in items:
            outlist.append(target_string % (getattr(item, props[0]), getattr(item, props[1])))
    else:
        outlist.append("[ingen]")
    return outlist

def time_locked(month, day, hour):
    return datetime.datetime.now() > datetime.datetime(APPLICATION_YEAR-1, month, day, hour)

def application_text(grants_application):
    previous_grants_text = enum_to_list(grants_application.previous_grants, "- %s, sted (land): %s", ['year', 'location'])
    other_grants_text = enum_to_list(grants_application.other_grants, "- %s, beløp: %s", ['provider', 'amount'])

    return """
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
""" % (grants_application.name,
       grants_application.address,
       grants_application.postal_code,
       grants_application.postal_city,
       grants_application.phone,
       grants_application.email,
       grants_application.organization,
       grants_application.learning_association_name,
       "\n".join(previous_grants_text),
       grants_application.location,
       grants_application.time_span,
       grants_application.expenses,
       grants_application.purpose,
       grants_application.study_program,
       "\n".join(other_grants_text),
       grants_application.sent_at.replace(tzinfo=UTC).astimezone(TZONE).strftime("%d.%m.%y %H:%M"))
