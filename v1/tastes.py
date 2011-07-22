import math
import random

import tornado.web as web

from apihandler import APIHandler, require_user
from constants import TASTES
from utils.yelp import search as yelp_search


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


class TasteQuery(APIHandler):
    """Retrieve a list of "tastes" that the user should be asked about."""

    @web.asynchronous
    @require_user
    def get(self):
        latitude = self.get_argument("lat")
        longitude = self.get_argument("lon")

        user_tastes = set()

        def collect_yelp(data):
            business_categories = set()
            for business in data["businesses"]:
                for foo, c in business["categories"]:
                    business_categories.add(c)
            business_categories -= user_tastes

            while len(business_categories) < 10:
                cat = random.choice(business_categories)
                business_categories.discard(cat)

            to_ask_range = math.ceil(len(user_tastes) / 5)
            to_ask_ranges = {0: 5, 1: 4, 2: 4, 3: 2}
            to_ask = 0
            if to_ask_range in to_ask_ranges:
                to_ask = to_ask_ranges[to_ask_range]
            else:
                to_ask = 2

            self._format_output({"result": "okay",
                                 "tastes": business_categories,
                                 "to_ask": to_ask})

            self.finish()

        yelp_search(collect_yelp, latitude=latitude, longitude=longitude)

        user_tastes = self.redis.sunion("tastes::like::%s" % self.email,
                                        "tastes::dislike::%s" % self.email)
        user_tastes = frozenset(user_tastes)

