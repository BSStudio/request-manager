import json
from urllib.parse import urlsplit

import requests
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from requests import RequestException
from rest_framework.generics import CreateAPIView
from rest_framework.throttling import ScopedRateThrottle

from api.v1.misc.serializers import ContactSerializer
from common.emails import email_contact_message


class ContactView(CreateAPIView):
    serializer_class = ContactSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "contact"

    def perform_create(self, serializer):
        email = serializer.data["email"]
        message = serializer.data["message"]
        name = serializer.data["name"]
        email_contact_message.delay(name, email, message)


# The frontend reports to Sentry through here, because ad blockers block
# Sentry's own address. Passing on only our DSN keeps this from being an open
# proxy.
@csrf_exempt
@require_POST
def sentry_tunnel(request):
    envelope_header = request.body.split(b"\n", 1)[0]
    try:
        dsn = json.loads(envelope_header).get("dsn")
    except (AttributeError, ValueError):
        return HttpResponseBadRequest()
    if dsn != settings.SENTRY_FRONTEND_DSN:
        return HttpResponseBadRequest()

    dsn = urlsplit(dsn)
    try:
        response = requests.post(
            f"https://{dsn.hostname}/api{dsn.path}/envelope/",
            data=request.body,
            headers={"Content-Type": "application/x-sentry-envelope"},
            timeout=10,
        )
    except RequestException:
        return HttpResponse(status=502)

    forwarded = HttpResponse(status=response.status_code)
    # Without these the SDK takes a 429 as a limit on everything and drops even
    # user feedback for a minute, without trying to send it.
    for header in ("Retry-After", "X-Sentry-Rate-Limits"):
        if header in response.headers:
            forwarded[header] = response.headers[header]
    return forwarded
