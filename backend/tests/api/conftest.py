import pytest
from django.db.models import Max

from common.models import User
from video_requests.models import Comment, CrewMember, Rating, Request, Todo, Video


def _missing_id_fixture(model):
    """A primary key no row of ``model`` holds, for the 404 half of an endpoint.

    Every detail endpoint needs one, and taking it from the highest key in the
    table keeps it deterministic instead of a random draw that has to be retried.
    """

    @pytest.fixture
    def missing_id():
        return (model.objects.aggregate(highest=Max("pk"))["highest"] or 0) + 1000

    return missing_id


not_existing_comment_id = _missing_id_fixture(Comment)
not_existing_crew_member_id = _missing_id_fixture(CrewMember)
not_existing_rating_id = _missing_id_fixture(Rating)
not_existing_request_id = _missing_id_fixture(Request)
not_existing_todo_id = _missing_id_fixture(Todo)
not_existing_user_id = _missing_id_fixture(User)
not_existing_video_id = _missing_id_fixture(Video)
