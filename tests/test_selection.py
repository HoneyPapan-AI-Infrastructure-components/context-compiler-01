import copy

import pytest

from context_compiler import DiscoveredFile, RankedFile, select_files


def _ranked(paths: list[str]) -> list[RankedFile]:
    return [RankedFile(path=path, score=len(paths) - index) for index, path in enumerate(paths)]


def test_selects_highest_ranked_first() -> None:
    ranked = _ranked(["a.txt", "b.txt", "c.txt"])
    files = [
        DiscoveredFile(path="a.txt", size=10),
        DiscoveredFile(path="b.txt", size=10),
        DiscoveredFile(path="c.txt", size=10),
    ]
    selected = select_files(ranked, files, 20)
    assert selected.paths == ("a.txt", "b.txt")
    assert selected.total_size == 20


def test_exact_budget_fit() -> None:
    ranked = _ranked(["a.txt", "b.txt"])
    files = [
        DiscoveredFile(path="a.txt", size=30),
        DiscoveredFile(path="b.txt", size=70),
    ]
    selected = select_files(ranked, files, 100)
    assert selected.paths == ("a.txt", "b.txt")
    assert selected.total_size == 100


def test_skips_oversized_and_selects_later() -> None:
    ranked = _ranked(["big.txt", "small.txt", "tiny.txt"])
    files = [
        DiscoveredFile(path="big.txt", size=90),
        DiscoveredFile(path="small.txt", size=20),
        DiscoveredFile(path="tiny.txt", size=10),
    ]
    selected = select_files(ranked, files, 50)
    assert selected.paths == ("small.txt", "tiny.txt")
    assert selected.total_size == 30


def test_zero_budget_returns_empty() -> None:
    ranked = _ranked(["a.txt"])
    files = [DiscoveredFile(path="a.txt", size=10)]
    selected = select_files(ranked, files, 0)
    assert selected.paths == ()
    assert selected.total_size == 0


def test_negative_budget_raises() -> None:
    ranked = _ranked(["a.txt"])
    files = [DiscoveredFile(path="a.txt", size=10)]
    with pytest.raises(ValueError):
        select_files(ranked, files, -1)


def test_empty_ranked_returns_empty() -> None:
    files = [DiscoveredFile(path="a.txt", size=10)]
    selected = select_files([], files, 100)
    assert selected.paths == ()
    assert selected.total_size == 0


def test_missing_discovered_entry_ignored() -> None:
    ranked = _ranked(["missing.txt", "a.txt"])
    files = [DiscoveredFile(path="a.txt", size=10)]
    selected = select_files(ranked, files, 100)
    assert selected.paths == ("a.txt",)
    assert selected.total_size == 10


def test_duplicate_ranked_paths_selected_once() -> None:
    ranked = [
        RankedFile(path="a.txt", score=3),
        RankedFile(path="a.txt", score=2),
        RankedFile(path="b.txt", score=1),
    ]
    files = [
        DiscoveredFile(path="a.txt", size=10),
        DiscoveredFile(path="b.txt", size=10),
    ]
    selected = select_files(ranked, files, 100)
    assert selected.paths == ("a.txt", "b.txt")
    assert selected.total_size == 20


def test_output_is_deterministic() -> None:
    ranked = _ranked(["b.txt", "a.txt", "c.txt"])
    files = [
        DiscoveredFile(path="a.txt", size=10),
        DiscoveredFile(path="b.txt", size=10),
        DiscoveredFile(path="c.txt", size=10),
    ]
    first = select_files(ranked, files, 20)
    second = select_files(list(ranked), list(reversed(files)), 20)
    assert first == second
    assert first.paths == ("b.txt", "a.txt")


def test_total_size_never_exceeds_budget() -> None:
    ranked = _ranked(["a.txt", "b.txt", "c.txt", "d.txt"])
    files = [
        DiscoveredFile(path="a.txt", size=40),
        DiscoveredFile(path="b.txt", size=40),
        DiscoveredFile(path="c.txt", size=40),
        DiscoveredFile(path="d.txt", size=5),
    ]
    for budget in [0, 1, 39, 40, 79, 80, 85, 200]:
        selected = select_files(ranked, files, budget)
        assert selected.total_size <= budget
        assert selected.total_size == sum(
            next(item.size for item in files if item.path == path)
            for path in selected.paths
        )


def test_caller_inputs_not_mutated() -> None:
    ranked = _ranked(["a.txt", "b.txt", "missing.txt"])
    files = [
        DiscoveredFile(path="a.txt", size=10),
        DiscoveredFile(path="b.txt", size=10),
    ]
    ranked_snapshot = copy.deepcopy(ranked)
    files_snapshot = copy.deepcopy(files)
    select_files(ranked, files, 15)
    assert ranked == ranked_snapshot
    assert files == files_snapshot
