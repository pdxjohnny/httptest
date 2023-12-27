import sys
import json
import time
import pathlib
import argparse
import contextlib
import urllib.request
from typing import Union, Optional

import httptest

import jwt
import jwcrypto.jwt


class TestOIDCHTTPServer(httptest.Handler):
    def do_GET(self):
        if self.path == "/token":
            self.json(
                {
                    "token": jwt.encode(
                        {
                            "iss": self.server.config["issuer"],
                            "aud": self.server.config["audience"],
                            "sub": self.server.config["subject"],
                        },
                        self.server.config["key"].export_to_pem(
                            private_key=True, password=None
                        ),
                        algorithm=self.server.config["algorithm"],
                        headers={"kid": self.server.config["key"].thumbprint()},
                    )
                }
            )
        elif self.path == "/.well-known/openid-configuration":
            self.json(
                {
                    "issuer": self.server.config["issuer"],
                    "jwks_uri": f'{self.server.config["issuer"]}/.well-known/jwks',
                    "response_types_supported": ["id_token"],
                    "claims_supported": ["sub", "aud", "exp", "iat", "iss"],
                    "id_token_signing_alg_values_supported": [
                        self.server.config["algorithm"]
                    ],
                    "scopes_supported": ["openid"],
                }
            )
        elif self.path == "/.well-known/jwks":
            self.json(
                {
                    "keys": [
                        {
                            **self.server.config["key"].export_public(as_dict=True),
                            "use": "sig",
                            "kid": self.server.config["key"].thumbprint(),
                        }
                    ]
                }
            )


def start_server(
    issuer: str,
    subject: str,
    audience: str,
    *,
    port: int = 0,
    addr: str = "127.0.0.1",
    private_key_pem_path: Optional[pathlib.Path] = None,
    token_path: Optional[pathlib.Path] = None,
):
    # Create or read in key
    algorithm = "RS256"
    if private_key_pem_path is not None and private_key_pem_path.exists():
        key = jwcrypto.jwt.JWK()
        key.import_from_pem(private_key_pem_path.read_bytes())
    else:
        key = jwcrypto.jwk.JWK.generate(kty="RSA", size=2048)
        if private_key_pem_path is not None:
            private_key_pem_path.write_bytes(
                key.export_to_pem(private_key=True, password=None),
            )

    with httptest.Server(
        TestOIDCHTTPServer,
        addr=(addr, port),
        config={
            "key": key,
            "algorithm": algorithm,
            "issuer": issuer,
            "subject": subject,
            "audience": audience,
        },
    ) as ts:
        if token_path is not None:
            with urllib.request.urlopen(ts.url() + "/token") as response:
                token_path.write_text(json.loads(response.read())["token"])
        print(ts.url())
        sys.stdout.flush()
        sys.stdout.close()
        sys.stdout = sys.stderr
        with contextlib.suppress(KeyboardInterrupt):
            while True:
                time.sleep(600)


def cli(fn):
    p = fn("oidc-server", description="Tiny single key OIDC server")
    p.add_argument("--issuer", required=True, type=str)
    p.add_argument("--subject", required=True, type=str)
    p.add_argument("--audience", required=True, type=str)
    p.add_argument("--port", required=False, type=int, default=0)
    p.add_argument("--addr", required=False, type=str, default="127.0.0.1")
    p.add_argument("--token-path", required=False, type=pathlib.Path)
    p.add_argument("--private-key-pem-path", required=False, type=pathlib.Path)

    return p


def main(argv=None):
    parser = cli(argparse.ArgumentParser)
    args = parser.parse_args(argv)
    start_server(**vars(args))


if __name__ == "__main__":
    main()
