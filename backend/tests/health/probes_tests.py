import pytest
from django.urls import reverse
from rest_framework.status import HTTP_200_OK


def test_livez_answers_without_the_database(client):
    # No django_db marker on purpose: /livez must answer without touching the DB.
    response = client.get(reverse("livez"))

    assert response.status_code == HTTP_200_OK
    assert response.content == b"ok"


@pytest.mark.django_db
def test_readyz_is_ok_when_the_database_and_redis_are_up(client):
    response = client.get(reverse("readyz"))

    assert response.status_code == HTTP_200_OK
