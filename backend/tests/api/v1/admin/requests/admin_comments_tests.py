import pytest
from model_bakery import baker
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    is_success,
)

from tests.api.helpers import assert_fields_exist, do_login, get_response

pytestmark = pytest.mark.django_db


def assert_response_keys(comment):
    assert_fields_exist(comment, ["author", "created", "id", "internal", "text"])

    author = comment.get("author")
    assert author is not None
    assert_fields_exist(author, ["avatar_url", "full_name", "id"])


@pytest.fixture
def comment_data():
    return {
        "internal": False,
        "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
        "Fusce faucibus est vitae erat pulvinar sodales. "
        "Pellentesque eleifend massa nisl, ac aliquet tortor luctus a. "
        "Sed viverra justo quis orci feugiat, non porta urna egestas.",
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
def test_list_comments(api_client, expected, request, user):
    video_request = baker.make("video_requests.Request")
    comments = baker.make("video_requests.Comment", request=video_request, _quantity=5)

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request:comment-list",
        kwargs={"request_pk": video_request.id},
    )
    response = api_client.get(url)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert len(response.data) == len(comments)
        for comment in response.data:
            assert_response_keys(comment)


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
def test_create_comment(api_client, comment_data, expected, request, user):
    video_request = baker.make("video_requests.Request")

    user = do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request:comment-list",
        kwargs={"request_pk": video_request.id},
    )
    response = api_client.post(url, comment_data)

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
def test_list_create_comments_error(
    api_client, comment_data, expected, method, not_existing_request_id, request, user
):
    video_request = baker.make("video_requests.Request")
    baker.make("video_requests.Comment", request=video_request, _quantity=5)

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request:comment-list",
        kwargs={"request_pk": not_existing_request_id},
    )

    response = get_response(api_client, method, url, comment_data)

    assert response.status_code == expected


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
def test_retrieve_comment(api_client, expected, request, user):
    video_request = baker.make("video_requests.Request")
    comments = baker.make("video_requests.Comment", request=video_request, _quantity=5)

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request:comment-detail",
        kwargs={"request_pk": video_request.id, "pk": comments[0].id},
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
@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_update_own_comment(api_client, comment_data, expected, method, request, user):
    video_request = baker.make("video_requests.Request")

    user = do_login(api_client, request, user)

    comment = baker.make("video_requests.Comment", author=user, request=video_request)

    assert comment.text != comment_data["text"]

    url = reverse(
        "api:v1:admin:requests:request:comment-detail",
        kwargs={"request_pk": video_request.id, "pk": comment.id},
    )

    response = get_response(api_client, method, url, comment_data)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_response_keys(response.data)

        assert response.data["internal"] == comment_data["internal"]
        assert response.data["text"] == comment_data["text"]

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
def test_update_others_comment(
    api_client, comment_data, expected, method, request, user
):
    video_request = baker.make("video_requests.Request")
    comment = baker.make("video_requests.Comment", request=video_request)

    user = do_login(api_client, request, user)

    assert comment.text != comment_data["text"]
    assert comment.author != user

    url = reverse(
        "api:v1:admin:requests:request:comment-detail",
        kwargs={"request_pk": video_request.id, "pk": comment.id},
    )

    response = get_response(api_client, method, url, comment_data)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_response_keys(response.data)

        assert response.data["internal"] == comment_data["internal"]
        assert response.data["text"] == comment_data["text"]

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
def test_destroy_own_comment(api_client, expected, request, user):
    video_request = baker.make("video_requests.Request")

    user = do_login(api_client, request, user)

    comment = baker.make("video_requests.Comment", author=user, request=video_request)

    url = reverse(
        "api:v1:admin:requests:request:comment-detail",
        kwargs={"request_pk": video_request.id, "pk": comment.id},
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
def test_destroy_others_comment(api_client, expected, request, user):
    video_request = baker.make("video_requests.Request")
    comment = baker.make("video_requests.Comment", request=video_request)

    user = do_login(api_client, request, user)

    assert comment.author != user

    url = reverse(
        "api:v1:admin:requests:request:comment-detail",
        kwargs={"request_pk": video_request.id, "pk": comment.id},
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
def test_retrieve_update_destroy_comment_error(
    api_client,
    comment_data,
    expected,
    method,
    not_existing_comment_id,
    not_existing_request_id,
    request,
    user,
):
    video_requests = baker.make("video_requests.Request", _quantity=2)
    comment = baker.make("video_requests.Comment", request=video_requests[0])

    do_login(api_client, request, user)

    # Existing request with not existing comment
    url = reverse(
        "api:v1:admin:requests:request:comment-detail",
        kwargs={
            "request_pk": video_requests[0].id,
            "pk": not_existing_comment_id,
        },
    )
    response = get_response(api_client, method, url, comment_data)

    assert response.status_code == expected

    # Not existing request with existing comment
    url = reverse(
        "api:v1:admin:requests:request:comment-detail",
        kwargs={"request_pk": not_existing_request_id, "pk": comment.id},
    )
    response = get_response(api_client, method, url, comment_data)

    assert response.status_code == expected

    # Not existing request with not existing comment
    url = reverse(
        "api:v1:admin:requests:request:comment-detail",
        kwargs={
            "request_pk": not_existing_request_id,
            "pk": not_existing_comment_id,
        },
    )
    response = get_response(api_client, method, url, comment_data)

    assert response.status_code == expected
