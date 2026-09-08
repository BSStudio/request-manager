from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from common.models import Ban, User


@receiver(post_save, sender=Ban)
def post_save_ban(sender, instance, **kwargs):
    instance.receiver.is_active = False
    instance.receiver.is_staff = False
    instance.receiver.is_superuser = False
    instance.receiver.groups.clear()
    for token in instance.receiver.outstandingtoken_set.all():
        try:
            refresh_token = RefreshToken(token.token)
            refresh_token.blacklist()
        except TokenError:
            continue
    instance.receiver.save()


@receiver(post_delete, sender=Ban)
def post_delete_ban(sender, instance, **kwargs):
    instance.receiver.is_active = True
    instance.receiver.save()


@receiver(m2m_changed, sender=User.groups.through)
def invalidate_group_names(sender, instance, action, reverse, **kwargs):
    # group_names is cached on the instance the change was made through, so the
    # reverse side (group.user_set) cannot be reached from here.
    if not reverse and action in ("post_add", "post_remove", "post_clear"):
        instance.invalidate_group_names()
