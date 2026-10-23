import json
import logging

from django.conf import settings
from pywebpush import WebPushException, webpush
from requests import RequestException

from common.models import User

logger = logging.getLogger(__name__)

PUSH_TTL = 60 * 60 * 24 * 7


def push_enabled() -> bool:
    return all(
        (
            settings.WEB_PUSH_CONTACT,
            settings.WEB_PUSH_VAPID_PRIVATE_KEY,
            settings.WEB_PUSH_VAPID_PUBLIC_KEY,
        )
    )


def send_push(user: User, payload: dict) -> None:
    if not push_enabled():
        return
    data = json.dumps(payload)
    for subscription in user.push_subscriptions.all():
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {"auth": subscription.auth, "p256dh": subscription.p256dh},
                },
                data=data,
                vapid_private_key=settings.WEB_PUSH_VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.WEB_PUSH_CONTACT},
                ttl=PUSH_TTL,
                timeout=10,
            )
        # ValueError: browser keys that do not decode.
        except (RequestException, ValueError, WebPushException) as error:
            response = getattr(error, "response", None)
            # The push service forgot the browser: unsubscribed or reinstalled.
            if response is not None and response.status_code in (404, 410):
                subscription.delete()
            else:
                # No exception text: it can quote the endpoint, see
                # PushSubscription.__str__.
                logger.error(
                    "Push to subscription %s failed: %s, status %s",
                    subscription.id,
                    type(error).__name__,
                    None if response is None else response.status_code,
                )
