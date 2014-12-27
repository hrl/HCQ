import re
import json
import urllib.parse

import tornado.web
import tornado.gen
import tornado.template
from tornado.ioloop import IOLoop
from tornado.httputil import HTTPHeaders
from tornado.httpclient import AsyncHTTPClient
from tornado.httpclient import HTTPRequest

from pyquery import PyQuery

from settings import (
    site_settings,
    redis_settings,
    query_settings,
)

import base
redis_cli = base.conn_redis()


class ClassQueryHandler(base.BaseHandler):
    def get(self):
        self.render('classroom.html',
                    get_date_CN=base.get_date_CN,
                    response_dict={'status': -1})

    @tornado.gen.coroutine
    def post(self):
        query_dict = {
            'Build': self.get_argument('Build', 'default'),
            'QueryDate': self.get_argument('QueryDate', base.get_date_CN()),
        }
        query_string = urllib.parse.urlencode(query_dict)
        response = yield AsyncHTTPClient().fetch(
            "http://127.0.0.1:%d" % site_settings["port"]
            + "/api/classroom/query"
            + '?%s' % query_string)
        if response.code == 200:
            response_dict = json.loads(response.body.decode('utf8'))
        else:
            response_dict = {
                'status': 1,
                'error': '服务器内部错误',
            }
        self.render('classroom.html',
                    get_date_CN=base.get_date_CN,
                    response_dict=response_dict)


class ClassCacheHandler(base.CacheFetchHandler):
    @tornado.gen.coroutine
    def get(self):
        # Init
        Build = self.get_argument('Build', 'default')
        QueryDate = self.get_argument('QueryDate', base.get_date_CN())

        Build_dict = query_settings['classroom']['Build']
        if Build not in Build_dict:
            Build = 'default'
        Build = Build_dict[Build]

        try:
            year, month, day = QueryDate.split('-')
            year = int(year)
            month = int(month)
            day = int(day)
            Term = base.get_Term(QueryDate)
            Term_today = base.get_Term()
            assert 2009 <= year
            assert 1 <= month <= 12
            assert 1 <= day <= 31
            assert Term == Term_today
        except:
            QueryDate = base.get_date_CN()
            Term = base.get_Term(QueryDate)

        cache_code = "%s|%s" % (QueryDate, Build)

        while True:
            # Check Cache
            cache_ans = yield self.check_cache(redis_cli, cache_code)
            if cache_ans is not None:
                # Cache Hit
                room_list = json.loads(cache_ans.decode('utf8'))
                break
            else:
                # Cache Miss
                if redis_cli.setnx(cache_code, "fetching"):
                    # Lock Acquired
                    redis_cli.expire(cache_code,
                                     site_settings['cache_fetch_timeout'])

                    # Fetch Classroom Detail from HUST
                    room_list = yield self.query_class(Build, QueryDate, Term)
                    room_list_json = json.dumps(room_list)
                    redis_cli.set(cache_code, room_list_json)
                    break
                else:
                    # Wait
                    pass

        response_dict = {
            'status': 0,
            'Build': Build,
            'QueryDate': QueryDate,
            'room_list': room_list,
        }
        response_json = json.dumps(response_dict)
        self.finish(response_json)

    @tornado.gen.coroutine
    def query_class(self, Build, QueryDate, Term):
        # Init
        room_list = []
        query_url = "http://202.114.5.131/index.aspx"
        post_dict = {
            'Term': Term,
            'Build': Build,
            'QueryDate': QueryDate,
            'Filter': '',
        }
        base_headers = HTTPHeaders()
        base_headers["User-Agent"] =\
            ("Mozilla/5.0 (X11; Linux x86_64) "
             "AppleWebKit/537.36 (KHTML, like Gecko) "
             "Chrome/37.0.2062.120 Safari/537.36")
        base_headers['Origin'] = 'http://202.114.5.131'
        base_headers['Referer'] = 'http://202.114.5.131/index.aspx'

        # Prepare
        pq_main = yield self.load_page_pq(base_headers, query_url)
        base.reload_validation_code(post_dict, pq_main)

        # Load ClassroomList
        post_dict['ScriptManager1'] = 'UpdatePanel1|btnRightall'
        post_dict['btnRightall'] = '>>'
        pq_class = yield self.load_page_pq(base_headers, query_url, post_dict)

        # Clean Dict
        del post_dict['ScriptManager1']
        del post_dict['btnRightall']

        # Prepare Classroom Detail
        base.reload_validation_code(post_dict, pq_class)
        post_dict['Button1'] = '查询'
        pq_detail = yield self.load_page_pq(base_headers, query_url, post_dict)

        # Clean Dict
        del post_dict['Button1']

        # Check Page
        page_list = pq_detail('#Pager')
        if page_list:
            page_max_a = page_list('a')\
                .filter(lambda: PyQuery(this).text() == '尾页')
            if page_max_a:
                page_max_href = page_max_a.attr('href')
                page_max_re = re.compile(r'''\d+''')
                page_max = int(page_max_re.findall(page_max_href)[0])
            else:
                page_max = 1
        else:
            page_max = 1

        # Load Classroom Detail
        page_current = 1
        while page_current <= page_max:
            pq_classroom_list = pq_detail('#gvItem').children()
            self.load_classroom_detail(room_list, pq_classroom_list)

            if page_current != page_max:
                # Load Next Page
                base.reload_validation_code(post_dict, pq_detail)
                post_dict['__EVENTTARGET'] = 'Pager'
                post_dict['__EVENTARGUMENT'] = str(page_current + 1)
                pq_detail = yield self.load_page_pq(
                    base_headers, query_url, post_dict)

                # Clean Dict
                del post_dict['__EVENTTARGET']
                del post_dict['__EVENTARGUMENT']

            page_current += 1

        raise tornado.gen.Return(room_list)

    def load_classroom_detail(self, room_list, pq_classroom_list):
        for i in range(1, len(pq_classroom_list)):
            pq_classroom = pq_classroom_list.eq(i).children()
            classroom_name = pq_classroom.eq(0).text()

            classroom_detail_list = []
            for n in range(1, 6):
                pq_class_detail = pq_classroom.eq(n).text()
                if not pq_class_detail:
                    classroom_detail_list.append(2*n - 1)
                    classroom_detail_list.append(2*n)

            for n in range(1, len(classroom_detail_list), 2):
                try:
                    if classroom_detail_list[n]+1 == classroom_detail_list[n+1]:
                        classroom_detail_list[n] = -1
                        classroom_detail_list[n+1] = -1
                except IndexError:
                    pass
            classroom_detail_list = list(
                filter(lambda x: x != -1, classroom_detail_list))

            classroom_detail = ''
            for n in range(0, len(classroom_detail_list), 2):
                classroom_detail += "%d-%d, " % (classroom_detail_list[n],
                                                 classroom_detail_list[n+1])
            classroom_detail = classroom_detail.strip(', ')

            if classroom_detail:
                room_list.append((classroom_name, classroom_detail))
