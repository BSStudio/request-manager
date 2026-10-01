import pytest

MISSING_PK = 2**31 - 1


@pytest.fixture
def missing_id():
    """A primary key no row holds, for the 404 half of a detail endpoint.

    Not ``Max(pk) + n``: Postgres sequences survive a test's rollback, so such a key
    can be handed to a row the test creates afterwards.
    """
    return MISSING_PK


not_existing_comment_id = missing_id
not_existing_crew_member_id = missing_id
not_existing_rating_id = missing_id
not_existing_request_id = missing_id
not_existing_todo_id = missing_id
not_existing_user_id = missing_id
not_existing_video_id = missing_id
