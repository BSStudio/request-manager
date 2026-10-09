import pytest
from django.apps import apps
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.db import connection
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from model_bakery import baker
from rest_framework.status import HTTP_200_OK, HTTP_302_FOUND

from common.admin import UserAdmin
from common.models import Ban, User
from tests.factories import make_user
from video_requests.models import Request


def admin_request(user):
    request = RequestFactory().post("/admin/common/user/")
    request.user = user
    request.session = {}
    request._messages = FallbackStorage(request)
    return request


def make_one_of_each(user):
    video_request = baker.make(
        "video_requests.Request", requester=user, responsible=user
    )
    video = baker.make("video_requests.Video", request=video_request, editor=user)
    baker.make("video_requests.CrewMember", request=video_request, member=user)
    baker.make("video_requests.Comment", request=video_request, author=user)
    baker.make("video_requests.Rating", video=video, author=user)
    baker.make(
        "video_requests.Todo", request=video_request, video=video, creator=user
    ).assignees.add(user)


def count_queries(client, url, data=None):
    with CaptureQueriesContext(connection) as queries:
        response = client.get(url, data)
    assert response.status_code == HTTP_200_OK
    return len(queries)


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
    ("codenames", "offered"),
    [(["view_user"], False), (["view_user", "add_ban"], True)],
)
def test_ban_selected_users_needs_the_permission_to_add_bans(codenames, offered):
    staff_member = make_user(username="staff_member", is_staff=True)
    staff_member.user_permissions.set(Permission.objects.filter(codename__in=codenames))

    actions = UserAdmin(User, AdminSite()).get_actions(admin_request(staff_member))

    assert ("ban_selected_users" in actions) is offered


@pytest.mark.django_db
def test_ban_admin_credits_the_ban_to_whoever_added_it(client):
    admin = make_user(username="banning_admin", is_admin=True, is_superuser=True)
    other_admin = make_user(username="other_admin", is_admin=True)
    to_ban = make_user(username="to_ban")

    client.force_login(admin)
    response = client.post(
        reverse("admin:common_ban_add"),
        # Read-only in the admin, so the form must ignore it.
        {"receiver": to_ban.id, "creator": other_admin.id, "reason": ""},
    )

    assert response.status_code == HTTP_302_FOUND
    assert Ban.objects.get(receiver=to_ban).creator == admin


@pytest.mark.django_db
@pytest.mark.parametrize("bans_self", [True, False])
def test_ban_admin_needs_a_receiver_other_than_the_admin(client, bans_self):
    admin = make_user(username="banning_admin", is_admin=True, is_superuser=True)

    client.force_login(admin)
    response = client.post(
        reverse("admin:common_ban_add"),
        {"receiver": admin.id if bans_self else "", "reason": ""},
    )

    assert response.status_code == HTTP_200_OK
    assert "receiver" in response.context["adminform"].form.errors
    assert not Ban.objects.exists()


@pytest.mark.django_db
def test_ban_admin_cannot_move_a_ban_to_another_user(client):
    admin = make_user(username="banning_admin", is_admin=True, is_superuser=True)
    banned = make_user(username="already_banned", banned=True)
    not_banned = make_user(username="not_banned")

    client.force_login(admin)
    response = client.post(
        reverse("admin:common_ban_change", args=(banned.id,)),
        {"receiver": not_banned.id, "reason": "Changed"},
    )

    assert response.status_code == HTTP_302_FOUND
    assert list(Ban.objects.values_list("receiver__username", "reason")) == [
        ("already_banned", "Changed")
    ]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model_name",
    ["comment", "crewmember", "rating", "request", "todo"],
)
def test_changelists_link_to_the_user_admin(client, model_name):
    # Every one of these lists renders a link to a user, so a hard coded admin
    # URL name would only break once the list is not empty.
    user = make_user(
        username="linked_user",
        first_name="Anna",
        last_name="Kovács",
        is_admin=True,
        is_superuser=True,
    )
    make_one_of_each(user)

    client.force_login(user)
    response = client.get(reverse(f"admin:video_requests_{model_name}_changelist"))

    assert response.status_code == HTTP_200_OK
    url = reverse("admin:common_user_change", args=(user.id,))
    assert f'<a href="{url}">Kovács Anna</a>' in response.content.decode()


@pytest.mark.django_db
def test_request_admin_keeps_who_added_the_request(client):
    admin = make_user(username="adding_admin", is_admin=True, is_superuser=True)
    requester = make_user(username="requester")
    form = {
        "title": "Added in the admin",
        "start_datetime_0": "2026-10-10",
        "start_datetime_1": "10:00:00",
        "end_datetime_0": "2026-10-10",
        "end_datetime_1": "12:00:00",
        "type": "Type",
        "place": "Place",
        "status": Request.Statuses.REQUESTED,
        "requester": requester.id,
        "additional_data": "{}",
        # Read-only in the admin, so both posts must ignore it.
        "requested_by": requester.id,
    }

    client.force_login(admin)
    added = client.post(reverse("admin:video_requests_request_add"), form)
    video_request = Request.objects.get(title="Added in the admin")
    changed = client.post(
        reverse("admin:video_requests_request_change", args=(video_request.id,)),
        form,
    )

    assert added.status_code == changed.status_code == HTTP_302_FOUND
    video_request.refresh_from_db()
    assert video_request.requested_by == admin


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


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model_name",
    ["comment", "crewmember", "rating", "request", "todo", "video"],
)
def test_changelists_can_be_sorted_by_every_column(client, model_name):
    # Django resolves a column's ordering only once someone sorts by it.
    user = make_user(username="sorting_admin", is_admin=True, is_superuser=True)
    make_one_of_each(user)

    client.force_login(user)
    url = reverse(f"admin:video_requests_{model_name}_changelist")
    columns = client.get(url).context["cl"].list_display

    for index in range(len(columns)):
        assert client.get(url, {"o": index}).status_code == HTTP_200_OK


@pytest.mark.django_db
def test_admin_login_passes_on_where_to_return(client):
    next_url = reverse("admin:video_requests_request_changelist")

    response = client.get(reverse("admin:login"), {"next": next_url})

    hidden_input = f'<input type="hidden" name="next" value="{next_url}">'
    assert hidden_input in response.content.decode()


@pytest.mark.django_db
def test_admin_login_tells_a_logged_in_user_why_they_are_back(client):
    client.force_login(make_user(username="requester"))

    response = client.get(reverse("admin:login"))

    assert "requester, but are not authorized" in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize("model_name", ["request", "video"])
def test_admins_link_to_the_same_page_in_the_app(client, model_name):
    user = make_user(username="linking_admin", is_admin=True, is_superuser=True)
    make_one_of_each(user)
    obj = apps.get_model("video_requests", model_name).objects.get()

    client.force_login(user)
    response = client.get(
        reverse(f"admin:video_requests_{model_name}_change", args=(obj.id,))
    )

    assert f'href="{obj.admin_url}"' in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model_name",
    ["comment", "crewmember", "rating", "request", "todo", "video"],
)
@pytest.mark.parametrize("view", ["changelist", "add"])
def test_admin_pages_run_as_many_queries_for_more_rows(client, model_name, view):
    user = make_user(username="counting_admin", is_admin=True, is_superuser=True)
    client.force_login(user)
    url = reverse(f"admin:video_requests_{model_name}_{view}")

    make_one_of_each(user)
    client.get(url)  # Fills Django's content type cache.
    one_row = count_queries(client, url)
    make_one_of_each(user)

    assert count_queries(client, url) == one_row


@pytest.mark.django_db
@pytest.mark.filterwarnings("error::django.core.paginator.UnorderedObjectListWarning")
@pytest.mark.parametrize(
    ("model_name", "field_name"),
    [("comment", "author"), ("rating", "video"), ("video", "request")],
)
def test_autocompletes_run_as_many_queries_for_more_results(
    client, model_name, field_name
):
    user = make_user(username="counting_admin", is_admin=True, is_superuser=True)
    client.force_login(user)
    url = reverse("admin:autocomplete")
    data = {
        "app_label": "video_requests",
        "model_name": model_name,
        "field_name": field_name,
    }

    make_one_of_each(user)
    one_result = count_queries(client, url, data)
    make_one_of_each(user)

    assert count_queries(client, url, data) == one_result
