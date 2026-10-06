"""The user a login hands back.

The frontend caches these instead of calling /me on every page load, so the
shape is a contract.
"""

import pytest
from django.contrib.auth.models import Group

from api.v1.login.serializers import SessionUserSerializer
from common.models import User
from tests.factories import make_user

pytestmark = pytest.mark.django_db


def session_user(user):
    return SessionUserSerializer(user).data


@pytest.mark.parametrize(
    "kwargs,expected_role",
    [
        ({"is_admin": True}, User.Roles.ADMIN),
        ({"is_staff": True}, User.Roles.STAFF),
        ({}, User.Roles.USER),
    ],
    ids=["admin", "staff", "user"],
)
def test_the_role_follows_the_users_permissions(kwargs, expected_role):
    assert session_user(make_user(**kwargs))["role"] == expected_role


def test_every_group_is_listed():
    groups = [f"Group{index}" for index in range(1, 6)]
    user = make_user()
    for name in groups:
        user.groups.add(Group.objects.get_or_create(name=name)[0])

    assert sorted(session_user(user)["groups"]) == groups


def test_a_user_in_no_group_gets_an_empty_list():
    assert session_user(make_user())["groups"] == []


def test_the_avatar_and_name_come_from_the_user():
    user = make_user(first_name="Foo", last_name="Bar")

    data = session_user(user)

    assert data["avatar_url"] == user.avatar_url
    assert data["name"] == "Bar Foo"


def test_a_user_without_an_avatar_gets_null():
    assert session_user(make_user(avatar={}))["avatar_url"] is None
