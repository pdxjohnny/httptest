#!/usr/bin/env python3
import json
import http.server
import multiprocessing

class FailedToStart(Exception): pass

class Handler(http.server.SimpleHTTPRequestHandler):

    def json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        print("Handler: json:", json.dumps(data).encode('utf-8'))
        self.wfile.write(json.dumps(data).encode('utf-8'))

class HTTPServer(http.server.HTTPServer):

    allow_reuse_address = True

    def serve_forever(self, *args, **kwargs):
        self.addr_queue.put(self.server_name)
        self.addr_queue.put(self.server_port)
        return super().serve_forever(*args, **kwargs)

class NoServer(object):

    def url(self):
        raise FailedToStart()

class Server(object):

    def __init__(self, testServerClass, addr=('127.0.0.1', 0)):
        self._testServerClass = testServerClass
        self._addr = addr
        self.server_name = addr[0]
        self.server_port = addr[1]

    def __call__(self, func, *args, **kwargs):
        def wrap(*args, **kwargs):
            s = HTTPServer(self._addr, self._testServerClass)
            self.__addr_queue = multiprocessing.Queue()
            s.addr_queue = self.__addr_queue
            t = multiprocessing.Process(target=s.serve_forever,
                    daemon=True)
            t.start()
            self.server_name = self.__addr_queue.get(True)
            self.server_port = self.__addr_queue.get(True)
            res = func(*args, ts=self, **kwargs)
            t.terminate()
            return res
        return wrap

    def url(self):
        return 'http://{0}:{1}/'.format(self.server_name, self.server_port)
