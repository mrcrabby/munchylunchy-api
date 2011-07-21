import json
import oauth2
import urllib
import urllib2

import settings


def request(url_params):
    """Returns response for API request."""

    # Unsigned URL
    encoded_params = ''
    if url_params:
        encoded_params = urllib.urlencode(url_params)
    host = "api.yelp.com"
    path = "/v2/search"
    url = 'http://%s%s?%s' % (host, path, encoded_params)
    # Sign the URL
    consumer = oauth2.Consumer(settings.YELP_CONSUMER_KEY,
                               settings.YELP_COMSUMER_SECRET)
    oauth_request = oauth2.Request('GET', url, {})
    oauth_request.update({'oauth_nonce': oauth2.generate_nonce(),
                          'oauth_timestamp': oauth2.generate_timestamp(),
                          'oauth_token': settings.YELP_TOKEN,
                          'oauth_consumer_key': settings.YELP_CONSUMER_KEY})

    token = oauth2.Token(token, settings.YELP_TOKEN_SECRET)
    oauth_request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer,
                               settings.YELP_TOKEN)
    signed_url = oauth_request.to_url()

    # Connect
    try:
        conn = urllib2.urlopen(signed_url, None)
        try:
            response = json.loads(conn.read())
        finally:
            conn.close()
    except urllib2.HTTPError, error:
        response = json.loads(error.read())

    return response


def search(latitude, longitude, categories=None, radius=3, limit=100):
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
              "radius_filter": radius * 1609}

    if categories is not None:
        params["category_filter"] = ",".join(categories)

    return request(params)

