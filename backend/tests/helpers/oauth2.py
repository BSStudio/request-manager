"""Mocked OAuth2 identity providers, shared by the login and connect flows.

An OAuth2 round trip needs three endpoints answering — the provider's authorize
redirect, its token endpoint and its userinfo endpoint — plus whatever extras a
given provider reads (a phone number, a profile photo). :class:`Provider`
describes one of them; :func:`mock_provider` stands it up with ``responses`` and
resets the module-level caches social_core keeps between tests.
"""

import random
import re
from dataclasses import dataclass, field
from string import ascii_letters, digits
from urllib.parse import urlparse

import responses
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

        start_url = self.backend.start().url
        target_url = self._target_url(start_url)
        responses.get(start_url, status=301, headers={"Location": target_url})
        responses.get(target_url, status=200, body="foobar")
        if self.provider.user_data_url:
            responses.get(
                self.provider.user_data_url, json=self.provider.user_data_body
            )

        responses.add(
            {"GET": responses.GET, "POST": responses.POST}[
                self.backend.ACCESS_TOKEN_METHOD
            ],
            self.backend.access_token_url(),
            status=200,
            json=self.provider.access_token_body,
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
        """A throwaway authorization code, as the provider would hand back."""
        return "".join(
            random.choice(ascii_letters + digits) for _ in range(15)
        )  # nosec
