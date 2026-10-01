import pytest

#: The largest value a Postgres ``integer`` column holds.
MISSING_PK = 2**31 - 1


@pytest.fixture
def missing_id():
    """A primary key no row holds, for the 404 half of a detail endpoint.

    A constant rather than ``Max(pk) + n``: Postgres sequences are not rolled back
    with a test's transaction, so a key derived from the rows present can be handed
    to a row the test creates afterwards.
    """
    return MISSING_PK


not_existing_comment_id = missing_id
not_existing_crew_member_id = missing_id
not_existing_rating_id = missing_id
not_existing_request_id = missing_id
not_existing_todo_id = missing_id
not_existing_user_id = missing_id
not_existing_video_id = missing_id
