import json

import tornado.web as web

import utils.dict2xml as dict2xml


RESPONSE_TYPE = ("json", "xml", )

class APIHandler(web.RequestHandler):
    """A class to make handling API requests super amazing."""

    def get(self, *args, **kwargs):
        response_type = "json"
        if self.get_argument("type", default="json") in RESPONSE_TYPE:
            response_type = self.get_argument("type", default="json")

        output = self.wrap_get(*args, **kwargs)

        if response_type == "json":
            output = json.dumps(output)

            if self.get_argument("callback", default="").isalpha():
                callback = self.get_argument("callback")
                output = "%s(%s);" % (callback, output)

            self.write(output)

        elif response_type == "xml":
            self.write('<?xml version="1.0"?><api>')
            self.write(dict2xml.convert_dict_to_xml(output))
            self.write('</api>')

    def wrap_get(self, *args, **kwargs):
        # By default, no endpoint already exists.
        raise web.HTTPError(404)

