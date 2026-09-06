from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from common.models import Ban


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
