import pytest
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_401_UNAUTHORIZED

pytestmark = pytest.mark.django_db


def test_logout_needs_a_session(api_client):
    response = api_client.post(reverse("api:v1:login:logout"))

    assert response.status_code == HTTP_401_UNAUTHORIZED
