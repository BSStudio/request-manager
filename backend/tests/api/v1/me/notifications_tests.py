from datetime import timedelta

import pytest
from django.utils import timezone
from model_bakery import baker
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT, is_success

from tests.api.asserts import assert_exact_fields, list_rows
from tests.api.helpers import do_login, login
from tests.api.matrix import any_user
from tests.factories import make_user
from video_requests.models import Notification

pytestmark = pytest.mark.django_db

NOTIFICATION_FIELDS = [
    "body",
    "created",
    "id",
    "kind",
    "read_at",
    "request",
    "title",
    "url",
]


def notification(recipient, **kwargs):
    return baker.make(
        "video_requests.Notification",
        recipient=recipient,
        kind=Notification.Kinds.STUDIO_MESSAGE,
        **kwargs,
    )


@any_user(HTTP_200_OK)
def test_list_shows_only_my_notifications_newest_first(
    api_client, expected, request, user
):
    user = do_login(api_client, request, user)
    older, newer = notification(user), notification(user)
    notification(make_user())

    response = api_client.get(reverse("api:v1:me:notification-list"))

    assert response.status_code == expected
    if is_success(response.status_code):
        rows = list_rows(response, pagination=True, expected_count=2)
        assert [row["id"] for row in rows] == [newer.id, older.id]
        assert_exact_fields(rows[0], NOTIFICATION_FIELDS)


@any_user(HTTP_200_OK)
def test_unread_count_counts_only_my_unread_ones(api_client, expected, request, user):
    user = do_login(api_client, request, user)
    notification(user)
    notification(user)
    notification(user, read_at=timezone.now())
    notification(make_user())

    response = api_client.get(reverse("api:v1:me:notification-unread-count"))

    assert response.status_code == expected
    if is_success(response.status_code):
        assert response.data == {"count": 2}


@any_user(HTTP_204_NO_CONTENT)
def test_marking_one_request_read_leaves_everything_else(
    api_client, expected, request, user
):
    user = do_login(api_client, request, user)
    target = notification(user)
    same_request = notification(user, request=target.request)
    read_before = timezone.now() - timedelta(days=1)
    already_read = notification(user, request=target.request, read_at=read_before)
    other_request = notification(user)
    someone_elses = notification(make_user(), request=target.request)

    response = api_client.post(
        reverse("api:v1:me:notification-read"), {"request": target.request_id}
    )

    assert response.status_code == expected
    if is_success(response.status_code):
        for row in (target, same_request, already_read, other_request, someone_elses):
            row.refresh_from_db()
        assert target.read_at and same_request.read_at
        assert already_read.read_at == read_before
        assert other_request.read_at is None
        assert someone_elses.read_at is None


def test_marking_without_a_request_marks_all_of_mine(api_client, basic_user):
    mine = [notification(basic_user), notification(basic_user)]
    someone_elses = notification(make_user())
    login(api_client, basic_user)

    response = api_client.post(reverse("api:v1:me:notification-read"), {})

    assert response.status_code == HTTP_204_NO_CONTENT
    assert all(Notification.objects.get(pk=row.pk).read_at for row in mine)
    assert Notification.objects.get(pk=someone_elses.pk).read_at is None


@pytest.mark.parametrize("whose", ["someone_else", "missing"])
def test_marking_a_request_i_have_nothing_on_changes_nothing(
    api_client, basic_user, missing_id, whose
):
    someone_elses = notification(make_user())
    request_id = someone_elses.request_id if whose == "someone_else" else missing_id
    login(api_client, basic_user)

    response = api_client.post(
        reverse("api:v1:me:notification-read"), {"request": request_id}
    )

    assert response.status_code == HTTP_204_NO_CONTENT
    assert Notification.objects.get(pk=someone_elses.pk).read_at is None
