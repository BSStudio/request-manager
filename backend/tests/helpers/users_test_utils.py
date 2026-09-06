import uuid

from django.contrib.auth.models import Group
from django.utils.timezone import localtime

from common.models import Ban, User, get_system_user

PASSWORD = "ae9U$89z#zyA!YoPE$6m"


def get_default_password():
    return PASSWORD


def create_user(
    username=None,
    password=PASSWORD,
    is_staff=False,
    is_admin=False,
    groups=None,
    banned=False,
):
    # Initial parameters
    if groups is None:
        groups = []
    suffix = localtime().strftime("%y%m%d_%H%M%S")
    username = username if username else str(uuid.uuid4())

    # Create user
    user = User.objects.create_user(
        username=username,
        password=password,
        email=f"{username}@example.com",
        last_name=f"Test_{suffix}",
    )
    if is_admin:
        user.first_name = "Admin"
    elif is_staff:
        user.first_name = "Staff"
    else:
        user.first_name = "User"

    # Set unusable password
    if password == "unusable":
        user.set_unusable_password()

    # Set permissions
    user.is_staff = is_staff or is_admin
    if is_admin:
        groups.append("Administrators")

    # Set user's profile
    user.avatar = {
        "provider": "gravatar",
        "microsoft-graph": "https://via.placeholder.com/150",
        "gravatar": "https://via.placeholder.com/200",
    }
    user.phone_number = "+36701234567"

    # Get or create groups and add user to them
    for group in groups:
        grp = Group.objects.get_or_create(name=group)[0]
        user.groups.add(grp)

    # Save user and return
    user.save()

    # Add user ban
    if banned:
        Ban.objects.create(creator=get_system_user(), receiver=user)

    return user
