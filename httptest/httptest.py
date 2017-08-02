#!/usr/bin/env python3
'''
httptest offers the Handler for serving test data and the HTTPServer
which is started and stopped using the httptest.Server() decorator.
'''
import json
import selectors
import threading
import http.server
import multiprocessing

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

class HTTPServer(http.server.HTTPServer):
    '''
    Starts and manages the running server process.
    '''

    allow_reuse_address = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__server = False
        self.__send = False

    #pylint: disable=arguments-differ
    def serve_forever(self, addr_queue, pipe):
        '''
        Start the server handle requests and wait for shutdown.
        '''
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
        '''
        Start the server in the background. Call stop_background to
        stop it. Raises AlreadyStarted if called again before
        stop_background is called. Returns the server hostname and
        port as a tuple.
        '''
        if self.__server is not False or self.__send is not False:
            raise AlreadyStarted()
        addr_queue = multiprocessing.Queue()
        recv, self.__send = multiprocessing.Pipe()
        self.__server = threading.Thread(target=self.serve_forever, args=(addr_queue, recv))
        self.__server.start()
        return addr_queue.get(True), addr_queue.get(True)

    def stop_background(self):
        '''
        Stop a running server. Raises NotStarted if called before
        start_background.
        '''
        if not self.__server or not self.__send:
            raise NotStarted()
        self.__send.send('shutdown')
        self.__server = False
        self.__send = False

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

    def __init__(self, testServerClass, addr=('127.0.0.1', 0)):
        self._class = testServerClass
        self._addr = addr
        self.server_name = addr[0]
        self.server_port = addr[1]

    def __call__(self, func, *args, **kwargs):
        def wrap(*args, **kwargs):
            '''
            Starts the HTTPServer runs the test then stops the server
            '''
            server = HTTPServer(self._addr, self._class)
            self.server_name, self.server_port = server.start_background()
            try:
                res = func(*args, ts=self, **kwargs)
            except:
                server.stop_background()
                raise
            server.stop_background()
            return res
        return wrap

    def url(self):
        '''
        Server URL formatted as http://server_name:server_port/
        '''
        return 'http://{0}:{1}/'.format(self.server_name, self.server_port)
