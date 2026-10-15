import unicodedata
from collections import defaultdict

import requests
from celery import shared_task
from django.conf import settings
from requests import RequestException

from video_requests.models import Video


def hungarian_sort_key(text: str) -> str:
    # Decomposed, an accented letter sorts next to its base letter, not after Z.
    return unicodedata.normalize("NFD", text)


def get_video_published_message(video: Video) -> str:
    names_by_position = defaultdict(set)
    for crew_member in video.request.crew.select_related("member"):
        names_by_position[crew_member.position].add(
            crew_member.member.get_full_name_eastern_order()
        )

    credits = [
        f"**{position}:** {', '.join(sorted(names_by_position[position], key=hungarian_sort_key))}"
        for position in sorted(names_by_position, key=hungarian_sort_key)
    ]
    if video.editor:
        credits.insert(0, f"**Vágó:** {video.editor.get_full_name_eastern_order()}")

    lines = [
        f"#### :clapper: {video.title}",
        f"[Videó]({video.published_url}) | [Értékelés a felkéréskezelőben]({video.admin_url})",
    ]
    if credits:
        lines += ["", *credits]
    return "\n".join(lines)


@shared_task(
    autoretry_for=(RequestException,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 10},
)
def post_video_published_to_mattermost(video_id):
    video = Video.objects.get(pk=video_id)  # nosec B113
    response = requests.post(
        settings.MATTERMOST_WEBHOOK_URL,
        json={"text": get_video_published_message(video)},
        timeout=30,
    )
    response.raise_for_status()
    video.set_publishing_flag("posted_on_mattermost")
    return f"Video {video_id} was posted on Mattermost successfully."
