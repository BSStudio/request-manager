from time import sleep

import pytest
from django.conf import settings
from django.contrib.auth.models import Group
from rest_framework.exceptions import ErrorDetail
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from common.models import User
from tests.api.helpers import login

pytestmark = pytest.mark.django_db


@pytest.mark.skip(reason="This needs to be moved to OAuth2 tests")
def test_login_inactive_user(api_client, basic_user):
    basic_user.is_active = False
    basic_user.save()

    url = reverse("api:v1:login:obtain_jwt_pair")
    response = api_client.post(
        url,
        {"username": basic_user.username, "password": "password"},
        format="json",
    )

    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.data["detail"] == ErrorDetail(
        string="No active account found with the given credentials",
        code="no_active_account",
    )


@pytest.mark.skip(reason="This needs to be moved to OAuth2 tests")
@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", "admin"),
        ("staff_user", "staff"),
        ("basic_user", "user"),
    ],
)
def test_custom_jwt_claims(api_client, expected, user, request):
    user = request.getfixturevalue(user)
    groups = ["Group1", "Group2", "Group3", "Group4", "Group5"]
    for group in groups:
        grp = Group.objects.get_or_create(name=group)[0]
        user.groups.add(grp)

    url = reverse("api:v1:login:obtain_jwt_pair")
    response = api_client.post(
        url,
        {"username": user.username, "password": "password"},
        format="json",
    )

    assert response.status_code == HTTP_200_OK

    token = AccessToken(response.data["access"])
    assert token.payload["avatar"] == user.userprofile.avatar_url
    for group in groups:
        assert group in token.payload["groups"]
    assert token.payload["name"] == user.get_full_name_eastern_order()
    assert token.payload["role"] == expected


def test_token_refresh(api_client, basic_user):
    refresh_url = reverse("api:v1:login:refresh_jwt_token")
    user_profile_url = reverse("api:v1:me:me-detail")

    # Create token
    token = RefreshToken.for_user(basic_user)

    # Set token
    access_token = str(token.access_token)
    refresh_token = str(token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    # Check if token works and user can access his profile
    response = api_client.get(user_profile_url)
    assert response.status_code == HTTP_200_OK

    # Wait for the token to expire
    sleep(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds() + 1)

    # The user should not be able to get the request because of the expired token
    response = api_client.get(user_profile_url)
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.data["detail"] == ErrorDetail(
        string="Given token not valid for any token type", code="token_not_valid"
    )

    # Use the refresh token for new access token
    response = api_client.post(refresh_url, {"refresh": refresh_token}, format="json")
    assert response.status_code == HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data

    # Check if new tokens were generated
    assert response.data["access"] != access_token
    assert response.data["refresh"] != refresh_token

    # Set the new access token
    access_token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    # Check if the new token works and user can access his profile again
    response = api_client.get(user_profile_url)
    assert response.status_code == HTTP_200_OK

    # The previous refresh token should be blacklisted and unable to use to get new tokens
    response = api_client.post(refresh_url, {"refresh": refresh_token}, format="json")
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.data["detail"] == ErrorDetail(
        string="Token is blacklisted", code="token_not_valid"
    )


def test_token_create_refresh_error_when_banned(admin_user, api_client, basic_user):
    logout_url = reverse("api:v1:login:logout")
    refresh_url = reverse("api:v1:login:refresh_jwt_token")

    # Create token
    token = RefreshToken.for_user(basic_user)

    # Set token
    access_token = str(token.access_token)
    refresh_token = str(token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    # Logout to create an already blacklisted token to test exception handling in signals.py
    response = api_client.post(logout_url, {"refresh": refresh_token}, format="json")
    assert response.status_code == HTTP_200_OK

    # Create token
    token = RefreshToken.for_user(basic_user)

    # Set token
    access_token = str(token.access_token)
    refresh_token = str(token)

    # Login as admin and ban user
    login(api_client, admin_user)
    url = reverse("api:v1:admin:users:user-ban", kwargs={"pk": basic_user.id})
    api_client.post(url, {})

    # Check if user is banned
    user = User.objects.get(pk=basic_user.id)
    assert not user.is_active
    assert user.ban.creator == admin_user

    # Try to refresh token of banned user
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    response = api_client.post(refresh_url, {"refresh": refresh_token}, format="json")
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.data["detail"] == ErrorDetail(
        string="Token is blacklisted", code="token_not_valid"
    )
