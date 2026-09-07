import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from django.urls import reverse
from rest_framework.status import HTTP_200_OK

from common.admin import UserAdmin
from common.models import Ban, User
from tests.helpers.users_test_utils import create_user
from tests.helpers.video_requests_test_utils import (
    create_comment,
    create_crew,
    create_rating,
    create_request,
    create_todo,
    create_video,
)
from video_requests.admin import user_change_url


def admin_request(user):
    request = RequestFactory().post("/admin/common/user/")
    request.user = user
    request.session = {}
    request._messages = FallbackStorage(request)
    return request


def ban_users(admin, usernames):
    request = admin_request(admin)
    UserAdmin(User, AdminSite()).ban_selected_users(
        request,
        User.objects.filter(username__in=usernames).order_by("username"),
    )
    return [message.message for message in request._messages]


@pytest.mark.django_db
def test_ban_selected_users_skips_an_already_banned_user():
    admin = create_user(username="banning_admin", is_admin=True)
    create_user(username="already_banned", banned=True)
    create_user(username="to_ban")

    reported = ban_users(admin, ["already_banned", "to_ban"])

    # The already banned user is processed first, so the second one proves that
    # the action did not stop there.
    assert Ban.objects.filter(receiver__username="to_ban").exists()
    assert reported == ["Banned 1 user(s), skipped 1: already_banned."]


@pytest.mark.django_db
def test_ban_selected_users_skips_a_self_ban():
    admin = create_user(username="admin_banning_himself", is_admin=True)
    create_user(username="to_ban")

    reported = ban_users(admin, ["admin_banning_himself", "to_ban"])

    assert not Ban.objects.filter(receiver=admin).exists()
    assert Ban.objects.filter(receiver__username="to_ban").exists()
    assert reported == ["Banned 1 user(s), skipped 1: admin_banning_himself."]


@pytest.mark.django_db
def test_ban_selected_users_reports_a_run_without_skips():
    admin = create_user(username="banning_admin", is_admin=True)
    create_user(username="to_ban")

    assert ban_users(admin, ["to_ban"]) == ["Successfully banned 1 user(s)."]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model_name",
    ["comment", "crewmember", "rating", "request", "todo"],
)
def test_changelists_link_to_the_user_admin(client, model_name):
    # Every one of these lists renders a link to a user, so a hard coded admin
    # URL name would only break once the list is not empty.
    user = create_user(username="linked_user", is_admin=True)
    user.is_superuser = True
    user.save()

    video_request = create_request(700, user, responsible=user)
    video = create_video(700, video_request, editor=user)
    create_crew(700, video_request, user, "Cameraman")
    create_comment(700, video_request, user, False)
    create_rating(700, video, user)
    create_todo(700, "Test todo", video_request, user).assignees.add(user)

    client.force_login(user)
    response = client.get(reverse(f"admin:video_requests_{model_name}_changelist"))

    assert response.status_code == HTTP_200_OK
    assert user_change_url(user.id) in response.content.decode()
