from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth.models import Group

from common.models import Ban, User

#: A rerun deletes every user whose address ends in this domain.
EMAIL_DOMAIN = "example.com"


@dataclass(frozen=True)
class Person:
    username: str
    last_name: str
    first_name: str
    is_staff: bool = False
    groups: tuple[str, ...] = ()


PEOPLE = (
    Person("admin.aladar", "Admin", "Aladár", True, (settings.ADMIN_GROUP,)),
    Person("szerk.szilvia", "Szerkesztő", "Szilvia", True, ("Főszerkesztő",)),
    Person("gyarto.gabor", "Gyártó", "Gábor", True, ("Gyártásvezető",)),
    Person("pr.piroska", "PR", "Piroska", True, ("PR felelős",)),
    Person("vago.vilma", "Vágó", "Vilma", True),
    Person("kamera.karoly", "Kamera", "Károly", True),
    Person("minta.anna", "Minta", "Anna"),
    Person("teszt.elek", "Teszt", "Elek"),
    Person("ures.peter", "Üres", "Péter"),
    Person("tiltott.tamas", "Tiltott", "Tamás"),
)


def create_user(
    username: str,
    last_name: str,
    first_name: str,
    *,
    number: int,
    is_staff: bool = False,
    groups: tuple[str, ...] = (),
) -> User:
    user = User(
        username=username,
        email=f"{username}@{EMAIL_DOMAIN}",
        first_name=first_name,
        last_name=last_name,
        phone_number=f"+3630{1000000 + number}",
        is_staff=is_staff,
    )
    user.set_unusable_password()
    user.save()
    user.groups.add(*(Group.objects.get_or_create(name=name)[0] for name in groups))
    return user


def create_people() -> dict[str, User]:
    users = {
        person.username: create_user(
            person.username,
            person.last_name,
            person.first_name,
            number=number,
            is_staff=person.is_staff,
            groups=person.groups,
        )
        for number, person in enumerate(PEOPLE)
    }
    Ban.objects.create(
        receiver=users["tiltott.tamas"],
        creator=users["admin.aladar"],
        reason="Többször küldött kamu felkérést",
    )
    return users
