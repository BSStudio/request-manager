import logging
import time
from ipaddress import ip_address

import sentry_sdk
from django.conf import settings

logger = logging.getLogger("api.access")


class SentryUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Requests with an API token are left out: DRF authenticates them later.
        if request.user.is_authenticated:
            sentry_sdk.set_user({"id": request.user.pk})
        return self.get_response(request)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def _client_ip(request):
        remote_addr = request.META.get("REMOTE_ADDR")
        forwarded = request.headers.get("x-forwarded-for")
        if not forwarded:
            return remote_addr

        # Walk hops from the right (unspoofable REMOTE_ADDR outward) and skip
        # trusted proxies: the first untrusted address is the real client.
        # Client-forged entries sit on the left, so they can never pass as a proxy.
        chain = [part.strip() for part in forwarded.split(",") if part.strip()]
        chain.append(remote_addr)

        for candidate in reversed(chain):
            try:
                addr = ip_address(candidate)
            except ValueError:
                continue
            if any(addr in network for network in settings.TRUSTED_PROXY_CIDRS):
                continue
            return candidate

        return remote_addr

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000

        if response.status_code >= 400:
            logger.warning(
                "%s %s %s %.0fms user=%s ip=%s",
                request.method,
                request.get_full_path(),
                response.status_code,
                duration_ms,
                getattr(request.user, "id", None),
                self._client_ip(request),
            )

        return response
