"""``TurnstileField`` against a mocked Cloudflare.

The rest of the suite runs it in testing mode, where it answers from a setting.
"""

import logging

import pytest
import responses
from django.core.exceptions import ImproperlyConfigured
from requests.exceptions import ConnectionError
from rest_framework.serializers import ValidationError

from common.rest_framework.turnstile import TurnstileField

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
INVALID = "Error verifying captcha, please try again."


@pytest.fixture
def live_turnstile(settings):
    """Take the field out of testing mode and give it a secret."""
    settings.TURNSTILE_TESTING = False
    settings.TURNSTILE_SECRET_KEY = "a-secret"  # nosec


def verify(token="a-token"):
    return TurnstileField().run_validation(token)


class TestTestingMode:
    def test_it_accepts_anything_while_told_to_pass(self, settings):
        settings.TURNSTILE_TESTING = True
        settings.TURNSTILE_TESTING_PASS = True

        assert verify() == "a-token"

    def test_it_rejects_everything_while_told_to_fail(self, settings):
        settings.TURNSTILE_TESTING = True
        settings.TURNSTILE_TESTING_PASS = False

        with pytest.raises(ValidationError) as error:
            verify()

        assert error.value.detail[0] == INVALID

    def test_it_passes_by_default_in_testing_mode(self, settings):
        settings.TURNSTILE_TESTING = True
        del settings.TURNSTILE_TESTING_PASS

        assert verify() == "a-token"


class TestLiveVerification:
    @responses.activate
    def test_a_token_cloudflare_accepts_passes(self, live_turnstile):
        responses.post(SITEVERIFY_URL, json={"success": True})

        assert verify() == "a-token"

        # The secret must never travel anywhere but Cloudflare.
        assert responses.calls[0].request.url == SITEVERIFY_URL
        assert "secret=a-secret" in responses.calls[0].request.body

    @responses.activate
    def test_a_token_cloudflare_rejects_fails(self, live_turnstile):
        responses.post(
            SITEVERIFY_URL,
            json={"success": False, "error-codes": ["invalid-input-response"]},
        )

        with pytest.raises(ValidationError) as error:
            verify()

        assert error.value.detail[0] == INVALID

    @responses.activate
    def test_cloudflare_returning_an_error_status_fails_closed(self, live_turnstile):
        responses.post(SITEVERIFY_URL, status=500)

        with pytest.raises(ValidationError) as error:
            verify()

        assert error.value.detail[0] == INVALID

    @responses.activate
    def test_cloudflare_being_unreachable_fails_closed_and_is_logged(
        self, caplog, live_turnstile
    ):
        responses.post(SITEVERIFY_URL, body=ConnectionError("no route to host"))

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValidationError):
                verify()

        assert "Failed to verify Turnstile captcha" in caplog.text

    def test_a_missing_secret_is_a_configuration_error_not_a_rejection(self, settings):
        # Failing closed here would hide a deployment mistake behind a message
        # telling the visitor to try again.
        settings.TURNSTILE_TESTING = False
        settings.TURNSTILE_SECRET_KEY = None

        with pytest.raises(ImproperlyConfigured):
            verify()


def test_the_field_is_never_serialized_back_out():
    assert TurnstileField().write_only is True
