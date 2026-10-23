import pytest

from common.push import push_enabled


@pytest.mark.parametrize(
    "public,private,contact,enabled",
    [
        ("pub", "priv", "mailto:push@example.com", True),
        (None, "priv", "mailto:push@example.com", False),
        ("pub", None, "mailto:push@example.com", False),
        ("pub", "priv", None, False),
    ],
)
def test_push_is_on_only_with_all_three_settings(
    settings, public, private, contact, enabled
):
    settings.WEB_PUSH_VAPID_PUBLIC_KEY = public
    settings.WEB_PUSH_VAPID_PRIVATE_KEY = private
    settings.WEB_PUSH_CONTACT = contact

    assert push_enabled() is enabled
