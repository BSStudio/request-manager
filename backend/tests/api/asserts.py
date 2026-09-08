"""Response-shape assertions shared by the API tests.

The serializers reuse a handful of shapes across every endpoint — a short user
reference, a full user, the pagination envelope — so the field lists live here
once. A serializer growing a field then fails in one place instead of twelve.
"""

#: How a user appears when they are somebody else's author/editor/member/creator.
USER_REFERENCE_FIELDS = ["avatar_url", "full_name", "id"]

#: How a user appears when they are the subject of the payload.
USER_DETAIL_FIELDS = [
    "avatar_url",
    "email",
    "full_name",
    "id",
    "is_staff",
    "phone_number",
]

PAGINATION_FIELDS = ["count", "links", "results", "total_pages"]
PAGINATION_LINK_FIELDS = ["next", "previous"]


def assert_exact_fields(data, expected_fields):
    """The payload carries every expected key and no others."""
    assert set(data) == set(expected_fields)


def assert_user_reference(user):
    assert user is not None
    assert_exact_fields(user, USER_REFERENCE_FIELDS)


def assert_user_details(user):
    assert user is not None
    assert_exact_fields(user, USER_DETAIL_FIELDS)


def assert_pagination_envelope(response, expected_count):
    assert_exact_fields(response.data, PAGINATION_FIELDS)
    assert_exact_fields(response.data["links"], PAGINATION_LINK_FIELDS)
    assert response.data["count"] == expected_count


def list_rows(response, pagination, expected_count):
    """Return the rows of a list response, checking the envelope around them.

    The list endpoints all take a ``pagination`` query parameter, so every one of
    their tests has to unwrap the same two shapes before it can look at a row.
    """
    if pagination:
        assert_pagination_envelope(response, expected_count)

    rows = response.data["results"] if pagination else response.data
    assert len(rows) == expected_count
    return rows
