import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from django.urls import reverse
from model_bakery import baker
from rest_framework.status import HTTP_200_OK

from common.admin import UserAdmin
from common.models import Ban, User
from tests.factories import make_user
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
    admin = make_user(username="banning_admin", is_admin=True)
    make_user(username="already_banned", banned=True)
    make_user(username="to_ban")

    reported = ban_users(admin, ["already_banned", "to_ban"])

    # The already banned user is processed first, so the second one proves that
    # the action did not stop there.
    assert Ban.objects.filter(receiver__username="to_ban").exists()
    assert reported == ["Banned 1 user, skipped 1: already_banned."]


@pytest.mark.django_db
def test_ban_selected_users_skips_a_self_ban():
    admin = make_user(username="admin_banning_himself", is_admin=True)
    make_user(username="to_ban")

    reported = ban_users(admin, ["admin_banning_himself", "to_ban"])

    assert not Ban.objects.filter(receiver=admin).exists()
    assert Ban.objects.filter(receiver__username="to_ban").exists()
    assert reported == ["Banned 1 user, skipped 1: admin_banning_himself."]


@pytest.mark.django_db
def test_ban_selected_users_reports_a_run_without_skips():
    admin = make_user(username="banning_admin", is_admin=True)
    make_user(username="to_ban")

    assert ban_users(admin, ["to_ban"]) == ["Successfully banned 1 user."]


@pytest.mark.django_db
def test_ban_selected_users_reports_the_plural_form():
    admin = make_user(username="banning_admin", is_admin=True)
    make_user(username="first_to_ban")
    make_user(username="second_to_ban")

    reported = ban_users(admin, ["first_to_ban", "second_to_ban"])

    assert reported == ["Successfully banned 2 users."]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model_name",
    ["comment", "crewmember", "rating", "request", "todo"],
)
def test_changelists_link_to_the_user_admin(client, model_name):
    # Every one of these lists renders a link to a user, so a hard coded admin
    # URL name would only break once the list is not empty.
    user = make_user(username="linked_user", is_admin=True, is_superuser=True)

    video_request = baker.make(
        "video_requests.Request", requester=user, responsible=user
    )
    video = baker.make("video_requests.Video", request=video_request, editor=user)
    baker.make("video_requests.CrewMember", request=video_request, member=user)
    baker.make("video_requests.Comment", request=video_request, author=user)
    baker.make("video_requests.Rating", video=video, author=user)
    baker.make(
        "video_requests.Todo", request=video_request, creator=user
    ).assignees.add(user)

    client.force_login(user)
    response = client.get(reverse(f"admin:video_requests_{model_name}_changelist"))

    assert response.status_code == HTTP_200_OK
    assert user_change_url(user.id) in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model_name",
    ["comment", "crewmember", "rating", "request", "todo", "video"],
)
def test_changelists_can_be_searched(client, model_name):
    # Django resolves the search_fields lookups only once someone searches.
    user = make_user(username="searching_admin", is_admin=True, is_superuser=True)

    client.force_login(user)
    response = client.get(
        reverse(f"admin:video_requests_{model_name}_changelist"), {"q": "title"}
    )

    assert response.status_code == HTTP_200_OK
