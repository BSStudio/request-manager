import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

from common.admin import UserAdmin
from common.models import Ban, User
from tests.helpers.users_test_utils import create_user


def admin_request(user):
    request = RequestFactory().post("/admin/common/user/")
    request.user = user
    request.session = {}
    request._messages = FallbackStorage(request)
    return request


def ban_users(admin, usernames):
    UserAdmin(User, AdminSite()).ban_selected_users(
        admin_request(admin),
        User.objects.filter(username__in=usernames).order_by("username"),
    )


@pytest.mark.django_db
def test_ban_selected_users_skips_an_already_banned_user():
    admin = create_user(username="banning_admin", is_admin=True)
    create_user(username="already_banned", banned=True)
    create_user(username="to_ban")

    ban_users(admin, ["already_banned", "to_ban"])

    # The already banned user is processed first, so the second one proves that
    # the action did not stop there.
    assert Ban.objects.filter(receiver__username="to_ban").exists()


@pytest.mark.django_db
def test_ban_selected_users_skips_a_self_ban():
    admin = create_user(username="admin_banning_himself", is_admin=True)
    create_user(username="to_ban")

    ban_users(admin, ["admin_banning_himself", "to_ban"])

    assert not Ban.objects.filter(receiver=admin).exists()
    assert Ban.objects.filter(receiver__username="to_ban").exists()
