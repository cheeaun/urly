#!/usr/bin/env python
#
# Copyright 2008 Adam Stiles
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy 
# of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required 
# by applicable law or agreed to in writing, software distributed under the 
# License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS 
# OF ANY KIND, either express or implied. See the License for the specific 
# language governing permissions and limitations under the License.
#

"""A url-shortener built on Google App Engine."""
__author__ = 'Adam Stiles'

""" 
All Urly records in the database have an id and an url. We base32 that
integer id to create a short code that represents that Urly.

/{code}                             Redirect user to urly with this code
/{code}(.json|.xml|.html)           Show user formatted urly with this code
/new(.json|.xml|.html)?url={url}  Create a new urly with this url or
                                    return existing one if it already exists
                                    Note special handling for 'new' code
                                    when we have a url GET parameter 'cause
                                    'new' by itself looks like a code
"""
import wsgiref.handlers
import re, os, logging
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import users
from urly import Urly
from view import MainView

class MainHandler(webapp.RequestHandler):
    """All non-static requests go through this handler.
    The code and format parameters are pre-populated by
    our routing regex... see main() below.
    """
    def get(self, code, format):
        if (code is None):
            MainView.render(self, 200, None, format)
            user = users.get_current_user()
            if user: self.response.out.write("<a href=\"" + users.create_logout_url('/') + "\">Logout</a>")
            return
        
        u = Urly.find_by_code(str(code))
        if u is not None:
            MainView.render(self, 200, u, format, preview=True)
        else:
            MainView.render(self, 404, None, format)

class ShortenHandler(webapp.RequestHandler):
    def get(self, format):
        url = self.request.get('url').strip()
        if url is not None:
            try:
                valid = Urly.validate_url(url)
                if valid:
                    u = Urly.find_or_create_by_url(url)
                    if u is not None:
                        MainView.render(self, 200, u, format)
                    else:
                        logging.error("Error creating urly by url: %s", str(url))
                        MainView.render(self, 400, None, format, url)
                else:
                    logging.error("Error creating urly by url: %s", str(url))
                    MainView.render(self, 400, None, format, url)
            except db.BadValueError:
                # url parameter is bad
                MainView.render(self, 400, None, format, url)
        else:
            self.redirect('/')
        
class AdminHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            if users.is_current_user_admin():
                values = {
                    
                }
                path = os.path.join(os.path.dirname(__file__), 'admin.html')
                self.response.out.write(template.render(path, values))
            else:
                self.redirect('/')
        else:
            self.redirect(users.create_login_url('/admin'))

def main():
    application = webapp.WSGIApplication([
        ('/([a-hjkmnp-tvz0-9]+)?(.xml|.json|.html)?', MainHandler),
        ('/shorten(.xml|.json|.html)', ShortenHandler),
        ('/admin?', AdminHandler)
    ], debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()
