httptest
########

HTTP testing inspired by golang's httptest package.

Usage
*****

.. code-block:: python

    import unittest
    import urllib.request

    import httptest

    class TestHTTPServer(httptest.Handler):

        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(bytes("what up", "utf-8"))

    class TestHTTPTestMethods(unittest.TestCase):

        @httptest.Server(TestHTTPServer)
        def test_call_response(self, ts=httptest.NoServer()):
            with urllib.request.urlopen(ts.url()) as f:
                self.assertEqual(f.read().decode('utf-8'), "what up")

    if __name__ == '__main__':
        unittest.main()
