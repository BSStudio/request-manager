import logging

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import IntegrityError

from common.models import Ban, User

logger = logging.getLogger(__name__)


@admin.register(User)
class ExtendedUserAdmin(UserAdmin):
    actions = [
        "ban_selected_users",
    ]
    fieldsets = UserAdmin.fieldsets + (
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
        for user in queryset:
            try:
                Ban.objects.create(receiver=user, creator=request.user)
            except IntegrityError:
                logger.warning("User %s is already banned, skipping.", user.username)
                continue
        self.message_user(request, "Successfully banned selected users.")


@admin.register(Ban)
class BanAdmin(admin.ModelAdmin):
    list_display = ("receiver", "created", "reason", "creator")
