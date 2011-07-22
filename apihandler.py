import json

import redis
import tornado.web as web

import settings
import utils.dict2xml as dict2xml


RESPONSE_TYPE = ("json", "xml", )

def require_user(func):
    def wrap(self, *args, **kwargs):
        email = self.get_attribute("email")
        token = self.get_attribute("token")
        if token != self.redis.get(email):
            raise web.HTTPError(403)

        self.email = email
        self.token = token

        return func(self, *args, **kwargs)
    return wrap


class APIHandler(web.RequestHandler):
    """A class to make handling API requests super amazing."""

    def initialize(self):
        self.redis = redis.Redis(host=settings.REDIS_HOST,
                                 port=6379,
                                 db=settings.REDIS_DB,
                                 password=settings.REDIS_AUTH)

    def get(self, *args, **kwargs):
        return self.wrap_request(self.wrap_get, *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.wrap_request(self.wrap_post, *args, **kwargs)

    def wrap_request(self, wrapper, *args, **kwargs):
        output = wrapper(*args, **kwargs)
        self._format_output(output)

    def _format_output(self, output):
        response_type = "json"
        if self.get_argument("type", default="json") in RESPONSE_TYPE:
            response_type = self.get_argument("type", default="json")

        if response_type == "json":
            output = json.dumps(output)

            if self.get_argument("callback", default="").isalnum():
                callback = self.get_argument("callback")
                output = "%s(%s);" % (callback, output)
                self.set_header("Content-Type", "application/javascript")
            else:
                self.set_header("Content-Type", "application/json")

            self.write(output)

        elif response_type == "xml":
            self.set_header("Content-Type", "text/xml")
            self.write('<?xml version="1.0"?><api>')
            self.write(dict2xml.convert_dict_to_xml(output))
            self.write('</api>')


    def wrap_get(self, *args, **kwargs):
        # By default, no endpoint already exists.
        raise web.HTTPError(404)

    def wrap_post(self, *args, **kwargs):
        # By default, no endpoint already exists.
        raise web.HTTPError(404)

