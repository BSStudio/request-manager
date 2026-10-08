from unittest.mock import patch

import pytest
import sentry_sdk
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from common.middleware import RequestLoggingMiddleware, SentryUserMiddleware


def resolve(remote_addr, forwarded=None):
    request = RequestFactory().get("/")
    request.META["REMOTE_ADDR"] = remote_addr
    if forwarded is None:
        request.META.pop("HTTP_X_FORWARDED_FOR", None)
    else:
        request.META["HTTP_X_FORWARDED_FOR"] = forwarded
    return RequestLoggingMiddleware._client_ip(request)


@pytest.mark.parametrize(
    "remote_addr,forwarded,expected",
    [
        # No proxy in front of us at all.
        ("172.21.0.3", None, "172.21.0.3"),
        # The peer is the trusted proxy; the client sits left of it.
        ("172.21.0.3", "203.0.113.7", "203.0.113.7"),
        ("172.21.0.3", "203.0.113.7, 10.0.0.5, 192.168.1.2", "203.0.113.7"),
        # The client prepends a fake internal IP. It stays left of the real hop
        # and must not be mistaken for the client.
        ("172.21.0.3", "10.9.9.9, 203.0.113.7", "203.0.113.7"),
        # Every hop is trusted, so there is no client address to find.
        ("172.21.0.3", "10.0.0.1, 192.168.0.1", "172.21.0.3"),
        ("172.21.0.3", "not-an-ip, 203.0.113.7", "203.0.113.7"),
        # Even REMOTE_ADDR fails to parse; the loop exhausts and returns it.
        ("garbage", "also-bad", "garbage"),
    ],
    ids=[
        "no_forwarded_header",
        "single_trusted_proxy",
        "multiple_trusted_proxies",
        "client_spoofed_entry",
        "all_hops_trusted",
        "malformed_entry",
        "all_entries_unparseable",
    ],
)
def test_client_ip(remote_addr, forwarded, expected):
    assert resolve(remote_addr, forwarded) == expected


class UserView(APIView):
    def get(self, request):
        return Response({"id": request.user.pk})


def sentry_user(request, view=lambda request: HttpResponse()):
    """The user of an event that Sentry sends during the request."""
    with (
        sentry_sdk.isolation_scope() as scope,
        patch("common.middleware.sentry_sdk.is_initialized", return_value=True),
    ):
        SentryUserMiddleware(view)(request)
        return scope.apply_to_event({}, {}).get("user")


@pytest.mark.django_db
def test_sentry_user_is_only_the_id(basic_user):
    request = RequestFactory().get("/")
    request.user = basic_user

    assert sentry_user(request) == {"id": basic_user.pk}


@pytest.mark.django_db
def test_sentry_user_of_api_token(service_account):
    token = Token.objects.get_or_create(user=service_account)[0]
    request = RequestFactory().get("/", HTTP_AUTHORIZATION=f"Token {token}")
    request.user = AnonymousUser()

    assert sentry_user(request, UserView.as_view()) == {"id": service_account.pk}


def test_sentry_user_not_set_when_logged_out():
    request = RequestFactory().get("/")
    request.user = AnonymousUser()

    assert sentry_user(request) is None
