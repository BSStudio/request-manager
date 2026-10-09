from core.settings.base import *

INSTALLED_APPS += ["social_django"]


# Social (OAuth2) User authentication
# https://python-social-auth.readthedocs.io/en/latest/index.html

# When using PostgreSQL, it’s recommended to use the built-in JSONB field to store the extracted extra_data.
SOCIAL_AUTH_JSONFIELD_ENABLED = True

# This redirect path is used only when the template tag login button is used
SOCIAL_AUTH_LOGIN_REDIRECT_URL = "/django-admin/"

# On projects behind a reverse proxy that uses HTTPS, the redirect URIs can have the wrong schema so we can force HTTPS.
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

# Use username, email, first and last name for user creation
SOCIAL_AUTH_USER_FIELDS = ["username", "email", "first_name", "last_name"]

# Do not let name to be changed by social profile.
SOCIAL_AUTH_IMMUTABLE_USER_FIELDS = ["first_name", "last_name"]

# Available OAuth2 providers
SOCIAL_AUTH_PROVIDERS = ["authsch", "bss-login", "google-oauth2", "microsoft-graph"]

# AuthSCH OAuth2 settings:
SOCIAL_AUTH_AUTHSCH_KEY = config("AUTH_SCH_CLIENT_ID", default=None)
SOCIAL_AUTH_AUTHSCH_SECRET = config("AUTH_SCH_CLIENT_SECRET", default=None)

# BSS Login OAuth2 settings:
SOCIAL_AUTH_BSS_LOGIN_KEY = config("AUTH_BSS_CLIENT_ID", default=None)
SOCIAL_AUTH_BSS_LOGIN_SECRET = config("AUTH_BSS_CLIENT_SECRET", default=None)
SOCIAL_AUTH_BSS_LOGIN_SUPERUSER_GROUP = config("AUTH_BSS_SUPERUSER_GROUP", default="")
SOCIAL_AUTH_BSS_LOGIN_EXCLUDE_GROUPS = config(
    "AUTH_BSS_EXCLUDE_GROUPS", default="", cast=Csv()
)
SOCIAL_AUTH_BSS_LOGIN_SYNC_TOKEN = config("AUTH_BSS_SYNC_TOKEN", default=None)

# Google OAuth2 settings:
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config("AUTH_GOOGLE_CLIENT_ID", default=None)
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config("AUTH_GOOGLE_CLIENT_SECRET", default=None)
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/user.phonenumbers.read",
]
SOCIAL_AUTH_GOOGLE_OAUTH2_EXTRA_DATA = [
    ("name", "name"),
    ("email", "email"),
]

# Microsoft OAuth2 settings:
SOCIAL_AUTH_MICROSOFT_GRAPH_KEY = config("AUTH_MICROSOFT_CLIENT_ID", default=None)
SOCIAL_AUTH_MICROSOFT_GRAPH_SECRET = config(
    "AUTH_MICROSOFT_CLIENT_SECRET", default=None
)
SOCIAL_AUTH_MICROSOFT_GRAPH_EXTRA_DATA = [
    ("expires_in", "expires"),
    ("displayName", "name"),
    ("mail", "email"),
    ("mobilePhone", "mobile"),
]

SOCIAL_AUTH_PIPELINE = (
    # Get the information we can about the user and return it in a simple
    # format to create the user instance later. In some cases the details are
    # already part of the auth response from the provider, but sometimes this
    # could hit a provider API.
    "social_core.pipeline.social_auth.social_details",
    # Fill in the full name from the first and last name, or the other way around.
    "social_core.pipeline.social_auth.social_names",
    # Get the social uid from whichever service we're authing through. The uid is
    # the unique identifier of the given user in the provider.
    "social_core.pipeline.social_auth.social_uid",
    # Verifies that the current auth process is valid within the current
    # project, this is where emails and domains whitelists are applied (if
    # defined).
    "social_core.pipeline.social_auth.auth_allowed",
    # Custom action: Return error if e-mail was not provided by OAuth.
    "common.social_core.pipeline.check_for_email",
    # Checks if the current social-account is already associated in the site.
    "social_core.pipeline.social_auth.social_user",
    # Make up a username for this person, appends a random string at the end if
    # there's any collision.
    "social_core.pipeline.user.get_username",
    # Custom action: Associates the current social details with another user
    # account with the same email address, including inactive placeholder
    # accounts created by the anonymous request flow.
    "common.social_core.pipeline.associate_by_email",
    # Custom action: Check if user has been banned.
    "common.social_core.pipeline.check_if_user_is_banned",
    # Custom action: Check if there is only one account from a provider is connected to a user.
    "common.social_core.pipeline.check_if_only_one_association_from_a_provider",
    # Custom action: Set user to active when first logs in.
    "common.social_core.pipeline.set_user_active_when_first_logs_in",
    # Custom action: Check if admin/staff user has already associated social profile to his/her account.
    "common.social_core.pipeline.check_if_admin_or_staff_user_already_associated",
    # Custom action: Disconnect all other profile on first staff logon for already existing user.
    "common.social_core.pipeline.disconnect_all_other_profiles_and_change_username_on_first_bss_login",
    # Create a user account if we haven't found one yet.
    "social_core.pipeline.user.create_user",
    # Create the record that associates the social account with the user.
    "social_core.pipeline.social_auth.associate_user",
    # Update the user record with any changed info from the auth service.
    "social_core.pipeline.user.user_details",
    # Custom action: Add phone number to user's profile.
    "common.social_core.pipeline.add_phone_number_to_profile",
    # Custom action: Get user's avatar.
    "common.social_core.pipeline.get_avatar",
    # Custom action: Set permissions and groups for staff users.
    "common.social_core.pipeline.set_groups_and_permissions_for_staff",
    # Populate the extra_data field in the social record with the values
    # specified by settings (and the default ones like access_token, etc.).
    "social_core.pipeline.social_auth.load_extra_data",
)

SOCIAL_AUTH_DISCONNECT_PIPELINE = (
    # Custom action: Verifies that the social association can be disconnected from the current
    # user (ensure that the user login mechanism is not compromised by this
    # disconnection).
    "common.social_core.pipeline.allowed_to_disconnect",
    # Custom action: Removes user's avatar.
    "common.social_core.pipeline.delete_avatar",
    # Collects the social associations to disconnect.
    "social_core.pipeline.disconnect.get_entries",
    # Revoke any access_token when possible.
    "social_core.pipeline.disconnect.revoke_tokens",
    # Removes the social associations.
    "social_core.pipeline.disconnect.disconnect",
)

AUTHENTICATION_BACKENDS += [
    "common.social_core.backends.AuthSCHOAuth2",
    "common.social_core.backends.BSSLoginOAuth2",
    "social_core.backends.google.GoogleOAuth2",
    "social_core.backends.microsoft.MicrosoftOAuth2",
]

# Add schedules task to sync users
CELERY_BEAT_SCHEDULE.update(
    {
        "sync_bss_users": {
            "task": "core.tasks.scheduled_sync_bss_users",
            "schedule": crontab(minute=15, hour=4),
        }
    }
)

if DJANGO_ADMIN and "django.contrib.admin" in INSTALLED_APPS:
    TEMPLATES[0]["OPTIONS"]["context_processors"] += [
        "social_django.context_processors.backends",
        "social_django.context_processors.login_redirect",
    ]
