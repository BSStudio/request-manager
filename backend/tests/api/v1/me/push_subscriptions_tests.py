import pytest
from model_bakery import baker
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    is_success,
)

from common.models import PushSubscription
from tests.api.helpers import do_login, login
from tests.api.matrix import any_user
from tests.factories import make_user

pytestmark = pytest.mark.django_db

ENDPOINT = "https://fcm.googleapis.com/fcm/send/abc123"
# What the browser's PushSubscription.toJSON() returns.
BODY = {
    "endpoint": ENDPOINT,
    "expirationTime": None,
    "keys": {"auth": "YXV0aA", "p256dh": "cDI1NmRo"},
}


@any_user(HTTP_204_NO_CONTENT)
def test_registering_a_browser_twice_keeps_one_row(api_client, expected, request, user):
    user = do_login(api_client, request, user)

    for _ in range(2):
        response = api_client.post(
            reverse("api:v1:me:push-subscription-list"), BODY, format="json"
        )

    assert response.status_code == expected
    if is_success(response.status_code):
        assert list(
            PushSubscription.objects.values_list("user", "endpoint", "p256dh", "auth")
        ) == [(user.id, ENDPOINT, "cDI1NmRo", "YXV0aA")]


def test_a_browser_registered_by_someone_else_moves_to_me(api_client, basic_user):
    baker.make(PushSubscription, endpoint=ENDPOINT, user=make_user())
    login(api_client, basic_user)

    api_client.post(reverse("api:v1:me:push-subscription-list"), BODY, format="json")

    assert PushSubscription.objects.get().user == basic_user


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://internal.example/push",
        "http://fcm.googleapis.com/fcm/send/abc",
        "http://localhost:6379/",
        "https://fcm.googleapis.com.example.com/x",
        "https://evilfcm.googleapis.com/x",
    ],
)
def test_only_push_service_endpoints_are_accepted(api_client, basic_user, endpoint):
    login(api_client, basic_user)

    response = api_client.post(
        reverse("api:v1:me:push-subscription-list"),
        BODY | {"endpoint": endpoint},
        format="json",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert not PushSubscription.objects.exists()


@pytest.mark.parametrize(
    "endpoint",
    [
        ENDPOINT,
        "https://updates.push.services.mozilla.com/wpush/v2/abc",
        "https://web.push.apple.com/abc",
        "https://wns2-par02p.notify.windows.com/w/?token=abc",
    ],
)
def test_the_push_services_browsers_use_are_accepted(api_client, basic_user, endpoint):
    login(api_client, basic_user)

    response = api_client.post(
        reverse("api:v1:me:push-subscription-list"),
        BODY | {"endpoint": endpoint},
        format="json",
    )

    assert response.status_code == HTTP_204_NO_CONTENT


@pytest.mark.parametrize("whose,remaining", [("mine", 0), ("someone_else", 1)])
def test_removing_deletes_only_my_row(api_client, basic_user, whose, remaining):
    owner = basic_user if whose == "mine" else make_user()
    baker.make(PushSubscription, endpoint=ENDPOINT, user=owner)
    login(api_client, basic_user)

    response = api_client.post(
        reverse("api:v1:me:push-subscription-remove"), {"endpoint": ENDPOINT}
    )

    assert response.status_code == HTTP_204_NO_CONTENT
    assert PushSubscription.objects.count() == remaining


@pytest.mark.parametrize(
    "public_key,status", [("BPublic", HTTP_200_OK), (None, HTTP_404_NOT_FOUND)]
)
def test_the_public_key_is_served_only_when_push_is_on(
    api_client, basic_user, settings, public_key, status
):
    settings.WEB_PUSH_VAPID_PUBLIC_KEY = public_key
    settings.WEB_PUSH_VAPID_PRIVATE_KEY = "priv"
    settings.WEB_PUSH_CONTACT = "mailto:push@example.com"
    login(api_client, basic_user)

    response = api_client.get(reverse("api:v1:me:push-subscription-key"))

    assert response.status_code == status
    if public_key:
        assert response.data == {"public_key": public_key}
