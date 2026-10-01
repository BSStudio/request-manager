"""Object factories for the test suite.

``Request.clean()`` rejects an ``end_datetime`` before ``start_datetime``, which
model_bakery's random dates hit half the time. ``ProjectBaker``, wired in through
``BAKER_CUSTOM_CLASS``, fills in valid dates, so call sites use plain ``baker``.

Users go through :func:`make_user`: the roles the API distinguishes are groups
and flags, not field values.
"""

from datetime import timedelta
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import Group
from django.utils import timezone
from model_bakery.baker import Baker

from common.models import Ban, User, get_system_user

DEFAULT_PASSWORD = "ae9U$89z#zyA!YoPE$6m"  # nosec
DEFAULT_PHONE_NUMBER = "+36701234567"
DEFAULT_AVATAR = {
    "provider": "gravatar",
    "gravatar": "https://example.com/gravatar.png",
    "microsoft-graph": "https://example.com/microsoft-graph.png",
}


def gen_phone_number() -> str:
    """Generator for ``BAKER_CUSTOM_FIELDS_GEN``.

    model_bakery has no built-in generator for ``PhoneNumberField``, so tests
    using ``_fill_optional`` on the user model would fail without one.
    """
    return DEFAULT_PHONE_NUMBER


def _request_defaults(attrs: dict) -> dict:
    """Keep ``Request.end_datetime`` after ``start_datetime``.

    Only fills what the caller left out, so a test that cares about the dates
    still owns them.
    """
    if "start_datetime" not in attrs:
        attrs["start_datetime"] = timezone.now()
    if "end_datetime" not in attrs:
        attrs["end_datetime"] = attrs["start_datetime"] + timedelta(hours=2)
    return attrs


_MODEL_DEFAULTS = {"video_requests.request": _request_defaults}


class ProjectBaker(Baker):
    """Baker that fills in what the models insist on. See the module docstring."""

    def make(self, **attrs):
        return super().make(**self._with_defaults(attrs))

    def prepare(self, **attrs):
        return super().prepare(**self._with_defaults(attrs))

    def _with_defaults(self, attrs: dict) -> dict:
        defaults = _MODEL_DEFAULTS.get(self.model._meta.label_lower)
        return defaults(attrs) if defaults else attrs


def make_user(
    *,
    username: str | None = None,
    email: str | None = None,
    password: str = DEFAULT_PASSWORD,
    first_name: str | None = None,
    last_name: str = "Test",
    is_staff: bool = False,
    is_admin: bool = False,
    is_service_account: bool = False,
    is_superuser: bool = False,
    groups: tuple[str, ...] = (),
    banned: bool = False,
    avatar: dict | None = None,
    phone_number: str = DEFAULT_PHONE_NUMBER,
) -> User:
    """Create a user in one of the roles the API distinguishes.

    ``is_admin`` implies staff plus membership of ``settings.ADMIN_GROUP``, which
    is what :attr:`User.is_admin` reads. Missing names default to the role, so a
    failure message says which caller it was.
    """
    role = _role_name(
        is_admin=is_admin,
        is_service_account=is_service_account,
        is_staff=is_staff,
    )
    # Unique by default: several tests need more than one user per role, and both
    # the username and the e-mail address are unique columns.
    username = username or f"{role.lower()}_{uuid4().hex[:12]}"
    user = User.objects.create_user(
        username=username,
        password=password,
        email=email if email is not None else f"{username}@example.com",
        first_name=first_name or role,
        last_name=last_name,
    )

    user.is_staff = is_staff or is_admin
    user.is_superuser = is_superuser
    user.avatar = DEFAULT_AVATAR if avatar is None else avatar
    user.phone_number = phone_number
    user.save()

    group_names = list(groups)
    if is_admin:
        group_names.append(settings.ADMIN_GROUP)
    if is_service_account:
        group_names.append(settings.SERVICE_ACCOUNTS_GROUP)
    for name in group_names:
        user.groups.add(Group.objects.get_or_create(name=name)[0])
    user.invalidate_group_names()

    if banned:
        Ban.objects.create(creator=get_system_user(), receiver=user)

    return user


def _role_name(*, is_admin: bool, is_service_account: bool, is_staff: bool) -> str:
    if is_admin:
        return "Admin"
    if is_service_account:
        return "Service"
    if is_staff:
        return "Staff"
    return "User"
