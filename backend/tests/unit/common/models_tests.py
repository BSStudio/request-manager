from unittest.mock import patch

import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from model_bakery import baker

from common.models import Ban, User, get_sentinel_user
from tests.factories import make_user

pytestmark = pytest.mark.django_db


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


class TestUserAvatarSchema:
    """The JSON schema behind the avatar field, checked on every save."""

    @pytest.fixture
    def user(self):
        return make_user()

    def test_the_default_avatar_is_valid(self, user):
        user.refresh_from_db()
        user.full_clean()  # Should not raise

    def test_the_provider_is_required(self, user):
        user.avatar = {"randomKey": "randomValue"}

        with pytest.raises(ValidationError) as error:
            user.full_clean()

        assert "'provider' is a required property" in error.value.messages[0]

    def test_the_provider_must_be_one_we_know(self, user):
        user.avatar = {"provider": "randomValue"}

        with pytest.raises(ValidationError) as error:
            user.full_clean()

        assert (
            "'randomValue' is not one of "
            "['google-oauth2', 'gravatar', 'microsoft-graph']"
            in error.value.messages[0]
        )

    def test_unknown_keys_are_rejected(self, user):
        user.avatar = {"provider": "microsoft-graph", "randomKey": "randomValue"}

        with pytest.raises(ValidationError) as error:
            user.full_clean()

        assert (
            "Additional properties are not allowed ('randomKey' was unexpected)"
            in error.value.messages[0]
        )

    def test_an_image_has_to_be_a_uri(self, user):
        user.avatar = {"provider": "microsoft-graph", "microsoft-graph": "randomValue"}

        with pytest.raises(ValidationError) as error:
            user.full_clean()

        assert "'randomValue' is not a 'uri'" in error.value.messages[0]


class TestUserSave:
    def test_duplicate_email_raises_a_validation_error(self):
        User.objects.create_user(username="first", email="Duplicate@example.com")

        with pytest.raises(ValidationError, match=r"E-mail address already in use\."):
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
        with pytest.raises(ValidationError, match=r"E-mail address already in use\."):
            second.save(update_fields=["email"])


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


class TestBan:
    def test_a_user_cannot_ban_themselves(self):
        user = make_user()

        with pytest.raises(ValidationError) as error:
            Ban.objects.create(creator=user, receiver=user)

        assert "Users cannot ban themselves." in error.value.messages[0]

    def test_a_ban_is_rolled_back_when_deactivating_the_receiver_fails(self):
        creator = make_user(username="banning_admin", is_admin=True)
        receiver = make_user(username="to_ban", groups=("Gyártásvezető",))

        # post_save runs after the insert, so everything it touches has to go
        # with the ban when it blows up.
        with patch.object(User, "save", side_effect=ValidationError("Nope.")):
            with pytest.raises(ValidationError):
                Ban.objects.create(receiver=receiver, creator=creator)

        assert not Ban.objects.filter(receiver=receiver).exists()
        receiver.refresh_from_db()
        assert receiver.is_active
        assert set(receiver.groups.values_list("name", flat=True)) == {"Gyártásvezető"}


class TestSentinelUser:
    def test_deleting_a_user_hands_their_rows_to_the_sentinel(self):
        user = make_user()
        video_request = baker.make(
            "video_requests.Request", requester=user, responsible=user
        )
        video = baker.make("video_requests.Video", request=video_request, editor=user)
        baker.make("video_requests.CrewMember", request=video_request, member=user)
        baker.make("video_requests.Comment", request=video_request, author=user)
        baker.make("video_requests.Rating", video=video, author=user)

        video_request.refresh_from_db()

        assert video_request.requester == user
        assert video_request.responsible == user
        assert video_request.videos.get().editor == user
        assert video_request.crew.get().member == user
        assert video_request.comments.get().author == user
        assert video_request.videos.get().ratings.get().author == user

        user.delete()
        video_request.refresh_from_db()

        sentinel_user = get_sentinel_user()
        assert video_request.requester == sentinel_user
        assert video_request.responsible == sentinel_user
        assert video_request.videos.get().editor == sentinel_user
        # The crew membership is cascaded away rather than reassigned.
        assert not video_request.crew.exists()
        assert video_request.comments.get().author == sentinel_user
        assert video_request.videos.get().ratings.get().author == sentinel_user
