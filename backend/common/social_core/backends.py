from django.utils.crypto import constant_time_compare
from social_core.backends.open_id_connect import OpenIdConnectAuth
from social_core.exceptions import AuthTokenError

from common.social_core.strategy import DRFStrategy


class BrowserNonceOpenIdConnectAuth(OpenIdConnectAuth):
    # For the API, the frontend builds the authorization URL, so social_core has no
    # stored nonce to check. The browser sends its own with the code instead.
    def validate_claims(self, id_token):
        if not isinstance(self.strategy, DRFStrategy):
            return super().validate_claims(id_token)
        self.validate_temporal_claims(id_token)
        nonce = self.data.get("nonce")
        if not nonce or not constant_time_compare(nonce, id_token.get("nonce", "")):
            raise AuthTokenError(self, "Incorrect id_token: nonce")


class AuthSCHOAuth2(BrowserNonceOpenIdConnectAuth):
    """AuthSCH OpenID Connect authentication backend"""

    name = "authsch"
    OIDC_ENDPOINT = "https://auth.sch.bme.hu"
    DEFAULT_SCOPE = [
        "directory.sch.bme.hu:sAMAccountName",
        "email",
        "openid",
        "phone",
        "profile",
    ]
    EXTRA_DATA = [
        ("expires_in", "expires"),
        ("name", "name"),
        ("email", "email"),
        ("phone_number", "mobile"),
    ]

    def get_user_details(self, response):
        """Return user details from AuthSCH account"""
        return {
            "username": f"{response.get('directory.sch.bme.hu:sAMAccountName')}@sch.bme.hu",
            "email": response.get("email"),
            "first_name": response.get("given_name"),
            "last_name": response.get("family_name"),
            "mobile": response.get("phone_number"),
        }


class BSSLoginOAuth2(BrowserNonceOpenIdConnectAuth):
    """BSS Login OpenID Connect authentication backend"""

    name = "bss-login"
    OIDC_ENDPOINT = "https://login.bsstudio.hu/application/o/request-manager"
    DEFAULT_SCOPE = [
        "email",
        "mobile",
        "openid",
        "profile",
    ]
    EXTRA_DATA = [
        ("expires_in", "expires"),
        ("name", "name"),
        ("email", "email"),
        ("mobile", "mobile"),
    ]

    def get_user_details(self, response):
        """Return user details from BSS Login"""
        return {
            "username": response.get("preferred_username"),
            "email": response.get("email"),
            "first_name": response.get("given_name"),
            "last_name": response.get("family_name"),
            "mobile": response.get("mobile"),
        }
