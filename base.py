import json
import redis
from urllib.parse import (
    urlsplit,
    urlunsplit
)

import tornado.web

from settings import (
    site_settings,
    redis_settings,
)


class BaseHandler(tornado.web.RequestHandler):
    pass


def conn_redis():
    return redis.StrictRedis(host=redis_settings["host"],
                             port=redis_settings["port"])
