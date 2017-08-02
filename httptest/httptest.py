#!/usr/bin/env python3
import json
import socket
import selectors
import threading
import http.server
import multiprocessing

class FailedToStart(Exception): pass

class AlreadyStarted(Exception): pass

class NotStarted(Exception): pass

class Handler(http.server.SimpleHTTPRequestHandler):

    def json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def log_message(self, f, *args, **kwargs):
        pass

class HTTPServer(http.server.HTTPServer):

    allow_reuse_address = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__server = False
        self.__send = False

    def serve_forever(self, addr_queue, pipe):
        addr_queue.put(self.server_name)
        addr_queue.put(self.server_port)
        with selectors.DefaultSelector() as selector:
            selector.register(self, selectors.EVENT_READ)
            selector.register(pipe, selectors.EVENT_READ)
            while True:
                ready = selector.select()
                for i in ready:
                    if i[0].fd != self.fileno():
                        return self.socket.close()
                    self._handle_request_noblock()

    def start_background(self):
        if self.__server != False or self.__send != False:
            raise AlreadyStarted()
        addr_queue = multiprocessing.Queue()
        recv, self.__send = multiprocessing.Pipe()
        self.__server = threading.Thread(target=self.serve_forever,
                args=(addr_queue, recv))
        self.__server.start()
        return addr_queue.get(True), addr_queue.get(True)

    def stop_background(self):
        if self.__server == False or self.__send == False:
            raise NotStarted()
        self.__send.send('shutdown')
        self.__server = False
        self.__send = False

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
            self.server_name, self.server_port = s.start_background()
            res = func(*args, ts=self, **kwargs)
            s.stop_background()
            return res
        return wrap

    def url(self):
        return 'http://{0}:{1}/'.format(self.server_name, self.server_port)
