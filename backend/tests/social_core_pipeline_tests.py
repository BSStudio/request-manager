from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from social_core.exceptions import NotAllowedToDisconnect
from social_django.models import DjangoStorage, UserSocialAuth

from common.social_core.pipeline import (
    add_phone_number_to_profile,
    allowed_to_disconnect,
    associate_by_email,
    check_for_email,
    check_if_admin_or_staff_user_already_associated,
    check_if_only_one_association_from_a_provider,
    check_if_user_is_banned,
    delete_avatar,
    disconnect_all_other_profiles_and_change_username_on_first_bss_login,
    set_groups_and_permissions_for_staff,
)
from tests.helpers.users_test_utils import create_user


class FakeStrategy:
    """The real storage, so the queries the pipeline runs are the real ones."""

    def __init__(self, request=None):
        self.storage = DjangoStorage
        self.request = request


class FakeBackend:
    def __init__(self, name, request=None):
        self.name = name
        self.strategy = FakeStrategy(request)


def anonymous_strategy():
    return FakeStrategy(request=SimpleNamespace(user=AnonymousUser()))


def test_check_for_email_requires_an_address():
    with pytest.raises(ValidationError):
        check_for_email({"email": ""})


def test_associate_by_email_skips_without_an_address():
    assert associate_by_email(FakeBackend("google-oauth2"), {}) is None


@pytest.mark.django_db
def test_associate_by_email_skips_when_already_authenticated():
    user = create_user()
    assert (
        associate_by_email(
            FakeBackend("google-oauth2"), {"email": user.email}, user=user
        )
        is None
    )


@pytest.mark.django_db
def test_check_if_user_is_banned_rejects_banned_users():
    user = create_user(banned=True)
    with pytest.raises(AuthenticationFailed):
        check_if_user_is_banned(FakeBackend("bss-login"), user=user)


@pytest.mark.django_db
def test_only_one_association_per_provider_is_allowed():
    user = create_user()
    UserSocialAuth.objects.create(user=user, provider="google-oauth2", uid="uid-1")

    with pytest.raises(ValidationError):
        check_if_only_one_association_from_a_provider(
            FakeBackend("google-oauth2"), user=user
        )


@pytest.mark.django_db
def test_staff_must_associate_their_social_profile_first():
    user = create_user(is_staff=True)

    with pytest.raises(AuthenticationFailed):
        check_if_admin_or_staff_user_already_associated(
            FakeBackend("google-oauth2"), anonymous_strategy(), user=user
        )


@pytest.mark.django_db
def test_first_bss_login_drops_other_profiles_and_syncs_the_username():
    user = create_user()
    UserSocialAuth.objects.create(user=user, provider="google-oauth2", uid="uid-2")

    disconnect_all_other_profiles_and_change_username_on_first_bss_login(
        FakeBackend("bss-login"),
        anonymous_strategy(),
        {"username": "directory.name"},
        user=user,
    )

    user.refresh_from_db()
    assert user.username == "directory.name"
    assert not UserSocialAuth.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_add_phone_number_keeps_an_existing_number():
    user = create_user()

    add_phone_number_to_profile(
        FakeBackend("google-oauth2"), {"mobile": "+36701111111"}, {}, user
    )

    user.refresh_from_db()
    assert str(user.phone_number) == "+36701234567"


@pytest.mark.django_db
def test_set_groups_and_permissions_skips_the_update_when_groups_match():
    user = create_user(groups=["Gyártásvezető"])

    set_groups_and_permissions_for_staff(
        FakeBackend("bss-login"), {"groups": ["Gyártásvezető"]}, user
    )

    user.refresh_from_db()
    assert user.is_staff
    assert not user.is_superuser
    assert set(user.groups.values_list("name", flat=True)) == {"Gyártásvezető"}


@pytest.mark.django_db
def test_last_login_method_cannot_be_disconnected():
    user = create_user()
    UserSocialAuth.objects.create(user=user, provider="google-oauth2", uid="uid-3")

    with pytest.raises(NotAllowedToDisconnect):
        allowed_to_disconnect(
            anonymous_strategy(), user, "google-oauth2", DjangoStorage.user
        )


@pytest.mark.django_db
def test_a_login_method_can_be_disconnected_when_another_one_remains():
    user = create_user()
    UserSocialAuth.objects.create(user=user, provider="google-oauth2", uid="uid-4")
    UserSocialAuth.objects.create(user=user, provider="microsoft-graph", uid="uid-5")

    allowed_to_disconnect(
        anonymous_strategy(), user, "google-oauth2", DjangoStorage.user
    )


@pytest.mark.django_db
def test_delete_avatar_removes_only_the_disconnected_provider():
    user = create_user()

    delete_avatar(anonymous_strategy(), user, "microsoft-graph", DjangoStorage.user)

    user.refresh_from_db()
    assert "microsoft-graph" not in user.avatar
    assert user.avatar["provider"] == "gravatar"


@pytest.mark.django_db
def test_delete_avatar_is_a_no_op_without_an_image_for_the_provider():
    user = create_user()
    user.avatar = {"provider": "gravatar", "gravatar": "https://example.com/a.png"}
    user.save()

    delete_avatar(anonymous_strategy(), user, "microsoft-graph", DjangoStorage.user)

    user.refresh_from_db()
    assert user.avatar == {
        "provider": "gravatar",
        "gravatar": "https://example.com/a.png",
    }
