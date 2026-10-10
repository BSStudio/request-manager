from common.models import User
from devtools.builders import (
    add_comment,
    add_crew,
    add_rating,
    add_todo,
    add_video,
    at,
    create_request,
)
from video_requests.models import Request, Todo, Video
from video_requests.utilities import update_request_status

LIVE = "Élő közvetítés"
MUSIC_VIDEO = "Zenés hangulatvideó"
REPORT_VIDEO = "Hangulatvideó riportokkal"
PROMO = "Promóciós videó"
DOCUMENTARY = "Előadás, rendezvény videós dokumentálása"


def create_scenarios(people: dict[str, User]) -> dict[str, Request]:
    anna = people["minta.anna"]
    elek = people["teszt.elek"]
    gabor = people["gyarto.gabor"]
    karoly = people["kamera.karoly"]
    szilvia = people["szerk.szilvia"]
    vilma = people["vago.vilma"]
    admin = people["admin.aladar"]

    scenarios = {}

    scenarios["requested"] = create_request(
        "Kari gólyabál",
        requester=anna,
        start=at(21, 20),
        hours=5,
        type=REPORT_VIDEO,
        place="Schönherz Kollégium, földszinti aula",
    )

    accepted = scenarios["accepted"] = create_request(
        "Őszi szakmai konferencia",
        requester=anna,
        start=at(7, 9),
        hours=8,
        type=LIVE,
        place="BME Q épület, QBF13",
        responsible=gabor,
        additional_data={"accepted": True},
    )
    add_crew(accepted, (karoly, "Operatőr"), (szilvia, "Rendező"))
    add_comment(
        accepted,
        anna,
        "Sziasztok! 9-kor kezdünk, de a regisztráció már fél 9-kor nyit. "
        "Elég, ha 8-ra odaértek?",
        created=at(-6, 10),
    )
    add_comment(
        accepted,
        gabor,
        "Szia Anna! Igen, 8-ra ott leszünk. A terem hátuljában kérnénk egy "
        "asztalt és egy konnektort a technikának.",
        created=at(-5, 9),
    )
    add_comment(
        accepted,
        gabor,
        "Két kamera kell, a nagyobbat Karcsi hozza.",
        created=at(-5, 9),
        internal=True,
    )
    add_comment(accepted, anna, "Rendben, intézem. Köszönöm!", created=at(-4, 14))
    add_comment(
        accepted,
        karoly,
        "A QBF13-ban a mikrofonokat a gondnoktól kell elkérni.",
        created=at(-2, 16),
        internal=True,
    )
    add_todo(accepted, gabor, "Akkumulátorok feltöltése", assignees=[karoly])
    add_todo(
        accepted,
        gabor,
        "Helyszínbejárás a teremben",
        assignees=[gabor],
        status=Todo.Statuses.CLOSED,
    )

    denied = scenarios["denied"] = create_request(
        "Szülinapi buli a koliban",
        requester=elek,
        start=at(14, 21),
        hours=4,
        type=MUSIC_VIDEO,
        place="Schönherz Kollégium, 17. emelet",
        additional_data={"accepted": False},
    )
    add_comment(
        denied,
        gabor,
        "Szia! Magánrendezvényre sajnos nem forgatunk, de jó bulit kívánunk!",
        created=at(-1, 12),
    )

    recorded = scenarios["recorded"] = create_request(
        "Egyetemi futóverseny",
        requester=anna,
        start=at(-3, 10),
        hours=4,
        type=REPORT_VIDEO,
        place="Kopaszi-gát",
        responsible=gabor,
        additional_data={"accepted": True},
    )
    add_crew(recorded, (karoly, "Operatőr"))

    uploaded = scenarios["uploaded"] = create_request(
        "Kollégiumi kulturális est",
        requester=elek,
        start=at(-6, 19),
        hours=4,
        type=MUSIC_VIDEO,
        place="Schönherz Kollégium, Kakas",
        responsible=gabor,
        additional_data={
            "accepted": True,
            "recording": {"path": "Felvételek/Kollégiumi kulturális est"},
        },
    )
    aftermovie = add_video(
        uploaded, "Aftermovie", Video.Statuses.IN_PROGRESS, editor=vilma
    )
    add_video(uploaded, "Fellépések egyben")
    add_todo(
        uploaded,
        gabor,
        "Zenék kiválasztása az aftermovie-hoz",
        assignees=[vilma],
        video=aftermovie,
    )
    add_todo(
        uploaded,
        gabor,
        "Drónos felvétel engedélyeztetése",
        status=Todo.Statuses.DISCARDED,
    )

    edited = scenarios["edited"] = create_request(
        "Tanszéki évzáró előadás",
        requester=anna,
        start=at(-15, 14),
        hours=2,
        type=DOCUMENTARY,
        place="BME K épület, Díszterem",
        responsible=gabor,
        additional_data={
            "accepted": True,
            "recording": {"path": "Felvételek/Tanszéki évzáró előadás"},
        },
    )
    add_video(edited, "Teljes előadás", Video.Statuses.EDITED, editor=vilma)
    add_video(edited, "Kérdések és válaszok", Video.Statuses.CODED, editor=vilma)
    add_video(edited, "Rövid összefoglaló", Video.Statuses.PUBLISHED, editor=vilma)

    archived = scenarios["archived"] = create_request(
        "Sportnap",
        requester=anna,
        start=at(-45, 9),
        hours=7,
        type=REPORT_VIDEO,
        place="BME sporttelep",
        responsible=gabor,
        additional_data={
            "accepted": True,
            "recording": {"path": "Felvételek/Sportnap", "copied_to_gdrive": True},
        },
    )
    add_video(archived, "Sportnap aftermovie", Video.Statuses.DONE, editor=vilma)

    done = scenarios["done"] = create_request(
        "Állásbörze",
        requester=anna,
        start=at(-60, 10),
        hours=6,
        type=PROMO,
        place="BME K épület, aula",
        responsible=gabor,
        additional_data={
            "accepted": True,
            "recording": {
                "path": "Felvételek/Állásbörze",
                "copied_to_gdrive": True,
                "removed": True,
            },
        },
    )
    add_crew(done, (karoly, "Operatőr"), (szilvia, "Riporter"))
    promo = add_video(
        done,
        "Állásbörze promóvideó",
        Video.Statuses.DONE,
        editor=vilma,
        aired=(at(-50, 0).date(), at(-45, 0).date()),
    )
    add_rating(
        promo, szilvia, 5, "Nagyon jól sikerült a vágás, a zene is passzol hozzá."
    )
    add_rating(promo, gabor, 4)

    canceled = scenarios["canceled"] = create_request(
        "Hallgatói fórum",
        requester=elek,
        start=at(10, 18),
        hours=2,
        type=LIVE,
        place="BME Q épület, QBF15",
        responsible=gabor,
        additional_data={"accepted": True, "canceled": True},
    )
    add_comment(
        canceled,
        elek,
        "Sajnos elmarad a fórum, de köszönjük, hogy elvállaltátok!",
        created=at(-1, 18),
    )

    failed = scenarios["failed"] = create_request(
        "Éjszakai kosármeccs",
        requester=anna,
        start=at(-20, 22),
        hours=2,
        type=REPORT_VIDEO,
        place="Schönherz Kollégium, tornaterem",
        responsible=gabor,
        additional_data={"accepted": True, "failed": True},
    )
    add_crew(failed, (karoly, "Operatőr"))
    add_comment(
        failed,
        karoly,
        "Lemerült mindkét akku, nem lett használható felvétel.",
        created=at(-19, 9),
        internal=True,
    )

    scenarios["pinned"] = create_request(
        "Félévnyitó koncert",
        requester=anna,
        start=at(-90, 19),
        hours=3,
        type=MUSIC_VIDEO,
        place="Schönherz Kollégium, Kakas",
        responsible=gabor,
        additional_data={
            "accepted": True,
            "status_by_admin": {
                "status": Request.Statuses.DONE,
                "admin_id": admin.id,
                "admin_name": admin.get_full_name_eastern_order(),
            },
        },
    )

    overdue = scenarios["overdue"] = create_request(
        "Diákköri konferencia",
        requester=anna,
        start=at(-40, 9),
        hours=8,
        type=DOCUMENTARY,
        place="BME I épület, IB028",
        responsible=gabor,
        additional_data={
            "accepted": True,
            "recording": {"path": "Felvételek/Diákköri konferencia"},
        },
    )
    add_video(overdue, "Díjátadó", Video.Statuses.IN_PROGRESS, editor=vilma)

    scenarios["on_behalf"] = create_request(
        "Szakkollégiumi nyílt nap",
        requester=elek,
        requested_by=people["pr.piroska"],
        start=at(30, 10),
        hours=6,
        type=PROMO,
        place="BME E épület, aula",
        additional_data={
            "requester": {
                "first_name": "Elek",
                "last_name": "Teszt",
                "phone_number": "+36209876543",
            }
        },
    )

    for request in scenarios.values():
        update_request_status(request)
    return scenarios
