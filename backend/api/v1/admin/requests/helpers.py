from collections.abc import Mapping

from api.v1.requests.utilities import create_user
from common.models import User
from video_requests.models import Request, Video


def check_and_remove_unauthorized_additional_data(
    additional_data: dict, user: User, original_data: Request | Video | None
) -> dict:
    """Remove keys and values which are used by other functions and should be changed only by authorized users"""
    additional_data.pop("requester", None)
    if "publishing" in additional_data:
        additional_data["publishing"].pop("email_sent_to_user", None)
    if not user.is_admin:
        additional_data.pop("status_by_admin", None)
        additional_data.pop("accepted", None)
        additional_data.pop("canceled", None)
        additional_data.pop("failed", None)
        additional_data.pop("calendar_id", None)
    else:
        if "status_by_admin" in additional_data:
            """
            Do not need to check whether other fields exists because validation schema makes
            both status and admin_id required at save.
            """
            if (
                original_data
                and (
                    "status_by_admin" in original_data.additional_data
                    and original_data.additional_data["status_by_admin"].get("status")
                    == additional_data["status_by_admin"].get("status")
                )
                or (
                    "status_by_admin" not in original_data.additional_data
                    and not additional_data["status_by_admin"].get("status")
                )
            ):
                additional_data.pop("status_by_admin")
            else:
                additional_data["status_by_admin"].update({"admin_id": user.id})
                additional_data["status_by_admin"].update(
                    {"admin_name": user.get_full_name_eastern_order()}
                )
    return additional_data


def get_or_create_requester_from_data(
    validated_data: dict, instance: Request | None = None
) -> None:
    validated_data["requester"], additional_data = create_user(validated_data)
    if additional_data:
        # handle_additional_data() is always called before this function,
        # so if there is additional_data in validated_data we should update that.
        # Otherwise, check if it is an existing object and update the original additional_data
        if validated_data.get("additional_data"):
            validated_data["additional_data"] = update_additional_data(
                validated_data["additional_data"], additional_data
            )
        elif instance:
            validated_data["additional_data"] = update_additional_data(
                instance.additional_data, additional_data
            )
        else:
            validated_data["additional_data"] = additional_data


def handle_additional_data(
    validated_data: dict, user: User, original_data: Request | Video | None = None
) -> dict:
    if "additional_data" in validated_data:
        validated_data["additional_data"] = (
            check_and_remove_unauthorized_additional_data(
                validated_data["additional_data"], user, original_data
            )
        )
        if original_data:
            validated_data["additional_data"] = update_additional_data(
                original_data.additional_data, validated_data["additional_data"]
            )
    return validated_data


def is_status_by_admin(obj: Request | Video) -> bool:
    try:
        return isinstance(obj.additional_data.get("status_by_admin").get("status"), int)
    except AttributeError:
        return False


def update_additional_data(orig_dict: dict, new_dict: dict) -> dict:
    """
    Update existing additional data.
    Replaces/extends changed keys and removes them if None is provided.
    Takes care of nested dictionaries.
    """
    for key, value in new_dict.items():
        if isinstance(value, Mapping):
            orig_dict[key] = update_additional_data(orig_dict.get(key, {}), value)
        # Currently, there is only one list in additional_data which needs to be replaced every time
        # to be able to delete from it. If there will be a list which will only be extended use this function.
        # elif isinstance(value, list):
        #     orig_dict[key] = orig_dict.get(key, []) + value
        else:
            if value is None:
                orig_dict.pop(key, None)
            else:
                orig_dict[key] = new_dict[key]
    return orig_dict
