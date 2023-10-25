import os
import time
import argparse
from functools import wraps

from .httptest import Server, CachingProxyHandler

def cache():
    '''
    Run a caching HTTP server. All requests get forwarded to an upstream server
    and cached on disk.
    '''
    parser = argparse.ArgumentParser(description=cache.__doc__)
    parser.add_argument('upstream',
                        help='Upstream HTTP server to forward requests to')
    parser.add_argument('--state-dir', dest='state_dir',
                        help='Directory to cache requests in',
                        default=os.path.join(os.path.expanduser('~'),
                                             '.cache', 'httptest'))
    parser.add_argument(
        "--addr", help="Address to bind to (default 127.0.0.1)", default="127.0.0.1"
    )
    parser.add_argument(
        "--port", help="Port to bind to (default random)", type=int, default=0
    )

    args = parser.parse_args()

    @Server(
        CachingProxyHandler.to(args.upstream, state_dir=args.state_dir),
        addr=(args.addr, args.port),
    )
    def waiter(ts):
        print('Serving on http://%s:%d' % (ts.server_name, ts.server_port,))
        while True:
            time.sleep(60)

    try:
        waiter()
    except KeyboardInterrupt:
        pass
