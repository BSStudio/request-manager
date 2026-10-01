"""Logging in through each identity provider, over social_core's real pipeline.

The provider endpoints are mocked in tests/helpers/oauth2_providers.py.
"""

import pytest
import responses
from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from tests.factories import make_user
from tests.helpers.oauth2_providers import (
    ALL_PROVIDERS,
    GOOGLE,
    MICROSOFT,
    MICROSOFT_AVATAR_URL,
)

pytestmark = pytest.mark.django_db

by_name = {"ids": lambda provider: provider.name}


def log_in(api_client, mocked):
    return api_client.post(
        reverse("api:v1:login:social"),
        {"provider": mocked.name, "code": mocked.code()},
    )


@pytest.mark.parametrize("provider", ALL_PROVIDERS, **by_name)
def test_login_hands_back_a_usable_token_pair(api_client, mock_provider, provider):
    mocked = mock_provider(provider)

    response = log_in(api_client, mocked)

    assert response.status_code == HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data

    access_token = AccessToken(response.data["access"])
    refresh_token = RefreshToken(response.data["refresh"])

    assert access_token["token_type"] == "access"
    assert refresh_token["token_type"] == "refresh"
    # Raises when the check fails, returns None otherwise.
    assert access_token.verify() is None


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
    # away, by e-mail, before any token is minted.
    banned_user = make_user(email=GOOGLE.user_data_body["email"], banned=True)
    mocked = mock_provider(GOOGLE)

    response = log_in(api_client, mocked)

    assert response.status_code == HTTP_400_BAD_REQUEST
    # The reason ("Your account is suspended.") is logged, not handed back:
    # handle_exception only forwards messages it can read off the exception.
    assert response.data is None
    assert not banned_user.social_auth.exists()
