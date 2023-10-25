#!/usr/bin/env python3
'''
httptest offers the Handler for serving test data and the HTTPServer
which is started and stopped using the httptest.Server() decorator.
'''
import os
import io
import json
import pickle
import socket
import hashlib
import inspect
import platform
import selectors
import threading
import http.server
import urllib.request
import multiprocessing
from urllib.parse import urlparse, urljoin
from contextlib import contextmanager

if getattr(http.server, 'ThreadingHTTPServer', False):
    ThreadingHTTPServer = http.server.ThreadingHTTPServer
else:
    import socketserver
    class ThreadingHTTPServer(socketserver.ThreadingMixIn,
                              http.server.HTTPServer):
        pass

class FailedToStart(Exception):
    '''
    The server failed to start so a NoServer instance was created
    '''
    pass

class AlreadyStarted(Exception):
    '''
    The server cannot be started because it is already running
    '''
    pass

class NotStarted(Exception):
    '''
    The server cannot be stopped because it isn't running
    '''
    pass

class Handler(http.server.SimpleHTTPRequestHandler):
    '''
    Handler to use with httptest.Server
    '''

    def json(self, data):
        '''
        Send a 200 with Content-type application/json using data as
        the json data to send.
        '''
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    #pylint: disable=arguments-differ
    def log_message(self, *args):
        '''
        Disables server logs
        '''
        pass

class CachingProxyHandler(Handler):
    '''
    Handler to use with httptest.Server which caches requests to an upstream
    server.
    '''

    @classmethod
    def to(cls, upstream, state_dir=None):
        '''
        Creates a CachingProxyHandler which will proxy requests to an upstream
        server.
        '''
        if state_dir is None:
            state_dir = os.path.join(os.getcwd(), '.cache', 'httptest')

        upstream = urlparse(upstream)

        class ConfiguredCachingProxyHandler(cls):
            UPSTREAM = upstream
            STATE_DIR = state_dir
        return ConfiguredCachingProxyHandler

    def proxied_url(self):
        url = self.UPSTREAM.geturl() + self.path
        while '//' in url:
            url = url.replace('//', '/')
        return url.replace(':/', '://')

    def cache_path(self, *args):
        if not os.path.isdir(self.STATE_DIR):
            os.makedirs(self.STATE_DIR)
        return os.path.join(self.STATE_DIR, *args)

    def cached(self, key):
        return bool(all(list(map(lambda needed: \
                    os.path.isfile(self.cache_path(key + needed)),
                    ['.url', '.status', '.headers', '.body']))))

    def cache_key(self):
        body = None
        if 'Content-Length' in self.headers:
            length = int(self.headers['Content-Length'])
            body = io.BytesIO(self.rfile.read(length))
        digest = hashlib.sha384()
        digest.update(self.requestline.encode('utf-8', errors='ignore'))
        def sort_headers(kv):
            '''
            Sort headers dict so it always is in the same order.
            '''
            return kv[0].lower()
        for k, v in sorted(self.headers.items(), key=sort_headers):
            digest.update(k.encode('utf-8', errors='ignore'))
            digest.update(v.encode('utf-8', errors='ignore'))
        if body is not None:
            digest.update(body.read())
            body.seek(0)
        return digest.hexdigest(), body

    @contextmanager
    def save_cache(self, key, req, status, headers, body):
        with open(self.cache_path(key + '.hits'), 'w') as fd:
            fd.write(str(0))
        with open(self.cache_path(key + '.request.pickle'), 'wb') as fd:
            pickle.dump(req, fd, pickle.HIGHEST_PROTOCOL)
        with open(self.cache_path(key + '.url'), 'w') as fd:
            fd.write(req.get_full_url())
        with open(self.cache_path(key + '.status'), 'w') as fd:
            fd.write(str(status))
        with open(self.cache_path(key + '.headers'), 'w') as fd:
            json.dump(dict(headers._headers), fd)
        with open(self.cache_path(key + '.body'), 'wb') as fd:
            fd.write(body.read())
        with open(self.cache_path(key + '.response.pickle'), 'wb') as fd:
            pickle.dump(body, fd, pickle.HIGHEST_PROTOCOL)
        with open(self.cache_path(key + '.body'), 'rb') as fd:
            yield fd

    @contextmanager
    def load_cache(self, key):
        if os.path.exists(self.cache_path(key + '.hits')):
            with open(self.cache_path(key + '.hits'), 'r') as fd:
                hits = int(fd.read())
            with open(self.cache_path(key + '.hits'), 'w') as fd:
                fd.write(str(hits + 1))
        with open(self.cache_path(key + '.status'), 'r') as fd:
            status = int(fd.read())
        with open(self.cache_path(key + '.headers'), 'r') as fd:
            headers = json.load(fd)
        with open(self.cache_path(key + '.body'), 'rb') as fd:
            yield status, headers, fd

    def do_forward(self):
        '''
        Forward the request by making a similar request with urllib
        '''
        self.headers.replace_header('Host', self.UPSTREAM.netloc)
        key, data = self.cache_key()
        if self.cached(key):
            # Load from cache
            if data is not None:
                data.close()
            with self.load_cache(key) as (status, headers, fd):
                self.send_response(status)
                for header, content in headers.items():
                    self.send_header(header, content)
                self.end_headers()
                try:
                    self.wfile.write(fd.read())
                except BrokenPipeError:
                    pass
        else:
            # Run request (not cached)
            req = urllib.request.Request(self.proxied_url(),
                                         headers=self.headers,
                                         data=data,
                                         method=self.command)
            try:
                with urllib.request.urlopen(req) as f:
                    self.send_response(f.status)
                    for header, content in f.headers.items():
                        self.send_header(header, content)
                    self.end_headers()
                    with self.save_cache(key, req, f.status, f.headers, f) as c:
                        try:
                            self.wfile.write(c.read())
                        except BrokenPipeError:
                            pass
            except urllib.error.HTTPError as e:
                self.send_response(e.status, message=e.reason)
                for header, content in e.headers.items():
                    self.send_header(header, content)
                self.end_headers()
                try:
                    self.wfile.write(e.read())
                except BrokenPipeError:
                    pass


# Make sure CachingProxyHandler responds to all HTTP methods
for method in 'GET HEAD POST PUT DELETE CONNECT OPTIONS TRACE PATCH'.split():
    setattr(CachingProxyHandler, 'do_' + method, CachingProxyHandler.do_forward)

class HTTPServer(ThreadingHTTPServer):
    '''
    Starts and manages the running server process.
    '''

    allow_reuse_address = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__server = False
        self.__control_send = False

    #pylint: disable=arguments-differ
    def serve_forever(self, addr_queue, control_recv):
        '''
        Start the server handle requests and wait for shutdown.
        '''
        addr_queue.put(self.server_name)
        addr_queue.put(self.server_port)
        with selectors.DefaultSelector() as selector:
            selector.register(self, selectors.EVENT_READ)
            selector.register(control_recv, selectors.EVENT_READ)
            while True:
                ready = selector.select()
                for i in ready:
                    if i[0].fd == control_recv.fileno():
                        control_recv.close()
                        return self.socket.close()
                    self._handle_request_noblock()

    def start_background(self):
        '''
        Start the server in the background. Call stop_background to
        stop it. Raises AlreadyStarted if called again before
        stop_background is called. Returns the server hostname and
        port as a tuple.
        '''
        if self.__server is not False or self.__control_send is not False:
            raise AlreadyStarted()
        addr_queue = multiprocessing.Queue()
        control_recv, self.__control_send = socket.socketpair(
            socket.AF_INET if platform.system() == "Windows" else socket.AF_UNIX,
            socket.SOCK_STREAM,
        )
        self.__server = threading.Thread(target=self.serve_forever, args=(addr_queue, control_recv))
        self.__server.start()
        return addr_queue.get(True), addr_queue.get(True)

    def stop_background(self):
        '''
        Stop a running server. Raises NotStarted if called before
        start_background.
        '''
        if not self.__server or not self.__control_send:
            raise NotStarted()
        # Send a byte to the other thread
        self.__control_send.send(b'\x01')
        self.__control_send.close()
        self.__server = False
        self.__control_send = False

class NoServer(object):
    '''
    Used for setting the test server (ts) to a default value for
    the test case.

    Example:
        def test_something(self, ts=httptest.NoServer()):
    '''

    def url(self):
        '''
        NoServer always raises FailedToStart on a call to url()
        '''
        raise FailedToStart()

class Server(object):
    '''
    Server is the decorator used on unittest methods.

    Example:
        class TestJSONServer(httptest.Handler):
            def do_GET(self):
                self.json([2, 4])

        class TestHandlerMethods(unittest.TestCase):
            @httptest.Server(TestJSONServer)
            def test_json(self, ts=httptest.NoServer()):
                with urllib.request.urlopen(ts.url()) as f:
                    self.assertEqual(f.read().decode("utf-8"), "[2, 4]")
    '''

    def __init__(self, testServerClass, addr=('127.0.0.1', 0), keyfile=None, certfile=None):
        self._class = testServerClass
        self._addr = addr
        self._keyfile = keyfile
        self._certfile = certfile
        self._protocol = "http"
        if self._keyfile and self._certfile:
            self._protocol = "https"
        self.server_name = "localhost"
        # NOTE This variable holds the reported server name after bind.
        # Python seems to be doing some kind of reverse lookup on the
        # server name. This leads to odd behavior depending on the system's
        # hosts file. GitHub Windows runners resolve to MiningMadness.com as
        # some kind of loopback block and MacOS runners resolve to
        # 1.0.0.127.in-addr.arpa which is probably some Apple thing.
        self._server_name = addr[0]
        self.server_port = addr[1]

    def __call__(self, func, *args, **kwargs):
        '''
        Starts the HTTPServer runs the test then stops the server
        '''
        if inspect.iscoroutinefunction(func):
            async def wrap(*args, **kwargs):
                with self:
                    return await func(*args, ts=self, **kwargs)
        else:
            def wrap(*args, **kwargs):
                with self:
                    return func(*args, ts=self, **kwargs)
        return wrap

    def __enter__(self):
        self.server = HTTPServer(self._addr, self._class)
        if self._keyfile and self._certfile:
            self.server.socket = ssl.wrap_socket(
                self.server.socket,
                keyfile=self._keyfile,
                certfile=self._certfile,
                server_side=True,
            )
        self._server_name, self.server_port = self.server.start_background()
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        self.server.stop_background()
        self.server = None

    def url(self):
        '''
        Server URL formatted as http://server_name:server_port/
        '''
        return '{0}://{1}:{2}/'.format(self._protocol, self.server_name, self.server_port)
