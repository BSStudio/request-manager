from functools import cache

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import JSONField
from django.db.models.functions import Lower
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from jsonschema import FormatChecker
from jsonschema import ValidationError as JsonValidationError
from jsonschema import validate
from phonenumber_field.modelfields import PhoneNumberField
from simple_history.models import HistoricalRecords

from common.schemas import USER_AVATAR_SCHEMA


def get_sentinel_user():
    return get_user_model().objects.get_or_create(
        username="deleted",
        defaults={
            "first_name": "Felhasználó",
            "last_name": "Törölt",
            "password": make_password(None),
        },
    )[0]


def get_anonymous_user():
    return get_user_model().objects.get_or_create(
        username="anonymous",
        defaults={
            "first_name": "Felhasználó",
            "last_name": "Nem Azonosított",
            "password": make_password(None),
        },
    )[0]


def get_system_user():
    return get_user_model().objects.get_or_create(
        username="system",
        defaults={
            "first_name": "Automatizáció",
            "last_name": "Rendszer",
            "password": make_password(None),
        },
    )[0]


def validate_avatar(value):
    try:
        validate(value, USER_AVATAR_SCHEMA, format_checker=FormatChecker())
    except JsonValidationError as e:
        raise ValidationError(e)


class User(AbstractUser):
    """
    Custom user model replacing django.contrib.auth.models.User.

    It keeps the original ``auth_user`` table and its join tables so that
    switching to it does not require moving any data.
    """

    groups = models.ManyToManyField(
        Group,
        verbose_name=_("groups"),
        blank=True,
        help_text=_(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_name="user_set",
        related_query_name="user",
        db_table="auth_user_groups",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_("Specific permissions for this user."),
        related_name="user_set",
        related_query_name="user",
        db_table="auth_user_user_permissions",
    )
    avatar = JSONField(
        encoder=DjangoJSONEncoder,
        validators=[validate_avatar],
        default=dict,
        blank=True,
    )
    phone_number = PhoneNumberField(blank=True)

    # Validated on every save, like UserProfile.save() did. The inherited fields
    # are not: username and e-mail arrive unchecked from the identity providers.
    # Model.clean() still normalises both.
    VALIDATED_ON_SAVE = ("avatar", "phone_number")

    class Roles(models.TextChoices):
        ADMIN = "admin", _("Admin")
        STAFF = "staff", _("Staff")
        USER = "user", _("User")

    class Meta(AbstractUser.Meta):
        db_table = "auth_user"
        constraints = [
            # Blank e-mail addresses are excluded: the sentinel, anonymous and
            # system accounts all share one.
            models.UniqueConstraint(
                Lower("email"),
                condition=~models.Q(email=""),
                name="unique_user_email",
                violation_error_message=_("E-mail address already in use."),
            )
        ]

    def clean(self):
        super().clean()
        if not isinstance(self.avatar, dict):
            raise ValidationError({"avatar": [_("Avatar must be an object.")]})
        provider = self.avatar.get("provider")
        if provider and not self.avatar.get(provider):
            raise ValidationError(
                {"avatar": [_("Avatar does not exist for this provider.")]}
            )

    def save(self, *args, **kwargs):
        self.full_clean(
            exclude=fields_excluded_from_clean(),
            validate_unique=False,
            validate_constraints=False,
        )
        # Constraints are validated separately: the exclude list above covers
        # e-mail, which would skip the unique constraint and let it surface as
        # an IntegrityError instead. The e-mail address is the only field the
        # constraints touch, so saves that leave it alone (the last_login write
        # on every login) do not pay for the extra query.
        update_fields = kwargs.get("update_fields")
        if update_fields is None or "email" in update_fields:
            self.validate_constraints()
        return super().save(*args, **kwargs)

    @property
    def avatar_url(self) -> str:
        return self.avatar.get(self.avatar.get("provider", None), None)

    @cached_property
    def group_names(self) -> frozenset[str]:
        # groups.all() rather than a filtered exists(): prefetch and cacheops apply.
        # Only user.groups changes refresh this: a group.user_set one cannot reach
        # the instance holding the cache.
        return frozenset(group.name for group in self.groups.all())

    def invalidate_group_names(self) -> None:
        self.__dict__.pop("group_names", None)

    @property
    def is_admin(self) -> bool:
        return self.is_staff and (
            self.is_superuser or settings.ADMIN_GROUP in self.group_names
        )

    @property
    def is_banned(self) -> bool:
        return hasattr(self, "ban")

    @property
    def is_service_account(self) -> bool:
        return settings.SERVICE_ACCOUNTS_GROUP in self.group_names

    @property
    def role(self) -> str:
        if self.is_admin:
            return self.Roles.ADMIN
        elif self.is_staff:
            return self.Roles.STAFF
        else:
            return self.Roles.USER

    def get_full_name_eastern_order(self) -> str:
        return f"{self.last_name} {self.first_name}".strip()


@cache
def fields_excluded_from_clean() -> list[str]:
    return [
        field.name
        for field in User._meta.fields
        if field.name not in User.VALIDATED_ON_SAVE
    ]


class Ban(models.Model):
    receiver = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="created_bans",
        on_delete=models.SET(get_sentinel_user),
    )
    reason = models.CharField(max_length=100, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.receiver == self.creator:
            raise ValidationError({"receiver": [_("Users cannot ban themselves.")]})

    def save(self, *args, **kwargs):
        self.full_clean()
        # Django sends post_save outside of any transaction, so a failure while
        # it deactivates the receiver would otherwise leave the ban behind.
        with transaction.atomic():
            return super().save(*args, **kwargs)


class AbstractComment(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET(get_sentinel_user)
    )
    created = models.DateTimeField(auto_now_add=True)
    text = models.TextField()
    internal = models.BooleanField(default=False)
    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True

    def get_owner(self):
        return self.author


class AbstractRating(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET(get_sentinel_user)
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(5), MinValueValidator(1)]
    )
    review = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True

    def get_owner(self):
        return self.author


class AbstractTodo(models.Model):
    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="assigned_todos", blank=True
    )
    created = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET(get_sentinel_user),
        related_name="created_todos",
    )
    description = models.TextField()

    class Meta:
        abstract = True

    def get_owner(self):
        return self.creator
