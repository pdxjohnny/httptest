#!/usr/bin/env python3
'''
Unit tests for httptest
'''
import unittest
import urllib.request

import httptest

class TestHTTPServer(httptest.Handler):
    '''
    Handler for testing httptest.Server
    '''

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(bytes("what up", "utf-8"))

class TestServerMethods(unittest.TestCase):
    '''
    Test cases for httptest.Server
    '''

    @httptest.Server(TestHTTPServer)
    def test_url(self, ts=httptest.NoServer()):
        '''
        Make sure the Server.url() method works.
        '''
        url = ts.url()
        self.assertIn(':', url)
        self.assertEqual(':'.join(url.split(':')[:-1]), 'http://localhost')

    @httptest.Server(TestHTTPServer)
    def test_call_response(self, ts=httptest.NoServer()):
        '''
        Make sure we can read the server's response.
        '''
        with urllib.request.urlopen(ts.url()) as f:
            self.assertEqual(f.read().decode('utf-8'), "what up")

class TestJSONServer(httptest.Handler):
    '''
    Handler for testing httptest.Handler
    '''

    def do_GET(self):
        '''
        Returns [2, 4]
        '''
        self.json([2, 4])

class TestHandlerMethods(unittest.TestCase):
    '''
    Test cases for httptest.Handler
    '''

    @httptest.Server(TestJSONServer)
    def test_json(self, ts=httptest.NoServer()):
        '''
        Make sure the server correctly encodes and sends us a json.
        '''
        with urllib.request.urlopen(ts.url()) as f:
            self.assertEqual(f.read().decode('utf-8'), "[2, 4]")

if __name__ == '__main__':
    unittest.main()
