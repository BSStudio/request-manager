import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from model_bakery import baker

from common.models import User


@pytest.mark.django_db
class TestUserClean:
    def test_avatar_must_be_dict(self):
        user = baker.make(User)
        user.avatar = "not a dict"
        with pytest.raises(ValidationError, match="Avatar must be an object"):
            user.clean()

    def test_avatar_invalid_provider_reference(self):
        user = baker.make(User)
        user.avatar = {"provider": "google-oauth2"}
        with pytest.raises(
            ValidationError, match="Avatar does not exist for this provider"
        ):
            user.clean()

    def test_avatar_valid_provider_reference(self):
        user = baker.make(User)
        user.avatar = {
            "provider": "gravatar",
            "gravatar": "https://example.com/avatar.png",
        }
        user.clean()  # Should not raise


@pytest.mark.django_db
class TestUserSave:
    def test_duplicate_email_raises_a_validation_error(self):
        User.objects.create_user(username="first", email="Duplicate@example.com")

        with pytest.raises(ValidationError, match="E-mail address already in use."):
            User.objects.create_user(username="second", email="duplicate@example.com")

    def test_blank_emails_are_allowed_for_several_users(self):
        User.objects.create_user(username="first", email="")
        User.objects.create_user(username="second", email="")  # Should not raise

    def test_a_save_that_leaves_the_email_alone_skips_the_constraint_query(
        self, django_assert_num_queries
    ):
        user = User.objects.create_user(username="first", email="first@example.com")

        # Only the write. update_last_login saves this way on every single
        # login, and the e-mail constraint has nothing to check there.
        with django_assert_num_queries(1):
            user.save(update_fields=["last_login"])

    def test_a_duplicate_email_is_still_rejected_when_only_the_email_is_saved(self):
        User.objects.create_user(username="first", email="Duplicate@example.com")
        second = User.objects.create_user(username="second")

        second.email = "duplicate@example.com"
        with pytest.raises(ValidationError, match="E-mail address already in use."):
            second.save(update_fields=["email"])


@pytest.mark.django_db
class TestUserGroupNames:
    def test_group_names_follows_every_group_change(self):
        user = baker.make(User)
        group = Group.objects.create(name="Testers")
        other_group = Group.objects.create(name="Reviewers")
        assert user.group_names == frozenset()

        user.groups.add(group)
        assert user.group_names == frozenset({"Testers"})

        user.groups.set([other_group])
        assert user.group_names == frozenset({"Reviewers"})

        user.groups.clear()
        assert user.group_names == frozenset()
