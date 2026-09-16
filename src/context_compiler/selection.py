from collections.abc import Sequence
from dataclasses import dataclass

from context_compiler.discovery import DiscoveredFile
from context_compiler.retrieval import RankedFile


@dataclass(frozen=True)
class SelectedContext:
    paths: tuple[str, ...]
    total_size: int


def select_files(
    ranked: Sequence[RankedFile],
    files: Sequence[DiscoveredFile],
    budget: int,
) -> SelectedContext:
    if budget < 0:
        raise ValueError(budget)
    if budget == 0 or len(ranked) == 0:
        return SelectedContext(paths=(), total_size=0)
    sizes = _sizes_by_path(files)
    seen: set[str] = set()
    chosen: list[str] = []
    total = 0
    remaining = budget
    for entry in ranked:
        if entry.path in seen:
            continue
        seen.add(entry.path)
        size = sizes.get(entry.path)
        if size is None:
            continue
        if size <= remaining:
            chosen.append(entry.path)
            total += size
            remaining -= size
    return SelectedContext(paths=tuple(chosen), total_size=total)


def _sizes_by_path(files: Sequence[DiscoveredFile]) -> dict[str, int]:
    sizes: dict[str, int] = {}
    for item in files:
        sizes[item.path] = item.size
    return sizes
