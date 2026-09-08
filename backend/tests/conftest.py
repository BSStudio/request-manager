"""Fixtures every suite that talks to the API needs.

The five callers live here rather than under tests/api/ because tests/workflows/
drives the same endpoints. Fixtures that only make sense for a single endpoint —
the missing ids behind every 404 — stay in tests/api/conftest.py.
"""

import pytest
from rest_framework.test import APIClient

from tests.factories import make_user


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    return make_user(username="admin", first_name="Admin", is_admin=True)


@pytest.fixture
def staff_user():
    return make_user(username="staff", first_name="Staff", is_staff=True)


@pytest.fixture
def basic_user():
    return make_user(username="basic", first_name="Basic")


@pytest.fixture
def service_account():
    return make_user(
        username="service-account",
        first_name="Service",
        last_name="Account",
        is_service_account=True,
    )
