import hashlib
import json
import math
import uuid

import tornado.web as web

from apihandler import APIHandler, require_user
import settings
from utils.yelp import search as yelp_search, business_data, parse_rating


class CreateGroup(APIHandler):
    """Create a group and get back an ID."""

    @require_user
    def wrap_get(self):
        def get_id():
            return hashlib.md5(str(uuid.uuid4())).hexdigest()[:4]

        group_id = get_id()
        while self.redis.exists("group::%s" % group_id):
            group_id = get_id()

        self.redis.sadd("group::%s" % group_id, self.email)

        return {"result": "okay",
                "group_id": group_id}


class GroupRegister(APIHandler):
    """Registers or confirms registration for a group."""

    def initialize(self):
        super(GroupRegister, self).initialize()
        self.onpage = 0
        self.total_results = 0
        self.total_pages = 0

    @web.asynchronous
    @require_user
    def post(self):
        group_id = self.get_argument("id")
        latitude = self.get_argument("lat") or 0
        longitude = self.get_argument("lon") or 0

        key = "group::%s" % group_id

        if not self.redis.exists(key):
            raise web.HTTPError(404)

        registration = "no"
        if self.redis.sismember(key, self.email):
            registration = "yes"
            if latitude and longitude:
                lat = self.redis.hget("group_props::%s" % group_id, "lat")
                lon = self.redis.hget("group_props::%s" % group_id, "lon")
                if not lat or not lon:
                    self.redis.hmset("group_props::%s" % group_id,
                                     {"lat": latitude, "lon": longitude})
                    lat = latitude
                    lon = longitude
                self.redis.hmset("group_pos::%s" % group_id,
                                 {self.email: "%f,%f" % (float(latitude), float(longitude))})

                print "Rendering choices..."
                self._render_choices(group_id, float(lat), float(lon))
                return

        else:
            self.redis.sadd(key, self.email)
            self.write({"result": "okay",
                        "registered": "new"})
            self.finish()
            return

    def _render_choices(self, group_id, lat, lon):
        members = self.redis.smembers("group::%s" % group_id)

        user_tastes = self.redis.sunion(map(lambda i: "tastes::like::%s" % i, members))
        user_dislikes = self.redis.sunion(map(lambda i: "tastes::dislike::%s" % i, members))

        print "Tastes: ", user_tastes
        print "Dislikes: ", user_dislikes

        histories = set()
        for member in members:
            for h in self.redis.lrange("places::history::%s" % member, 0, 3):
                histories.add(h)

        place_reasons_key = "places::reasons::group_%s::%%s" % group_id
        place_scores = "places::group_score::%s" % group_id

        self.redis.delete(place_scores)

        def process_businesses(businesses):
            for business in businesses:
                key = business["id"]
                reason_key = place_reasons_key % key
                self.redis.delete(reason_key)

                score = 0

                if business["distance"] < 500:
                    self.redis.sadd(reason_key, "distance")
                    score += 1
                else:
                    distance = business["distance"]
                    if distance > 1000:
                        distance -= 1000
                        score -= math.floor(distance / 500)

                place_rating = parse_rating(business["rating_img_url"])
                if place_rating > 4:
                    self.redis.sadd(reason_key, "great_rating")
                    score += 2
                elif place_rating > 3:
                    self.redis.sadd(reason_key, "good_rating")
                    score += 1

                for friendly_cat, category in business["categories"]:
                    if category in user_dislikes:
                        score -= 3
                    else:
                        self.redis.sadd(reason_key, "notrecent")

                    # Add the data to redis for this session
                    print place_scores, score, key
                    self.redis.zadd(place_scores, key, score)

        def yelp_callback(data):
            self.total_results = data["total"]
            self.total_pages = math.ceil(self.total_results / 20)
            self.total_pages = min(self.total_pages, settings.YELP_PAGES)

            yelp_rec_callback(data)

        def yelp_rec_callback(data):

            process_businesses(data["businesses"])

            self.onpage += 1
            print "Page?", self.onpage, self.total_pages
            if self.onpage >= self.total_pages:
                after_yelp()
                return

            print "Searching Yelp..."
            yelp_search(yelp_rec_callback, latitude=lat, longitude=lon,
                        offset=self.onpage * 20, redis=self.redis)

        def after_yelp():
            print "After yelp"

            def get_tiny_business(choice):
                id_, score = choice
                data = json.loads(self.redis.get("cache::business::%s" % id_))
                return data["name"], score

            picks = self.redis.zrevrange(place_scores, 0, 3, withscores=True)
            picks = map(get_tiny_business, picks)

            #pick_reasons = self.redis.smembers(place_reasons_key % pick)
            #self.redis.delete(place_reasons_key % pick)

            self.write({"result": "okay",
                        "registered": "yes",
                        "members": list(members),
                        "choices": picks})
            self.finish()

        print "Searching Yelp initially... (g)"
        yelp_search(yelp_callback, latitude=lat, longitude=lon,
                    categories=user_tastes, redis=self.redis)


class GroupPoll(APIHandler):
    """Poll for new information from the database."""

    @require_user
    def wrap_get(self):
        group_id = self.get_argument("id")
        key = "group::%s" % group_id
        zkey = "places::group_score::%s" % group_id

        def get_tiny_business(choice):
            id_, score = choice
            data = json.loads(self.redis.get("cache::business::%s" % id_))
            return {"name": data["name"],
                    "points": score,
                    "latitude": data["location"]["coordinate"]["latitude"],
                    "longitude": data["location"]["coordinate"]["longitude"]}

        choices = self.redis.zrevrange(zkey, 0, 3, withscores=True)

        return {"members": list(self.redis.smembers(key)),
                "choices": map(get_tiny_business, choices),
                "latitude": self.redis.hget("group_props::%s" % group_id,
                                            "lat"),
                "longitude": self.redis.hget("group_props::%s" % group_id,
                                             "lon"),}


