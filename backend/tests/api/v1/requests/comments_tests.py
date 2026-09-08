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
    assert_fields_exist(comment, ["author", "created", "id", "text"])

    author = comment.get("author")
    assert author is not None
    assert_fields_exist(author, ["avatar_url", "full_name", "id"])


@pytest.fixture
def comment_data():
    return {
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
        ("basic_user", HTTP_200_OK),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_list_comments_own_request(api_client, expected, request, user):
    user = do_login(api_client, request, user)

    video_request = baker.make("video_requests.Request", requester=user)
    own_internal_comments = baker.make(
        "video_requests.Comment",
        author=user,
        internal=True,
        request=video_request,
        _quantity=3,
    )

    comments = baker.make(
        "video_requests.Comment", internal=False, request=video_request, _quantity=3
    )
    internal_comments = baker.make(
        "video_requests.Comment", internal=True, request=video_request, _quantity=2
    )

    url = reverse(
        "api:v1:requests:request:comment-list",
        kwargs={"request_pk": video_request.id},
    )
    response = api_client.get(url)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert len(response.data) == len(comments)
        for comment in response.data:
            assert_response_keys(comment)
            assert not any(
                comment["id"] == internal_comment.id
                for internal_comment in internal_comments + own_internal_comments
            )


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_201_CREATED),
        ("staff_user", HTTP_201_CREATED),
        ("basic_user", HTTP_201_CREATED),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_create_comment_own_request(api_client, comment_data, expected, request, user):
    user = do_login(api_client, request, user)

    video_request = baker.make("video_requests.Request", requester=user)

    url = reverse(
        "api:v1:requests:request:comment-list",
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


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_404_NOT_FOUND),
        ("staff_user", HTTP_404_NOT_FOUND),
        ("basic_user", HTTP_404_NOT_FOUND),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_list_create_comments_errors(
    api_client, comment_data, expected, method, not_existing_request_id, request, user
):
    video_request = baker.make("video_requests.Request")
    user = do_login(api_client, request, user)

    # Comments by the user
    baker.make(
        "video_requests.Comment",
        author=user,
        internal=False,
        request=video_request,
        _quantity=3,
    )
    # Internal comments by the user
    baker.make(
        "video_requests.Comment",
        author=user,
        internal=True,
        request=video_request,
        _quantity=3,
    )

    # Basic comments
    baker.make(
        "video_requests.Comment", internal=False, request=video_request, _quantity=3
    )
    # Internal comments
    baker.make(
        "video_requests.Comment", internal=True, request=video_request, _quantity=2
    )

    # A request where the requester is not the user logged in
    url = reverse(
        "api:v1:requests:request:comment-list",
        kwargs={"request_pk": video_request.id},
    )
    response = get_response(api_client, method, url, comment_data)

    assert response.status_code == expected

    # Not existing request
    url = reverse(
        "api:v1:requests:request:comment-list",
        kwargs={"request_pk": not_existing_request_id},
    )
    response = get_response(api_client, method, url, comment_data)

    assert response.status_code == expected


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_200_OK),
        ("staff_user", HTTP_200_OK),
        ("basic_user", HTTP_200_OK),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_retrieve_comment(api_client, expected, request, user):
    user = do_login(api_client, request, user)

    video_request = baker.make("video_requests.Request", requester=user)
    comments = baker.make(
        "video_requests.Comment", internal=False, request=video_request, _quantity=5
    )

    url = reverse(
        "api:v1:requests:request:comment-detail",
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
        ("basic_user", HTTP_200_OK),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_update_own_comment(api_client, comment_data, expected, method, request, user):
    user = do_login(api_client, request, user)

    video_request = baker.make("video_requests.Request", requester=user)
    comment = baker.make(
        "video_requests.Comment", author=user, internal=False, request=video_request
    )

    assert comment.text != comment_data["text"]

    url = reverse(
        "api:v1:requests:request:comment-detail",
        kwargs={"request_pk": video_request.id, "pk": comment.id},
    )

    response = get_response(api_client, method, url, comment_data)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_response_keys(response.data)
        assert response.data["text"] == comment_data["text"]
        assert response.data["author"]["id"] == user.id


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_204_NO_CONTENT),
        ("staff_user", HTTP_204_NO_CONTENT),
        ("basic_user", HTTP_204_NO_CONTENT),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_destroy_own_comment(api_client, expected, request, user):
    user = do_login(api_client, request, user)

    video_request = baker.make("video_requests.Request", requester=user)
    comment = baker.make(
        "video_requests.Comment", author=user, internal=False, request=video_request
    )

    url = reverse(
        "api:v1:requests:request:comment-detail",
        kwargs={"request_pk": video_request.id, "pk": comment.id},
    )
    response = api_client.delete(url)

    assert response.status_code == expected


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_404_NOT_FOUND),
        ("staff_user", HTTP_404_NOT_FOUND),
        ("basic_user", HTTP_404_NOT_FOUND),
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
    user = do_login(api_client, request, user)

    video_request = baker.make("video_requests.Request")
    video_request_own = baker.make("video_requests.Request", requester=user)

    internal_comment = baker.make(
        "video_requests.Comment", internal=True, request=video_request
    )
    internal_comment_own = baker.make(
        "video_requests.Comment", author=user, internal=True, request=video_request
    )
    not_internal_comment = baker.make(
        "video_requests.Comment", internal=False, request=video_request
    )
    not_internal_comment_own = baker.make(
        "video_requests.Comment", author=user, internal=False, request=video_request
    )

    internal_comment_request_own = baker.make(
        "video_requests.Comment", internal=True, request=video_request_own
    )
    internal_comment_own_request_own = baker.make(
        "video_requests.Comment", author=user, internal=True, request=video_request_own
    )
    not_internal_comment_request_own = baker.make(
        "video_requests.Comment", internal=False, request=video_request_own
    )
    not_internal_comment_own_request_own = baker.make(
        "video_requests.Comment", author=user, internal=False, request=video_request_own
    )

    for request_id in [video_request.id, video_request_own.id, not_existing_request_id]:
        for comment_id in [
            internal_comment.id,
            internal_comment_own.id,
            not_internal_comment.id,
            not_internal_comment_own.id,
            internal_comment_request_own.id,
            internal_comment_own_request_own.id,
            not_existing_comment_id,
        ]:
            url = reverse(
                "api:v1:requests:request:comment-detail",
                kwargs={
                    "request_pk": request_id,
                    "pk": comment_id,
                },
            )
            response = get_response(api_client, method, url, comment_data)

            assert response.status_code == expected

        if not method == "GET" or request_id == video_request.id:
            url = reverse(
                "api:v1:requests:request:comment-detail",
                kwargs={
                    "request_pk": request_id,
                    "pk": not_internal_comment_request_own,
                },
            )
            response = get_response(api_client, method, url, comment_data)

            assert response.status_code == expected

        if request_id == video_request.id:
            url = reverse(
                "api:v1:requests:request:comment-detail",
                kwargs={
                    "request_pk": request_id,
                    "pk": not_internal_comment_own_request_own,
                },
            )
            response = get_response(api_client, method, url, comment_data)

            assert response.status_code == expected
