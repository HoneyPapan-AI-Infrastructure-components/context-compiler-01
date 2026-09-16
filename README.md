# Context Compiler

V0 foundation: clean Python project skeleton with a minimal passing
test suite. No retrieval, chunking, ranking, or compilation logic yet.

## Scope

- In scope: repository layout, packaging metadata, import sanity test.
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
  py.typed
tests/
  test_package.py
```

## Quickstart

Requires Python `>=3.10` and [`uv`](https://docs.astral.sh/uv/).

```bash
uv run --group dev pytest -q
```

## Status

V0 — skeleton only. `context_compiler` exposes `__version__` (`0.1.0`)
and nothing else.
