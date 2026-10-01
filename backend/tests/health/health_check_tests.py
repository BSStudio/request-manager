import json
import re
from io import StringIO

import pytest
from django.conf import settings
from django.core.management import call_command
from rest_framework.status import HTTP_200_OK

pytestmark = pytest.mark.django_db

#: Every backing service a health report must list; the endpoint and the
#: management command run the same check.
EXPECTED_CHECKS = [
    "Cache(alias='default')",
    "Database(alias='default')",
    "Mail(alias='default')",
    "Storage(alias='default')",
]

REDIS_CHECK = re.compile(r"Redis\(host='[^']+', port=6379\)")


def test_the_endpoint_reports_every_backing_service(client):
    token = (
        f"/{settings.HEALTH_CHECK_URL_TOKEN}"
        if getattr(settings, "HEALTH_CHECK_URL_TOKEN", None) is not None
        else ""
    )

    response = client.get(f"/health{token}?format=json")

    assert response.status_code == HTTP_200_OK
    reported = json.loads(response.content)
    for check in EXPECTED_CHECKS:
        assert check in reported
    assert any(REDIS_CHECK.search(key) for key in reported)


def test_the_management_command_reports_every_backing_service():
    with StringIO() as out:
        # The command signals its verdict through the exit code.
        with pytest.raises(SystemExit) as exit_info:
            call_command("health_check", "health_check", "--no-http", stdout=out)

        assert exit_info.value.code == 0
        reported = out.getvalue()
        for check in EXPECTED_CHECKS:
            assert check in reported
        assert REDIS_CHECK.search(reported)
