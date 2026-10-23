from django.conf import settings


def push_enabled() -> bool:
    return all(
        (
            settings.WEB_PUSH_CONTACT,
            settings.WEB_PUSH_VAPID_PRIVATE_KEY,
            settings.WEB_PUSH_VAPID_PUBLIC_KEY,
        )
    )
