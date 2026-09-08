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

    @admin.action(description=_("Ban selected users"))
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
    list_display = ("receiver", "created", "reason", "creator")
