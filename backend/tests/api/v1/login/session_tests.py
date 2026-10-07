import pytest
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_415_UNSUPPORTED_MEDIA_TYPE,
)
from rest_framework.test import APIClient

from common.models import Ban, User, get_system_user
from tests.helpers.oauth2_providers import ALL_PROVIDERS, GOOGLE

pytestmark = pytest.mark.django_db

ME_URL = reverse("api:v1:me:me-detail")


def log_in(client, mock_provider, provider=GOOGLE):
    mocked = mock_provider(provider)
    return client.post(
        reverse("api:v1:login:social"),
        {"provider": mocked.name, "code": mocked.code()},
    )


def logged_in_user():
    return User.objects.get(email__iexact=GOOGLE.user_data_body["email"])


@pytest.fixture
def csrf_client():
    return APIClient(enforce_csrf_checks=True)


@pytest.mark.parametrize("provider", ALL_PROVIDERS, ids=lambda p: p.name)
def test_login_starts_a_session(api_client, mock_provider, provider):
    response = log_in(api_client, mock_provider, provider)
    assert response.status_code == HTTP_200_OK

    user = User.objects.get(pk=response.data["id"])
    assert response.data["name"] == user.get_full_name_eastern_order()
    assert response.data["role"] == user.role
    assert response.data["avatar_url"] == user.avatar_url
    assert sorted(response.data["groups"]) == sorted(user.group_names)

    response = api_client.get(ME_URL)
    assert response.status_code == HTTP_200_OK
    assert response.data["id"] == user.id


def test_login_replaces_an_existing_session(api_client, mock_provider, basic_user):
    api_client.force_login(basic_user)

    assert log_in(api_client, mock_provider).status_code == HTTP_200_OK

    assert api_client.get(ME_URL).data["id"] == logged_in_user().id


def test_login_rejects_form_data(api_client, mock_provider):
    mocked = mock_provider(GOOGLE)

    response = api_client.post(
        reverse("api:v1:login:social"),
        {"provider": mocked.name, "code": mocked.code()},
        format="multipart",
    )

    assert response.status_code == HTTP_415_UNSUPPORTED_MEDIA_TYPE


def test_session_requests_need_a_csrf_token(csrf_client, mock_provider):
    log_in(csrf_client, mock_provider)
    data = {"first_name": "Changed"}

    assert csrf_client.patch(ME_URL, data).status_code == HTTP_403_FORBIDDEN

    response = csrf_client.patch(
        ME_URL, data, HTTP_X_CSRFTOKEN=csrf_client.cookies["csrftoken"].value
    )
    assert response.status_code == HTTP_200_OK


def test_logout_ends_the_session(csrf_client, mock_provider):
    log_in(csrf_client, mock_provider)

    response = csrf_client.post(
        reverse("api:v1:login:logout"),
        HTTP_X_CSRFTOKEN=csrf_client.cookies["csrftoken"].value,
    )

    assert response.status_code == HTTP_204_NO_CONTENT
    assert csrf_client.get(ME_URL).status_code == HTTP_401_UNAUTHORIZED


def test_logout_needs_a_session(api_client):
    response = api_client.post(reverse("api:v1:login:logout"))

    assert response.status_code == HTTP_401_UNAUTHORIZED


def test_a_ban_ends_the_session(api_client, mock_provider):
    log_in(api_client, mock_provider)

    Ban.objects.create(creator=get_system_user(), receiver=logged_in_user())

    assert api_client.get(ME_URL).status_code == HTTP_401_UNAUTHORIZED
