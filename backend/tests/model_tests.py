import pytest
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
