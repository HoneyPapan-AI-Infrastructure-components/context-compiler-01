import os
from pathlib import Path

import pytest

from context_compiler import DiscoveredFile, discover_files


def test_discovers_nested_files(tmp_path: Path) -> None:
    (tmp_path / "top.txt").write_text("top")
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    (nested / "deep.txt").write_text("deep")
    found = discover_files(str(tmp_path))
    assert [item.path for item in found] == ["a/b/deep.txt", "top.txt"]


def test_records_file_size(tmp_path: Path) -> None:
    (tmp_path / "f.txt").write_text("hello world")
    assert discover_files(tmp_path) == [DiscoveredFile(path="f.txt", size=11)]


def test_excludes_default_directories(tmp_path: Path) -> None:
    for name in [
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        "dist",
        "build",
        "coverage",
        ".next",
        "target",
    ]:
        excluded = tmp_path / name
        excluded.mkdir()
        (excluded / "junk.txt").write_text("junk")
    (tmp_path / "keep.txt").write_text("keep")
    assert [item.path for item in discover_files(tmp_path)] == ["keep.txt"]


def test_excludes_directories_at_any_depth(tmp_path: Path) -> None:
    package = tmp_path / "src"
    package.mkdir()
    cache = package / "__pycache__"
    cache.mkdir()
    (cache / "cached.pyc").write_text("cached")
    (package / "mod.py").write_text("mod")
    assert [item.path for item in discover_files(tmp_path)] == ["src/mod.py"]


def test_discovers_file_named_like_excluded_directory(tmp_path: Path) -> None:
    (tmp_path / "build").write_text("x")
    assert discover_files(tmp_path) == [DiscoveredFile(path="build", size=1)]


def test_results_are_sorted_deterministically(tmp_path: Path) -> None:
    names = ["z.txt", "a.txt", "m.txt", "sub/b.txt", "sub/a.txt", "a/nested.txt"]
    for name in reversed(names):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(name)
    first = discover_files(tmp_path)
    second = discover_files(tmp_path)
    assert [item.path for item in first] == sorted(names)
    assert first == second


def test_paths_are_relative_posix(tmp_path: Path) -> None:
    deep = tmp_path / "a" / "b"
    deep.mkdir(parents=True)
    (deep / "deep.txt").write_text("deep")
    found = discover_files(tmp_path)
    assert found == [DiscoveredFile(path="a/b/deep.txt", size=4)]
    for item in found:
        assert not Path(item.path).is_absolute()
        assert "\\" not in item.path


def test_empty_repository_returns_empty_list(tmp_path: Path) -> None:
    assert discover_files(tmp_path) == []


def test_nonexistent_path_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        discover_files(tmp_path / "missing")


def test_file_path_raises(tmp_path: Path) -> None:
    target = tmp_path / "f.txt"
    target.write_text("x")
    with pytest.raises(NotADirectoryError):
        discover_files(target)


def test_internal_file_symlink_discovered(tmp_path: Path) -> None:
    real = tmp_path / "real.txt"
    real.write_text("data")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(real)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported")
    found = discover_files(tmp_path)
    assert [item.path for item in found] == ["link.txt", "real.txt"]
    assert {item.size for item in found} == {4}


def test_external_file_symlink_skipped(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside")
    try:
        (root / "link.txt").symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported")
    assert discover_files(root) == []


def test_directory_symlink_not_followed(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    real = tmp_path / "real"
    real.mkdir()
    (real / "secret.txt").write_text("secret")
    try:
        (root / "linked").symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported")
    assert discover_files(root) == []


def test_broken_symlink_skipped(tmp_path: Path) -> None:
    try:
        (tmp_path / "link.txt").symlink_to(tmp_path / "missing.txt")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported")
    assert discover_files(tmp_path) == []


def test_unreadable_directory_skipped(tmp_path: Path) -> None:
    if os.name != "posix":
        pytest.skip("posix permissions required")
    if os.geteuid() == 0:
        pytest.skip("root ignores permissions")
    locked = tmp_path / "locked"
    locked.mkdir()
    (locked / "hidden.txt").write_text("hidden")
    locked.chmod(0o000)
    try:
        assert discover_files(tmp_path) == []
    finally:
        locked.chmod(0o700)
