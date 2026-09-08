"""Fixtures every suite that talks to the API needs.

The five callers live here rather than under tests/api/ because tests/workflows/
drives the same endpoints. Fixtures that only make sense for a single endpoint —
the missing ids behind every 404 — stay in tests/api/conftest.py.
"""

import pytest
import responses
from rest_framework.test import APIClient

from tests.factories import make_user
from tests.helpers.oauth2 import MockedProvider, reset_social_core_caches


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


@pytest.fixture
def requester():
    """Somebody outside the studio who asked us to film something."""
    return make_user(username="requester", first_name="Requester")


@pytest.fixture
def editor_in_chief():
    """Copied in on everything the crew is told; the group name is load-bearing."""
    return make_user(is_staff=True, groups=("Főszerkesztő",))


@pytest.fixture
def production_manager():
    return make_user(is_staff=True, groups=("Gyártásvezető",))


@pytest.fixture
def pr_responsible():
    return make_user(is_staff=True, groups=("PR felelős",))


@pytest.fixture
def mock_provider():
    """Factory: stand an identity provider's OAuth2 endpoints up on ``responses``.

    Requesting it intercepts outbound HTTP for the whole test, so another fixture
    can register providers too. social_core keeps its test models in module level
    caches, so those are emptied on both sides.
    """
    reset_social_core_caches()

    def _mock_provider(provider):
        mocked = MockedProvider(provider)
        mocked.mock_endpoints()
        return mocked

    with responses.mock:
        yield _mock_provider
    reset_social_core_caches()
