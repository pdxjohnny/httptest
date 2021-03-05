#!/usr/bin/env python3
'''
Unit tests for httptest
'''
import os
import glob
import asyncio
import tempfile
import unittest
import urllib.error
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

    def test_async_call_response(self):
        '''
        Check that httptest.Server works for coroutine functions.
        '''
        @httptest.Server(TestHTTPServer)
        async def run_test(ts=httptest.NoServer()):
            with urllib.request.urlopen(ts.url()) as f:
                self.assertEqual(f.read().decode('utf-8'), "what up")
        loop = asyncio.new_event_loop()
        loop.run_until_complete(run_test())
        loop.close()

class TestCachingMethods(unittest.TestCase):
    '''
    Test cases for httptest.CachingProxyHandler
    '''

    @httptest.Server(TestHTTPServer)
    def test_forwards_get(self, ts=httptest.NoServer()):
        '''
        Make sure we can read the server's response.
        '''
        with tempfile.TemporaryDirectory() as tempdir:
            @httptest.Server(httptest.CachingProxyHandler.to(ts.url(),
                             state_dir=tempdir))
            def test_cached(ts=httptest.NoServer()):
                with urllib.request.urlopen(ts.url() + 'get') as f:
                    self.assertEqual(f.read().decode('utf-8'), "what up")
                self.assertEqual(len(list(glob.glob(os.path.join(tempdir,
                    '*')))), 4)
                with open(glob.glob(os.path.join(tempdir, '*.body'))[0], 'wb') \
                        as fd:
                    fd.write(b"waassss aaaap")
                with urllib.request.urlopen(ts.url() + 'get') as f:
                    self.assertEqual(f.read().decode('utf-8'), "waassss aaaap")

            test_cached()

    @httptest.Server(TestHTTPServer)
    def test_forwards_error(self, ts=httptest.NoServer()):
        '''
        Make sure we can read the server's response.
        '''
        with tempfile.TemporaryDirectory() as tempdir:
            @httptest.Server(httptest.CachingProxyHandler.to(ts.url(),
                             state_dir=tempdir))
            def test_cached(ts=httptest.NoServer()):
                req = urllib.request.Request(ts.url() + 'p', method='POST')
                with self.assertRaises(urllib.error.HTTPError):
                    with urllib.request.urlopen(req) as f:
                        pass

            test_cached()

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
