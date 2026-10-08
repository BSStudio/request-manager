"""Mocked OAuth2 identity providers for the login and connect tests."""

import hashlib
import json
import random
import re
import time
from dataclasses import dataclass, field
from secrets import token_urlsafe
from string import ascii_letters, digits
from urllib.parse import urlparse

import jwt
import responses
from cryptography.hazmat.primitives.asymmetric import rsa
from social_core.backends.open_id_connect import OpenIdConnectAuth
from social_core.backends.utils import load_backends
from social_core.tests.models import (
    TestAssociation,
    TestCode,
    TestNonce,
    TestUserSocialAuth,
)
from social_core.tests.models import User as TestUser
from social_core.utils import module_member, parse_qs, url_add_parameters

from common.social_core.helpers import load_strategy

GRAVATAR_URL = re.compile(r"https://(www|secure)\.gravatar\.com/avatar/.*")

#: Signs the ID tokens of every mocked OpenID Connect provider.
ID_TOKEN_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
ID_TOKEN_KEY_ID = "test-key"

#: social_core caches these across tests; every test has to start from empty.
SOCIAL_CORE_CACHES = (
    TestUser,
    TestUserSocialAuth,
    TestNonce,
    TestAssociation,
    TestCode,
)


@dataclass(frozen=True)
class Provider:
    """Everything needed to impersonate one identity provider."""

    name: str
    backend_path: str
    user_data_url: str
    user_data_body: dict
    access_token_body: dict = field(
        default_factory=lambda: {"access_token": "foobar", "token_type": "bearer"}
    )
    #: Extra GET endpoints the backend or the pipeline reads, as url -> json.
    extra_json: dict = field(default_factory=dict)
    #: The same, for endpoints answering with a raw body. Values may be
    #: callables, so reading a fixture file off disk stays lazy.
    extra_body: dict = field(default_factory=dict)


def reset_social_core_caches():
    for cache in SOCIAL_CORE_CACHES:
        cache.reset_cache()


class MockedProvider:
    """A provider whose OAuth2 endpoints answer from ``responses``."""

    raw_complete_url = "/complete/{0}"

    def __init__(self, provider):
        self.provider = provider
        backend_class = module_member(provider.backend_path)
        self.strategy = load_strategy()
        self.backend = backend_class(self.strategy, redirect_uri="")
        self.complete_url = self.strategy.build_absolute_uri(
            self.raw_complete_url.format(self.backend.name)
        )
        # Force backends loading, to trash the PSA cache.
        load_backends((provider.backend_path,), force_load=True)
        self.browser_nonce = token_urlsafe()
        #: Goes into the ID token.
        self.nonce = hashlib.sha256(self.browser_nonce.encode()).hexdigest()

    @property
    def name(self):
        return self.provider.name

    def mock_endpoints(self):
        """Register every request the flow will make. Call inside ``responses``."""
        responses.get(GRAVATAR_URL, status=404)
        for url, body in self.provider.extra_json.items():
            responses.get(url, json=body)
        for url, body in self.provider.extra_body.items():
            responses.get(url, body=body() if callable(body) else body)
        if isinstance(self.backend, OpenIdConnectAuth):
            self._mock_discovery()

        start_url = self.backend.start().url
        target_url = self._target_url(start_url)
        responses.get(start_url, status=301, headers={"Location": target_url})
        responses.get(target_url, status=200, body="foobar")
        if self.provider.user_data_url:
            responses.get(
                self.provider.user_data_url, json=self.provider.user_data_body
            )

        # Answered on request, so a test can still change the nonce.
        responses.add_callback(
            {"GET": responses.GET, "POST": responses.POST}[
                self.backend.ACCESS_TOKEN_METHOD
            ],
            self.backend.access_token_url(),
            callback=lambda request: (200, {}, json.dumps(self._access_token_body())),
            content_type="application/json",
        )

    def _access_token_body(self):
        if isinstance(self.backend, OpenIdConnectAuth):
            return {**self.provider.access_token_body, "id_token": self.id_token()}
        return self.provider.access_token_body

    def _mock_discovery(self):
        endpoint = self.backend.OIDC_ENDPOINT
        responses.get(
            f"{endpoint}/.well-known/openid-configuration",
            json={
                "issuer": endpoint,
                "authorization_endpoint": f"{endpoint}/authorize",
                "token_endpoint": f"{endpoint}/token",
                "userinfo_endpoint": self.provider.user_data_url,
                "jwks_uri": f"{endpoint}/jwks",
            },
        )
        jwk = jwt.algorithms.RSAAlgorithm.to_jwk(
            ID_TOKEN_KEY.public_key(), as_dict=True
        )
        responses.get(
            f"{endpoint}/jwks",
            json={"keys": [{**jwk, "alg": "RS256", "kid": ID_TOKEN_KEY_ID}]},
        )

    def id_token(self):
        now = int(time.time())
        client_id, _ = self.backend.get_key_and_secret()
        claims = {
            "iss": self.backend.OIDC_ENDPOINT,
            "sub": self.provider.user_data_body["sub"],
            "aud": client_id,
            "iat": now,
            "exp": now + 300,
            "nonce": self.nonce,
        }
        return jwt.encode(
            claims, ID_TOKEN_KEY, algorithm="RS256", headers={"kid": ID_TOKEN_KEY_ID}
        )

    def _target_url(self, start_url):
        """Where the provider would redirect back to, state parameters included."""
        target_url = self.strategy.build_absolute_uri(self.complete_url)
        start_query = parse_qs(urlparse(start_url).query)
        redirect_uri = start_query.get("redirect_uri")

        if getattr(self.backend, "STATE_PARAMETER", False) and start_query.get("state"):
            target_url = url_add_parameters(target_url, {"state": start_query["state"]})

        if redirect_uri and getattr(self.backend, "REDIRECT_STATE", False):
            redirect_query = parse_qs(urlparse(redirect_uri).query)
            if redirect_query.get("redirect_state"):
                target_url = url_add_parameters(
                    target_url, {"redirect_state": redirect_query["redirect_state"]}
                )
        return target_url

    @staticmethod
    def code():
        return "".join(
            random.choice(ascii_letters + digits) for _ in range(15)
        )  # nosec
