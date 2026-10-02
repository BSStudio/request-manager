"""The four identity providers the site accepts, as mocked OAuth2 endpoints."""

from base64 import b64encode

from django.conf import settings

from tests.helpers.oauth2 import Provider


def default_avatar_bytes():
    """The photo Microsoft Graph would return, base64 as the real API does."""
    path = (
        settings.BACKEND_DIR / "templates" / "static" / "images" / "default_avatar.png"
    )
    with open(path, "rb") as image_file:
        return b64encode(image_file.read())


AUTHSCH = Provider(
    name="authsch",
    backend_path="common.social_core.backends.AuthSCHOAuth2",
    user_data_url="https://auth.sch.bme.hu/oidc/userinfo",
    user_data_body={
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
    },
)

BSS_LOGIN = Provider(
    name="bss-login",
    backend_path="common.social_core.backends.BSSLoginOAuth2",
    user_data_url="https://login.bsstudio.hu/application/o/userinfo/",
    user_data_body={
        "email": "foobar@example.com",
        "email_verified": True,
        "mobile": "+36509999999",
        "name": "Foo Bar",
        "given_name": "Foo",
        "family_name": "Bar",
        "preferred_username": "foobar",
        "nickname": "foobar",
        "groups": ["Group1", "Group2"],
    },
)

GOOGLE = Provider(
    name="google-oauth2",
    backend_path="social_core.backends.google.GoogleOAuth2",
    user_data_url="https://www.googleapis.com/oauth2/v3/userinfo",
    user_data_body={
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
    },
    extra_json={
        "https://people.googleapis.com/v1/people/me": {
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
    },
)

MICROSOFT_AVATAR_URL = "https://graph.microsoft.com/v1.0/me/photos/240x240/$value"

MICROSOFT = Provider(
    name="microsoft-graph",
    backend_path="social_core.backends.microsoft.MicrosoftOAuth2",
    user_data_url="https://graph.microsoft.com/v1.0/me",
    user_data_body={
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
    },
    access_token_body={
        "access_token": "foobar",
        "token_type": "bearer",
        "id_token": "",
        "expires_in": 3600,
        "expires_on": 1423650396,
        "not_before": 1423646496,
    },
    extra_body={MICROSOFT_AVATAR_URL: default_avatar_bytes},
    extra_json={
        "https://graph.microsoft.com/beta/me/profile/phones": {
            "@odata.context": "https://graph.microsoft.com/beta/$metadata"
            "#users('foobar%40foobar.com')/profile/phones",
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
    },
)

ALL_PROVIDERS = [AUTHSCH, BSS_LOGIN, GOOGLE, MICROSOFT]
