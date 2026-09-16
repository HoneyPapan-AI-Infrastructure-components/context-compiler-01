import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Union

from context_compiler.discovery import DiscoveredFile


@dataclass(frozen=True)
class RankedFile:
    path: str
    score: int


_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

_PATH_WEIGHT = 2


def tokenize(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.lower())


def retrieve_files(
    root: Union[str, Path],
    query: str,
    files: Sequence[DiscoveredFile],
    limit: Union[int, None] = 10,
) -> list[RankedFile]:
    if not isinstance(query, str):
        raise TypeError(query)
    if limit is not None and limit < 0:
        raise ValueError(limit)
    terms = set(tokenize(query))
    if not terms or not files or limit == 0:
        return []
    resolved_root = Path(root).resolve()
    scored = _score_all(resolved_root, files, terms)
    scored.sort(key=lambda entry: (-entry.score, entry.path))
    if limit is None:
        return scored
    return scored[:limit]


def _score_all(
    resolved_root: Path, files: Sequence[DiscoveredFile], terms: set[str]
) -> list[RankedFile]:
    scored: list[RankedFile] = []
    for item in files:
        score = _score_file(resolved_root, item.path, terms)
        if score > 0:
            scored.append(RankedFile(path=item.path, score=score))
    return scored


def _score_file(resolved_root: Path, relative: str, terms: set[str]) -> int:
    path_counts = Counter(tokenize(relative))
    content_counts = Counter(tokenize(_read_text(resolved_root, relative)))
    return sum(
        content_counts.get(term, 0) + _PATH_WEIGHT * path_counts.get(term, 0)
        for term in terms
    )


def _read_text(resolved_root: Path, relative: str) -> str:
    data = _resolve_within_root(resolved_root, relative).read_bytes()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return ""


def _resolve_within_root(resolved_root: Path, relative: str) -> Path:
    if Path(relative).is_absolute():
        raise ValueError(relative)
    target = (resolved_root / relative).resolve()
    if not target.is_relative_to(resolved_root):
        raise ValueError(relative)
    return target
