import hashlib
import time
import traceback

from apihandler import APIHandler


class PingHandler(APIHandler):

    def wrap_get(self):
        return {"pong": True}


class RedisHealth(APIHandler):

    def wrap_get(self):

        try:
            testkey = hashlib.md5(str(time.time())).hexdigest()
            self.redis.set(testkey, "test")
            result = self.redis.get(testkey)
            self.redis.delete(testkey)
            assert result == "test"
        except AssertionError:
            traceback.print_exc()
            return {"result": "fail"}
        else:
            return {"result": "okay"}

