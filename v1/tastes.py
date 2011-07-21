import tornado.web as web

from apihandler import APIHandler, require_user
from constants import TASTES


class TasteSet(APIHandler):
    """Set a taste preference."""

    @require_user
    def wrap_post(self):
        taste = self.get_argument("taste")
        if taste not in TASTES:
            raise web.HTTPError(400)

        preference = self.get_argument("preference")
        if preference not in ("like", "dislike", ):
            raise web.HTTPError(400)

        self.redis.sadd("tastes::%s::%s" % (preference, self.email), taste)

        return {"result": "okay"}

