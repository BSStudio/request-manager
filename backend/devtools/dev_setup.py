"""Prepare a checkout for development; in a git worktree, give it its own database and Redis indexes.

Run as `uv run python -m devtools.dev_setup [--prune [--dry-run]]` from `backend/`. It imports no
Django: a fresh worktree has no `backend/.env`, so `manage.py` could not even list the devtools commands.
"""

import argparse
import hashlib
import os
import re
import shutil
import subprocess  # nosec B404
import sys
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import psycopg
from decouple import RepositoryEnv
from psycopg import sql

WORKTREE_FILES = ["backend/.env", "frontend/.env"]
PREFIX = "rm_"
MAX_IDENTIFIER_BYTES = 63
MAIN_REDIS_INDEXES = {0, 1}
# The fallbacks core/settings/base.py uses.
DATABASE_DEFAULTS = {
    "DATABASE_HOST": "postgres",
    "DATABASE_PORT": "5432",
    "DATABASE_USER": "request_manager",
    "DATABASE_PASSWORD": "change_me",  # nosec B105
    "DATABASE_NAME": "request_manager_db",
}


class SetupError(Exception):
    pass


def _git(cwd: Path, *args: str) -> str | None:
    result = subprocess.run(  # nosec B603 B607
        ["git", *args], cwd=cwd, capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else None


def main_checkout_of(cwd: Path) -> Path | None:
    git_dir = _git(cwd, "rev-parse", "--path-format=absolute", "--git-dir")
    common_dir = _git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if not git_dir or not common_dir:
        return None
    if Path(git_dir).resolve() == Path(common_dir).resolve():
        return None
    return Path(common_dir).resolve().parent


def worktree_root(cwd: Path) -> Path | None:
    root = _git(cwd, "rev-parse", "--show-toplevel")
    return Path(root) if root else None


def worktree_roots(cwd: Path) -> list[Path]:
    porcelain = _git(cwd, "worktree", "list", "--porcelain") or ""
    return [
        Path(line.removeprefix("worktree "))
        for line in porcelain.splitlines()
        if line.startswith("worktree ")
    ]


def worktree_key(root: Path, main_checkout: Path) -> str:
    try:
        return root.relative_to(main_checkout / ".claude" / "worktrees").as_posix()
    except ValueError:
        return root.name


def database_name(key: str, prefix: str = PREFIX) -> str:
    name = re.sub(r"[^a-z0-9]+", "_", f"{prefix}{key}".lower()).strip("_")
    if len(name.encode()) <= MAX_IDENTIFIER_BYTES:
        return name
    digest = hashlib.sha256(name.encode()).hexdigest()[:8]
    return f"{name[: MAX_IDENTIFIER_BYTES - len(digest) - 1]}_{digest}"


def set_env_value(text: str, key: str, value: str) -> str:
    eol = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(eol)
    # Lead (optional `export`, the key, `=`), a quoted or bare value, then whatever follows it.
    pattern = re.compile(
        rf"^(\s*(?:export\s+)?{re.escape(key)}\s*=\s*)(?:([\"'])(?:.*?)\2|[^\s#]*)(.*)$"
    )
    for index, line in enumerate(lines):
        if match := pattern.match(line):
            quote = match.group(2) or ""
            lines[index] = f"{match.group(1)}{quote}{value}{quote}{match.group(3)}"
            return eol.join(lines)
    body = text if not text or text.endswith(eol) else f"{text}{eol}"
    return f"{body}{key} = {value}{eol}"


def redis_index(url: str) -> int | None:
    path = urlsplit(url).path.strip("/")
    return int(path) if path.isdigit() else None


def with_redis_index(url: str, index: int) -> str:
    return urlunsplit(urlsplit(url)._replace(path=f"/{index}"))


def free_redis_pair(claimed: set[int]) -> tuple[int, int]:
    for first in range(2, 15, 2):
        if first not in claimed and first + 1 not in claimed:
            return first, first + 1
    raise RuntimeError(
        "No free Redis index pair: indexes 2-15 are all claimed by other worktrees."
    )


def stale_databases(
    existing: Iterable[str], live: Iterable[str], prefix: str = PREFIX
) -> list[str]:
    live = set(live)
    return [name for name in existing if name.startswith(prefix) and name not in live]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m devtools.dev_setup")
    parser.add_argument(
        "--prune",
        action="store_true",
        help="drop the databases of removed worktrees",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="with --prune: list the databases, drop nothing",
    )
    args = parser.parse_args(argv)
    # Keeps these lines in order with manage.py's output when stdout is a pipe or a file.
    sys.stdout.reconfigure(line_buffering=True)

    root = worktree_root(Path.cwd())
    if root is None:
        print("Not inside a git checkout.", file=sys.stderr)
        return 1
    main_checkout = main_checkout_of(root)
    try:
        if args.prune:
            _prune(root, main_checkout or root, args.dry_run)
        else:
            _setup(root, main_checkout)
    except SetupError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


def _setup(root: Path, main_checkout: Path | None) -> None:
    backend = root / "backend"
    env_path = backend / ".env"
    if main_checkout:
        _step("Copying gitignored files from the main checkout")
        for relative in WORKTREE_FILES:
            target, source = root / relative, main_checkout / relative
            if target.exists():
                print(f"    {relative} exists, leaving it alone.")
            elif source.exists():
                shutil.copy2(source, target)
                print(f"    Copied {relative}.")
            else:
                print(f"    {relative} is not in the main checkout, skipped.")
    if not env_path.exists():
        raise SetupError(
            "backend/.env is missing: create it from backend/.env.sample (see backend/README.md)."
        )

    overrides: dict[str, str] = {}
    if main_checkout:
        overrides = _worktree_values(root, main_checkout, env_path)
        text = env_path.read_bytes().decode()
        for key, value in overrides.items():
            text = set_env_value(text, key, value)
        env_path.write_bytes(text.encode())
        print(f"    backend/.env points at {overrides['DATABASE_NAME']}.")

    _step("Starting Postgres and Redis")
    _run(
        ["docker", "compose", "-f", "docker-compose.dev.yaml", "up", "-d", "--wait"],
        root,
    )

    settings = _database_settings(env_path, overrides)
    if main_checkout:
        _step(f"Creating {settings['DATABASE_NAME']}")
        print("    Created." if _create_database(settings) else "    Exists.")

    # decouple reads the environment before backend/.env, so a value exported in the shell
    # would point manage.py at another database.
    env = {**os.environ, **overrides}
    manage = [sys.executable, "manage.py"]
    _step("Applying migrations")
    _run([*manage, "migrate"], backend, env)
    _step("Collecting static files")
    _run([*manage, "collectstatic", "--no-input"], backend, env)

    if main_checkout:
        # The seed wipes data, so a worktree database gets it only while empty: fresh, or left
        # so by an interrupted first run.
        if _user_count(settings) == 0:
            _step("Seeding")
            _run([*manage, "seed_dev_data", "--no-input"], backend, env)
        else:
            print(
                "    Already seeded, skipping the seed, which would wipe this worktree's data."
            )
    print("\nDev environment ready.")


def _worktree_values(root: Path, main_checkout: Path, env_path: Path) -> dict[str, str]:
    data = RepositoryEnv(str(env_path)).data
    cache = data.get("CACHE_REDIS", "redis://redis:6379/0")
    broker = data.get("CELERY_BROKER", "redis://redis:6379/1")
    own = redis_index(cache)
    if own in range(2, 15, 2) and redis_index(broker) == own + 1:
        first = own
    else:
        claimed = set(MAIN_REDIS_INDEXES)
        for other in worktree_roots(root):
            if other.resolve() in (root.resolve(), main_checkout.resolve()):
                continue
            other_env = other / "backend" / ".env"
            if other_env.exists():
                other_data = RepositoryEnv(str(other_env)).data
                for key in ("CACHE_REDIS", "CELERY_BROKER"):
                    index = redis_index(other_data.get(key, ""))
                    if index is not None:
                        claimed.add(index)
        try:
            first, _ = free_redis_pair(claimed)
        except RuntimeError as error:
            raise SetupError(str(error)) from error
    return {
        "DATABASE_NAME": database_name(worktree_key(root, main_checkout)),
        "CACHE_REDIS": with_redis_index(cache, first),
        "CELERY_BROKER": with_redis_index(broker, first + 1),
    }


def _database_settings(env_path: Path, overrides: dict[str, str]) -> dict[str, str]:
    data = RepositoryEnv(str(env_path)).data
    return {
        key: overrides.get(key) or os.environ.get(key) or data.get(key) or default
        for key, default in DATABASE_DEFAULTS.items()
    }


def _connect(settings: dict[str, str], dbname: str) -> psycopg.Connection:
    try:
        return psycopg.connect(
            host=settings["DATABASE_HOST"],
            port=settings["DATABASE_PORT"],
            user=settings["DATABASE_USER"],
            password=settings["DATABASE_PASSWORD"],
            dbname=dbname,
            connect_timeout=5,
            autocommit=True,
        )
    except psycopg.OperationalError as error:
        reason = (
            str(error).strip().splitlines()[-1]
            if str(error).strip()
            else type(error).__name__
        )
        raise SetupError(
            f"Postgres is not reachable at {settings['DATABASE_HOST']}:{settings['DATABASE_PORT']}: {reason}"
        ) from error


def _create_database(settings: dict[str, str]) -> bool:
    with _connect(settings, "postgres") as connection:
        name = settings["DATABASE_NAME"]
        if connection.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", [name]
        ).fetchone():
            return False
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        return True


def _user_count(settings: dict[str, str]) -> int:
    with _connect(settings, settings["DATABASE_NAME"]) as connection:
        return connection.execute("SELECT count(*) FROM auth_user").fetchone()[0]


def _prune(root: Path, main_checkout: Path, dry_run: bool) -> None:
    _step(
        "Listing the databases of removed worktrees (dry run)"
        if dry_run
        else "Dropping the databases of removed worktrees"
    )
    env_path = root / "backend" / ".env"
    if not env_path.exists():
        raise SetupError("backend/.env is missing: it holds the database credentials.")
    live = [
        database_name(worktree_key(other, main_checkout))
        for other in worktree_roots(root)
        if other.resolve() != main_checkout.resolve()
    ]
    with _connect(_database_settings(env_path, {}), "postgres") as connection:
        existing = [
            row[0] for row in connection.execute("SELECT datname FROM pg_database")
        ]
        stale = stale_databases(existing, live)
        if not stale:
            print("    Nothing to drop.")
        for name in stale:
            if dry_run:
                print(f"    Would drop {name}.")
                continue
            try:
                connection.execute(
                    sql.SQL("DROP DATABASE {}").format(sql.Identifier(name))
                )
                print(f"    Dropped {name}.")
            except psycopg.Error as error:
                print(f"    Could not drop {name}: {str(error).strip()}")
    print("\nDry run, nothing dropped." if dry_run else "\nPruned.")


def _step(message: str) -> None:
    print(f"\n==> {message}")


def _run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    try:
        result = subprocess.run(command, cwd=cwd, env=env)  # nosec B603
    except FileNotFoundError as error:
        raise SetupError(f"{command[0]} is not installed or not on PATH.") from error
    if result.returncode != 0:
        raise SetupError(
            f"{' '.join(command[1:])} failed with exit code {result.returncode}."
        )


if __name__ == "__main__":
    sys.exit(main())
