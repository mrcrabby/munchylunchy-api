import auth
import health
import tastes


def url(pattern, handler):
    return ("/v1/%s" % pattern, handler)


def register(patterns):
    """Register API v1."""
    patterns.extend([
        url("auth/browserid", auth.AuthBrowserID),
        url("auth/token", auth.AuthToken),
        url("health/ping", health.PingHandler),
        url("health/redis", health.RedisHealth),
        url("tastes/set", tastes.TasteSet),
        url("tastes/list", tastes.TasteList),
        url("tastes/clear", tastes.TasteClear),
    ])
    return patterns
