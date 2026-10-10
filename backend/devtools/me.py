from common.models import User
from devtools.builders import (
    add_comment,
    add_crew,
    add_todo,
    add_video,
    at,
    create_request,
)
from video_requests.models import Request, Video
from video_requests.utilities import update_request_status


def attach_to(
    user: User, people: dict[str, User], scenarios: dict[str, Request]
) -> None:
    gabor = people["gyarto.gabor"]

    requested = create_request(
        "Klubnyitó buli",
        requester=user,
        start=at(12, 20),
        hours=4,
        type="Hangulatvideó riportokkal",
        place="Schönherz Kollégium, Kakas",
    )

    accepted = create_request(
        "Kerekasztal-beszélgetés",
        requester=user,
        start=at(5, 18),
        hours=2,
        type="Élő közvetítés",
        place="Schönherz Kollégium, földszinti aula",
        responsible=gabor,
        additional_data={"accepted": True},
    )
    add_comment(
        accepted,
        user,
        "Sziasztok! A színpad mellé be tudtok állni a kamerával?",
        created=at(-3, 10),
    )
    add_comment(
        accepted,
        gabor,
        "Szia! Igen, előtte még átnézzük a helyszínt.",
        created=at(-2, 11),
    )
    add_todo(accepted, gabor, "Streamkulcs beállítása", assignees=[user])
    add_todo(accepted, gabor, "Hangpult bekötésének kipróbálása", assignees=[user])

    done = create_request(
        "Interjú a klubvezetővel",
        requester=user,
        start=at(-70, 15),
        hours=2,
        type="Promóciós videó",
        place="Schönherz Kollégium, stúdió",
        responsible=gabor,
        additional_data={
            "accepted": True,
            "recording": {
                "path": "Felvételek/Interjú a klubvezetővel",
                "copied_to_gdrive": True,
                "removed": True,
            },
        },
    )
    add_video(done, "Interjú", Video.Statuses.DONE, editor=user)

    add_crew(scenarios["accepted"], (user, "Operatőr"))
    add_crew(scenarios["done"], (user, "Riporter"))

    for request in (requested, accepted, done):
        update_request_status(request)
