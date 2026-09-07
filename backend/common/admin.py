import logging

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from common.models import Ban, User

logger = logging.getLogger(__name__)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    actions = [
        "ban_selected_users",
    ]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Profile", {"fields": ("phone_number", "avatar")}),
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
                f"Banned {banned} user(s), skipped {len(skipped)}: "
                f"{', '.join(skipped)}.",
                messages.WARNING,
            )
        else:
            self.message_user(request, f"Successfully banned {banned} user(s).")


@admin.register(Ban)
class BanAdmin(admin.ModelAdmin):
    list_display = ("receiver", "created", "reason", "creator")
