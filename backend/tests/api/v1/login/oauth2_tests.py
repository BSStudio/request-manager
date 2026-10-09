"""Logging in through each identity provider, over social_core's real pipeline.

The provider endpoints are mocked in tests/helpers/oauth2_providers.py.
"""

from urllib.parse import parse_qs, urlparse

import pytest
import responses
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK, HTTP_302_FOUND, HTTP_400_BAD_REQUEST
from social_core.exceptions import AuthTokenError

from tests.factories import make_user
from tests.helpers.oauth2_providers import (
    AUTHSCH,
    BSS_LOGIN,
    GOOGLE,
    MICROSOFT,
    MICROSOFT_AVATAR_URL,
)

pytestmark = pytest.mark.django_db

OPENID_PROVIDERS = pytest.mark.parametrize(
    "provider", [AUTHSCH, BSS_LOGIN], ids=lambda provider: provider.name
)


def log_in(api_client, mocked, nonce=None):
    return api_client.post(
        reverse("api:v1:login:social"),
        {
            "provider": mocked.name,
            "code": mocked.code(),
            "nonce": mocked.browser_nonce if nonce is None else nonce,
        },
    )


def log_in_to_django_admin(client, mocked, nonce=None, next_url=None):
    # Here social_django builds the authorization URL, not the frontend.
    start = client.post(
        reverse("social:begin", args=[mocked.name]),
        {} if next_url is None else {"next": next_url},
    )
    query = parse_qs(urlparse(start.url).query)
    mocked.nonce = query["nonce"][0] if nonce is None else nonce
    return client.get(
        reverse("social:complete", args=[mocked.name]),
        {"code": mocked.code(), "state": query["state"][0]},
    )


@OPENID_PROVIDERS
@pytest.mark.parametrize("nonce", ["", "someone-elses"], ids=["empty", "foreign"])
def test_openid_login_needs_the_nonce_of_the_browser_that_started_it(
    api_client, mock_provider, provider, nonce
):
    mocked = mock_provider(provider)

    response = log_in(api_client, mocked, nonce)

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert (
        not get_user_model()
        .objects.filter(email__iexact=provider.user_data_body["email"])
        .exists()
    )


@OPENID_PROVIDERS
def test_openid_login_does_not_accept_the_nonce_the_provider_got(
    api_client, mock_provider, provider
):
    # That is the hash, which the state in the redirect URL gives away too.
    mocked = mock_provider(provider)

    response = log_in(api_client, mocked, mocked.nonce)

    assert response.status_code == HTTP_400_BAD_REQUEST


@OPENID_PROVIDERS
def test_openid_login_allows_the_provider_clock_to_run_ahead(
    api_client, mock_provider, provider
):
    mocked = mock_provider(provider)
    mocked.clock_ahead_seconds = 30

    assert log_in(api_client, mocked).status_code == HTTP_200_OK


@OPENID_PROVIDERS
def test_django_admin_login_checks_the_nonce_social_core_stored(
    client, mock_provider, provider
):
    response = log_in_to_django_admin(client, mock_provider(provider))

    assert response.status_code == HTTP_302_FOUND
    assert response.url == settings.SOCIAL_AUTH_LOGIN_REDIRECT_URL


def test_django_admin_login_returns_to_the_page_it_started_from(client, mock_provider):
    next_url = reverse("admin:video_requests_request_changelist")

    response = log_in_to_django_admin(
        client, mock_provider(BSS_LOGIN), next_url=next_url
    )

    assert response.status_code == HTTP_302_FOUND
    assert response.url == next_url


@OPENID_PROVIDERS
@pytest.mark.parametrize("nonce", ["", "someone-elses"], ids=["empty", "foreign"])
def test_django_admin_login_rejects_a_nonce_social_core_did_not_store(
    client, mock_provider, provider, nonce
):
    with pytest.raises(AuthTokenError, match="nonce"):
        log_in_to_django_admin(client, mock_provider(provider), nonce)


def test_login_matches_an_inactive_placeholder_account(api_client, mock_provider):
    # The anonymous request flow creates inactive placeholder accounts holding
    # the requester's e-mail. A first social login must match one of those
    # instead of creating a duplicate user.
    user_model = get_user_model()
    placeholder = user_model.objects.create_user(
        username="foobar@foobar.com",
        email="foobar@foobar.com",
        is_active=False,
    )
    placeholder.set_unusable_password()
    placeholder.save()

    mocked = mock_provider(MICROSOFT)
    assert log_in(api_client, mocked).status_code == HTTP_200_OK

    placeholder.refresh_from_db()
    assert placeholder.is_active
    assert user_model.objects.filter(email__iexact="foobar@foobar.com").count() == 1
    assert placeholder.social_auth.filter(provider="microsoft-graph").exists()


def test_login_without_any_photo_leaves_the_avatar_provider_unset(
    api_client, mock_provider
):
    # No Microsoft photo and no Gravatar must leave the provider unset, so
    # User.full_clean() does not later reject a dangling provider.
    mocked = mock_provider(MICROSOFT)
    responses.replace(responses.GET, MICROSOFT_AVATAR_URL, status=404)

    assert log_in(api_client, mocked).status_code == HTTP_200_OK

    user = get_user_model().objects.get(email__iexact="foobar@foobar.com")
    assert user.avatar.get("provider") is None
    assert user.avatar_url is None


def test_a_banned_account_cannot_log_in(api_client, mock_provider):
    # The provider still authenticates them; the pipeline is what turns them
    # away, by e-mail, before a session starts.
    banned_user = make_user(email=GOOGLE.user_data_body["email"], banned=True)
    mocked = mock_provider(GOOGLE)

    response = log_in(api_client, mocked)

    assert response.status_code == HTTP_400_BAD_REQUEST
    # The reason ("Your account is suspended.") is logged, not handed back:
    # handle_exception only forwards messages it can read off the exception.
    assert response.data is None
    assert not banned_user.social_auth.exists()
