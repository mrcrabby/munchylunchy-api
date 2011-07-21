import hashlib
import json
import urllib
import urllib2

from tornado.web import HTTPError

from apihandler import APIHandler
from settings import SECRET


class AuthBrowserID(APIHandler):

    def wrap_post(self):
        assertion = self.get_argument("assertion")
        verification_url = "https://browserid.org/verify?%s"
        verification_url %= urllib.urlencode(assertion=assertion,
                                             audience="munchylunchy.com")

        response = json.loads(urllib2.urlopen(verification_url).read())
        if response["status"] == "okay":
            token = hashlib.sha256("".join([response["valid-until"],
                                            SECRET,
                                            response["email"]])).hexdigest()
            self.redis.set(response["email"], token)

            return {"result": "okay",
                    "email": response["email"],
                    "token": token}

        else:
            raise HTTPError(403)


class AuthToken(APIHandler):

    def wrap_post(self):
        assertion = self.get_argument("token")
        token = self.redis.get(response["email"])
        if token:
            return {"result": "okay"}
        else:
            return {"result": "fail"}

