
---

## `IMPLEMENTATION_PLAN.md`

```markdown
# Implementation Plan

## Phase 1

Goal

Deterministic runtime.

Deliverables

- filesystem scanner
- bundle discovery
- YAML extraction
- metadata cache
- graph construction
- CLI

Commands

discover

catalog

query

show

links

backlinks

graph

compose

lint-links

Acceptance Criteria

✓ Runs on Python 3.10+

✓ Uses only lightweight dependencies

✓ No database

✓ No daemon

✓ Cache rebuilt automatically

✓ All commands produce JSON

✓ YAML output for CLI

---

## Phase 2

Performance

- incremental indexing

- parallel scanning

- file watching

- content hashing

---

## Phase 3

MCP

Only wraps existing Runtime API.

No duplicated logic.

---

## Phase 4

Optional semantic search

Embeddings

Hybrid retrieval

Must remain optional.

---

## Testing

pytest

Unit tests

Golden-file tests

Performance benchmarks

Cross-platform CI

---

## Borrow From Existing Projects

OKF_Studio_EGT

- link validation
- anchor validation

scaccogatto

- modular Skills

okfcli

- CLI UX

R OKF

- ingestion

OKFy

- runtime retrieval

Hermes

- runtime commands

---

## Code Quality

Type hints

Dataclasses

Logging

Docstrings

Small modules

Dependency injection where useful

No global state

90%+ test coverage
