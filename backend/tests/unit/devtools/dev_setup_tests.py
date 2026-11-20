import os
import subprocess
from pathlib import Path

import pytest

from devtools.dev_setup import (
    claimed_redis_indexes,
    database_name,
    free_redis_pair,
    main_checkout_of,
    redis_index,
    set_env_value,
    stale_databases,
    with_redis_index,
    worktree_key,
    worktree_root,
    worktree_roots,
)


def test_database_name_prefixes_and_replaces_other_characters():
    assert database_name("feature-auth") == "rm_feature_auth"
    assert database_name("Agent-Files") == "rm_agent_files"


def test_nested_branch_keeps_its_whole_path():
    key = worktree_key(Path("/r/.claude/worktrees/feat/short-links"), Path("/r"))
    assert key == "feat/short-links"
    assert database_name(key) == "rm_feat_short_links"


def test_worktree_outside_the_folder_uses_its_name():
    assert worktree_key(Path("/elsewhere/agent-files"), Path("/r")) == "agent-files"


def test_long_name_fits_63_bytes_with_a_stable_hash():
    name = database_name("x" * 80)
    assert len(name.encode()) == 63
    assert name == database_name("x" * 80)
    assert name != database_name("x" * 81)


def test_set_env_value_keeps_the_comment_and_crlf():
    text = "A = 1\r\nDATABASE_NAME = request_manager_db  # Optional\r\nB = 2\r\n"
    assert (
        set_env_value(text, "DATABASE_NAME", "rm_x")
        == "A = 1\r\nDATABASE_NAME = rm_x  # Optional\r\nB = 2\r\n"
    )


def test_set_env_value_keeps_quotes_and_export():
    assert (
        set_env_value('export DATABASE_NAME="a"\n', "DATABASE_NAME", "rm_x")
        == 'export DATABASE_NAME="rm_x"\n'
    )


def test_set_env_value_appends_a_missing_key():
    assert (
        set_env_value("A=1\n", "DATABASE_NAME", "rm_x") == "A=1\nDATABASE_NAME = rm_x\n"
    )


def test_redis_index():
    assert redis_index("redis://localhost:6381/4") == 4
    assert redis_index("redis://localhost:6381") is None


def test_with_redis_index_keeps_host_and_port():
    assert with_redis_index("redis://localhost:6381/0", 4) == "redis://localhost:6381/4"


def test_free_redis_pair_skips_claimed_indexes():
    assert free_redis_pair({0, 1}) == (2, 3)
    assert free_redis_pair({0, 1, 2, 3}) == (4, 5)
    assert free_redis_pair({0, 1, 3}) == (4, 5)


def test_claimed_redis_indexes_read_every_env_with_the_settings_defaults():
    worktree = {
        "CACHE_REDIS": "redis://localhost:6381/4",
        "CELERY_BROKER": "redis://localhost:6381/5",
    }
    assert claimed_redis_indexes([worktree, {}]) == {0, 1, 4, 5}


def test_claimed_redis_indexes_follow_a_main_checkout_off_0_and_1():
    main = {
        "CACHE_REDIS": "redis://localhost:6381/2",
        "CELERY_BROKER": "redis://localhost:6381/3",
    }
    assert free_redis_pair(claimed_redis_indexes([main])) == (4, 5)


def test_no_free_pair_raises():
    with pytest.raises(RuntimeError):
        free_redis_pair(set(range(16)) - {15})


def test_prune_spares_main_e2e_and_test_databases():
    existing = [
        "request_manager_db",
        "request_manager_e2e",
        "test_rm_a",
        "rm_a",
        "rm_b",
        "postgres",
    ]
    assert stale_databases(existing, ["rm_a"]) == ["rm_b"]


@pytest.fixture
def repo(tmp_path, monkeypatch):
    root = (tmp_path / "repo").resolve()
    root.mkdir()
    empty_config = tmp_path / "gitconfig"
    empty_config.touch()
    # Neither the developer's git config (commit signing, hooks) nor a calling hook's
    # GIT_DIR / GIT_INDEX_FILE has a say in a throwaway repo.
    for key in [key for key in os.environ if key.startswith("GIT_")]:
        monkeypatch.delenv(key)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty_config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")

    def git(*args):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)

    git("init", "-q", "-b", "main")
    (root / "README.md").write_text("x\n")
    git("add", "README.md")
    git(
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@example.com",
        "commit",
        "-q",
        "-m",
        "init",
    )
    git("worktree", "add", "-q", "-b", "w", str(Path(".claude", "worktrees", "w")))
    return root


def test_main_checkout_is_none_at_the_root(repo):
    assert main_checkout_of(repo) is None


def test_main_checkout_from_inside_a_worktree(repo):
    assert main_checkout_of(repo / ".claude" / "worktrees" / "w").resolve() == repo


def test_worktree_root_from_a_nested_folder(repo):
    nested = repo / ".claude" / "worktrees" / "w" / "nested"
    nested.mkdir()
    assert worktree_root(nested).resolve() == repo / ".claude" / "worktrees" / "w"


def test_worktree_roots_lists_main_first(repo):
    assert [root.resolve() for root in worktree_roots(repo)] == [
        repo,
        repo / ".claude" / "worktrees" / "w",
    ]
