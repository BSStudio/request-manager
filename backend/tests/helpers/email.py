from django.conf import settings
from django.core.mail import get_connection
from django.core.mail.backends.base import BaseEmailBackend


class CombinedEmailBackend(BaseEmailBackend):
    """Send through every backend in ``EMAIL_BACKEND_LIST``.

    Used by ``pytest --save-emails``: the file backend writes the rendered
    messages to disk for the CI artifact, while the in-memory one keeps
    ``mail.outbox`` populated so the assertions still work.
    """

    def send_messages(self, email_messages):
        for backend in getattr(settings, "EMAIL_BACKEND_LIST", []):
            get_connection(backend).send_messages(email_messages)
        return len(email_messages)
