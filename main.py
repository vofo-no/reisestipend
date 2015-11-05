#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

reload(sys)
sys.setdefaultencoding('utf8')

import webapp2

from myapp.views import *

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/admin', AdminHandler),
    ('/prioriter', PrioritizeHandler),
    ('/otp', OtpHandler),
    (r'/otp/(.+)', OtpHandler)
], debug=True)
