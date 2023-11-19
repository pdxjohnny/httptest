"""
Usage
*****

.. code-block:: console

    $ python github_webhook_event_logger.py -R org/repo
"""
import os
import sys
import json
import pathlib
import argparse
import subprocess
import http.server

import httptest


class GitHubWebhookLogger(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Content-length", 3)
        self.end_headers()
        self.wfile.write(b"OK\n")

        payload = json.loads(self.rfile.read())
        payload_path = pathlib.Path(
            ".".join(
                [
                    self.headers["X-github-event"],
                    *(
                        [
                            ":".join([key, value])
                            for key, value in payload.items()
                            if isinstance(value, str) and not os.sep in value
                        ]
                        + ["json"]
                    ),
                ],
            )
        )

        payload_path.write_text(json.dumps(payload, indent=4, sort_keys=True))

    @classmethod
    def cli(cls, argv=None):
        parser = argparse.ArgumentParser(description="Log GitHub webhook events")
        parser.add_argument(
            "-R",
            "--repo",
            dest="org_and_repo",
            required=True,
            type=str,
            help="GitHub repo in format org/repo",
        )
        parser.add_argument(
            "--state-dir",
            dest="state_dir",
            type=pathlib.Path,
            help="Directory to cache requests in",
            default=pathlib.Path(os.getcwd(), ".cache", "httptest"),
        )

        args = parser.parse_args(argv)

        if not args.state_dir.is_dir():
            args.state_dir.mkdir(parents=True)

        with httptest.Server(cls) as logging_server:
            with httptest.Server(
                httptest.CachingProxyHandler.to(
                    logging_server.url(), state_dir=str(args.state_dir.resolve())
                )
            ) as cache_server:
                subprocess.check_call(
                    [
                        "gh",
                        "webhook",
                        "forward",
                        f"--repo={args.org_and_repo}",
                        "--events=*",
                        f"--url={cache_server.url()}",
                    ]
                )


if __name__ == "__main__":
    GitHubWebhookLogger.cli(sys.argv[1:])
