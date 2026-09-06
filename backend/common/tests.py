import json
import re
from io import StringIO

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import RequestFactory, TestCase
from rest_framework import status

from common.middleware import RequestLoggingMiddleware
from common.models import Ban, get_sentinel_user
from common.templatetags.extra_tags import settings_value
from tests.helpers.users_test_utils import create_user
from tests.helpers.video_requests_test_utils import (
    create_comment,
    create_crew,
    create_rating,
    create_request,
    create_video,
)


class CommonTestCase(TestCase):
    def setUp(self):
        self.user = create_user()

    def test_sentinel_user_on_user_delete(self):
        user = create_user()
        request = create_request(100, user, responsible=user)
        video = create_video(200, request, editor=user)
        create_crew(300, request, user, "Test")
        create_comment(400, request, user, False)
        create_rating(500, video, user)

        request.refresh_from_db()

        self.assertEqual(request.requester, user)
        self.assertEqual(request.responsible, user)
        self.assertEqual(request.videos.get().editor, user)
        self.assertEqual(request.crew.get().member, user)
        self.assertEqual(request.comments.get().author, user)
        self.assertEqual(request.videos.get().ratings.get().author, user)

        user.delete()
        request.refresh_from_db()

        sentinel_user = get_sentinel_user()
        self.assertEqual(request.requester, sentinel_user)
        self.assertEqual(request.responsible, sentinel_user)
        self.assertEqual(request.videos.get().editor, sentinel_user)
        self.assertFalse(request.crew.exists())
        self.assertEqual(request.comments.get().author, sentinel_user)
        self.assertEqual(request.videos.get().ratings.get().author, sentinel_user)

    def test_health_check_api_endpoint_works(self):
        token = (
            f"/{settings.HEALTH_CHECK_URL_TOKEN}"
            if hasattr(settings, "HEALTH_CHECK_URL_TOKEN")
            and settings.HEALTH_CHECK_URL_TOKEN is not None
            else ""
        )
        response = self.client.get(f"/health{token}?format=json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.data = json.loads(response.content)
        self.assertIn("Cache(alias='default')", response.data)
        self.assertIn("Database(alias='default')", response.data)
        self.assertIn(
            "Mail(backend='django.core.mail.backends.dummy.EmailBackend')",
            response.data,
        )
        self.assertIn("Storage(alias='default')", response.data)
        self.assertTrue(
            any(
                re.search(r"Redis\(host='[^']+', port=6379\)", key)
                for key in response.data
            )
        )

    def test_health_check_management_command_works(self):
        with StringIO() as out:
            with self.assertRaises(SystemExit) as cm:
                call_command("health_check", "health_check", "--no-http", stdout=out)
            self.assertEqual(cm.exception.code, 0)
            self.assertIn("Cache(alias='default')", out.getvalue())
            self.assertIn("Database(alias='default')", out.getvalue())
            self.assertIn(
                "Mail(backend='django.core.mail.backends.dummy.EmailBackend')",
                out.getvalue(),
            )
            self.assertIn("Storage(alias='default')", out.getvalue())
            self.assertRegex(out.getvalue(), r"Redis\(host='[^']+', port=6379\)")

    def test_user_avatar_json_validation(self):
        self.user.refresh_from_db()
        self.user.full_clean()

        with self.assertRaises(ValidationError) as context:
            self.user.avatar = {"randomKey": "randomValue"}
            self.user.full_clean()
        self.assertIn(
            "'provider' is a required property",
            context.exception.messages[0],
        )

        with self.assertRaises(ValidationError) as context:
            self.user.avatar = {"provider": "randomValue"}
            self.user.full_clean()
        self.assertIn(
            "'randomValue' is not one of ['google-oauth2', 'gravatar', 'microsoft-graph']",
            context.exception.messages[0],
        )

        with self.assertRaises(ValidationError) as context:
            self.user.avatar = {
                "provider": "microsoft-graph",
                "randomKey": "randomValue",
            }
            self.user.full_clean()
        self.assertIn(
            "Additional properties are not allowed ('randomKey' was unexpected)",
            context.exception.messages[0],
        )

        with self.assertRaises(ValidationError) as context:
            self.user.avatar = {
                "provider": "microsoft-graph",
                "microsoft-graph": "randomValue",
            }
            self.user.full_clean()
        self.assertIn(
            "'randomValue' is not a 'uri'",
            context.exception.messages[0],
        )

    def test_settings_template_tag(self):
        self.assertEqual(settings_value("BASE_URL"), settings.BASE_URL)

    def test_user_ban_validation(self):
        with self.assertRaises(ValidationError) as context:
            Ban.objects.create(creator=self.user, receiver=self.user)
        self.assertIn(
            "Users cannot ban themselves.",
            context.exception.messages[0],
        )


class ClientIPResolutionTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _resolve(self, remote_addr, forwarded=None):
        request = self.factory.get("/")
        request.META["REMOTE_ADDR"] = remote_addr
        if forwarded is None:
            request.META.pop("HTTP_X_FORWARDED_FOR", None)
        else:
            request.META["HTTP_X_FORWARDED_FOR"] = forwarded
        return RequestLoggingMiddleware._client_ip(request)

    def test_no_forwarded_header_returns_remote_addr(self):
        self.assertEqual(self._resolve("172.21.0.3"), "172.21.0.3")

    def test_single_trusted_proxy_returns_real_client(self):
        # peer is the trusted proxy; client sits left of it.
        self.assertEqual(
            self._resolve("172.21.0.3", forwarded="203.0.113.7"), "203.0.113.7"
        )

    def test_multiple_trusted_proxies_are_skipped(self):
        self.assertEqual(
            self._resolve("172.21.0.3", forwarded="203.0.113.7, 10.0.0.5, 192.168.1.2"),
            "203.0.113.7",
        )

    def test_client_spoofed_entry_is_ignored(self):
        # Client prepends a fake internal IP; it stays left of the real hop and
        # must not be mistaken for the client.
        self.assertEqual(
            self._resolve("172.21.0.3", forwarded="10.9.9.9, 203.0.113.7"),
            "203.0.113.7",
        )

    def test_all_hops_trusted_falls_back_to_remote_addr(self):
        self.assertEqual(
            self._resolve("172.21.0.3", forwarded="10.0.0.1, 192.168.0.1"),
            "172.21.0.3",
        )

    def test_malformed_entries_are_skipped(self):
        self.assertEqual(
            self._resolve("172.21.0.3", forwarded="not-an-ip, 203.0.113.7"),
            "203.0.113.7",
        )

    def test_all_entries_unparseable_falls_back_to_remote_addr(self):
        # Even REMOTE_ADDR fails to parse; the loop exhausts and returns it.
        self.assertEqual(
            self._resolve("garbage", forwarded="also-bad"),
            "garbage",
        )
