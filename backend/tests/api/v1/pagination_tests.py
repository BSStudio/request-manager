from urllib.parse import parse_qs, urlparse

import pytest
from model_bakery import baker
from rest_framework.reverse import reverse
from rest_framework.status import is_success

from tests.api.asserts import assert_exact_fields
from tests.api.helpers import login

pytestmark = pytest.mark.django_db


def assert_pagination_fields(expected, response, video_requests_len):
    assert_exact_fields(response.data, ["count", "links", "results", "total_pages"])
    assert_exact_fields(response.data["links"], ["next", "previous"])

    assert response.data["count"] == video_requests_len
    assert len(response.data["results"]) == expected[0]
    assert response.data["total_pages"] == expected[1]


@pytest.mark.parametrize(
    "parameters,expected",
    [
        ({}, (100, 2)),
        ({"page_size": 200}, (200, 1)),
        ({"page_size": 25}, (25, 8)),
        ({"pagination": False}, None),
        ({"pagination": True}, (100, 2)),
        ({"page_size": 25, "pagination": False}, None),
        ({"page_size": 25, "pagination": True}, (25, 8)),
    ],
)
def test_pagination(admin_user, api_client, expected, parameters):
    video_requests = baker.make("video_requests.Request", _quantity=200)

    login(api_client, admin_user)

    url = reverse("api:v1:admin:requests:request-list")
    response = api_client.get(url, parameters)

    assert is_success(response.status_code)

    if not expected:
        assert len(response.data) == len(video_requests)
        return

    assert_pagination_fields(expected, response, len(video_requests))
    assert response.data["links"]["previous"] is None

    if response.data["total_pages"] > 1:
        assert response.data["links"]["next"] is not None

        url = response.data["links"]["next"]
        response = api_client.get(url)

        assert_pagination_fields(expected, response, len(video_requests))
        assert response.data["links"]["previous"] is not None

        page = int(parse_qs(urlparse(url).query)["page"][0])

        if page < response.data["total_pages"]:
            assert response.data["links"]["next"] is not None

            url = reverse("api:v1:admin:requests:request-list")
            response = api_client.get(
                url, parameters | {"page": response.data["total_pages"]}
            )

            assert_pagination_fields(expected, response, len(video_requests))
            assert response.data["links"]["previous"] is not None
            assert response.data["links"]["next"] is None

            return

    assert response.data["links"]["next"] is None
