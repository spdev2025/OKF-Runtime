# Architecture Decision Records (ADR)

This directory records significant architectural decisions made during the development of OKF Runtime.

## Purpose

Architectural decisions often appear obvious when they are made but become less clear as a project evolves and new contributors join.

This repository records the reasoning behind major design choices so contributors understand not only **what** was decided, but **why**.

Unless superseded by a later ADR, these decisions represent the project's architectural direction.

---

# Status Values

- Proposed
- Accepted
- Superseded
- Deprecated

---

# ADR Index

| ADR | Title | Status |
|------|-------|--------|
| 0001 | Project Vision | Accepted |
| 0002 | Library First Architecture | Accepted |
| 0003 | Zero Infrastructure | Accepted |
| 0004 | Python First | Accepted |
| 0005 | Filesystem Is Source of Truth | Accepted |
| 0006 | Disposable Cache | Accepted |
| 0007 | Deterministic Runtime | Accepted |
| 0008 | SKILL.md Compatibility | Accepted |
| 0009 | MCP Is Optional | Accepted |
| 0010 | Progressive Enhancement | Accepted |

---

# ADR-0001 Project Vision

## Status

Accepted

## Decision

OKF Runtime will focus on deterministic retrieval and runtime operations for Open Knowledge Format repositories.

It will intentionally **not** compete with authoring or validation tools.

## Rationale

Current OKF tooling already provides:

- authoring
- enrichment
- validation

The missing capability is efficient runtime consumption.

The runtime should reduce LLM token consumption by moving deterministic operations outside the model.

---

# ADR-0002 Library First

## Status

Accepted

## Decision

The Python library is the primary product.

CLI, SKILL.md and MCP are wrappers.

```
Python Library

↓

CLI

↓

Skill

↓

MCP
```

## Rationale

Avoid duplicated implementations.

Ensure all interfaces expose identical functionality.

Simplify testing.

---

# ADR-0003 Zero Infrastructure

## Status

Accepted

## Decision

No mandatory external infrastructure.


## Rationale

The project should work immediately on any machine running Python.

Most OKF repositories are sufficiently small that filesystem scanning is fast enough.

Optional integrations may be added later.

---

# ADR-0004 Python First

## Status

Accepted

## Decision

The reference implementation is Python.

## Rationale

Python is available in nearly every AI coding environment.

Future ports (Node, Go, Rust) are welcome but secondary, Node could be next on roadmap/sugested for contributors.

---

# ADR-0005 Filesystem Is Source of Truth

## Status

Accepted

## Decision

Markdown files remain authoritative.

Caches are derived artifacts.

The runtime never modifies source bundles.

## Consequences

Deleting `.cache/` must never lose information.

---

# ADR-0006 Disposable Cache

## Status

Accepted

## Decision

Cache files are regenerated automatically.

Phase 1 uses modification timestamps.

Future versions may introduce content hashing.

## Rationale

Simple.

Reliable.

No database migration required.

---

# ADR-0007 Deterministic Runtime

## Status

Accepted

## Decision

Deterministic algorithms should replace LLM reasoning whenever possible.

Examples include:

- metadata extraction
- graph construction
- querying
- bundle discovery
- reverse link generation
- composition

## Rationale

LLMs should reason about knowledge rather than parse or search it.

---

# ADR-0008 SKILL.md Compatibility

## Status

Accepted

## Decision

The project follows the Agent Skills directory layout.

```
SKILL.md

scripts/

references/
```

Python implementation remains reusable as a standard library package.

Scripts should be thin wrappers around the runtime API.

## Rationale

Compatibility with Claude Code, Codex, Cursor, Gemini CLI and other Skill-compatible agents while preserving software engineering best practices.

---

# ADR-0009 Optional MCP

## Status

Accepted

## Decision

MCP support is optional.

The runtime must not depend on MCP.

Future MCP implementations simply expose the Runtime API.

## Rationale

MCP is a transport protocol, not business logic.

Keeping MCP optional reduces complexity and improves portability.

---

# ADR-0010 Progressive Enhancement

## Status

Accepted

## Decision

Features are layered.

```
Filesystem

↓

Runtime

↓

CLI

↓

Skill

↓

MCP

↓

Semantic Search
```

Each layer depends only on the layers below.

## Rationale

Users should only pay the complexity cost for the features they actually use.

This also makes long-term maintenance significantly easier.

---

# Future ADR Candidates

Potential future decisions include:

- SQLite vs JSON cache
- Content hashing strategy
- Incremental indexing
- Plugin architecture
- Semantic search
- Embedding providers
- Cross-repository discovery
- Parallel scanning
- Python API stability policy
- Versioning strategy
- Extension mechanism
- Bundle composition algorithm
- Graph traversal heuristics
- Query language design