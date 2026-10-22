from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils.timezone import now
from model_bakery import baker

from common.models import User
from common.utilities import create_calendar_event
from video_requests.models import Project
from video_requests.services import create_request, delete_project, set_project

pytestmark = pytest.mark.django_db


def test_set_project_records_the_change_in_history():
    project = baker.make("video_requests.Project")
    video_request = baker.make("video_requests.Request")

    set_project(video_request, project)

    assert video_request.history.count() == 2
    assert video_request.history.latest().project_id == project.id


def test_delete_project_keeps_its_requests_unassigned():
    project, other = baker.make("video_requests.Project", _quantity=2)
    in_project = baker.make("video_requests.Request", project=project)
    in_other = baker.make("video_requests.Request", project=other)

    project_id = project.id

    delete_project(project)

    assert not Project.objects.filter(pk=project_id).exists()
    in_project.refresh_from_db()
    assert in_project.project is None
    assert in_project.history.latest().project_id is None
    in_other.refresh_from_db()
    assert in_other.project == other


def test_calendar_event_waits_for_the_commit(django_capture_on_commit_callbacks):
    user = baker.make(User)
    with patch.object(create_calendar_event, "delay") as delay:
        with django_capture_on_commit_callbacks(execute=True):
            video_request = create_request(
                title="Megnyitó",
                start_datetime=now(),
                end_datetime=now() + timedelta(hours=1),
                type="Élő közvetítés",
                place="Aula",
                requester=user,
                requested_by=user,
                send_confirmation=False,
            )
            delay.assert_not_called()

    delay.assert_called_once_with(video_request.id)
