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
