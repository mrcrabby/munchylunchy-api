import math
import uuid

import tornado.web as web

from apihandler import APIHandler, require_user
from utils.yelp import search as yelp_search, parse_rating, business_data

class DecideHandler(APIHandler):

    def initialize(self):
        super(DecideHandler, self).initialize()
        self.onpage = 0
        self.total_results = 0
        self.total_pages = 0

    @web.asynchronous
    @require_user
    def get(self):
        lat = self.get_argument("lat")
        lon = self.get_argument("lon")

        user_tastes = self.redis.smembers("tastes::like::%s" % self.email)
        user_dislikes = self.redis.smembers("tastes::dislike::%s" % self.email)

        user_history = self.redis.lrange("places::history::%s" % self.email,
                                         0, 5)

        place_reasons_key = "places::reasons::%s::%%s" % self.email
        place_scores = "places::score::%s" % str(uuid.uuid4())

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
                        score -= 4
                    elif category in user_tastes:
                        score += 3
                        self.redis.sadd(reason_key, "like:%s" % category)

                if key in user_history:
                    score -= 3
                else:
                    self.redis.sadd(reason_key, "notrecent")

                # Add the data to redis for this session
                print place_scores, score, key
                self.redis.zadd(place_scores, key, score)

        def yelp_callback(data):
            self.total_results = data["total"]
            self.total_pages = math.ceil(self.total_results / 20)
            self.total_pages = min(self.total_pages, 2)

            yelp_rec_callback(data)

        def yelp_rec_callback(data):

            process_businesses(data["businesses"])

            self.onpage += 1
            print "Page?", self.onpage, self.total_pages
            if self.onpage == self.total_pages:
                after_yelp()
                return

            print "Searching Yelp..."
            yelp_search(yelp_rec_callback, latitude=lat, longitude=lon,
                        offset=self.onpage * 20)

        def after_yelp():
            print "After yelp"
            pick = self.redis.zrevrange(place_scores, 0, 1)[0]
            pick_reasons = []

            def pick_output(data):
                print "Pick output"
                self.write({"result": "okay",
                            "business": data,
                            "reasons": list(pick_reasons)})
                self.finish()

            business_data(pick_output, pick)
            pick_reasons = self.redis.smembers(place_reasons_key % pick)
            self.redis.delete(place_reasons_key % pick)
            self.redis.lpush("places::history::%s" % self.email, pick)

        print "Searching Yelp initially..."
        yelp_search(yelp_callback, latitude=lat, longitude=lon,
                    categories=user_tastes)

