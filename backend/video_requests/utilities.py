import json
from datetime import timedelta

import requests
from celery import shared_task
from django.conf import settings
from django.utils.timezone import localtime
from requests import RequestException

from common.models import get_system_user
from common.utilities import get_pr_responsible
from video_requests.emails import email_user_video_published
from video_requests.mattermost import post_video_published_to_mattermost
from video_requests.models import Request, Todo, Video
from video_requests.notifications import (
    notify_user_request_accepted,
    notify_user_video_published,
)


def update_request_status(request: Request, called_from_video: bool = False) -> None:
    # Check if the status is set by admin (overwrites everything)
    if (
        "status_by_admin" in request.additional_data
        and "status" in request.additional_data["status_by_admin"]
        and request.additional_data["status_by_admin"].get("status")
    ):
        request.status = request.additional_data["status_by_admin"]["status"]

    # If status is not set by admin follow the flow and check if all required data are provided.
    else:
        # Incrementing this status variable if the required part is correct.
        status = Request.Statuses.REQUESTED

        # Check if request is accepted else consider as denied
        if "accepted" in request.additional_data:
            status = (
                Request.Statuses.ACCEPTED
                if request.additional_data["accepted"] is True
                else Request.Statuses.DENIED
            )
            if request.additional_data.get("external", {}).get(
                "sch_events_callback_url"
            ) and (
                request.status == Request.Statuses.REQUESTED
                or (
                    request.status == Request.Statuses.DENIED
                    and status == Request.Statuses.ACCEPTED
                )
                or (
                    request.status >= Request.Statuses.ACCEPTED
                    and status == Request.Statuses.DENIED
                )
            ):
                notify_sch_event_management_system.delay_on_commit(request.id)

        # If the request is accepted but canceled by requester set the status
        if (
            Request.Statuses.ACCEPTED <= status <= Request.Statuses.DONE
            and "canceled" in request.additional_data
        ):
            status = (
                Request.Statuses.CANCELED
                if request.additional_data["canceled"] is True
                else status
            )

        # If the request is accepted, but we failed to record it set the status
        if (
            Request.Statuses.ACCEPTED <= status <= Request.Statuses.DONE
            and "failed" in request.additional_data
        ):
            status = (
                Request.Statuses.FAILED
                if request.additional_data["failed"] is True
                else status
            )

        # If the status is not canceled or failed and the request is accepted check if the end date is earlier than now
        if (
            Request.Statuses.ACCEPTED <= status <= Request.Statuses.DONE
            and request.end_datetime < localtime()
        ):
            status = Request.Statuses.RECORDED

        # If path in recording is specified consider as successful recording and update video status
        if status == Request.Statuses.RECORDED and request.additional_data.get(
            "recording", {}
        ).get("path"):
            status = Request.Statuses.UPLOADED
            for video in request.videos.all():
                update_video_status(video, True, status)

        # If all videos are edited set the request status
        if (
            status == Request.Statuses.UPLOADED
            and request.videos.exists()
            and all(
                video.status >= Video.Statuses.EDITED for video in request.videos.all()
            )
        ):
            status = Request.Statuses.EDITED

        # If all videos are done and the recording is copied to Google Drive set the status
        if (
            status == Request.Statuses.EDITED
            and all(
                video.status == Video.Statuses.DONE for video in request.videos.all()
            )
            and "copied_to_gdrive" in request.additional_data["recording"]
        ):
            status = (
                Request.Statuses.ARCHIVED
                if request.additional_data["recording"]["copied_to_gdrive"] is True
                else status
            )

        # If the recording is removed set the status
        if (
            status == Request.Statuses.ARCHIVED
            and "removed" in request.additional_data["recording"]
        ):
            status = (
                Request.Statuses.DONE
                if request.additional_data["recording"]["removed"] is True
                else status
            )

        # Set the request status to the final score
        request.status = status

    # Once only: acceptance can be withdrawn and given again.
    already_sent = request.additional_data.get("accepted_notification_sent")
    if request.additional_data.get("accepted") is True and not already_sent:
        request.additional_data["accepted_notification_sent"] = True
        notify_user_request_accepted.delay_on_commit(request.id)

    request.save()
    if not called_from_video:
        for video in request.videos.all():
            update_video_status(video, True)


def update_video_status(
    video: Video, called_from_request: bool = False, request_status: int = 1
) -> None:
    # Check if the status is set by admin (overwrites everything)
    if (
        "status_by_admin" in video.additional_data
        and "status" in video.additional_data["status_by_admin"]
        and video.additional_data["status_by_admin"].get("status")
    ):
        video.status = video.additional_data["status_by_admin"]["status"]

    # If status is not set by admin follow the flow and check if all required data are provided.
    else:
        # Incrementing this status variable if the required part is correct.
        status = Video.Statuses.PENDING

        # If the event was recorded and the video has an editor
        if (
            max(video.request.status, request_status) >= Request.Statuses.UPLOADED
            and video.editor
        ):
            status = Video.Statuses.IN_PROGRESS

        # Check if the editing_done field is True
        if (
            status == Video.Statuses.IN_PROGRESS
            and "editing_done" in video.additional_data
        ):
            status = (
                Video.Statuses.EDITED
                if video.additional_data["editing_done"] is True
                else status
            )

        # A video kept as it was, like a live stream, needs neither an editor nor a cut
        if video.additional_data.get("editing_skipped") and (
            max(video.request.status, request_status) >= Request.Statuses.UPLOADED
        ):
            status = Video.Statuses.EDITED

        # Check if the video is coded on the website
        if (
            status == Video.Statuses.EDITED
            and "coding" in video.additional_data
            and "website" in video.additional_data["coding"]
        ):
            status = (
                Video.Statuses.CODED
                if video.additional_data["coding"]["website"] is True
                else status
            )

        # Check if the video is published on the website
        if status == Video.Statuses.CODED and video.additional_data.get(
            "publishing", {}
        ).get("website"):
            status = Video.Statuses.PUBLISHED

            # If the current status of the video is before published
            if video.status < Video.Statuses.PUBLISHED:
                # Check if there is a task or create one to share on social platforms
                if not Todo.objects.filter(
                    creator=get_system_user(), video=video
                ).exists():
                    todo = Todo.objects.create(
                        creator=get_system_user(),
                        description="Megosztás közösségi platformokon",
                        request=video.request,
                        video=video,
                    )
                    todo.assignees.set(get_pr_responsible())
                    todo.save()
                # Check if requester was already notified or send an e-mail to watch and rate us
                if (
                    not video.additional_data["publishing"].get(
                        "email_sent_to_user", False
                    )
                    and not video.request.requester.is_staff
                ):
                    email_user_video_published.delay_on_commit(video.id)
                if not video.additional_data["publishing"].get(
                    "notification_sent_to_user", False
                ):
                    video.set_publishing_flag("notification_sent_to_user")
                    notify_user_video_published.delay_on_commit(video.id)
                if settings.MATTERMOST_WEBHOOK_URL and not video.additional_data[
                    "publishing"
                ].get("posted_on_mattermost", False):
                    post_video_published_to_mattermost.delay_on_commit(video.id)

        # Check if the HQ export has been moved to its place
        if (
            status == Video.Statuses.PUBLISHED
            and "archiving" in video.additional_data
            and "hq_archive" in video.additional_data["archiving"]
        ):
            status = (
                Video.Statuses.DONE
                if video.additional_data["archiving"]["hq_archive"] is True
                else status
            )

        # Set the video status to the final score
        video.refresh_from_db()  # update object from DB because async task might have changed additional_data
        video.status = status

    # Save the status and update the status of the request as well
    video.save()
    if not called_from_request:
        update_request_status(video.request, True)


def recalculate_deadline(instance: Request, data: dict) -> dict:
    """
    If we change the end_datetime of an existing video request but
    - we did not include a deadline in the request body
    - OR the deadline present is the same as the original
    - AND the original equal seems to be an automatically calculated one
    we recalculate the deadline and add 3 weeks to the new end_datetime
    """
    end_datetime = data.get("end_datetime")
    if end_datetime and end_datetime != instance.end_datetime:
        deadline = data.get("deadline")
        if (not deadline or deadline == instance.deadline) and (
            instance.end_datetime + timedelta(weeks=3)
        ).date() == instance.deadline:
            data["deadline"] = (end_datetime + timedelta(weeks=3)).date()
    return data


@shared_task(
    bind=True,
    autoretry_for=(RequestException,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 10},
)
def notify_sch_event_management_system(self, request_id):
    request = Request.objects.get(pk=request_id)  # nosec B113

    accept = request.additional_data["accepted"]
    url = request.additional_data["external"]["sch_events_callback_url"]

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {settings.SCH_EVENTS_TOKEN}",
        "Content-Type": "application/json",
    }
    data = json.dumps({"accept": accept})
    url = requests.head(url, headers=headers, allow_redirects=True, timeout=10).url
    response = requests.post(
        url, data=data, headers=headers, allow_redirects=False, timeout=30
    )
    response.raise_for_status()
    return response.json()
