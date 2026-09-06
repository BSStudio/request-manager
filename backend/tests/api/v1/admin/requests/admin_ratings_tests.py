from random import randint

import pytest
from model_bakery import baker
from rest_framework.exceptions import ErrorDetail
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    is_success,
)

from tests.api.helpers import assert_fields_exist, do_login, get_response
from video_requests.models import Rating, Video

pytestmark = pytest.mark.django_db


def assert_response_keys(rating):
    assert_fields_exist(rating, ["author", "created", "id", "rating", "review"])

    author = rating.get("author")
    assert author is not None
    assert_fields_exist(author, ["avatar_url", "full_name", "id"])


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


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_200_OK),
        ("staff_user", HTTP_200_OK),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_list_ratings(api_client, expected, request, user):
    video_request = baker.make("video_requests.Request")
    video = baker.make(
        "video_requests.Video", request=video_request, status=Video.Statuses.DONE
    )
    ratings = baker.make(
        "video_requests.Rating", rating=randint(1, 5), video=video, _quantity=5
    )

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request:video:rating-list",
        kwargs={"request_pk": video_request.id, "video_pk": video.id},
    )
    response = api_client.get(url)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert len(response.data) == len(ratings)
        for rating in response.data:
            assert_response_keys(rating)


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_201_CREATED),
        ("staff_user", HTTP_201_CREATED),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_create_rating(api_client, expected, rating_data, request, user):
    video_request = baker.make("video_requests.Request")
    video = baker.make(
        "video_requests.Video", request=video_request, status=Video.Statuses.DONE
    )

    user = do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request:video:rating-list",
        kwargs={"request_pk": video_request.id, "video_pk": video.id},
    )
    response = api_client.post(url, rating_data)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_response_keys(response.data)

        assert response.data["author"]["avatar_url"] == user.avatar_url
        assert (
            response.data["author"]["full_name"] == user.get_full_name_eastern_order()
        )
        assert response.data["author"]["id"] == user.id

        response = api_client.get(url)

        assert response.status_code == HTTP_200_OK
        assert len(response.data) == 1


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_404_NOT_FOUND),
        ("staff_user", HTTP_404_NOT_FOUND),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_list_create_ratings_error(
    api_client,
    expected,
    method,
    not_existing_request_id,
    not_existing_video_id,
    rating_data,
    request,
    user,
):
    video_request = baker.make("video_requests.Request")
    video = baker.make(
        "video_requests.Video", request=video_request, status=Video.Statuses.DONE
    )
    baker.make("video_requests.Rating", rating=randint(1, 5), video=video, _quantity=5)

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request:video:rating-list",
        kwargs={"request_pk": not_existing_request_id, "video_pk": video.id},
    )
    response = get_response(api_client, method, url, rating_data)

    assert response.status_code == expected

    url = reverse(
        "api:v1:admin:requests:request:video:rating-list",
        kwargs={"request_pk": video_request.id, "video_pk": not_existing_video_id},
    )
    response = get_response(api_client, method, url, rating_data)

    assert response.status_code == expected

    url = reverse(
        "api:v1:admin:requests:request:video:rating-list",
        kwargs={
            "request_pk": not_existing_request_id,
            "video_pk": not_existing_video_id,
        },
    )
    response = get_response(api_client, method, url, rating_data)

    assert response.status_code == expected


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_400_BAD_REQUEST),
        ("staff_user", HTTP_400_BAD_REQUEST),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_create_rating_error_video_not_edited(
    api_client, expected, rating_data, request, user
):
    video_request = baker.make("video_requests.Request")
    video = baker.make(
        "video_requests.Video", request=video_request, status=Video.Statuses.IN_PROGRESS
    )

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request:video:rating-list",
        kwargs={"request_pk": video_request.id, "video_pk": video.id},
    )
    response = api_client.post(url, rating_data)

    assert response.status_code == expected

    if response.status_code == HTTP_400_BAD_REQUEST:
        assert response.data["non_field_errors"][0] == ErrorDetail(
            string="The video has not been edited yet.", code="invalid"
        )


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_400_BAD_REQUEST),
        ("staff_user", HTTP_400_BAD_REQUEST),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_create_rating_error_one_rating_per_video(
    api_client, expected, rating_data, request, user
):
    video_request = baker.make("video_requests.Request")
    video = baker.make(
        "video_requests.Video", request=video_request, status=Video.Statuses.DONE
    )

    user = do_login(api_client, request, user)

    baker.make("video_requests.Rating", author=user, rating=randint(1, 5), video=video)

    url = reverse(
        "api:v1:admin:requests:request:video:rating-list",
        kwargs={"request_pk": video_request.id, "video_pk": video.id},
    )
    response = api_client.post(url, rating_data)

    assert response.status_code == expected

    if response.status_code == HTTP_400_BAD_REQUEST:
        assert response.data["non_field_errors"][0] == ErrorDetail(
            string="You have already posted a rating.", code="invalid"
        )


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_200_OK),
        ("staff_user", HTTP_200_OK),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_retrieve_rating(api_client, expected, request, user):
    video_request = baker.make("video_requests.Request")
    video = baker.make(
        "video_requests.Video", request=video_request, status=Video.Statuses.DONE
    )
    ratings = baker.make(
        "video_requests.Rating", rating=randint(1, 5), video=video, _quantity=5
    )

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request:video:rating-detail",
        kwargs={
            "request_pk": video_request.id,
            "video_pk": video.id,
            "pk": ratings[0].id,
        },
    )
    response = api_client.get(url)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_response_keys(response.data)


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_200_OK),
        ("staff_user", HTTP_200_OK),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_retrieve_own_rating(api_client, expected, request, user):
    user = do_login(api_client, request, user)

    video_request = baker.make("video_requests.Request")
    video = baker.make(
        "video_requests.Video", request=video_request, status=Video.Statuses.DONE
    )
    rating = baker.make(
        "video_requests.Rating", author=user, rating=randint(1, 5), video=video
    )

    url = reverse(
        "api:v1:admin:requests:request:video:rating-own",
        kwargs={"request_pk": video_request.id, "video_pk": video.id},
    )
    response = api_client.get(url)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_response_keys(response.data)
        assert response.data["rating"] == rating.rating
        assert response.data["review"] == rating.review

        assert response.data["author"]["id"] == user.id


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_200_OK),
        ("staff_user", HTTP_200_OK),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_update_own_rating(api_client, expected, method, rating_data, request, user):
    video_request = baker.make("video_requests.Request")
    video = baker.make(
        "video_requests.Video", request=video_request, status=Video.Statuses.DONE
    )

    user = do_login(api_client, request, user)

    rating = baker.make(
        "video_requests.Rating", author=user, rating=randint(1, 4), video=video
    )

    assert rating.rating != rating_data["rating"]
    assert rating.review != rating_data["review"]

    url = reverse(
        "api:v1:admin:requests:request:video:rating-detail",
        kwargs={"request_pk": video_request.id, "video_pk": video.id, "pk": rating.id},
    )

    response = get_response(api_client, method, url, rating_data)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_response_keys(response.data)

        assert response.data["rating"] == rating_data["rating"]
        assert response.data["review"] == rating_data["review"]

        assert response.data["author"]["id"] == user.id


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_200_OK),
        ("staff_user", HTTP_403_FORBIDDEN),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_update_others_rating(api_client, expected, method, rating_data, request, user):
    video_request = baker.make("video_requests.Request")
    video = baker.make(
        "video_requests.Video", request=video_request, status=Video.Statuses.DONE
    )
    rating = baker.make("video_requests.Rating", rating=randint(1, 4), video=video)

    user = do_login(api_client, request, user)

    assert rating.rating != rating_data["rating"]
    assert rating.review != rating_data["review"]
    assert rating.author != user

    url = reverse(
        "api:v1:admin:requests:request:video:rating-detail",
        kwargs={"request_pk": video_request.id, "video_pk": video.id, "pk": rating.id},
    )

    response = get_response(api_client, method, url, rating_data)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_response_keys(response.data)

        assert response.data["rating"] == rating_data["rating"]
        assert response.data["review"] == rating_data["review"]

        assert response.data["author"]["id"] != user.id


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_204_NO_CONTENT),
        ("staff_user", HTTP_204_NO_CONTENT),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_destroy_own_rating(api_client, expected, request, user):
    video_request = baker.make("video_requests.Request")
    video = baker.make(
        "video_requests.Video", request=video_request, status=Video.Statuses.DONE
    )

    user = do_login(api_client, request, user)

    rating = baker.make(
        "video_requests.Rating", author=user, rating=randint(1, 5), video=video
    )

    url = reverse(
        "api:v1:admin:requests:request:video:rating-detail",
        kwargs={"request_pk": video_request.id, "video_pk": video.id, "pk": rating.id},
    )
    response = api_client.delete(url)

    assert response.status_code == expected


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_204_NO_CONTENT),
        ("staff_user", HTTP_403_FORBIDDEN),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_destroy_others_rating(api_client, expected, request, user):
    video_request = baker.make("video_requests.Request")
    video = baker.make(
        "video_requests.Video", request=video_request, status=Video.Statuses.DONE
    )
    rating = baker.make("video_requests.Rating", rating=randint(1, 5), video=video)

    user = do_login(api_client, request, user)

    assert rating.author != user

    url = reverse(
        "api:v1:admin:requests:request:video:rating-detail",
        kwargs={"request_pk": video_request.id, "video_pk": video.id, "pk": rating.id},
    )
    response = api_client.delete(url)

    assert response.status_code == expected


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_404_NOT_FOUND),
        ("staff_user", HTTP_404_NOT_FOUND),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("method", ["GET", "DELETE", "PATCH", "PUT"])
def test_retrieve_update_destroy_rating_error(
    api_client,
    expected,
    method,
    not_existing_request_id,
    not_existing_video_id,
    rating_data,
    request,
    user,
):
    def get_not_existing_rating_id():
        while True:
            non_existing_id = randint(1000, 100000)
            if not Rating.objects.filter(pk=non_existing_id).exists():
                return non_existing_id

    video_request = baker.make("video_requests.Request")
    videos = baker.make(
        "video_requests.Video",
        request=video_request,
        status=Video.Statuses.DONE,
        _quantity=2,
    )
    rating = baker.make("video_requests.Rating", rating=randint(1, 5), video=videos[0])

    do_login(api_client, request, user)

    # Existing request, existing video, not existing rating
    url = reverse(
        "api:v1:admin:requests:request:video:rating-detail",
        kwargs={
            "request_pk": video_request.id,
            "video_pk": videos[0].id,
            "pk": get_not_existing_rating_id(),
        },
    )
    response = get_response(api_client, method, url, rating_data)

    assert response.status_code == expected

    # Existing request, not existing video, existing rating
    url = reverse(
        "api:v1:admin:requests:request:video:rating-detail",
        kwargs={
            "request_pk": video_request.id,
            "video_pk": not_existing_video_id,
            "pk": rating.id,
        },
    )
    response = get_response(api_client, method, url, rating_data)

    assert response.status_code == expected

    # Existing request, not existing video, not existing rating
    url = reverse(
        "api:v1:admin:requests:request:video:rating-detail",
        kwargs={
            "request_pk": video_request.id,
            "video_pk": not_existing_video_id,
            "pk": get_not_existing_rating_id(),
        },
    )
    response = get_response(api_client, method, url, rating_data)

    assert response.status_code == expected

    # Not existing request, existing video, existing rating
    url = reverse(
        "api:v1:admin:requests:request:video:rating-detail",
        kwargs={
            "request_pk": not_existing_request_id,
            "video_pk": videos[0].id,
            "pk": rating.id,
        },
    )
    response = get_response(api_client, method, url, rating_data)

    assert response.status_code == expected

    # Not existing request, existing video, not existing rating
    url = reverse(
        "api:v1:admin:requests:request:video:rating-detail",
        kwargs={
            "request_pk": not_existing_request_id,
            "video_pk": videos[0].id,
            "pk": get_not_existing_rating_id(),
        },
    )
    response = get_response(api_client, method, url, rating_data)

    assert response.status_code == expected

    # Not existing request, not existing video, existing rating
    url = reverse(
        "api:v1:admin:requests:request:video:rating-detail",
        kwargs={
            "request_pk": not_existing_request_id,
            "video_pk": not_existing_video_id,
            "pk": rating.id,
        },
    )
    response = get_response(api_client, method, url, rating_data)

    assert response.status_code == expected

    # Not existing request, not existing video, not existing rating
    url = reverse(
        "api:v1:admin:requests:request:video:rating-detail",
        kwargs={
            "request_pk": not_existing_request_id,
            "video_pk": not_existing_video_id,
            "pk": get_not_existing_rating_id(),
        },
    )
    response = get_response(api_client, method, url, rating_data)

    assert response.status_code == expected


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_404_NOT_FOUND),
        ("staff_user", HTTP_404_NOT_FOUND),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_retrieve_own_rating_error(api_client, expected, request, user):
    # Create a rating but not by our own user
    video_request = baker.make("video_requests.Request")
    video = baker.make(
        "video_requests.Video", request=video_request, status=Video.Statuses.DONE
    )
    baker.make("video_requests.Rating", rating=randint(1, 5), video=video)

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request:video:rating-own",
        kwargs={"request_pk": video_request.id, "video_pk": video.id},
    )
    response = api_client.get(url)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_response_keys(response.data)


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_400_BAD_REQUEST),
        ("staff_user", HTTP_400_BAD_REQUEST),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("method", ["PATCH", "POST", "PUT"])
@pytest.mark.parametrize("rating_value", [-10, 10])
def test_create_update_rating_invalid_rating(
    api_client,
    expected,
    method,
    rating_value,
    request,
    user,
):
    data = {"rating": rating_value, "review": "Failure"}

    video_request = baker.make("video_requests.Request")
    video = baker.make(
        "video_requests.Video", request=video_request, status=Video.Statuses.DONE
    )

    user = do_login(api_client, request, user)

    rating = baker.make(
        "video_requests.Rating", author=user, rating=randint(1, 5), video=video
    )

    if method == "POST":
        url = reverse(
            "api:v1:admin:requests:request:video:rating-list",
            kwargs={"request_pk": video_request.id, "video_pk": video.id},
        )
    else:
        url = reverse(
            "api:v1:admin:requests:request:video:rating-detail",
            kwargs={
                "request_pk": video_request.id,
                "video_pk": video.id,
                "pk": rating.id,
            },
        )

    response = get_response(api_client, method, url, data)

    assert response.status_code == expected

    if response.status_code == HTTP_400_BAD_REQUEST:
        if rating_value < 1:
            assert response.data["rating"][0] == ErrorDetail(
                string="Ensure this value is greater than or equal to 1.",
                code="min_value",
            )
        elif rating_value > 5:
            assert response.data["rating"][0] == ErrorDetail(
                string="Ensure this value is less than or equal to 5.", code="max_value"
            )
