from functools import partial

from django.db import transaction
from django.db.models.signals import m2m_changed, post_delete, pre_delete
from django.dispatch import receiver
from simple_history.signals import pre_create_historical_m2m_records

from video_requests.emails import email_staff_todo_assigned
from video_requests.models import Todo, Video
from video_requests.utilities import update_request_status


@receiver(post_delete, sender=Video)
def update_request_status_after_video_delete(sender, instance, **kwargs):
    update_request_status(instance.request)


def send_notification_to_new_assignees(
    sender, instance, action, reverse, model, pk_set, **kwargs
):
    if action == "post_add" and not reverse:
        # In this case pk_set will be the set of user ids added as new assignees
        # The task reads the todo, which a worker can only see once committed.
        transaction.on_commit(
            partial(email_staff_todo_assigned.delay, instance.id, list(pk_set))
        )


m2m_changed.connect(send_notification_to_new_assignees, sender=Todo.assignees.through)


# The deletion record of a todo must keep its assignees, so that restoring it
# brings them back. Django deletes the assignee rows before the todo, so
# simple-history would find none by the time it writes that record.
@receiver(pre_delete, sender=Todo)
def remember_assignees_of_deleted_todo(sender, instance, **kwargs):
    instance.deleted_assignees = list(
        Todo.assignees.through.objects.filter(todo=instance)
    )


@receiver(pre_create_historical_m2m_records)
def add_assignees_to_deletion_record(
    sender, rows, history_instance, instance, **kwargs
):
    if history_instance.history_type == "-" and isinstance(instance, Todo):
        rows.extend(
            sender(
                history=history_instance,
                id=row.id,
                todo_id=row.todo_id,
                user_id=row.user_id,
            )
            for row in instance.deleted_assignees
        )
