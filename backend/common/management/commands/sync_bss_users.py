import logging
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db.models import Q

from common.models import User
from common.social_core.backends import BSSLoginOAuth2
from common.social_core.pipeline import set_groups_and_permissions_for_staff

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Synchronizes BSS users with Django"

    def handle(self, *args, **options):
        # Call Authentik core_users_list endpoint
        # https://docs.goauthentik.io/developer-docs/api/reference/core-users-list
        resp = requests.get(
            "https://login.bsstudio.hu/api/v3/core/users/?is_active=true&page_size=1000&path=users&type=internal",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {settings.SOCIAL_AUTH_BSS_LOGIN_SYNC_TOKEN}",
            },
            timeout=(5, 30),
        )

        resp.raise_for_status()

        total_created = 0
        total_demoted = 0
        users_found = []

        if resp.json()["pagination"]["total_pages"] > 1:
            raise NotImplementedError("Response has more than one page.")

        for result in resp.json()["results"]:
            # If there is a user with the same username as the user from our directory raise exception
            # Note: We assume if there is already a user who's not staff then he's not the one from our directory
            if User.objects.filter(
                username=result["username"], is_staff=False
            ).exists():
                logger.error(
                    "User with username %s already exists as non-staff.",
                    result["username"],
                    stack_info=True,
                )
                continue

            # In really rare cases e-mail address might exist for a different user
            # We want manual interaction and validation here, so we raise exception and continue
            if (
                User.objects.filter(email__iexact=result["email"])
                .exclude(username=result["username"])
                .exists()
            ):
                logger.error(
                    "E-mail address %s is already assigned to a different user (sync user: %s).",
                    result["email"],
                    result["username"],
                    stack_info=True,
                )
                continue

            # These columns are NOT NULL, so the entry cannot be written.
            # Report it and let it be fixed in the directory.
            missing_attributes = [
                attribute
                for attribute in ("first_name", "last_name", "mobile")
                if not result["attributes"].get(attribute)
            ]
            if missing_attributes:
                logger.error(
                    "User %s is missing attributes in the directory: %s.",
                    result["username"],
                    ", ".join(missing_attributes),
                    stack_info=True,
                )
                # Counted as found so that a directory problem cannot demote
                # somebody who really is staff.
                users_found.append(result["username"])
                continue

            user, created = User.objects.get_or_create(
                username=result["username"],
                defaults={"is_staff": True, "password": make_password(None)},
            )

            user.first_name = result["attributes"].get("first_name")
            user.last_name = result["attributes"].get("last_name")
            user.email = result["email"]
            user.phone_number = result["attributes"].get("mobile")

            avatar_url_hostname = urlparse(result.get("avatar", "")).hostname
            if avatar_url_hostname and (
                avatar_url_hostname == "gravatar.com"
                or avatar_url_hostname.endswith(".gravatar.com")
            ):
                user.avatar["gravatar"] = result["avatar"]

                if not user.avatar.get("provider", None):
                    user.avatar["provider"] = "gravatar"

            user.save()

            # Use the social-auth pipeline function to set the groups, but we need some transformation
            groups = [group["name"] for group in result["groups_obj"]]
            set_groups_and_permissions_for_staff(
                BSSLoginOAuth2, {"groups": groups}, user
            )

            if created:
                total_created += 1

            users_found.append(user.username)

        # Demote users who have staff or admin privileges but were not found in our directory
        for user in User.objects.filter(
            Q(is_superuser=True) | Q(is_staff=True)
        ).exclude(username__in=users_found):
            user.is_superuser = False
            user.is_staff = False
            user.groups.clear()
            user.save()  # Save modifications
            total_demoted += 1
            logger.info(
                "%s (%s) has been demoted.", user.get_full_name(), user.username
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Found {len(users_found)} user(s), {total_created} new, {total_demoted} demoted."
            )
        )
