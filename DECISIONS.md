# Decisions

## V0 is local and deterministic

Context Compiler V0 runs locally and accepts a repository plus a task.

It produces a bounded context bundle.

## Python for V0

Python is used for prototype velocity and because the first version does not require infrastructure or high-throughput serving.

## CLI first

The core is interface-independent.

The CLI is the first adapter.

HTTP and MCP are future adapters after the core behavior is proven.

## Retrieval starts lexical

V0 uses filesystem discovery and lexical retrieval.

Semantic retrieval, embeddings, and model-assisted query expansion are deferred until simpler retrieval has been measured.

## No external infrastructure

V0 does not require a database, cache, vector store, hosted model, or external service.