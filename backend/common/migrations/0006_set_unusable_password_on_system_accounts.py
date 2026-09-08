from django.contrib.auth.hashers import make_password
from django.db import migrations


def set_unusable_passwords(apps, schema_editor):
    """An empty password is not a valid hash: checking it raises instead of failing."""
    User = apps.get_model("common", "User")
    users = list(User.objects.filter(password=""))  # nosec B106
    for user in users:
        user.password = make_password(None)
    User.objects.bulk_update(users, ["password"])


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0005_merge_user_profile_into_user"),
    ]

    operations = [
        migrations.RunPython(set_unusable_passwords, migrations.RunPython.noop),
    ]
