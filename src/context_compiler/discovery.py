from dataclasses import dataclass
from os import DirEntry, scandir
from pathlib import Path
from typing import Union


@dataclass(frozen=True)
class DiscoveredFile:
    path: str
    size: int


_EXCLUDED_DIRECTORIES = frozenset(
    {
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
    }
)


def discover_files(root: Union[str, Path]) -> list[DiscoveredFile]:
    resolved_root = Path(root).resolve()
    if not resolved_root.exists():
        raise FileNotFoundError(resolved_root)
    if not resolved_root.is_dir():
        raise NotADirectoryError(resolved_root)
    found: list[DiscoveredFile] = []
    _collect(resolved_root, resolved_root, "", found)
    found.sort(key=lambda item: item.path)
    return found


def _collect(resolved_root: Path, directory: Path, prefix: str, found: list[DiscoveredFile]) -> None:
    try:
        entries = sorted(scandir(directory), key=lambda entry: entry.name)
    except OSError:
        return
    for entry in entries:
        try:
            _collect_entry(resolved_root, entry, prefix, found)
        except (OSError, RuntimeError):
            continue


def _collect_entry(resolved_root: Path, entry: DirEntry[str], prefix: str, found: list[DiscoveredFile]) -> None:
    name = entry.name
    relative = prefix + "/" + name if prefix else name
    if entry.is_symlink():
        _collect_symlink(resolved_root, entry, relative, found)
        return
    if entry.is_dir(follow_symlinks=False):
        if name not in _EXCLUDED_DIRECTORIES:
            _collect(resolved_root, Path(entry.path), relative, found)
        return
    if entry.is_file(follow_symlinks=False):
        found.append(DiscoveredFile(path=relative, size=entry.stat(follow_symlinks=False).st_size))


def _collect_symlink(resolved_root: Path, entry: DirEntry[str], relative: str, found: list[DiscoveredFile]) -> None:
    target = Path(entry.path).resolve()
    if target.is_dir():
        return
    if not target.is_relative_to(resolved_root):
        return
    if not target.is_file():
        return
    found.append(DiscoveredFile(path=relative, size=target.stat().st_size))
