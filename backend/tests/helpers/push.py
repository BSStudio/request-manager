import os
from base64 import urlsafe_b64encode

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from common.models import PushSubscription


def b64(data: bytes) -> str:
    return urlsafe_b64encode(data).rstrip(b"=").decode()


def subscribe(user, endpoint="https://fcm.googleapis.com/fcm/send/abc"):
    """A subscription with real browser keys, which the payload is encrypted to."""
    browser_key = ec.generate_private_key(ec.SECP256R1()).public_key()
    return PushSubscription.objects.create(
        user=user,
        endpoint=endpoint,
        p256dh=b64(
            browser_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
        ),
        auth=b64(os.urandom(16)),
    )
