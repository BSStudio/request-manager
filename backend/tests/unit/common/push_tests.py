import pytest
import requests
import responses
from model_bakery import baker

from common.models import PushSubscription
from common.push import PUSH_TTL, push_enabled, send_push
from tests.factories import make_user
from tests.helpers.push import b64, subscribe

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "public,private,contact,enabled",
    [
        ("pub", "priv", "mailto:push@example.com", True),
        (None, "priv", "mailto:push@example.com", False),
        ("pub", None, "mailto:push@example.com", False),
        ("pub", "priv", None, False),
    ],
)
def test_push_is_on_only_with_all_three_settings(
    settings, public, private, contact, enabled
):
    settings.WEB_PUSH_VAPID_PUBLIC_KEY = public
    settings.WEB_PUSH_VAPID_PRIVATE_KEY = private
    settings.WEB_PUSH_CONTACT = contact

    assert push_enabled() is enabled


@responses.activate
def test_a_push_goes_to_every_browser_with_a_week_to_live(push_on):
    user = make_user()
    for name in ("a", "b"):
        subscribe(user, f"https://fcm.googleapis.com/fcm/send/{name}")
        responses.post(f"https://fcm.googleapis.com/fcm/send/{name}", status=201)

    send_push(user, {"title": "Új felkérés"})

    assert len(responses.calls) == 2
    for call in responses.calls:
        assert call.request.headers["TTL"] == str(PUSH_TTL)
        assert call.request.headers["Authorization"].startswith("vapid ")
        assert call.request.req_kwargs["timeout"] == 10


@pytest.mark.parametrize("status", [404, 410])
@responses.activate
def test_a_gone_browser_is_forgotten(push_on, status):
    subscription = subscribe(make_user())
    responses.post(subscription.endpoint, status=status)

    send_push(subscription.user, {})

    assert not PushSubscription.objects.exists()


@pytest.mark.parametrize(
    "answer",
    [
        {"status": 500},
        {"body": requests.ConnectionError("down")},
        {"body": requests.Timeout("slow")},
    ],
    ids=["server_error", "unreachable", "timeout"],
)
@responses.activate
def test_a_failing_push_service_is_logged_without_the_endpoint(push_on, caplog, answer):
    user = make_user()
    failing = subscribe(user, "https://fcm.googleapis.com/fcm/send/failing")
    working = subscribe(user, "https://fcm.googleapis.com/fcm/send/working")
    responses.post(failing.endpoint, **answer)
    responses.post(working.endpoint, status=201)

    send_push(user, {})

    assert PushSubscription.objects.count() == 2
    assert len(responses.calls) == 2
    assert f"subscription {failing.id}" in caplog.text
    assert failing.endpoint not in caplog.text


@pytest.mark.parametrize(
    "p256dh", [b64(b"\x04" + b"\x01" * 64), "a"], ids=["off_curve", "not_base64"]
)
@responses.activate
def test_a_browser_with_broken_keys_is_logged(push_on, caplog, p256dh):
    user = make_user()
    broken = baker.make(
        PushSubscription,
        user=user,
        endpoint="https://fcm.googleapis.com/fcm/send/broken",
        p256dh=p256dh,
        auth="YXV0aA",
    )
    working = subscribe(user, "https://fcm.googleapis.com/fcm/send/working")
    responses.post(working.endpoint, status=201)

    send_push(user, {})

    assert len(responses.calls) == 1
    assert PushSubscription.objects.count() == 2
    assert f"subscription {broken.id}" in caplog.text


@responses.activate
def test_nothing_is_sent_while_push_is_off(settings):
    settings.WEB_PUSH_VAPID_PRIVATE_KEY = None
    user = make_user()
    subscribe(user)

    send_push(user, {})

    assert not responses.calls
