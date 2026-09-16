import os
from pathlib import Path

import pytest

from context_compiler import (
    DiscoveredFile,
    RankedFile,
    discover_files,
    retrieve_files,
    tokenize,
)


def _write(root: Path, relative: str, content: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)


def _discovered(root: Path) -> list[DiscoveredFile]:
    return discover_files(root)


def test_empty_query_returns_empty(tmp_path: Path) -> None:
    _write(tmp_path, "a.txt", "hello world")
    assert retrieve_files(tmp_path, "", _discovered(tmp_path)) == []


def test_blank_and_punctuation_queries_return_empty(tmp_path: Path) -> None:
    _write(tmp_path, "a.txt", "hello world")
    files = _discovered(tmp_path)
    assert retrieve_files(tmp_path, "   ", files) == []
    assert retrieve_files(tmp_path, "!!! ... ,,,", files) == []


def test_no_matches_returns_empty(tmp_path: Path) -> None:
    _write(tmp_path, "a.txt", "hello world")
    assert retrieve_files(tmp_path, "zebra", _discovered(tmp_path)) == []


def test_repeated_query_terms_match_single_occurrence(tmp_path: Path) -> None:
    _write(tmp_path, "a.txt", "auth login")
    _write(tmp_path, "b.txt", "nothing relevant here")
    files = _discovered(tmp_path)
    assert retrieve_files(tmp_path, "auth auth auth", files) == retrieve_files(
        tmp_path, "auth", files
    )


def test_repeated_content_terms_rank_higher(tmp_path: Path) -> None:
    _write(tmp_path, "once.txt", "auth overview")
    _write(tmp_path, "often.txt", "auth auth auth auth")
    ranked = retrieve_files(tmp_path, "auth", _discovered(tmp_path))
    assert [item.path for item in ranked] == ["often.txt", "once.txt"]
    assert ranked[0].score > ranked[1].score


def test_content_match_outranks_path_only_match(tmp_path: Path) -> None:
    _write(tmp_path, "auth.txt", "nothing relevant here")
    _write(tmp_path, "notes.txt", "auth auth auth")
    ranked = retrieve_files(tmp_path, "auth", _discovered(tmp_path))
    assert [item.path for item in ranked] == ["notes.txt", "auth.txt"]


def test_path_match_returned_for_empty_file(tmp_path: Path) -> None:
    _write(tmp_path, "auth.txt", "")
    ranked = retrieve_files(tmp_path, "auth", _discovered(tmp_path))
    assert ranked == [RankedFile(path="auth.txt", score=2)]


def test_ties_broken_by_path(tmp_path: Path) -> None:
    _write(tmp_path, "b.txt", "auth")
    _write(tmp_path, "a.txt", "auth")
    ranked = retrieve_files(tmp_path, "auth", _discovered(tmp_path))
    assert ranked == [
        RankedFile(path="a.txt", score=1),
        RankedFile(path="b.txt", score=1),
    ]


def test_ordering_is_deterministic(tmp_path: Path) -> None:
    _write(tmp_path, "c.txt", "auth beta")
    _write(tmp_path, "a.txt", "auth beta")
    _write(tmp_path, "b.txt", "auth auth beta")
    files = _discovered(tmp_path)
    first = retrieve_files(tmp_path, "auth beta", files)
    second = retrieve_files(tmp_path, "auth beta", list(reversed(files)))
    assert first == second
    assert [item.path for item in first] == ["b.txt", "a.txt", "c.txt"]


def test_matching_is_case_insensitive(tmp_path: Path) -> None:
    _write(tmp_path, "a.txt", "Authentication HELPERS")
    files = _discovered(tmp_path)
    assert retrieve_files(tmp_path, "authentication", files) != []
    assert retrieve_files(tmp_path, "AUTHENTICATION", files) == retrieve_files(
        tmp_path, "authentication", files
    )


def test_punctuation_in_query_and_content(tmp_path: Path) -> None:
    _write(tmp_path, "src/get_user.py", "def get_user(user_id):\n    return user_id\n")
    files = _discovered(tmp_path)
    assert [item.path for item in retrieve_files(tmp_path, "get_user", files)] == [
        "src/get_user.py"
    ]
    assert retrieve_files(tmp_path, "get-user", files) == retrieve_files(
        tmp_path, "get user", files
    )
    assert [item.path for item in retrieve_files(tmp_path, "user_id", files)] == [
        "src/get_user.py"
    ]


def test_python_source_file_retrieved(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "src/auth.py",
        "def authenticate(user, password):\n    token = login(user, password)\n    return token\n",
    )
    _write(tmp_path, "src/billing.py", "def charge(invoice):\n    return invoice.total\n")
    ranked = retrieve_files(tmp_path, "authenticate login token", _discovered(tmp_path))
    assert [item.path for item in ranked] == ["src/auth.py"]


def test_markdown_text_file_retrieved(tmp_path: Path) -> None:
    _write(tmp_path, "docs/deploy.md", "# Deploy\n\nRun the release checklist before deploy.\n")
    _write(tmp_path, "docs/cooking.md", "# Cooking\n\nRecipes and ingredients.\n")
    ranked = retrieve_files(tmp_path, "deploy release checklist", _discovered(tmp_path))
    assert [item.path for item in ranked] == ["docs/deploy.md"]


def test_limit_bounds_result_count(tmp_path: Path) -> None:
    for name in ["a.txt", "b.txt", "c.txt"]:
        _write(tmp_path, name, "auth")
    files = _discovered(tmp_path)
    assert [item.path for item in retrieve_files(tmp_path, "auth", files, limit=2)] == [
        "a.txt",
        "b.txt",
    ]
    assert len(retrieve_files(tmp_path, "auth", files, limit=None)) == 3
    assert retrieve_files(tmp_path, "auth", files, limit=0) == []


def test_negative_limit_raises(tmp_path: Path) -> None:
    _write(tmp_path, "a.txt", "auth")
    with pytest.raises(ValueError):
        retrieve_files(tmp_path, "auth", _discovered(tmp_path), limit=-1)


def test_tokenize_splits_paths_and_code() -> None:
    assert tokenize("src/Auth-Helpers.PY") == ["src", "auth", "helpers", "py"]
    assert tokenize("get_user(user_id)") == ["get", "user", "user", "id"]
    assert tokenize("Hello, World!") == ["hello", "world"]
    assert tokenize("") == []
    assert tokenize("!!!") == []


def test_non_string_query_raises() -> None:
    with pytest.raises(TypeError):
        retrieve_files(".", None, [])  # type: ignore[arg-type]


def test_missing_file_raises(tmp_path: Path) -> None:
    stale = [DiscoveredFile(path="gone.txt", size=0)]
    with pytest.raises(OSError):
        retrieve_files(tmp_path, "auth", stale)


def test_non_utf8_file_scores_path_only(tmp_path: Path) -> None:
    target = tmp_path / "auth.bin"
    target.write_bytes(b"\xff\xfe\x00auth\x01\x02")
    _write(tmp_path, "plain.txt", "nothing relevant")
    files = _discovered(tmp_path)
    assert [item.path for item in retrieve_files(tmp_path, "auth", files)] == [
        "auth.bin"
    ]


def test_unreadable_file_raises(tmp_path: Path) -> None:
    if os.name != "posix":
        pytest.skip("posix permissions required")
    if os.geteuid() == 0:
        pytest.skip("root ignores permissions")
    target = tmp_path / "secret.txt"
    target.write_text("auth secrets")
    target.chmod(0o000)
    try:
        with pytest.raises(OSError):
            retrieve_files(tmp_path, "auth", _discovered(tmp_path))
    finally:
        target.chmod(0o600)


def test_files_outside_discovered_list_are_ignored(tmp_path: Path) -> None:
    hidden = tmp_path / ".git"
    hidden.mkdir()
    (hidden / "hidden.txt").write_text("auth auth auth")
    _write(tmp_path, "visible.txt", "nothing relevant here")
    files = [item for item in _discovered(tmp_path) if item.path != ".git/hidden.txt"]
    assert [item.path for item in files] == ["visible.txt"]
    assert retrieve_files(tmp_path, "auth", files) == []


def test_untracked_file_not_in_discovered_list_is_ignored(tmp_path: Path) -> None:
    _write(tmp_path, "indexed.txt", "nothing relevant")
    _write(tmp_path, "unindexed.txt", "auth auth auth")
    files = [item for item in _discovered(tmp_path) if item.path == "indexed.txt"]
    assert retrieve_files(tmp_path, "auth", files) == []


def test_paths_are_preserved_posix(tmp_path: Path) -> None:
    deep = tmp_path / "a" / "b"
    deep.mkdir(parents=True)
    (deep / "notes.txt").write_text("auth notes")
    ranked = retrieve_files(tmp_path, "auth", _discovered(tmp_path))
    assert [item.path for item in ranked] == ["a/b/notes.txt"]
    for item in ranked:
        assert not Path(item.path).is_absolute()
        assert "\\" not in item.path


def test_scores_exposed_and_sorted(tmp_path: Path) -> None:
    _write(tmp_path, "a.txt", "auth auth")
    _write(tmp_path, "b.txt", "auth")
    ranked = retrieve_files(tmp_path, "auth", _discovered(tmp_path))
    assert all(isinstance(item.score, int) and item.score > 0 for item in ranked)
    assert [item.score for item in ranked] == sorted(
        [item.score for item in ranked], reverse=True
    )


def test_end_to_end_discover_then_retrieve(tmp_path: Path) -> None:
    _write(tmp_path, "src/auth.py", "def authenticate(user):\n    return login(user)\n")
    _write(tmp_path, "README.md", "# Project\n\nGeneral overview.\n")
    files = discover_files(tmp_path)
    assert [item.path for item in files] == ["README.md", "src/auth.py"]
    ranked = retrieve_files(tmp_path, "authenticate login", files)
    assert [item.path for item in ranked] == ["src/auth.py"]
