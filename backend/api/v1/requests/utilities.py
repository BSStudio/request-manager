from common.models import User


def create_user(validated_data: dict) -> tuple[User, dict | None]:
    user = User()
    user.first_name = validated_data.pop("requester_first_name")
    user.last_name = validated_data.pop("requester_last_name")
    user.email = validated_data.pop("requester_email").lower()
    user.username = user.email
    user.set_unusable_password()
    user.is_active = False
    phone_number = validated_data.pop("requester_mobile")

    if User.objects.filter(email__iexact=user.email).exists():
        # If user with given e-mail address already exist set it as requester but save the provided data.
        # The user's data will be not overwritten so useful to check phone number or anything else.
        additional_data = {
            "requester": {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone_number": phone_number.as_e164,
            }
        }
        return User.objects.get(email__iexact=user.email), additional_data
    else:
        user.phone_number = phone_number
        user.save()
        return user, None
