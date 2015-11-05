#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dateutil import tz

APPLICATION_YEAR = 2016
APPLICATION_URL = "https://reisestipend-1117.appspot.com/"
TZONE = tz.gettz('Europe/Oslo')
UTC = tz.gettz('UTC')

def application_text(grants_application):
    previous_grants_text = []
    if len(grants_application.previous_grants) > 0:
        for item in grants_application.previous_grants:
            previous_grants_text.append("- %s, sted (land): %s" % (item.year, item.location))
    else:
        previous_grants_text.append("[ingen]")

    other_grants_text = []
    if len(grants_application.other_grants) > 0:
        for item in grants_application.other_grants:
            other_grants_text.append("- %s, beløp: %s" % (item.provider, item.amount))
    else:
        other_grants_text.append("[ingen]")

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
