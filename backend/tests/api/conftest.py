import pytest
from django.db.models import Max
from rest_framework.test import APIClient

from common.models import User
from tests.factories import make_user
from video_requests.models import Comment, CrewMember, Rating, Request, Todo, Video


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    return make_user(username="admin", first_name="Admin", is_admin=True)


@pytest.fixture
def staff_user():
    return make_user(username="staff", first_name="Staff", is_staff=True)


@pytest.fixture
def basic_user():
    return make_user(username="basic", first_name="Basic")


@pytest.fixture
def service_account():
    return make_user(
        username="service-account",
        first_name="Service",
        last_name="Account",
        is_service_account=True,
    )


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
