# Context Compiler

V0 foundation: clean Python project with filesystem discovery and a
passing test suite. No lexical retrieval, chunking, ranking, or
compilation logic yet.

## Scope

- In scope: repository layout, packaging metadata, filesystem
  discovery (`discover_files`), import sanity tests.
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
  py.typed
tests/
  test_discovery.py
  test_package.py
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

## Quickstart

Requires Python `>=3.10` and [`uv`](https://docs.astral.sh/uv/).

```bash
uv run --group dev pytest -q
```

## Status

V0 — filesystem discovery only. `context_compiler` exposes
`__version__` (`0.1.0`), `DiscoveredFile`, and `discover_files`.
