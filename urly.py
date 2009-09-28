# Copyright 2008 Adam Stiles
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy 
# of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required 
# by applicable law or agreed to in writing, software distributed under the 
# License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS 
# OF ANY KIND, either express or implied. See the License for the specific 
# language governing permissions and limitations under the License.

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import urlfetch
import logging, re

class Urly(db.Model):
    """Our one-and-only model"""  
    url = db.LinkProperty(required=True)
    created_at = db.DateTimeProperty(auto_now_add=True)
    ip_address = db.StringProperty()
    clicks = db.IntegerProperty(default=0)

    # Crockford's Base 32 http://www.crockford.com/wrmg/base32.html
    KEY_BASE = "0123456789abcdefghjkmnpqrstvwxyz"
    BASE = 32

    def code(self):
        """Return our code, our base-32 encoded id"""
        if not self.is_saved():
            return None
        nid = self.key().id()
        s = []
        while nid:
            nid, c = divmod(nid, Urly.BASE)
            s.append(Urly.KEY_BASE[c])
        s.reverse()
        return "".join(s)
        
    def to_json(self):
        """JSON is so simple that we won't worry about a template at this point"""
        return "{\"code\":\"%s\", \"url\":\"%s\", \"ok\":%s, \"status_code\":%d}\n" % (self.code(), self.url, "true", 200);
    
    def to_xml(self):
        """Like JSON, XML is simple enough that we won't template now"""
        msg = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        msg += "<urly code=\"%s\" url=\"%s\" ok=\"%s\" status_code=\"%d\" />\n" % (self.code(), self.url, "true", 200)
        return msg

    def save_in_cache(self):
        """We don't really care if this fails"""
        memcache.set(self.code(), self.key().id())
    
    @staticmethod
    def find_or_create_by_url(url):
        query = db.Query(Urly)
        query.filter('url =', url)
        u = query.get()
        if not u:
            u = Urly(url=url)
            u.put()
            u.save_in_cache()
        return u

    @staticmethod
    def code_to_id(code):
        aid = 0L
        for c in code:
            aid *= Urly.BASE 
            aid += Urly.KEY_BASE.index(c)
        return aid
    
    @staticmethod
    def find_by_code(code):
        try:
            aid = memcache.get(code)
        except:
            # http://code.google.com/p/googleappengine/issues/detail?id=417
            logging.error("Urly.find_by_code() memcached error")
        
        if aid is not None:
            logging.info("Urly.find_by_code() cache HIT: %s", str(code))
        else:
            logging.info("Urly.find_by_code() cache MISS: %s", str(code))
            aid = Urly.code_to_id(code)
        
        try:
            u = Urly.get_by_id(int(aid))
            if u is not None:
                u.save_in_cache()
            return u
        except db.BadValueError:
            return None
        except db.BadKeyError:
            return None
            
    @staticmethod
    def validate_url(url):
        """Validate the URL?"""
        exp = re.compile('^https?://.+')
        match = exp.match(url)
        if match:
            try:
                result = urlfetch.fetch(url, method="HEAD")
                if result.status_code == 405:
                    logging.info("The URL returns 405, no HEAD request")
                    result = urlfetch.fetch(url, allow_truncated=True)
                if result.status_code == 200: return True
            except urlfetch.Error:
                logging.error("The URL doesn't exist")
        return False