import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.netutil
import tornado.process

from settings import site_settings

from views import (
    ClassQueryHandler,
    ClassCacheHandler,
)

application = tornado.web.Application([
    (r"/", ClassQueryHandler),
    (r"/api/classroom/query", ClassCacheHandler),
], **site_settings)

if __name__ == "__main__":
    sockets = tornado.netutil.bind_sockets(9000)
#    tornado.process.fork_processes(0)
    server = tornado.httpserver.HTTPServer(application, xheaders=True)
    server.add_sockets(sockets)
    tornado.ioloop.IOLoop.instance().start()
