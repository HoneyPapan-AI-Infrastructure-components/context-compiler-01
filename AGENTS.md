# Context Compiler

## Goal

Build a deterministic local system that compiles a repository and task into a bounded context bundle.

## Development

Prefer the smallest implementation that satisfies the current requirement.

Keep the core independent of CLI, HTTP, MCP, and model providers.

Do not add infrastructure before the current retrieval capability requires it.

Write tests for externally observable behavior and important invariants.

Keep behavior deterministic.

Do not add explanatory comments. Use clear names and small functions instead.

Run the relevant tests before considering a change complete.

## Workflow

Read the existing code before changing it.

Trace consumers before changing boundary contracts.

Make one logical change at a time.

Do not modify unrelated files.