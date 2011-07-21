import tornado.ioloop
import tornado.web as web

from apihandler import APIHandler

patterns = []

import v1.apiv1 as apiv1
apiv1.register(patterns)


class APIRootHandler(APIHandler):
    """Give a general summary of the application."""

    def wrap_get(self):
        return {"version": 1,
                "latest_url": "/v1/"}


if __name__ == "__main__":
    print "Starting server..."
    patterns.extend([(r"/", APIRootHandler)])
    application = tornado.web.Application(patterns)

    application.listen(80)
    print "Listening"
    tornado.ioloop.IOLoop.instance().start()

