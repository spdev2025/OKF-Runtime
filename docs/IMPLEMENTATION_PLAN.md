
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

## Phase 1.5 — Trust Signals (OKF Spec v0.2 §5–§7, §11–§13)

Goal

Bring the runtime up to the OKF v0.2 spec surface for provenance, trust,
lifecycle, and actor conventions, without touching Phase 2+ performance
or Phase 3 MCP concerns. Everything builds on the existing Phase 1
scanner → parser → metadata → CLI pipeline.

Deliverables

### 1. Nested YAML parser (indented mappings + list-of-dicts)

Extend `parser.parse_frontmatter()` to handle:
- **Indented scalar mappings**: `generated: { by: …, at: … }` (already
  inlined) and the block-style equivalent with indented `by:` / `at:` lines.
- **List-of-dicts**: `verified` as a YAML list where each `- { by, at }`
  item is a mapping, plus the single-mapping shorthand (§5.2).
- **Nested list-of-dicts**: `sources` entries with per-source credibility
  signals (`author`, `usage_count`, `last_modified`) and sibling
  `usage_window` (§5.1).
- **Nested mappings**: `executor: { resource, receipt }` and
  `attester: { resource }` (§10.2).

The parser remains dependency-free (no PyYAML) and handles precisely the
subset described in the spec.

File: `okf_runtime/parser.py`

### 2. TrustSignals dataclass

A frozen dataclass that holds the trust surface of a concept:

```
@dataclass(frozen=True)
class TrustSignals:
    generated: ActorEvent | None
    verified: list[ActorEvent]
    status: str           # "draft" | "stable" | "deprecated"; default "stable"
    stale_after: str | None  # YYYY-MM-DD
    sources: list[Source]
    usage_window: dict[str, str] | None

    @property
    def trust_tier(self) -> str:
        # §5.3: unverified → machine-confirmed → human-reviewed

    @property
    def is_stale(self) -> bool:
        # §5.5: today >= stale_after
```

File: `okf_runtime/models.py`

### 3. ActorEvent and Source dataclasses

```
@dataclass(frozen=True)
class ActorEvent:
    by: str       # actor convention §7
    at: str | None  # ISO 8601

@dataclass(frozen=True)
class Source:
    resource: str
    id: str | None
    title: str | None
    author: str | None
    usage_count: int | None
    last_modified: str | None
    usage_window: dict[str, str] | None  # per-entry override
```

File: `okf_runtime/models.py`

### 4. `extract_trust_signals()` in parser

A pure function: `dict[str, Any] → TrustSignals`. Called by
`parse_document()` after frontmatter extraction. Handles:
- `verified` bare-mapping → one-element list normalization (§5.2).
- Absent `status` → `"stable"` (§5.4).
- Absent everything → a zero-value `TrustSignals`.

File: `okf_runtime/parser.py`

### 5. Trust-extended Document and RuntimeIndex

- **Document**: add `trust: TrustSignals` field; surface `trust_tier`,
  `is_stale`, `status` properties that delegate to `TrustSignals`.
  Update `to_catalog_record()` to include `trust_tier`, `status`,
  `is_stale`.
- **RuntimeIndex**: add `trust_index: dict[str, dict[str, Any]]` mapping
  each concept_id to its serialized trust surface. Add
  `trust_tier_index: dict[str, list[str]]` grouping concept_ids by tier.

File: `okf_runtime/models.py`

### 6. `build_trust_index()` in metadata

Constructs `trust_index` and `trust_tier_index` from `documents`. Feeds
`RuntimeIndex`.

File: `okf_runtime/metadata.py`

### 7. Trust-aware `query()` filters

Extend `query_metadata()` / `_matches()` to support synthetic filter keys:
- `trust_tier=unverified|machine-confirmed|human-reviewed` — filters on
  derived tier.
- `status=draft|stable|deprecated` — §5.4.
- `stale=true|false` — computed from `stale_after` vs today.

These keys are not raw frontmatter; they are computed by the runtime,
matching the spec's intent that trust tiers are *derived*, not stored.

File: `okf_runtime/metadata.py`

### 8. `okf trust` CLI command

Subcommand: `okf trust [concept_id]`

- **No argument (bundle summary)**: prints per-tier counts, stale count,
  status breakdown, overall trust distribution.
- **With concept_id**: prints the full trust surface for one concept
  (trust_tier, is_stale, status, generated, verified events, sources
  with credibility signals).

Output format follows `--format json|yaml` convention.

File: `okf_runtime/cli.py`

### 9. `--min-trust` flag on `compose`

`okf compose <topic> --min-trust machine-confirmed`

Excludes concepts whose trust_tier is below the requested minimum from the
composed sub-bundle. Tier ordering: unverified < machine-confirmed <
human-reviewed.

File: `okf_runtime/cli.py`, `okf_runtime/compose.py`

### 10. `docs/OKFmin.SPEC.v02.md` distillation

A minimal, machine-readable distillation of the OKF v0.2 spec that ships
with the runtime. Covers §4.1 (frontmatter schema), §5 (provenance/trust/
lifecycle), §7 (actor convention), §11 (conformance), and §13 (v0.1
migration fallbacks).

File: `docs/OKFmin.SPEC.v02.md`

### 11. `okf_version` detection from `index.md` frontmatter

When a bundle-root `index.md` has frontmatter with `okf_version`, the
runtime records it in `RuntimeIndex.okf_version` (§12). The parser allows
frontmatter on `index.md` only for this purpose. `okf trust` and
`okf catalog` surface the detected version.

File: `okf_runtime/parser.py`, `okf_runtime/models.py`, `okf_runtime/api.py`

### 12. `tests/test_trust.py` golden-file tests

Golden-file tests using the v0.2 Appendix A worked example
(income-statement bundle) as the fixture:
- Parse nested frontmatter (generated, verified, sources, stale_after,
  executor, attester).
- Verify trust_tier derivation for all three tiers.
- Verify is_stale for stale and fresh concepts.
- Verify trust_index and trust_tier_index construction.
- Verify query with trust_tier=, status=, stale= filters.
- Verify compose with --min-trust filtering.
- Verify okf_version detection.

File: `tests/test_trust.py`, `tests/fixtures/v02-income-statement/`

Acceptance Criteria

✓ All existing Phase 1 tests still pass (no regressions)

✓ Nested YAML parsing handles all v0.2 frontmatter shapes without PyYAML

✓ Trust tiers derived exactly per §5.3 rules

✓ Staleness computed per §5.5

✓ `verified` bare-mapping normalized per §5.2

✓ Absent trust fields ⇒ concept still consumable (§11)

✓ `okf trust` produces JSON and YAML output

✓ `--min-trust` filters compose output correctly

✓ `okf_version` detected from bundle-root `index.md`

✓ Golden-file tests cover the Appendix A worked example

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
