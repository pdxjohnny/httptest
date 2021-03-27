httptest
========

.. image:: https://travis-ci.org/pdxjohnny/httptest.svg?branch=master&event=push
    :target: https://travis-ci.org/pdxjohnny/httptest
    :alt: Build Status
.. image:: https://codecov.io/gh/pdxjohnny/httptest/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/pdxjohnny/httptest
    :alt: codecov
.. image:: https://img.shields.io/pypi/v/httptest.svg
    :target: https://pypi.org/project/httptest
    :alt: PyPI version

HTTP testing inspired by golang's httptest package. Supports wrapping asyncio
coroutine functions (``async def``).

For internals and contribution guidelines, see
`CONTRIBUTING.rst <CONTRIBUTING.rst>`_.

Usage
-----

You can use ``httptest`` as a decorator for test functions or as a context
manager to just start an HTTP server on a random port in a ``with`` block.

Context Manager
+++++++++++++++

.. code-block:: python

    import unittest
    import urllib.request

    import httptest

    class TestHTTPServer(httptest.Handler):

        def do_GET(self):
            contents = "what up".encode()
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.send_header("Content-length", len(contents))
            self.end_headers()
            self.wfile.write(contents)

    def main():
        with httptest.Server(TestHTTPServer) as ts:
            with urllib.request.urlopen(ts.url()) as f:
                assert f.read().decode('utf-8') == "what up"

    if __name__ == '__main__':
        main()

Simple HTTP Server Handler
++++++++++++++++++++++++++

.. code-block:: python

    import unittest
    import urllib.request

    import httptest

    class TestHTTPServer(httptest.Handler):

        def do_GET(self):
            contents = "what up".encode()
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.send_header("Content-length", len(contents))
            self.end_headers()
            self.wfile.write(contents)

    class TestHTTPTestMethods(unittest.TestCase):

        @httptest.Server(TestHTTPServer)
        def test_call_response(self, ts=httptest.NoServer()):
            with urllib.request.urlopen(ts.url()) as f:
                self.assertEqual(f.read().decode('utf-8'), "what up")

    if __name__ == '__main__':
        unittest.main()

Asyncio Support
+++++++++++++++

Asyncio support for the unittest package landed in Python 3.8. As
`IsolatedAsyncioTestCase <https://docs.python.org/3/library/unittest.html#unittest.IsolatedAsyncioTestCase>`_

If you want a quick way to add ``asyncio`` test cases you can import the helper
from `intel/dffml <https://github.com/intel/dffml>`_ if you are using Python
verisons prior to 3.8.

.. code-block:: python

    import sys
    import unittest
    import urllib.request
    if sys.version_info.minor == 3 \
            and sys.version_info.minor <= 7:
        from dffml.util.asynctestcase import AsyncTestCase
    else:
        # In Python 3.8
        from unittest import IsolatedAsyncioTestCase as AsyncTestCase

    import httptest

    class TestHTTPServer(httptest.Handler):

        def do_GET(self):
            contents = "what up".encode()
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.send_header("Content-length", len(contents))
            self.end_headers()
            self.wfile.write(contents)

    class TestHTTPTestMethods(AsyncTestCase):

        @httptest.Server(TestHTTPServer)
        async def test_call_response(self, ts=httptest.NoServer()):
            with urllib.request.urlopen(ts.url()) as f:
                self.assertEqual(f.read().decode('utf-8'), "what up")

    if __name__ == '__main__':
        unittest.main()

In your project's ``setup.cfg``, add ``dffml`` in ``tests_require``.

.. code-block:: ini

    tests_require =
        httptest>=0.0.18
        dffml>=0.4.0

Auto Install
------------

If you're making a python package, you'll want to add ``httptest`` to your
``setup.py`` file's ``tests_require`` section.

This way, when your run ``python -m unittest discover -v`` setuptools will
install ``httptest`` for you in a package local directory, if it's not already
installed.

.. code-block:: ini

    tests_require =
        httptest>=0.0.18
