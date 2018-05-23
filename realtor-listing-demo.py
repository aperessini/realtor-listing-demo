# Aaron Peressini
# steinaua@oregonstate.edu

from google.appengine.ext import ndb
import webapp2
import json
import urlparse
import logging
import sys
import datetime
from datetime import date
import random
from google.appengine.api import users
from webapp2_extras import jinja2

class Listing(ndb.Model):
    listing_id = ndb.StringProperty()
    mls_num = ndb.IntegerProperty()
    street1 = ndb.StringProperty(required=True)
    street2 = ndb.StringProperty(default=None)
    city = ndb.StringProperty(required=True) 
    state = ndb.StringProperty(required=True)
    zipcode = ndb.StringProperty(required=True)
    neighborhood = ndb.StringProperty(default=None)
    sales_price = ndb.StringProperty(required=True)
    date_listed = ndb.DateProperty()
    bedrooms = ndb.IntegerProperty(required=True)
    bathrooms = ndb.IntegerProperty(required=True)
    garage_size = ndb.IntegerProperty(required=True)
    sq_ft = ndb.IntegerProperty(required=True)
    lot_size = ndb.IntegerProperty(required=True)
    description = ndb.StringProperty()
    photos = ndb.BlobProperty(repeated=True)
    listing_author = ndb.StringProperty(required=True) #User's userid

class BaseHandler(webapp2.RequestHandler):
    @webapp2.cached_property
    def jinja2(self):
        # Returns a Jinja2 renderer cached in the app registry.
        return jinja2.get_jinja2(app=self.app)

    def render_response(self, _template, **context):
        # Renders a template and writes the result to the response.
        rv = self.jinja2.render_template(_template, **context)
        self.response.write(rv)

class ListingHandler(BaseHandler):

    def get(self, id=None):

        if id:
            listing = ndb.Key(urlsafe=id).get()            
            listing_dict = listing.to_dict()
            listing_dict['date_listed'] = json.dumps(listing_dict['date_listed'], default=str)
            listing_dict['self'] = "/listings/" + id
            sys.stdout.write(str(listing_dict))
            content = listing_dict
            self.render_response('listing.html', listing=content)
    
        else:
            query = Listing.query()
            listings = query.fetch()
            listings = sorted(listings, key=lambda listing: listing.date_listed)
            listing_list = []
            for listing in listings:
                listing_dict = listing.to_dict()
                listing_dict['date_listed'] = json.dumps(listing_dict['date_listed'], default=str)
                listing_dict['self'] = "/listings/" + str(listing.listing_id)
                listing_list.append(listing_dict)
            listings = {}
            for listing in listing_list:
                mls_num = str(listing.pop('mls_num'))
                listings[mls_num] = listing
                #sys.stdout.write(str(listing))
            #listings = map(json.dumps, listing_list)
            #content = json.dumps(listings)
            #sys.stdout.write(str(listings))
            self.render_response('listings.html', listings=listings)
    

    def post(self):
        user = users.get_current_user()
        sys.stdout.flush()
        sys.stdout.write(str(self.request.POST['street2']))
        listing_data = json.loads(json.dumps(urlparse.parse_qs(self.request.body)))
        query = Listing.query().filter(ndb.AND(Listing.street1 == listing_data['street1'][0],
                                     Listing.city == listing_data['city'][0],
                                     Listing.state == listing_data['state'][0]))
        new_list = list(query.fetch())
        if(len(new_list) > 0):
            self.response.write(str(new_list))
            self.response.write('Listing already exists for that home.')
        else:        
            sys.stdout.write(str(listing_data))
            if str(listing_data['street2'][0]) == 'none':
                listing_data['street2'][0] = ''

            if 'photos' not in listing_data:
                listing_data['photos'] = []

            month, day, year = map(int, listing_data['date_listed'][0].split("/"))
            listing_data['date_listed'][0] = date(year, month, day)
            
            new_listing = Listing(street1=str(listing_data['street1'][0]), street2=str(listing_data['street2'][0]),
                city=str(listing_data['city'][0]), state=str(listing_data['state'][0]), zipcode=str(listing_data['zipcode'][0]),
                neighborhood=str(listing_data['neighborhood'][0]), sales_price=str(listing_data['sales_price'][0]), photos=[], date_listed=listing_data['date_listed'][0],
                bedrooms=int(listing_data['bedrooms'][0]), bathrooms=int(listing_data['bathrooms'][0]), garage_size=int(listing_data['garage_size'][0]),
                sq_ft=int(listing_data['sq_ft'][0]), lot_size=int(listing_data['lot_size'][0]), description=str(listing_data['description'][0]), listing_author=user.user_id())

            num = random.randint(1000, 999999)    
            query = Listing.query(Listing.mls_num == num)
            listing_list = list(query.fetch())
            while(len(listing_list) > 0):
                num = random.randomint(1000, 999999)    
                query = Listing.query(Listing.mls_num == num)
                listing_list = list(query.fetch())

            new_listing.mls_num = num
            listing_key = new_listing.put()
            new_listing = listing_key.get()
            new_listing.listing_id = new_listing.key.urlsafe()
            sys.stdout.write(new_listing.listing_id)
            new_listing.put()
            listing_dict = new_listing.to_dict()
            listing_dict['self'] = '/listings/' + new_listing.listing_id
            #content = json.dumps(listing_dict)
            self.redirect('/listings?')

class HomePageHandler(BaseHandler):

    def get(self):
        user = users.get_current_user()
        if user:
            nickname = user.nickname()
            logout_url = users.create_logout_url('/')
            greeting = 'Welcome, {}! (<a href="{}">sign out</a>)'.format(
                nickname, logout_url)
            self.response.write(greeting)
            content = {}
            self.render_response('home.html', **content)
        else:
            login_url = users.create_login_url('/')
            greeting = '<a href="{}">Sign in</a>'.format(login_url)
            self.response.write(greeting)
    
        
allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods
app = webapp2.WSGIApplication([
    ('/', HomePageHandler),
    ('/listings', ListingHandler),
    ('/listings/(.*)', ListingHandler),
], debug=True)



