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

        inverse = "like" if preference == "dislike" else "dislike"

        self.redis.sadd("tastes::%s::%s" % (preference, self.email), taste)
        self.redis.srem("tastes::%s::%s" % (inverse, self.email), taste)

        return {"result": "okay"}


class TasteList(APIHandler):
    """Fetch a list of the user's taste preferences."""

    @require_user
    def wrap_get(self):
        likes = self.redis.smembers("tastes::like::%s" % self.email)
        dislikes = self.redis.smembers("tastes::dislike::%s" % self.email)
        return {"likes": likes,
                "dislikes": dislikes}


class TasteClear(APIHandler):
    """Clear a taste preference."""

    @require_user
    def wrap_post(self):
        taste = self.get_argument("taste")
        if taste not in TASTES:
            raise web.HTTPError(400)

        self.redis.srem("tastes::like::%s" % self.email, taste)
        self.redis.srem("tastes::dislike::%s" % self.email, taste)

        return {"result": "ok"}

