import pytest
from django.core.exceptions import ValidationError
from model_bakery import baker

from common.models import User


@pytest.mark.django_db
class TestUserProfileClean:
    def test_avatar_must_be_dict(self):
        profile = baker.make(User).userprofile
        profile.avatar = "not a dict"
        with pytest.raises(ValidationError, match="Avatar must be an object"):
            profile.clean()

    def test_avatar_invalid_provider_reference(self):
        profile = baker.make(User).userprofile
        profile.avatar = {"provider": "google-oauth2"}
        with pytest.raises(
            ValidationError, match="Avatar does not exist for this provider"
        ):
            profile.clean()

    def test_avatar_valid_provider_reference(self):
        profile = baker.make(User).userprofile
        profile.avatar = {
            "provider": "gravatar",
            "gravatar": "https://example.com/avatar.png",
        }
        profile.clean()  # Should not raise
