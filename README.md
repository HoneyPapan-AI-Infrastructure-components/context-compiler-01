# Context Compiler

V0 foundation: clean Python project with filesystem discovery,
deterministic lexical retrieval, and a passing test suite. No
chunking, compilation logic, or infrastructure yet.

## Scope

- In scope: repository layout, packaging metadata, filesystem
  discovery (`discover_files`), deterministic lexical retrieval
  (`retrieve_files`), import sanity tests.
- Out of scope: LLMs, embeddings, vector databases, Redis, Postgres,
  HTTP servers/clients, MCP, or any other infrastructure.
- No application dependencies. Standard library only.

See `AGENTS.md` for contributor rules and `DECISIONS.md` for the
decision log.

## Layout

```text
AGENTS.md
README.md
DECISIONS.md
pyproject.toml
src/context_compiler/
  __init__.py
  discovery.py
  retrieval.py
  py.typed
tests/
  test_discovery.py
  test_package.py
  test_retrieval.py
```

## Discovery

`discover_files(root)` walks a repository and returns
`DiscoveredFile` entries (`path`, `size`) with repository-relative
POSIX paths in stable sorted order. Generated and infrastructure
directories (`.git`, `node_modules`, `.venv`, `venv`,
`__pycache__`, `dist`, `build`, `coverage`, `.next`, `target`) are
pruned during traversal.

Error contract: a nonexistent path raises `FileNotFoundError`; a file
path raises `NotADirectoryError`; any I/O error encountered during
traversal (for example an unreadable directory) propagates as
`OSError`. Discovery never returns partial results silently.

Symlink contract: directory symlinks are never followed or emitted;
file symlinks resolving outside the repository are skipped; broken
symlinks and symlink loops are skipped; an internal file symlink is
emitted under the symlink path with the target's size.

```python
from context_compiler import discover_files

for item in discover_files("/path/to/repo"):
    print(item.path, item.size)
```

## Retrieval

`retrieve_files(root, query, files, limit=10)` scores previously
discovered files against a query and returns `RankedFile` entries
(`path`, `score`) with repository-relative POSIX paths.

Tokenization: text is lowercased, then every `[a-z0-9]+` run is a
token. This splits punctuation, whitespace, path separators, dots,
underscores, and hyphens, so `src/auth_helpers.py` tokenizes to
`src`, `auth`, `helpers`, `py`.

Ranking signals, per unique query token: term frequency in file
content plus twice the term frequency in the repository-relative
path. Repeated query terms are deduplicated. Only files with a
positive score are returned, ordered by descending score with ties
broken by ascending path. Output is deterministic for identical
repository and query input regardless of input file order.

`limit` bounds the result count (`None` is unbounded, `0` returns
an empty list, negative raises `ValueError`). Empty, blank, or
punctuation-only queries return an empty list.

Retrieval only scores the `files` it is given and never walks the
filesystem itself, so excluded directories stay excluded as long as
callers pass `discover_files` output through.

Error contract: any I/O error while reading file content
propagates as `OSError` (stale or missing entries raise
`FileNotFoundError`); retrieval never skips an unreadable file
silently. Entries must use repository-relative paths as produced
by `discover_files`: absolute paths, paths resolving outside the
root, and symlinks escaping the root raise `ValueError` before
any content is read. Files that are not valid UTF-8 contribute
path matches only. A non-string query raises `TypeError`.

```python
from context_compiler import discover_files, retrieve_files

files = discover_files("/path/to/repo")
for item in retrieve_files("/path/to/repo", "authenticate login", files):
    print(item.path, item.score)
```

## Quickstart

Requires Python `>=3.10` and [`uv`](https://docs.astral.sh/uv/).

```bash
uv run --group dev pytest -q
```

## Status

V0 — filesystem discovery plus lexical retrieval.
`context_compiler` exposes `__version__` (`0.1.0`),
`DiscoveredFile`, `discover_files`, `RankedFile`,
`retrieve_files`, and `tokenize`.
