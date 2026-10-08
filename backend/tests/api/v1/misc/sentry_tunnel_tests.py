import json

import pytest
import requests
import responses
from django.test import Client
from django.urls import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_502_BAD_GATEWAY,
)

DSN = "https://public@o1.ingest.sentry.io/2"
ENVELOPE_URL = "https://o1.ingest.sentry.io/api/2/envelope/"


@pytest.fixture(autouse=True)
def frontend_dsn(settings):
    settings.SENTRY_FRONTEND_DSN = DSN


@pytest.fixture
def client():
    # The Sentry SDK posts without a CSRF token.
    return Client(enforce_csrf_checks=True)


def post_envelope(client, body):
    return client.post(
        reverse("api:v1:misc:sentry_tunnel"),
        body,
        content_type="text/plain;charset=UTF-8",
    )


def make_envelope(dsn):
    header = json.dumps({"dsn": dsn, "event_id": "9ec79c33ec9942ab8353589fcb2e04dc"})
    item_header = json.dumps({"type": "event"})
    item = json.dumps({"message": "Something broke"})
    return f"{header}\n{item_header}\n{item}"


@responses.activate
@pytest.mark.parametrize("status", [HTTP_200_OK, HTTP_429_TOO_MANY_REQUESTS])
def test_forwards_frontend_envelope(client, status):
    sentry = responses.post(ENVELOPE_URL, status=status)
    envelope = make_envelope(DSN)

    response = post_envelope(client, envelope)

    assert response.status_code == status
    assert sentry.call_count == 1
    assert sentry.calls[0].request.body == envelope.encode()


@responses.activate
def test_passes_on_rate_limits(client):
    rate_limits = "60:error:organization:usage_exceeded"
    responses.post(
        ENVELOPE_URL,
        headers={"Retry-After": "60", "X-Sentry-Rate-Limits": rate_limits},
        status=HTTP_429_TOO_MANY_REQUESTS,
    )

    response = post_envelope(client, make_envelope(DSN))

    assert response.status_code == HTTP_429_TOO_MANY_REQUESTS
    assert response["Retry-After"] == "60"
    assert response["X-Sentry-Rate-Limits"] == rate_limits


@responses.activate
@pytest.mark.parametrize(
    "dsn",
    [
        "https://public@o1.ingest.sentry.io/3",
        "https://public@example.com/2",
        None,
    ],
)
def test_rejects_other_dsn(client, dsn):
    response = post_envelope(client, make_envelope(dsn))

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert len(responses.calls) == 0


@responses.activate
@pytest.mark.parametrize("body", ["", "not json", "[]"])
def test_rejects_malformed_envelope(client, body):
    response = post_envelope(client, body)

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert len(responses.calls) == 0


@responses.activate
def test_sentry_unreachable(client):
    responses.post(ENVELOPE_URL, body=requests.ConnectionError())

    response = post_envelope(client, make_envelope(DSN))

    assert response.status_code == HTTP_502_BAD_GATEWAY


def test_only_post(client):
    response = client.get(reverse("api:v1:misc:sentry_tunnel"))

    assert response.status_code == HTTP_405_METHOD_NOT_ALLOWED
