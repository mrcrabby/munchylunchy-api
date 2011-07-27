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
        verification_url %= urllib.urlencode({"assertion": assertion,
                                              "audience": "munchylunchy.com"})

        response = json.loads(urllib2.urlopen(verification_url).read())
        if response["status"] == "okay":
            token = hashlib.sha256("".join([str(response["valid-until"]),
                                            SECRET,
                                            response["email"]])).hexdigest()
            user_key = "users::%s" % response["email"]
            self.redis.set(user_key, token)
            self.redis.expireat(user_key, int(response["valid-until"] / 1000))

            return {"result": "okay",
                    "email": response["email"],
                    "token": token}

        else:
            print response
            raise HTTPError(403)


class AuthToken(APIHandler):

    def wrap_post(self):
        assertion = self.get_argument("token")
        token = self.redis.get(response["email"])
        if token:
            return {"result": "okay"}
        else:
            return {"result": "fail"}

