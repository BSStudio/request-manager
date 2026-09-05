import logging

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin
from django.db import IntegrityError
from django.urls import reverse
from django.utils.html import format_html

from common.models import Ban, User, UserProfile

logger = logging.getLogger(__name__)


@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    list_display = ["user", "phone_number", "avatar_url", "user_link"]
    search_fields = ["user__username"]

    @admin.display(description="Link to User")
    def user_link(self, obj):
        url = reverse("admin:common_user_change", args=(obj.user.id,))
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())


@admin.register(User)
class ExtendedUserAdmin(UserAdmin):
    actions = [
        "ban_selected_users",
    ]
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
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
