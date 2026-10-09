import logging

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from common.models import Ban, User

logger = logging.getLogger(__name__)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    actions = [
        "ban_selected_users",
    ]
    fieldsets = BaseUserAdmin.fieldsets + (
        (_("Profile"), {"fields": ("phone_number", "avatar")}),
    )
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "phone_number",
        "is_staff",
        "is_admin",
        "is_superuser",
    )

    def get_queryset(self, request):
        # is_admin in list_display reads group_names on every staff row.
        return super().get_queryset(request).prefetch_related("groups")

    @admin.display(boolean=True, description=_("Is admin"))
    def is_admin(self, obj):
        return obj.is_admin

    def has_ban_permission(self, request):
        return request.user.has_perm("common.add_ban")

    @admin.action(description=_("Ban selected users"), permissions=["ban"])
    def ban_selected_users(self, request, queryset):
        banned = 0
        skipped = []
        for user in queryset:
            try:
                Ban.objects.create(receiver=user, creator=request.user)
            except (ValidationError, IntegrityError) as error:
                logger.warning("Skipping ban for %s: %s", user.username, error)
                skipped.append(user.username)
                continue
            banned += 1

        if skipped:
            self.message_user(
                request,
                ngettext(
                    "Banned %(count)d user, skipped %(skipped)d: %(usernames)s.",
                    "Banned %(count)d users, skipped %(skipped)d: %(usernames)s.",
                    banned,
                )
                % {
                    "count": banned,
                    "skipped": len(skipped),
                    "usernames": ", ".join(skipped),
                },
                messages.WARNING,
            )
        else:
            self.message_user(
                request,
                ngettext(
                    "Successfully banned %(count)d user.",
                    "Successfully banned %(count)d users.",
                    banned,
                )
                % {"count": banned},
            )


@admin.register(Ban)
class BanAdmin(admin.ModelAdmin):
    autocomplete_fields = ["receiver"]
    list_display = ("receiver", "created", "reason", "creator")
    search_fields = [
        "receiver__username",
        "receiver__first_name",
        "receiver__last_name",
        "receiver__email",
    ]

    def get_readonly_fields(self, request, obj=None):
        # The receiver is the primary key: changing it would save a second ban
        # and leave the first one in place.
        return ["creator"] if obj is None else ["receiver", "creator"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "receiver":
            # save_model() sets the creator, too late for Ban.clean() to turn a
            # self-ban into a form error.
            kwargs["queryset"] = User.objects.exclude(pk=request.user.pk)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creator = request.user
        super().save_model(request, obj, form, change)
