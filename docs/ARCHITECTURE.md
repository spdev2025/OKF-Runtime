# OKF Runtime

## Vision

OKF Runtime is a lightweight deterministic retrieval engine for the Open Knowledge Format (OKF) [spec.](../references/OKFmin.SPEC.md).

Unlike existing OKF tooling, which primarily focuses on authoring, enrichment, and validation, OKF Runtime focuses on efficient **consumption** of large OKF repositories by AI coding agents.

The runtime moves deterministic work out of the LLM, including:

- Repository discovery
- Bundle discovery
- Metadata extraction
- Metadata indexing
- Graph construction
- Link analysis
- Metadata querying
- Bundle composition

This allows AI agents to spend context and reasoning on understanding knowledge instead of locating and parsing it.

---

# Goals

## Primary Goals

- Deterministic retrieval
- Minimal token consumption
- Minimal dependencies
- Cross-platform portability
- Simple installation
- Agent-friendly APIs
- Community-driven FOSS project

## Non-goals

The runtime should **not** require:

- Database server (e.g.  DuckDB, Neo4j, Vector database )
- Docker
- Background daemon
- Cloud services

Everything should work anywhere Python 3.10+ runs.

---

# Core Principles

## 1. Deterministic Before AI

Whenever a problem can be solved deterministically, it should not consume LLM context or reasoning.

Examples:

- Finding bundles
- Reading YAML frontmatter
- Building backlinks
- Querying metadata
- Detecting broken links
- Building dependency graphs

The runtime performs these tasks.

The LLM performs reasoning.

---

## 2. Library First

The runtime is primarily a reusable library.

Everything else is built on top of it.

```
okf-runtime/
│
├── SKILL.md
├── README.md
├── LICENSE
├── pyproject.toml
│
├── okf_runtime/             # Python implementation
│
├── tests/                   # Runtime tests and fixtures
├── scripts/
│   └── okf.py               # Thin agent-facing CLI wrapper
├── references/              # Agent-facing, on-demand material
│   ├── USAGE.md
│   ├── OKFmin.SPEC.md
│   ├── OKF-Version-0.2-min.md
│   ├── OKF-SPEC-Version-0.2.md
│   ├── OKF-v0.2-SPEC-for-consumer-agent-context.md
│   ├── OKF-DELTA-0.1-to-0.2.md
│   └── SKILLminSPEC.md
└── docs/                    # Maintainer-facing documentation
    ├── ADR.md
    ├── ARCHITECTURE.md
    ├── CONTRIBUTING_GUIDE.md
    ├── IMPLEMENTATION_PLAN.md
    └── refactor.md
```

Business logic must never exist only inside the CLI or MCP layer.

---

## 3. Filesystem Is The Source of Truth

Markdown files remain authoritative.

The runtime never mutates source bundles.

Caches are disposable.

Deleting `.cache/` must never lose information.

---

## 4. Zero Infrastructure

The runtime should require no installation beyond Python.

Optional enhancements may exist later but must never become mandatory.

---

## 5. Progressive Enhancement

Features should be layered.

```
Filesystem

↓

Runtime Library

↓

CLI

↓

SKILL.md

↓

(optional)

MCP

↓

(optional)

Semantic Search
```

Users should only pay complexity for features they use.

---

# Architecture

```
Repository

↓

Bundle Discovery

↓

Filesystem Scanner

↓

Markdown Parser

↓

YAML Frontmatter Parser

↓

Metadata Model

↓

Graph Builder

↓

Runtime API

↓

CLI

↓

(optional)

MCP
```

---

# Runtime Components

## Scanner

Responsible for:

- discovering bundles
- locating markdown files
- excluding runtime artifacts
- incremental change detection

Inputs

Filesystem

Outputs

List of markdown documents

---

## Parser

Responsible for

- parsing frontmatter
- validating YAML
- extracting markdown body
- extracting links
- extracting anchors

Produces deterministic document objects.

---

## Metadata

Provides:

- catalog
- metadata index
- tag index
- type index

Supports deterministic queries without loading markdown bodies.

---

## Graph

Builds

- forward links
- reverse links
- neighborhoods
- dependency graph

Graph construction is deterministic.

---

## Cache

Provides lightweight acceleration.

Example

```
.cache/

metadata.json

links.json

reverse_links.json

hashes.json
```

Cache may be regenerated at any time.

---

## Compose

Creates temporary OKF bundles from deterministic graph traversal.

Responsibilities

- topic composition
- dependency inclusion
- context reduction
- boundary reporting

Compose must never modify source files.

---

## Lint

Quality assurance only.

Examples

- broken links
- broken anchors
- orphan documents
- unreachable documents
- duplicate identifiers

Linting extends beyond strict OKF conformance.

---

# Public Python API

The runtime exposes a stable Python API.

Example

```python
from okf_runtime import (
    discover,
    catalog,
    query,
    show,
    graph,
    compose,
    lint_links,
)
```

The CLI simply wraps these functions.

The MCP server will wrap the same API.

---

# CLI Design

The CLI should remain thin.

Example

```
okf discover

okf catalog

okf query type=Concept

okf graph oauth

okf compose authentication

okf lint-links
```

The CLI contains no business logic.

---

# Cache Strategy

Phase 1

- modification timestamps

Phase 2

- content hashes

Phase 3

- incremental rebuilds

No database is required.

---

# Dependency Philosophy

Preferred

- Standard Library
- PyYAML

Avoid large dependency trees.

New dependencies should provide substantial value before being accepted.

---

# Borrowed Ideas

The project intentionally synthesizes ideas from multiple existing implementations.

## OKF_Studio_EGT

Borrow

- repository traversal
- link validation
- anchor validation
- documentation QA

## scaccogatto/okf-skills

Borrow

- modular Skill organization
- validator architecture
- visualization concepts

## fabricioctelles/skills

Borrow

- SKILL.md conventions
- progressive documentation

## okfcli

Borrow

- JSON-first CLI philosophy
- runtime commands
- graph operations

## OKFy

Borrow

- runtime retrieval
- MCP integration patterns

## Hermes OKF

Borrow

- runtime command design

## R OKF Package

Borrow

- deterministic ingestion
- graph construction
- metadata extraction

---

# Roadmap

## Phase 1

Deterministic runtime

- Scanner
- Parser
- Metadata
- Graph
- Cache
- CLI

## Phase 2

Performance

- Incremental indexing
- Parallel scanning
- File watching

## Phase 3

Optional MCP

MCP should only expose existing Runtime APIs.

No duplicated logic.

## Phase 4

Optional semantic search

- Embeddings
- Hybrid retrieval

Remain optional.

---

# Success Criteria

The project succeeds if it becomes:

- the usefull runtime implementation for OKF
- installable in seconds
- usable by any Python-based coding agent
- dependency-light
- deterministic
- extensible
- easy for the community to contribute to

Validation tools already exist.

Authoring tools already exist.

OKF Runtime aims to provide the missing deterministic **consumer/runtime layer** for the OKF ecosystem.
