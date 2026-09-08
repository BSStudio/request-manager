"""The extra claims the access token carries.

The frontend reads these instead of calling /me on every page load, so the shape
is a contract. ``get_token`` is a classmethod over a user, which is all it needs.
"""

import pytest
from django.contrib.auth.models import Group

from api.v1.login.serializers import TokenObtainPairOAuth2Serializer
from common.models import User
from tests.factories import make_user

pytestmark = pytest.mark.django_db


def claims(user):
    return TokenObtainPairOAuth2Serializer.get_token(user).payload


@pytest.mark.parametrize(
    "kwargs,expected_role",
    [
        ({"is_admin": True}, User.Roles.ADMIN),
        ({"is_staff": True}, User.Roles.STAFF),
        ({}, User.Roles.USER),
    ],
    ids=["admin", "staff", "user"],
)
def test_the_role_claim_follows_the_users_permissions(kwargs, expected_role):
    assert claims(make_user(**kwargs))["role"] == expected_role


def test_every_group_is_listed():
    groups = [f"Group{index}" for index in range(1, 6)]
    user = make_user()
    for name in groups:
        user.groups.add(Group.objects.get_or_create(name=name)[0])

    assert sorted(claims(user)["groups"]) == groups


def test_a_user_in_no_group_gets_an_empty_list():
    assert claims(make_user())["groups"] == []


def test_the_avatar_and_name_come_from_the_user():
    user = make_user(first_name="Foo", last_name="Bar")

    payload = claims(user)

    assert payload["avatar"] == user.avatar_url
    assert payload["name"] == "Bar Foo"


def test_a_user_without_an_avatar_gets_a_null_claim():
    assert claims(make_user(avatar={}))["avatar"] is None
