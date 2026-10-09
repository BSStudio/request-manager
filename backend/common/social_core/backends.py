import hashlib

from django.utils.crypto import constant_time_compare
from social_core.backends.open_id_connect import OpenIdConnectAuth
from social_core.exceptions import AuthResponseError


class BrowserNonceOpenIdConnectAuth(OpenIdConnectAuth):
    # Seconds the provider's clock may run ahead of ours.
    JWT_LEEWAY = 60

    # Set by the API views. There the frontend builds the authorization URL, so
    # social_core stored no nonce, and the provider got this one's SHA-256 hash.
    browser_nonce = None

    def validate_temporal_claims(self, id_token):
        # PyJWT already checked nbf with the leeway, social_core would again without.
        super().validate_temporal_claims(
            {claim: value for claim, value in id_token.items() if claim != "nbf"}
        )

    def validate_claims(self, id_token):
        if self.browser_nonce is None:
            return super().validate_claims(id_token)
        self.validate_temporal_claims(id_token)
        nonce = hashlib.sha256(self.browser_nonce.encode()).hexdigest()
        if not constant_time_compare(nonce, id_token.get("nonce", "")):
            raise AuthResponseError(
                self,
                "Incorrect id_token: nonce",
                code="nonce_mismatch",
                stage="token_validation",
            )


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
