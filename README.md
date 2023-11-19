# httptest

[![Tests](https://github.com/pdxjohnny/httptest/actions/workflows/tests.yml/badge.svg?branch=master)](https://github.com/pdxjohnny/httptest/actions/workflows/tests.yml) [![codecov](https://codecov.io/gh/pdxjohnny/httptest/branch/master/graph/badge.svg)](https://codecov.io/gh/pdxjohnny/httptest)

HTTP testing inspired by golang's httptest package. Supports wrapping asyncio
coroutine functions (`async def`).

## Usage

### Context Manager

```python
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
```

### Simple HTTP Server Handler

```python
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
```

### Serve Files

```python
import pathlib
import unittest
import http.server
import urllib.request

import httptest

FILE_PATH = pathlib.Path(__file__)

class TestHTTPTestMethods(unittest.TestCase):

    @httptest.Server(
        lambda *args: http.server.SimpleHTTPRequestHandler(
            *args, directory=FILE_PATH.parent
        )
    )
    def test_call_response(self, ts=httptest.NoServer()):
        with urllib.request.urlopen(ts.url() + FILE_PATH.name) as f:
            self.assertEqual(f.read().decode('utf-8'), FILE_PATH.read_text())

if __name__ == '__main__':
    unittest.main()
```

### Asyncio Support

Asyncio support for the unittest package hasn't yet landed in Python.
[python/issue32972](https://bugs.python.org/issue32972).
It should land in 3.8, check it out
[here](https://github.com/python/cpython/pull/13386).

If you want a quick way to add `asyncio` test cases you can import the helper
from [intel/dffml](https://github.com/intel/dffml).

```python
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
```

In your project's `setup.py`, add `dffml` in `tests_require`.

```python
setup(
    name='your_package',
    ...
    tests_require=[
        'httptest>=0.1.0',
        'dffml>=0.4.0.post0'
    ]
)
```

## Auto Install

If you're making a python package, you'll want to add `httptest` to your
`setup.py` file's `tests_require` section.

This way, when your run `python setup.py test` setuptools will install
`httptest` for you in a package local directory, if it's not already installed.

```python
setup(
    name='your_package',
    ...
    tests_require=[
        'httptest>=0.1.0'
    ]
)
```

## Cache Server

Run the caceh server and use it's URL in place of the upstream URL whatever you want to intercept on

```console
$ httptest-cache --state-dir .cache/httptest --addr 0.0.0.0 --port 7000 http://localhost:8000
Serving on http://localhost:7000
```

Inspect cached objects in the cache dir

```console
$ python -c 'import sys, pathlib, pickle, pprint; pprint.pprint(pickle.loads(pathlib.Path(sys.argv[-1]).read_bytes()).headers)' .cache/httptest/f31bc77712e808fffdab85a33631e414f25715588b1a026d6b8a4e0171b67e99859ab71b1933c93b0078d1e47da9a929.request.pickle
{'Accept': '*/*',
 'Accept-encoding': 'gzip',
 'Connection': 'close',
 'Content-length': '8159',
 'Content-type': 'application/json',
 'Host': 'localhost:45709',
 'Request-hmac': '1700084205.d96d4f546acedddc142b1168642a74c738685d1ac4aa07984e9a1850bb73ddee',
 'User-agent': 'GitHub-Hookshot/dc69923',
 'X-as': '',
 'X-country': '',
 'X-forwarded-for': '10.56.101.48',
 'X-forwarded-proto': 'https',
 'X-github-delivery': '12dac8d6-83ff-11ee-97c9-119c09045ae0',
 'X-github-event': 'push',
 'X-github-hook-id': '443288828',
 'X-github-hook-installation-target-id': '621131680',
 'X-github-hook-installation-target-type': 'repository',
 'X-github-request-id': '1271:336E:974AC:15C2D2:655539ED',
 'X-glb-edge-region': 'iad',
 'X-glb-edge-site': 'ash1-iad',
 'X-glb-via': 'hostname=glb-proxy-1c66317.ash1-iad.github.net site=ash1-iad '
              'region=iad service=kube-public t=1700084205.902',
 'X-haproxy-ssl-fc-cipher': 'TLS_AES_128_GCM_SHA256',
 'X-haproxy-ssl-fc-protocol': 'TLSv1.3',
 'X-haproxy-ssl-fc-use-keysize': '128',
 'X-real-ip': '10.56.101.48',
 'X-region': '',
 'X-request-start': 't=1700084205915930',
 'X-ssl-ja3-hash': '7a15285d4efc355608b304698cd7f9ab'}
```

## Examples

See the [examples/](https://github.com/pdxjohnny/httptest/tree/master/examples/)
directory for more examples.

- [github_webhook_event_logger.py](https://github.com/pdxjohnny/httptest/tree/master/examples/github_webhook_event_logger.py)
