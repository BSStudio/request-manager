from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from common.models import User
from common.utilities import get_editor_in_chief, get_production_manager
from video_requests.models import Comment, Request, Todo, Video

TEXT_HTML = "text/html"


def get_email_avatar_url(user):
    # Microsoft avatars are stored as data: URIs, which Gmail and Outlook do not show.
    url = user.avatar_url
    return url if url and not url.lower().startswith("data:") else None


@shared_task
def email_user_new_request_confirmation(request_id):
    request = Request.objects.get(pk=request_id)  # nosec B113
    context = {
        "request": request,
        "is_registered": request.requester.is_active,
    }

    msg_plain = render_to_string("email/txt/user_new_request_confirmation.txt", context)
    msg_html = render_to_string(
        "email/html/user_new_request_confirmation.html", context
    )

    subject = f"{request.title} | Forgatási felkérésedet fogadtuk"
    editor_in_chief_email_address = [user.email for user in get_editor_in_chief()]

    msg = EmailMultiAlternatives(
        subject=subject,
        body=msg_plain,
        to=[request.requester.email],
        cc=[settings.DEFAULT_REPLY_EMAIL],
        bcc=editor_in_chief_email_address,
        reply_to=[settings.DEFAULT_REPLY_EMAIL],
    )

    msg.attach_alternative(msg_html, TEXT_HTML)
    msg.send()
    return f"Request confirmation e-mail was sent to {request.requester.email} successfully."


@shared_task
def email_user_video_published(video_id):
    video = Video.objects.get(pk=video_id)  # nosec B113
    context = {
        "video": video,
        "is_registered": video.request.requester.is_active,
    }

    msg_plain = render_to_string("email/txt/user_video_published.txt", context)
    msg_html = render_to_string("email/html/user_video_published.html", context)

    subject = f"{video.request.title} | Új videót publikáltunk"

    msg = EmailMultiAlternatives(
        subject=subject,
        body=msg_plain,
        to=[video.request.requester.email],
        reply_to=[settings.DEFAULT_REPLY_EMAIL],
    )

    msg.attach_alternative(msg_html, TEXT_HTML)
    msg.send()
    video.refresh_from_db()
    video.additional_data["publishing"]["email_sent_to_user"] = True
    video.save()
    return f"Video published e-mail was sent to {video.request.requester.email} successfully."


@shared_task
def email_user_new_comment(comment_id):
    comment = Comment.objects.get(pk=comment_id)  # nosec B113
    context = {
        "comment": comment,
        "commenter_avatar_url": get_email_avatar_url(comment.author),
        "commenter_name": comment.author.get_full_name_eastern_order(),
    }

    msg_plain = render_to_string("email/txt/user_new_comment.txt", context)
    msg_html = render_to_string("email/html/user_new_comment.html", context)

    subject = f"{comment.request.title} | Új üzenet a BSS-től"

    msg = EmailMultiAlternatives(
        subject=subject,
        body=msg_plain,
        to=[comment.request.requester.email],
        reply_to=[settings.DEFAULT_REPLY_EMAIL],
    )

    msg.attach_alternative(msg_html, TEXT_HTML)
    msg.send()
    return f"New comment e-mail was sent to {comment.request.requester.email} successfully."


def email_staff_weekly_tasks(recording, editing_no_vids, editing_unedited_vids):
    context = {
        "recording": recording,
        "editing_no_vids": editing_no_vids,
        "editing_unedited_vids": editing_unedited_vids,
    }

    msg_plain = render_to_string("email/txt/staff_weekly_tasks.txt", context)
    msg_html = render_to_string("email/html/staff_weekly_tasks.html", context)

    subject = "E heti forgatások és vágandó anyagok"

    msg = EmailMultiAlternatives(
        subject=subject,
        body=msg_plain,
        to=[settings.WEEKLY_TASK_EMAIL],
        reply_to=[settings.WEEKLY_TASK_EMAIL],
    )

    msg.attach_alternative(msg_html, TEXT_HTML)
    msg.send()


def email_crew_daily_reminder(request, crew_members):
    context = {
        "request": request,
    }
    msg_plain = render_to_string("email/txt/crew_daily_reminder.txt", context)
    msg_html = render_to_string("email/html/crew_daily_reminder.html", context)

    subject = f"Emlékeztető | {request.title} | Mai forgatás"

    msg = EmailMultiAlternatives(
        subject=subject,
        body=msg_plain,
        to=[user.member.email for user in crew_members],
    )

    msg.attach_alternative(msg_html, TEXT_HTML)
    msg.send()


@shared_task
def email_crew_new_comment(comment_id):
    comment = Comment.objects.get(pk=comment_id)  # nosec B113
    context = {
        "comment": comment,
        "commenter_avatar_url": get_email_avatar_url(comment.author),
        "commenter_name": comment.author.get_full_name_eastern_order(),
    }

    msg_plain = render_to_string("email/txt/crew_new_comment.txt", context)
    msg_html = render_to_string("email/html/crew_new_comment.html", context)

    if comment.internal:
        subject = f"{comment.request.title} | Új belső megjegyzés"
    elif comment.author_id == comment.request.requester_id:
        subject = f"{comment.request.title} | Új üzenet a felkérőtől"
    else:
        subject = f"{comment.request.title} | Új üzenet a felkérőnek"
    editor_in_chief_email_address = [user.email for user in get_editor_in_chief()]
    responsible_email_address = (
        [comment.request.responsible.email]
        if comment.request.responsible and comment.request.responsible.is_staff
        else []
    )
    crew_members_email_addresses = [
        user.member.email for user in comment.request.crew.filter(member__is_staff=True)
    ]

    msg = EmailMultiAlternatives(
        subject=subject,
        body=msg_plain,
        to=crew_members_email_addresses,
        cc=list(set().union(editor_in_chief_email_address, responsible_email_address)),
    )

    msg.attach_alternative(msg_html, TEXT_HTML)
    msg.send()
    return f"New comment e-mail was sent to {[crew_members_email_addresses, editor_in_chief_email_address, responsible_email_address]} successfully."


@shared_task
def email_crew_request_modified(
    request_id, changed_by_name, changed_datetime, changed_values
):
    request = Request.objects.get(pk=request_id)
    context = {
        "changed_by_name": changed_by_name,
        "changed_datetime": changed_datetime,
        "changed_values": changed_values,
        "request": request,
    }

    msg_plain = render_to_string("email/txt/crew_request_modified.txt", context)
    msg_html = render_to_string("email/html/crew_request_modified.html", context)

    subject = f"{request.title} | Felkérés módosítva"
    editor_in_chief_email_address = [user.email for user in get_editor_in_chief()]
    responsible_email_address = (
        [request.responsible.email]
        if request.responsible and request.responsible.is_staff
        else []
    )
    crew_members_email_addresses = [
        user.member.email for user in request.crew.filter(member__is_staff=True)
    ]

    msg = EmailMultiAlternatives(
        subject=subject,
        body=msg_plain,
        to=crew_members_email_addresses,
        cc=list(set().union(editor_in_chief_email_address, responsible_email_address)),
    )

    msg.attach_alternative(msg_html, TEXT_HTML)
    msg.send()
    return f"Request modified notification e-mail was sent to {[crew_members_email_addresses, editor_in_chief_email_address, responsible_email_address]} successfully."


@shared_task
def email_staff_todo_assigned(todo_id, user_ids):
    todo = Todo.objects.get(pk=todo_id)

    assignment_type = "video" if todo.video else "request"
    title = todo.video.title if todo.video else todo.request.title

    context = {"assignment_type": assignment_type, "title": title, "todo": todo}

    msg_plain = render_to_string("email/txt/staff_todo_assigned.txt", context)
    msg_html = render_to_string("email/html/staff_todo_assigned.html", context)

    subject = "Feladatot rendeltek hozzád"

    assignees_email_address = [
        user.email for user in User.objects.filter(id__in=user_ids, is_staff=True)
    ]

    msg = EmailMultiAlternatives(
        subject=subject,
        body=msg_plain,
        to=assignees_email_address,
    )

    msg.attach_alternative(msg_html, TEXT_HTML)
    msg.send()
    return f"Todo assignment notification was sent to {assignees_email_address} successfully."


def email_production_manager_unfinished_requests(requests):
    context = {"requests": requests}

    msg_plain = render_to_string(
        "email/txt/production_manager_unfinished_requests.txt", context
    )
    msg_html = render_to_string(
        "email/html/production_manager_unfinished_requests.html", context
    )

    subject = "Lezáratlan anyagok"
    production_manager_email_address = [user.email for user in get_production_manager()]

    msg = EmailMultiAlternatives(
        subject=subject,
        body=msg_plain,
        to=production_manager_email_address,
    )

    msg.attach_alternative(msg_html, TEXT_HTML)
    msg.send()


def email_responsible_overdue_requests(responsible, requests):
    context = {"requests": requests, "summary": False}

    msg_plain = render_to_string("email/txt/responsible_overdue_request.txt", context)
    msg_html = render_to_string("email/html/responsible_overdue_request.html", context)

    subject = "Lejárt határidejű felkéréseid"

    msg = EmailMultiAlternatives(
        subject=subject,
        body=msg_plain,
        to=[responsible.email],
    )

    msg.attach_alternative(msg_html, TEXT_HTML)
    msg.send()


def email_staff_overdue_requests(requests):
    context = {"requests": requests, "summary": True}

    msg_plain = render_to_string("email/txt/responsible_overdue_request.txt", context)
    msg_html = render_to_string("email/html/responsible_overdue_request.html", context)

    subject = "Lejárt határidejű felkérések"
    recipients = {user.email for user in get_editor_in_chief()} | {
        user.email for user in get_production_manager()
    }

    msg = EmailMultiAlternatives(
        subject=subject,
        body=msg_plain,
        to=sorted(recipients),
    )

    msg.attach_alternative(msg_html, TEXT_HTML)
    msg.send()
