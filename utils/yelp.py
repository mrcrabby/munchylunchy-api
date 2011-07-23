import json
import oauth2
import urllib
import urllib2

from tornado.httpclient import AsyncHTTPClient

import settings


AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")

def request(url_params, endpoint, callback):
    """Returns response for API request."""

    # Unsigned URL
    encoded_params = ''
    if url_params:
        encoded_params = urllib.urlencode(url_params)
    host = "api.yelp.com"
    url = 'http://%s%s?%s' % (host, endpoint, encoded_params)

    # Sign the URL
    consumer = oauth2.Consumer(settings.YELP_CONSUMER_KEY,
                               settings.YELP_CONSUMER_SECRET)
    oauth_request = oauth2.Request('GET', url, {})
    oauth_request.update({'oauth_nonce': oauth2.generate_nonce(),
                          'oauth_timestamp': oauth2.generate_timestamp(),
                          'oauth_token': settings.YELP_TOKEN,
                          'oauth_consumer_key': settings.YELP_CONSUMER_KEY})

    token = oauth2.Token(settings.YELP_TOKEN, settings.YELP_TOKEN_SECRET)
    oauth_request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer,
                               token)
    # Nobody likes unicode in their URL.
    signed_url = str(oauth_request.to_url())

    # Connect
    def wrap_callback(response):
        if response.error:
            print "Yelp API error: %s" % response.error
            print response.body
        else:
            callback(json.loads(response.body))

    client = AsyncHTTPClient()
    client.fetch(signed_url, wrap_callback)


def search(callback, latitude, longitude, categories=None, radius=3,
           limit=20, offset=0):
    """
    Search Yelp for restaurants near a set of geocoords.

    Notes:
    - Radius:
        Units: Miles
        Max: 24
    """

    params = {"term": "food",
              "ll": "%s,%s" % (latitude, longitude),
              "limit": limit,
              "sort": 1,
              "radius_filter": radius * 1609,
              "offset": offset}

    if categories is not None:
        params["category_filter"] = ",".join(categories)

    request(params, "/v2/search", callback)


def business_data(callback, id_):
    """Get the business listing for a Yelp business."""
    request({}, "/v2/business/%s" % id_, callback)

def parse_rating(url):
    """Get the rating from the rating image url."""

    ratings = {"stars_5": 5,
               "stars_4_half": 4.5,
               "stars_4": 4,
               "stars_3_half": 3.5,
               "stars_3": 3,
               "stars_2_half": 2.5,
               "stars_2": 2,
               "stars_1_half": 1.5,
               "stars_1": 1}

    for rating in ratings:
        if "%s." % rating in url:
            return ratings[rating]

    return 0

