import logging
from base64 import b64encode

import requests
from django.conf import settings
from django.contrib.auth.models import Group
from libgravatar import Gravatar, sanitize_email
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from social_core.exceptions import AuthException, NotAllowedToDisconnect
from social_django.models import UserSocialAuth

logger = logging.getLogger(__name__)


def check_for_email(details, *args, **kwargs):
    if not details.get("email"):
        raise ValidationError("Email was not provided by OAuth provider.")


def associate_by_email(backend, details, user=None, *args, **kwargs):
    """
    Drop-in replacement for social_core.pipeline.social_auth.associate_by_email
    that also matches inactive accounts created by the anonymous request flow.
    """
    if user:
        return None

    email = details.get("email")
    if not email:
        return None

    user_model = backend.strategy.storage.user.user_model()
    users = list(user_model.objects.filter(email__iexact=email))
    if len(users) == 0:
        return None
    if len(users) > 1:
        raise AuthException(
            backend, "The given email address is associated with another account"
        )
    return {"user": users[0], "is_new": False}


def check_if_user_is_banned(backend, user=None, *args, **kwargs):
    if user and user.is_banned:
        raise AuthenticationFailed(detail="Your account is suspended.")


def check_if_only_one_association_from_a_provider(
    backend, new_association=True, user=None, *args, **kwargs
):
    """
    Check if there is only one association from a provider to a user.
    Only one profile can be connected to a user from a provider.
    """
    if (
        user
        and new_association
        and backend.strategy.storage.user.get_social_auth_for_user(
            user, provider=backend.name
        ).count()
        > 0
    ):
        msg = [
            "There is already a connected account from this provider. Please disconnect the other one first."
        ]
        raise ValidationError({backend: msg})


def set_user_active_when_first_logs_in(backend, user=None, *args, **kwargs):
    if user and not backend.strategy.storage.user.get_social_auth_for_user(user):
        user.is_active = True
        user.save()
        logger.info(
            "User account has been activated for %s (%s)",
            user.get_full_name(),
            user.username,
        )


def check_if_admin_or_staff_user_already_associated(
    backend, strategy, user=None, is_new=False, new_association=True, *args, **kwargs
):
    """
    A staff or admin member must associate his/her social profile first.
    (S)he has to log in with her/his BSS Login account and associate the profile.
    Runs only at login process. (Request sender user is anonymous).
    """
    if (
        strategy.request.user.is_anonymous
        and not is_new
        and new_association
        and user
        and (user.is_superuser or user.is_staff)
        and not backend.name == "bss-login"
        and not backend.strategy.storage.user.get_social_auth_for_user(
            user, provider=backend.name
        ).exists()
    ):
        raise AuthenticationFailed(
            detail="Your social profile is not associated with your account."
        )


def disconnect_all_other_profiles_and_change_username_on_first_bss_login(
    backend,
    strategy,
    details,
    user=None,
    is_new=False,
    new_association=True,
    *args,
    **kwargs,
):
    """
    As non-staff users can change their e-mail addresses, and we match social logins by e-mail address
    make sure to drop all other connected social profiles when a staff user connect get his privileges the first time.
    This only happens if an account with the same e-mail already existed for security reasons.
    We also change the username to match our directory.
    """
    if (
        strategy.request.user.is_anonymous
        and not is_new
        and new_association
        and user
        and backend.name == "bss-login"
        and not backend.strategy.storage.user.get_social_auth_for_user(
            user, provider=backend.name
        ).exists()
    ):
        UserSocialAuth.objects.filter(user=user).delete()
        user.username = details.get("username")
        user.save()


def add_phone_number_to_profile(backend, details, response, user, *args, **kwargs):
    if user.phone_number:
        return

    phone_number = None

    # AuthSCH
    if details.get("mobile"):
        phone_number = details.get("mobile")

    # BSS Login
    if details.get("mobile"):
        phone_number = details.get("mobile")

    # Google
    elif (
        backend.name == "google-oauth2"
        and "https://www.googleapis.com/auth/user.phonenumbers.read"
        in response["scope"]
    ):
        resp = requests.get(
            "https://people.googleapis.com/v1/people/me?personFields=phoneNumbers",
            headers={"Authorization": f"Bearer {response['access_token']}"},
            timeout=5,
        )
        if resp.status_code == 200 and len(resp.json().get("phoneNumbers", [])) > 0:
            phone_number = resp.json()["phoneNumbers"][0]["value"]

    elif backend.name == "microsoft-graph":
        if response["mobilePhone"]:
            phone_number = response["mobilePhone"]
        else:
            resp = requests.get(
                "https://graph.microsoft.com/beta/me/profile/phones",
                headers={"Authorization": f"Bearer {response['access_token']}"},
                timeout=5,
            )
            if resp.status_code == 200 and len(resp.json().get("value", [])) > 0:
                phone_number = f"+{resp.json()['value'][0]['number']}"

    # Set phone number
    if not user.phone_number and phone_number:
        user.phone_number = phone_number
        user.save()


def get_avatar(backend, response, user, *args, **kwargs):
    if backend.name == "google-oauth2" and response.get("picture"):
        user.avatar["google-oauth2"] = response["picture"][:-6]

    elif backend.name == "microsoft-graph":
        resp = requests.get(
            "https://graph.microsoft.com/v1.0/me/photos/504x504/$value",
            headers={
                "Authorization": f"Bearer {response['access_token']}",
                "Content-Type": "image/jpg",
            },
            timeout=5,
        )
        if resp.status_code == 200:
            user.avatar["microsoft-graph"] = (
                f"data:image/jpg;base64,{b64encode(resp.content).decode('utf-8')}"
            )

    url = Gravatar(sanitize_email(user.email)).get_image(
        size=500, use_ssl=True, default="404"
    )
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        user.avatar["gravatar"] = url
        if not user.avatar.get("provider", None):
            user.avatar["provider"] = "gravatar"
    except requests.exceptions.HTTPError:
        logger.debug("Gravatar not found for %s", user.email)

    if (
        not user.avatar.get("provider", None)
        and backend.name in ["google-oauth2", "microsoft-graph"]
        and user.avatar.get(backend.name)
    ):
        user.avatar["provider"] = backend.name

    user.save()


def set_groups_and_permissions_for_staff(backend, response, user, *args, **kwargs):
    if not backend.name == "bss-login":
        return

    mirror_groups_except = frozenset(settings.SOCIAL_AUTH_BSS_LOGIN_EXCLUDE_GROUPS)
    provided_group_names = frozenset(response.get("groups", []))
    target_group_names = provided_group_names - mirror_groups_except
    current_group_names = frozenset(
        user.groups.values_list("name", flat=True).iterator()
    )

    if target_group_names != current_group_names:
        existing_groups = list(
            Group.objects.filter(name__in=target_group_names).iterator()
        )
        existing_group_names = frozenset(group.name for group in existing_groups)

        new_groups = [
            Group.objects.get_or_create(name=name)[0]
            for name in target_group_names
            if name not in existing_group_names
        ]

        user.groups.set(existing_groups + new_groups)
        user.invalidate_group_names()

    user.is_staff = True
    user.is_superuser = (
        settings.SOCIAL_AUTH_BSS_LOGIN_SUPERUSER_GROUP in provided_group_names
    )

    user.save()


def allowed_to_disconnect(
    strategy, user, name, user_storage, association_id=None, *args, **kwargs
):
    if not (
        UserSocialAuth.objects.filter(user=user).exclude(provider=name).exists()
        or user.is_staff
    ):
        raise NotAllowedToDisconnect()


def delete_avatar(
    strategy, user, name, user_storage, association_id=None, *args, **kwargs
):
    if user.avatar.pop(name, None):
        user.save()
