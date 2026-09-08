import random
import re
from base64 import b64encode
from string import ascii_letters, digits
from urllib.parse import urlparse

import responses
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from social_core.backends.utils import load_backends
from social_core.tests.models import (
    TestAssociation,
    TestCode,
    TestNonce,
    TestUserSocialAuth,
    User,
)
from social_core.utils import module_member, parse_qs, url_add_parameters

from common.social_core.helpers import load_strategy


class BaseBackendTest(APITestCase):
    backend = None
    backend_path = None
    name = None
    strategy = None
    complete_url = ""
    raw_complete_url = "/complete/{0}"

    def setUp(self):
        self.mock_gravatar()
        Backend = module_member(self.backend_path)
        self.strategy = load_strategy()
        self.backend = Backend(self.strategy, redirect_uri=self.complete_url)
        self.name = self.backend.name.upper().replace("-", "_")
        self.complete_url = self.strategy.build_absolute_uri(
            self.raw_complete_url.format(self.backend.name)
        )
        backends = (self.backend_path,)
        # Force backends loading to trash PSA cache
        load_backends(backends, force_load=True)
        User.reset_cache()
        TestUserSocialAuth.reset_cache()
        TestNonce.reset_cache()
        TestAssociation.reset_cache()
        TestCode.reset_cache()

    def tearDown(self):
        self.backend = None
        self.strategy = None
        self.name = None
        self.complete_url = None
        User.reset_cache()
        TestUserSocialAuth.reset_cache()
        TestNonce.reset_cache()
        TestAssociation.reset_cache()
        TestCode.reset_cache()

    @staticmethod
    def mock_gravatar():
        responses.get(
            re.compile(r"https://(www|secure)\.gravatar\.com/avatar/.*"), status=404
        )


class OAuth2Test(BaseBackendTest):
    user_data_body = None
    user_data_url = ""
    access_token_body = None
    access_token_status = 200

    @staticmethod
    def _method(method):
        return {"GET": responses.GET, "POST": responses.POST}[method]

    def handle_state(self, start_url, target_url):
        start_query = parse_qs(urlparse(start_url).query)
        redirect_uri = start_query.get("redirect_uri")

        if getattr(self.backend, "STATE_PARAMETER", False) and start_query.get("state"):
            target_url = url_add_parameters(target_url, {"state": start_query["state"]})

        if redirect_uri and getattr(self.backend, "REDIRECT_STATE", False):
            redirect_query = parse_qs(urlparse(redirect_uri).query)
            if redirect_query.get("redirect_state"):
                target_url = url_add_parameters(
                    target_url, {"redirect_state": redirect_query["redirect_state"]}
                )
        return target_url

    def auth_handlers(self, start_url):
        target_url = self.handle_state(
            start_url, self.strategy.build_absolute_uri(self.complete_url)
        )
        responses.get(start_url, status=301, headers={"Location": target_url})
        responses.get(target_url, status=200, body="foobar")
        if self.user_data_url:
            responses.get(self.user_data_url, json=self.user_data_body)
        return target_url

    def pre_complete_callback(self):
        responses.add(
            self._method(self.backend.ACCESS_TOKEN_METHOD),
            self.backend.access_token_url(),
            status=self.access_token_status,
            json=self.access_token_body,
        )

    def do_rest_login(self, provider):
        start_url = self.backend.start().url
        self.auth_handlers(start_url)
        self.pre_complete_callback()

        url = reverse("api:v1:login:social")
        response = self.client.post(
            url,
            {
                "provider": provider,
                "code": "".join(
                    random.choice(ascii_letters + digits) for _ in range(15)
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        access_token = AccessToken(response.data["access"])
        refresh_token = RefreshToken(response.data["refresh"])

        self.assertEqual(access_token["token_type"], "access")
        self.assertEqual(refresh_token["token_type"], "refresh")
        self.assertIsNone(
            access_token.verify()
        )  # Throws exception when check fails otherwise returns None


@override_settings(SOCIAL_AUTH_PROVIDERS=["authsch"])
class AuthSCHOAuth2Test(OAuth2Test):
    access_token_body = {"access_token": "foobar", "token_type": "bearer"}
    backend_path = "common.social_core.backends.AuthSCHOAuth2"
    user_data_body = {
        "name": "Foo Bar",
        "family_name": "Foo",
        "given_name": "Bar",
        "birthdate": "1995-03-17",
        "updated_at": 1722802228,
        "email": "foobar@example.com",
        "email_verified": True,
        "phone_number": "+36509999999",
        "phone_number_verified": False,
        "directory.sch.bme.hu:sAMAccountName": "foobar",
        "meta.directory.sch.bme.hu:updated_at": 1722802226,
        "sub": "c97e69cc-2dc2-4f4f-a99e-d7917f9ce335",
    }
    user_data_url = "https://auth.sch.bme.hu/oidc/userinfo"

    @responses.activate
    def test_login(self):
        self.do_rest_login("authsch")


@override_settings(SOCIAL_AUTH_PROVIDERS=["bss-login"])
class BSSLoginOAuth2Test(OAuth2Test):
    access_token_body = {"access_token": "foobar", "token_type": "bearer"}
    backend_path = "common.social_core.backends.BSSLoginOAuth2"
    user_data_body = {
        "email": "foobar@example.com",
        "email_verified": True,
        "mobile": "+36509999999",
        "name": "Foo Bar",
        "given_name": "Foo",
        "family_name": "Bar",
        "preferred_username": "foobar",
        "nickname": "foobar",
        "groups": ["Group1", "Group2"],
    }
    user_data_url = "https://login.bsstudio.hu/application/o/userinfo/"

    @responses.activate
    def test_login(self):
        self.do_rest_login("bss-login")


@override_settings(SOCIAL_AUTH_PROVIDERS=["google-oauth2"])
class GoogleOAuth2Test(OAuth2Test):
    access_token_body = {"access_token": "foobar", "token_type": "bearer"}
    backend_path = "social_core.backends.google.GoogleOAuth2"
    phone_data_body = {
        "etag": "%Q307aI9ABA8FgzBDoJx71iyhrZWyM3HsaWwP",
        "phoneNumbers": [
            {
                "canonicalForm": "+36509999999",
                "formattedType": "Mobile",
                "metadata": {
                    "primary": True,
                    "source": {"type": "PROFILE", "id": "961158263084132371526"},
                    "verified": True,
                },
                "type": "mobile",
                "value": "+36509999999",
            }
        ],
        "resourceName": "people/961158263084132371526",
    }
    phone_data_url = "https://people.googleapis.com/v1/people/me"
    user_data_body = {
        "email": "foo@bar.com",
        "email_verified": True,
        "family_name": "Bar",
        "given_name": "Foo",
        "locale": "en",
        "name": "Foo Bar",
        "picture": "https://lh5.googleusercontent.com/-ui-GqpNh5Ms/"
        "AAAAAAAAAAI/AAAAAAAAAZw/a7puhHMO_fg/photo.jpg",
        "scope": [  # TODO: Check if it's really returned in real call
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/user.phonenumbers.read",
        ],
        "sub": "101010101010101010101",
    }
    user_data_url = "https://www.googleapis.com/oauth2/v3/userinfo"

    def setUp(self):
        responses.get(re.compile(f"{self.phone_data_url}.*"), json=self.phone_data_body)
        super().setUp()

    @responses.activate
    def test_login(self):
        self.do_rest_login("google-oauth2")


class MicrosoftOAuth2Test(OAuth2Test):
    backend_path = "social_core.backends.microsoft.MicrosoftOAuth2"
    user_data_url = "https://graph.microsoft.com/v1.0/me"
    user_data_body = {
        "displayName": "foo bar",
        "givenName": "foobar",
        "jobTitle": "Auditor",
        "mail": "foobar@foobar.com",
        "mobilePhone": None,
        "officeLocation": "12/1110",
        "preferredLanguage": "en-US",
        "surname": "Bowen",
        "userPrincipalName": "foobar",
        "id": "48d31887-5fad-4d73-a9f5-3c356e68a038",
    }
    access_token_body = {
        "access_token": "foobar",
        "token_type": "bearer",
        "id_token": "",
        "expires_in": 3600,
        "expires_on": 1423650396,
        "not_before": 1423646496,
    }
    phone_data_body = {
        "@odata.context": "https://graph.microsoft.com/beta/$metadata#users('foobar%40foobar.com')/profile/phones",
        "value": [
            {
                "displayName": None,
                "type": "other",
                "number": "36509999999",
                "allowedAudiences": "me",
                "createdDateTime": "2022-05-06T12:58:14.336767Z",
                "lastModifiedDateTime": "2022-05-06T12:58:14.336767Z",
                "id": "d1e8c842-c150-590a-1cd5-a64d2da05457",
                "isSearchable": False,
                "inference": None,
                "createdBy": {
                    "user": None,
                    "device": None,
                    "application": {"displayName": "MSA", "id": None},
                },
                "lastModifiedBy": {
                    "user": None,
                    "device": None,
                    "application": {"displayName": "MSA", "id": None},
                },
                "source": {"type": ["MSA"]},
            }
        ],
    }
    phone_data_url = "https://graph.microsoft.com/beta/me/profile/phones"
    avatar_image_url = "https://graph.microsoft.com/v1.0/me/photos/504x504/$value"

    def setUp(self):
        with open(
            settings.BACKEND_DIR
            / "templates"
            / "static"
            / "images"
            / "default_avatar.png",
            "rb",
        ) as image_file:
            responses.get(self.avatar_image_url, body=b64encode(image_file.read()))
        responses.get(self.phone_data_url, json=self.phone_data_body)
        super().setUp()

    @responses.activate
    def test_login(self):
        self.do_rest_login("microsoft-graph")

    @responses.activate
    def test_login_matches_inactive_placeholder_account(self):
        # Anonymous request flow creates inactive placeholder accounts with the
        # requester's email. The first social login must match such an account
        # instead of creating a duplicate user.
        UserModel = get_user_model()
        placeholder = UserModel.objects.create_user(
            username="foobar@foobar.com",
            email="foobar@foobar.com",
            is_active=False,
        )
        placeholder.set_unusable_password()
        placeholder.save()

        self.do_rest_login("microsoft-graph")

        placeholder.refresh_from_db()
        self.assertTrue(placeholder.is_active)
        self.assertEqual(
            UserModel.objects.filter(email__iexact="foobar@foobar.com").count(), 1
        )
        self.assertTrue(
            placeholder.social_auth.filter(provider="microsoft-graph").exists()
        )

    @responses.activate
    def test_login_without_avatar_does_not_set_provider(self):
        # No Microsoft photo and no Gravatar must leave the provider unset, so
        # User.full_clean() does not later reject the dangling provider.
        responses.replace(responses.GET, self.avatar_image_url, status=404)

        self.do_rest_login("microsoft-graph")

        UserModel = get_user_model()
        user = UserModel.objects.get(email__iexact="foobar@foobar.com")
        self.assertIsNone(user.avatar.get("provider"))
        self.assertIsNone(user.avatar_url)
