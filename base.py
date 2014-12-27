import json
import time
import datetime
import urllib.parse

import redis
import tornado.web
import tornado.gen
from tornado.ioloop import IOLoop
from tornado.httputil import HTTPHeaders
from tornado.httpclient import HTTPError
from tornado.httpclient import AsyncHTTPClient
from tornado.httpclient import HTTPRequest

from pyquery import PyQuery
from lunardate import LunarDate

from dateutil.tz import (
    tzlocal,
    gettz,
)

from settings import (
    site_settings,
    redis_settings,
)


class BaseHandler(tornado.web.RequestHandler):
    pass


class RedisHandler(BaseHandler):
    @tornado.gen.coroutine
    def check_cache(self, redis_cli, cache_code):
        current_status = redis_cli.get(cache_code)
        while current_status:
            if current_status.decode('utf8') == "fetching":
                pass
            else:
                break
            yield tornado.gen.Task(IOLoop.instance().add_timeout,
                                   time.time() + 0.5)
            current_status = redis_cli.get(cache_code)

        if current_status:
            raise tornado.gen.Return(current_status)
        else:
            raise tornado.gen.Return(None)


class CacheFetchHandler(RedisHandler):
    @tornado.gen.coroutine
    def load_page_pq(self, headers, url, post_dict=None):
        if post_dict is None:
            headers['Content-Type'] =\
                'text/html'
            request = HTTPRequest(url,
                                  headers=headers)
        else:
            post_data = urllib.parse.urlencode(post_dict).encode('utf8')
            headers['Content-Type'] =\
                'application/x-www-form-urlencoded; charset=UTF-8'
            request = HTTPRequest(url,
                                  headers=headers,
                                  method="POST",
                                  body=post_data)
        try:
            response = yield AsyncHTTPClient().fetch(request)
        except HTTPError as e:
            response = e.response

        if str(response.code)[0] == "2":
            pq = PyQuery(response.body.decode('utf8', 'ignore'))
            raise tornado.gen.Return(pq)
        else:
            raise tornado.gen.Return(None)


def conn_redis():
    return redis.StrictRedis(host=redis_settings["host"],
                             port=redis_settings["port"])


def get_date_CN():
    tz_CN = gettz('Asia/Shanghai')
    time_local = datetime.datetime.now(tzlocal())
    time_CN = time_local.astimezone(tz_CN)
    return time_CN.strftime('%Y-%m-%d')


def reload_validation_code(post_dict, pq_page):
    base_code = pq_page('input')\
        .filter(lambda: PyQuery(this).attr('id').startswith('_'))
    for i in range(len(base_code)):
        code = base_code.eq(i)
        post_dict[code.attr('id')] = code.attr('value')


def get_Term(date=None, seazon=None):
    # getTerm(year, seazon):
    #   getTerm(2014, 0): 2014 Spring
    #   getTerm(2014, 1): 2014 Autumn
    # getTerm([date]):
    #   getTerm('2014-09-01')
    if date is None:
        date = get_date_CN()

    if seazon is not None:
        year = date
    else:
        year, month, day = date.split('-')
        year = int(year)
        month = int(month)
        day = int(day)

        year_lunar = LunarDate.fromSolarDate(year, month, day).year
        if month < 8:
            if year_lunar == year:
                seazon = 0
            else:
                seazon = 1
        else:
            seazon = 1

        year = year_lunar

    return str((year - 2009) * 2 + seazon)
