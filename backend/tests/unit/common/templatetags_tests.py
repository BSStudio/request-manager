from django.conf import settings

from common.templatetags.extra_tags import settings_value


def test_settings_value_reads_from_the_settings_module():
    assert settings_value("BASE_URL") == settings.BASE_URL
