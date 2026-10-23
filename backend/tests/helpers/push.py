import os

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from py_vapid.utils import b64urlencode

from common.models import PushSubscription


def subscribe(user, endpoint="https://fcm.googleapis.com/fcm/send/abc"):
    """A subscription with real browser keys, which the payload is encrypted to."""
    browser_key = ec.generate_private_key(ec.SECP256R1()).public_key()
    return PushSubscription.objects.create(
        user=user,
        endpoint=endpoint,
        p256dh=b64urlencode(
            browser_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
        ),
        auth=b64urlencode(os.urandom(16)),
    )
