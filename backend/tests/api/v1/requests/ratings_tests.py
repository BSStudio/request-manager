import pytest
from model_bakery import baker
from rest_framework.exceptions import ErrorDetail
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    is_success,
)

from tests.api.asserts import assert_exact_fields
from tests.api.helpers import do_login, get_response
from tests.api.matrix import any_user
from video_requests.models import Rating, Video

pytestmark = pytest.mark.django_db


def assert_response_keys(rating):
    assert_exact_fields(rating, ["created", "rating", "review"])


@pytest.fixture
def rating_data():
    return {
        "rating": 5,
        "review": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
        "Donec eu elit facilisis, cursus mi et, dignissim mauris. "
        "Morbi eu nunc pretium, luctus dui sit amet, rhoncus est. "
        "Quisque cursus lorem nec dolor commodo pretium. "
        "In ullamcorper ut nibh quis sollicitudin.",
    }


@any_user(HTTP_201_CREATED)
def test_create_rating(api_client, expected, rating_data, request, user):
    user = do_login(api_client, request, user)

    video_request = baker.make("video_requests.Request", requester=user)
    video = baker.make(
        "video_requests.Video", request=video_request, status=Video.Statuses.DONE
    )

    url = reverse(
        "api:v1:requests:request:video:rating-detail",
        kwargs={"request_pk": video_request.id, "video_pk": video.id},
    )
    response = api_client.post(url, rating_data)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_response_keys(response.data)
        rating = Rating.objects.filter(
            video__request__pk=video_request.id, video__pk=video.id
        ).first()
        assert rating.author == user
        assert rating.rating == rating_data["rating"]
        assert rating.review == rating_data["review"]


@any_user(HTTP_400_BAD_REQUEST)
def test_create_rating_validation(api_client, expected, rating_data, request, user):
    user = do_login(api_client, request, user)

    video_request = baker.make("video_requests.Request", requester=user)
    video = baker.make(
        "video_requests.Video", request=video_request, status=Video.Statuses.DONE
    )
    baker.make("video_requests.Rating", author=user, video=video)

    url = reverse(
        "api:v1:requests:request:video:rating-detail",
        kwargs={"request_pk": video_request.id, "video_pk": video.id},
    )
    response = api_client.post(url, rating_data)

    assert response.status_code == expected

    if response.status_code == HTTP_400_BAD_REQUEST:
        assert response.data["non_field_errors"][0] == ErrorDetail(
            string="You have already posted a rating.",
            code="invalid",
        )

    video = baker.make(
        "video_requests.Video", request=video_request, status=Video.Statuses.PENDING
    )

    url = reverse(
        "api:v1:requests:request:video:rating-detail",
        kwargs={"request_pk": video_request.id, "video_pk": video.id},
    )
    response = api_client.post(url, rating_data)

    assert response.status_code == expected

    if response.status_code == HTTP_400_BAD_REQUEST:
        assert response.data["non_field_errors"][0] == ErrorDetail(
            string="The video has not been published yet.",
            code="invalid",
        )


@any_user(
    {
        "DELETE": HTTP_204_NO_CONTENT,
        "GET": HTTP_200_OK,
        "PATCH": HTTP_200_OK,
        "PUT": HTTP_200_OK,
    }
)
@pytest.mark.parametrize("method", ["DELETE", "GET", "PATCH", "PUT"])
def test_retrieve_update_destroy_rating(
    api_client, expected, method, rating_data, request, user
):
    user = do_login(api_client, request, user)

    video_request = baker.make("video_requests.Request", requester=user)
    video = baker.make(
        "video_requests.Video", request=video_request, status=Video.Statuses.DONE
    )
    baker.make("video_requests.Rating", author=user, video=video)

    url = reverse(
        "api:v1:requests:request:video:rating-detail",
        kwargs={"request_pk": video_request.id, "video_pk": video.id},
    )
    response = get_response(api_client, method, url, rating_data)

    assert response.status_code == expected[method]

    if response.status_code == HTTP_200_OK:
        assert_response_keys(response.data)

        if method in ["PATCH", "PUT"]:
            assert response.data["rating"] == rating_data["rating"]
            assert response.data["review"] == rating_data["review"]


@any_user(HTTP_404_NOT_FOUND)
@pytest.mark.parametrize("method", ["DELETE", "GET", "PATCH", "POST", "PUT"])
def test_create_retrieve_update_destroy_rating_errors(
    api_client,
    expected,
    method,
    not_existing_request_id,
    not_existing_video_id,
    rating_data,
    request,
    user,
):
    user = do_login(api_client, request, user)

    video_request = baker.make("video_requests.Request", requester=user)
    video_request_not_own = baker.make("video_requests.Request")
    video = baker.make(
        "video_requests.Video", request=video_request, status=Video.Statuses.DONE
    )
    video_not_own = baker.make(
        "video_requests.Video",
        request=video_request_not_own,
        status=Video.Statuses.DONE,
    )

    url = reverse(
        "api:v1:requests:request:video:rating-detail",
        kwargs={"request_pk": video_request.id, "video_pk": not_existing_video_id},
    )
    response = get_response(api_client, method, url, rating_data)

    assert response.status_code == expected

    url = reverse(
        "api:v1:requests:request:video:rating-detail",
        kwargs={"request_pk": video_request.id, "video_pk": video_not_own.id},
    )
    response = get_response(api_client, method, url, rating_data)

    assert response.status_code == expected

    url = reverse(
        "api:v1:requests:request:video:rating-detail",
        kwargs={"request_pk": not_existing_request_id, "video_pk": video.id},
    )
    response = get_response(api_client, method, url, rating_data)

    assert response.status_code == expected

    url = reverse(
        "api:v1:requests:request:video:rating-detail",
        kwargs={
            "request_pk": not_existing_request_id,
            "video_pk": not_existing_video_id,
        },
    )
    response = get_response(api_client, method, url, rating_data)

    assert response.status_code == expected

    url = reverse(
        "api:v1:requests:request:video:rating-detail",
        kwargs={
            "request_pk": video_request_not_own.id,
            "video_pk": not_existing_video_id,
        },
    )
    response = get_response(api_client, method, url, rating_data)

    assert response.status_code == expected

    url = reverse(
        "api:v1:requests:request:video:rating-detail",
        kwargs={"request_pk": video_request_not_own.id, "video_pk": video_not_own.id},
    )
    response = get_response(api_client, method, url, rating_data)

    assert response.status_code == expected

    url = reverse(
        "api:v1:requests:request:video:rating-detail",
        kwargs={"request_pk": video_request_not_own.id, "video_pk": video.id},
    )
    response = get_response(api_client, method, url, rating_data)

    assert response.status_code == expected

    if not method == "POST":
        url = reverse(
            "api:v1:requests:request:video:rating-detail",
            kwargs={"request_pk": video_request.id, "video_pk": video.id},
        )
        response = get_response(api_client, method, url, rating_data)

        assert response.status_code == expected
