from django.db import migrations


class Migration(migrations.Migration):
    """
    The token_blacklist app of djangorestframework-simplejwt is no longer
    installed, so nothing would ever migrate its tables away.
    """

    dependencies = [
        ("common", "0009_label_user_profile_fields"),
    ]

    operations = [
        migrations.RunSQL(
            """
            DROP TABLE IF EXISTS token_blacklist_blacklistedtoken;
            DROP TABLE IF EXISTS token_blacklist_outstandingtoken;
            DELETE FROM django_migrations WHERE app = 'token_blacklist';
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
