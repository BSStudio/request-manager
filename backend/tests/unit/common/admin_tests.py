import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_302_FOUND

from common.admin import UserAdmin
from common.models import Ban, User
from tests.factories import make_user


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
def test_admin_login_passes_on_where_to_return(client):
    next_url = reverse("admin:video_requests_request_changelist")

    response = client.get(reverse("admin:login"), {"next": next_url})

    content = response.content.decode()
    assert f'<input type="hidden" name="next" value="{next_url}">' in content
    assert "not authorized" not in content


@pytest.mark.django_db
def test_admin_login_has_a_logged_in_user_log_out_first(client):
    client.force_login(make_user(username="requester"))
    login_url = f"{reverse('admin:login')}?next=/django-admin/"

    page = client.get(login_url).content.decode()
    logged_out = client.post(reverse("admin_switch_account"), {"next": login_url})

    assert "requester, but are not authorized" in page
    assert reverse("social:begin", args=["bss-login"]) not in page
    assert f'<input type="hidden" name="next" value="{login_url}">' in page
    assert logged_out.url == login_url
    assert "_auth_user_id" not in client.session
