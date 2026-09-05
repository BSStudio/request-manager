from django.db import migrations


def move_user_content_type(apps, schema_editor):
    """
    The user model moved from the auth app to the common app but kept its table.
    Repoint the existing content type so the permissions and admin log entries
    attached to it survive the move instead of being orphaned next to a freshly
    created common.user content type.
    """
    ContentType = apps.get_model("contenttypes", "ContentType")
    if ContentType.objects.filter(app_label="common", model="user").exists():
        return
    ContentType.objects.filter(app_label="auth", model="user").update(
        app_label="common"
    )
    ContentType.objects.clear_cache()


def restore_user_content_type(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    if ContentType.objects.filter(app_label="auth", model="user").exists():
        return
    ContentType.objects.filter(app_label="common", model="user").update(
        app_label="auth"
    )
    ContentType.objects.clear_cache()


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0003_alter_ban_creator"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(move_user_content_type, restore_user_content_type),
    ]
