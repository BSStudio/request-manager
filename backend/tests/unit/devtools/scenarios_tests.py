import pytest
from django.utils.timezone import localdate

from devtools.people import create_people
from devtools.scenarios import create_scenarios
from video_requests.models import Request, Todo, Video

pytestmark = pytest.mark.django_db

S = Request.Statuses


@pytest.fixture
def scenarios():
    return create_scenarios(create_people())


@pytest.mark.parametrize(
    "key,status",
    [
        ("requested", S.REQUESTED),
        ("accepted", S.ACCEPTED),
        ("denied", S.DENIED),
        ("recorded", S.RECORDED),
        ("uploaded", S.UPLOADED),
        ("edited", S.EDITED),
        ("archived", S.ARCHIVED),
        ("done", S.DONE),
        ("canceled", S.CANCELED),
        ("failed", S.FAILED),
        ("pinned", S.DONE),
        ("overdue", S.UPLOADED),
        ("on_behalf", S.REQUESTED),
    ],
)
def test_each_scenario_reaches_its_status(scenarios, key, status):
    assert Request.objects.get(pk=scenarios[key].pk).status == status


def test_scenarios_cover_every_request_status(scenarios):
    statuses = set(
        Request.objects.filter(
            pk__in=[request.pk for request in scenarios.values()]
        ).values_list("status", flat=True)
    )
    assert statuses == set(S.values)


def test_scenarios_cover_every_video_status(scenarios):
    statuses = set(
        Video.objects.filter(request__in=scenarios.values()).values_list(
            "status", flat=True
        )
    )
    assert statuses == set(Video.Statuses.values)


def test_the_pinned_status_was_set_by_an_admin(scenarios):
    assert scenarios["pinned"].additional_data["status_by_admin"]["status"] == S.DONE


def test_the_overdue_request_is_overdue(scenarios):
    overdue = Request.objects.filter(
        status__range=[S.REQUESTED, S.UPLOADED], deadline__lt=localdate()
    )
    assert scenarios["overdue"] in overdue


def test_the_thread_mixes_public_messages_and_internal_notes(scenarios):
    comments = scenarios["accepted"].comments.all()
    assert {comment.internal for comment in comments} == {True, False}
    assert scenarios["accepted"].requester in {comment.author for comment in comments}
    assert len({comment.created.date() for comment in comments}) > 1


def test_no_two_messages_in_the_thread_share_a_time(scenarios):
    # Messages with the same time show in id order, so a note could appear before
    # the reply it follows.
    created = [comment.created for comment in scenarios["accepted"].comments.all()]
    assert len(set(created)) == len(created)


def test_one_request_was_submitted_on_someone_elses_behalf(scenarios):
    request = scenarios["on_behalf"]
    assert request.requested_by != request.requester
    assert set(request.additional_data["requester"]) == {
        "first_name",
        "last_name",
        "phone_number",
    }


def test_todos_cover_every_status_with_assignees_and_videos(scenarios):
    todos = Todo.objects.filter(request__in=scenarios.values())
    assert set(todos.values_list("status", flat=True)) == set(Todo.Statuses.values)
    assert todos.filter(assignees__isnull=False).exists()
    assert todos.filter(video__isnull=False).exists()


def test_only_test_people_appear(scenarios):
    for request in scenarios.values():
        assert request.requester.email.endswith("@example.com")
        assert request.requested_by.email.endswith("@example.com")
