import random
from datetime import timedelta

from django.utils.text import slugify

from common.models import User
from devtools.builders import (
    add_comment,
    add_crew,
    add_rating,
    add_video,
    at,
    create_request,
)
from devtools.people import create_user
from video_requests.models import Request, Video
from video_requests.utilities import update_request_status

SEED = 1848
REQUEST_COUNT = 150
PEOPLE_COUNT = 30
STAFF_COUNT = 6

LAST_NAMES = (
    "Kovács",
    "Szabó",
    "Tóth",
    "Nagy",
    "Horváth",
    "Varga",
    "Kiss",
    "Molnár",
    "Németh",
    "Farkas",
    "Balogh",
    "Papp",
    "Takács",
    "Juhász",
    "Mészáros",
    "Simon",
)
FIRST_NAMES = (
    "Bence",
    "Máté",
    "Levente",
    "Dávid",
    "Ádám",
    "Gergő",
    "Balázs",
    "Zsófia",
    "Hanna",
    "Luca",
    "Réka",
    "Eszter",
    "Lili",
    "Dóra",
    "Petra",
    "Boglárka",
)
EVENTS = (
    "Kari napok",
    "Gólyabál",
    "Szakmai nap",
    "Állásbörze",
    "Félévnyitó koncert",
    "Sportnap",
    "Diákköri konferencia",
    "Nyílt nap",
    "Jótékonysági est",
    "Kollégiumi vetélkedő",
    "Hallgatói fórum",
    "Tavaszi koncert",
    "Workshop",
    "Kosárbajnokság",
    "Színházi előadás",
    "Mentorprogram nyitórendezvény",
)
TYPES = (
    "Élő közvetítés",
    "Zenés hangulatvideó",
    "Hangulatvideó riportokkal",
    "Promóciós videó",
    "Előadás, rendezvény videós dokumentálása",
)
PLACES = (
    "Schönherz Kollégium, Kakas",
    "Schönherz Kollégium, földszinti aula",
    "BME Q épület, QBF13",
    "BME K épület, Díszterem",
    "BME I épület, IB028",
    "BME sporttelep",
    "Kopaszi-gát",
)
VIDEO_TITLES = (
    "Aftermovie",
    "Teljes felvétel",
    "Rövid összefoglaló",
    "Interjúk",
    "Promóvideó",
)
POSITIONS = ("Operatőr", "Rendező", "Riporter", "Hangtechnikus", "Fotós")
MESSAGES = (
    (
        "Sziasztok! Mikorra érdemes kint lennetek?",
        "Szia! Egy órával a kezdés előtt ott leszünk.",
    ),
    (
        "Kell valami a helyszínen a technikához?",
        "Elég egy konnektor a terem hátuljában, köszönjük!",
    ),
    (
        "Lehet, hogy fél órát csúszik a kezdés. Ez gond?",
        "Nem gond, alkalmazkodunk hozzá.",
    ),
)
OUTCOMES = {
    Request.Statuses.DONE: 60,
    Request.Statuses.ARCHIVED: 15,
    Request.Statuses.DENIED: 12,
    Request.Statuses.CANCELED: 8,
    Request.Statuses.FAILED: 5,
}


def create_bulk(people: dict[str, User]) -> list[Request]:
    rng = random.Random(SEED)  # nosec B311: test data, not security
    names = rng.sample(
        [(last, first) for last in LAST_NAMES for first in FIRST_NAMES], PEOPLE_COUNT
    )
    generated = [
        create_user(
            f"{slugify(last)}.{slugify(first)}.{number:02d}",
            last,
            first,
            number=100 + number,
            is_staff=number < STAFF_COUNT,
        )
        for number, (last, first) in enumerate(names)
    ]
    crew = [user for user in people.values() if user.is_staff] + generated[:STAFF_COUNT]
    requesters = generated[STAFF_COUNT:]

    requests = [
        _create_past_request(rng, rng.choice(requesters), crew)
        for _ in range(REQUEST_COUNT)
    ]
    for request in requests:
        update_request_status(request)
    return requests


def _create_past_request(rng: random.Random, requester: User, crew) -> Request:
    start = at(-rng.randint(60, 3 * 365), rng.choice((9, 10, 14, 17, 19)))
    title = f"{rng.choice(EVENTS)} {start.year}"
    outcome = rng.choices(list(OUTCOMES), weights=list(OUTCOMES.values()))[0]
    responsible = rng.choice(crew)
    request = create_request(
        title,
        requester=requester,
        start=start,
        hours=rng.randint(2, 6),
        type=rng.choice(TYPES),
        place=rng.choice(PLACES),
        responsible=responsible,
        additional_data=_outcome_data(outcome, title),
        created=start - timedelta(days=rng.randint(7, 40)),
    )

    if rng.random() < 0.4:
        question, answer = rng.choice(MESSAGES)
        add_comment(request, requester, question, created=start - timedelta(days=5))
        add_comment(request, responsible, answer, created=start - timedelta(days=4))

    if outcome in (Request.Statuses.ARCHIVED, Request.Statuses.DONE):
        add_crew(
            request,
            *(
                (member, rng.choice(POSITIONS))
                for member in rng.sample(crew, rng.randint(1, 3))
            ),
        )
        for video_title in rng.sample(VIDEO_TITLES, rng.randint(1, 3)):
            video = add_video(
                request, video_title, Video.Statuses.DONE, editor=rng.choice(crew)
            )
            for author in rng.sample(crew, rng.randint(0, 2)):
                add_rating(video, author, rng.randint(3, 5))
    return request


def _outcome_data(outcome: int, title: str) -> dict:
    if outcome == Request.Statuses.DENIED:
        return {"accepted": False}
    if outcome == Request.Statuses.CANCELED:
        return {"accepted": True, "canceled": True}
    if outcome == Request.Statuses.FAILED:
        return {"accepted": True, "failed": True}
    recording = {"path": f"Felvételek/{title}", "copied_to_gdrive": True}
    if outcome == Request.Statuses.DONE:
        recording["removed"] = True
    return {"accepted": True, "recording": recording}
