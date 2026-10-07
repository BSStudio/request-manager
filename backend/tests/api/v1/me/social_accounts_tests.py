"""Connecting and disconnecting the login methods on an existing account.

The pipeline steps deciding whether a disconnect is allowed are unit tested in
tests/unit/common/social_core/pipeline_tests.py.
"""

import pytest
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
)
from social_core.exceptions import NotAllowedToDisconnect
from social_django.models import UserSocialAuth

from tests.api.helpers import login
from tests.helpers.oauth2_providers import ALL_PROVIDERS, GOOGLE, MICROSOFT

pytestmark = pytest.mark.django_db

by_name = {"ids": lambda provider: provider.name}


def social_url(provider_name):
    return reverse(
        "api:v1:me:social_connect_disconnect", kwargs={"provider": provider_name}
    )


def connect(api_client, mocked):
    return api_client.post(
        social_url(mocked.name), {"code": mocked.code(), "nonce": mocked.nonce}
    )


class TestConnect:
    @pytest.mark.parametrize("provider", ALL_PROVIDERS, **by_name)
    def test_a_provider_can_be_added_to_an_account(
        self, api_client, basic_user, mock_provider, provider
    ):
        login(api_client, basic_user)
        mocked = mock_provider(provider)

        response = connect(api_client, mocked)

        assert response.status_code == HTTP_201_CREATED
        assert UserSocialAuth.objects.filter(
            user=basic_user, provider=provider.name
        ).exists()

    def test_a_second_provider_joins_the_first(
        self, api_client, basic_user, mock_provider
    ):
        login(api_client, basic_user)
        connect(api_client, mock_provider(GOOGLE))
        connect(api_client, mock_provider(MICROSOFT))

        assert set(basic_user.social_auth.values_list("provider", flat=True)) == {
            GOOGLE.name,
            MICROSOFT.name,
        }

    def test_reconnecting_the_same_account_is_idempotent(
        self, api_client, basic_user, mock_provider
    ):
        # The provider hands back the same uid, so this is not a new
        # association and the one-per-provider rule does not fire.
        login(api_client, basic_user)
        assert connect(api_client, mock_provider(GOOGLE)).status_code == (
            HTTP_201_CREATED
        )

        response = connect(api_client, mock_provider(GOOGLE))

        assert response.status_code == HTTP_201_CREATED
        assert basic_user.social_auth.filter(provider=GOOGLE.name).count() == 1

    def test_a_provider_already_on_somebody_else_is_refused(
        self, api_client, basic_user, mock_provider, staff_user
    ):
        login(api_client, staff_user)
        assert connect(api_client, mock_provider(GOOGLE)).status_code == (
            HTTP_201_CREATED
        )

        login(api_client, basic_user)
        response = connect(api_client, mock_provider(GOOGLE))

        assert response.status_code == HTTP_400_BAD_REQUEST
        assert not basic_user.social_auth.exists()

    def test_an_unknown_provider_is_rejected(self, api_client, basic_user):
        login(api_client, basic_user)

        response = api_client.post(social_url("not-a-provider"), {"code": "whatever"})

        assert response.status_code == HTTP_400_BAD_REQUEST
        assert response.data["provider"] == "Invalid provider."

    def test_the_code_is_required(self, api_client, basic_user):
        login(api_client, basic_user)

        response = api_client.post(social_url(GOOGLE.name), {})

        assert response.status_code == HTTP_400_BAD_REQUEST
        assert "code" in response.data

    def test_an_anonymous_caller_cannot_connect_anything(self, api_client):
        response = api_client.post(social_url(GOOGLE.name), {"code": "whatever"})

        assert response.status_code == HTTP_401_UNAUTHORIZED


class TestDisconnect:
    @pytest.fixture
    def two_providers(self, api_client, basic_user, mock_provider):
        login(api_client, basic_user)
        for provider in (GOOGLE, MICROSOFT):
            assert connect(api_client, mock_provider(provider)).status_code == (
                HTTP_201_CREATED
            )
        return basic_user

    def test_one_of_two_login_methods_can_be_dropped(self, api_client, two_providers):
        response = api_client.delete(social_url(GOOGLE.name))

        assert response.status_code == HTTP_204_NO_CONTENT
        assert list(two_providers.social_auth.values_list("provider", flat=True)) == [
            MICROSOFT.name
        ]

    def test_dropping_a_provider_that_was_not_connected_changes_nothing(
        self, api_client, two_providers
    ):
        response = api_client.delete(social_url("authsch"))

        assert response.status_code == HTTP_204_NO_CONTENT
        assert two_providers.social_auth.count() == 2

    def test_an_unknown_provider_is_rejected(self, api_client, basic_user):
        login(api_client, basic_user)

        response = api_client.delete(social_url("not-a-provider"))

        assert response.status_code == HTTP_400_BAD_REQUEST
        assert response.data["provider"] == "Invalid provider."

    def test_an_anonymous_caller_cannot_disconnect_anything(self, api_client):
        response = api_client.delete(social_url(GOOGLE.name))

        assert response.status_code == HTTP_401_UNAUTHORIZED

    @pytest.mark.xfail(
        raises=NotAllowedToDisconnect,
        strict=True,
        reason=(
            "Bug: delete() lets the pipeline's NotAllowedToDisconnect escape, so "
            "removing your only way of logging in answers 500 instead of a 400 "
            "carrying the reason. post() funnels the same exceptions through "
            "handle_exception."
        ),
    )
    def test_the_last_login_method_cannot_be_dropped(
        self, api_client, basic_user, mock_provider
    ):
        login(api_client, basic_user)
        assert connect(api_client, mock_provider(GOOGLE)).status_code == (
            HTTP_201_CREATED
        )

        response = api_client.delete(social_url(GOOGLE.name))

        assert response.status_code == HTTP_400_BAD_REQUEST
        assert basic_user.social_auth.count() == 1

    def test_staff_may_drop_their_last_login_method(
        self, api_client, mock_provider, staff_user
    ):
        # Staff can be signed in again through BSS Login, so the guard lets them.
        login(api_client, staff_user)
        assert connect(api_client, mock_provider(GOOGLE)).status_code == (
            HTTP_201_CREATED
        )

        response = api_client.delete(social_url(GOOGLE.name))

        assert response.status_code == HTTP_204_NO_CONTENT
        assert not staff_user.social_auth.exists()
