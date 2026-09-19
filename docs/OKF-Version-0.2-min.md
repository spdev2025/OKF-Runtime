# OKF v0.2 — Minimal Spec

Implementation reference for OKF v0.2. Scope: agentic coding — parsers, validators, generators, attestation runners. Contains every MUST/SHOULD/MAY rule and field. Excludes §1 narrative and §13 history (see `OKF-DELTA-0.1-to-0.2.md`). Full spec: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md or OKF-SPEC-Version-0.2.md locally.

OKF: a directory tree of UTF-8 markdown files (YAML frontmatter + body) representing knowledge about data/systems. No registry, no central authority, no required tooling. Permissive consumption: a consumer MUST NOT reject a bundle over a soft violation (§11). v0.2 adds provenance, trust, lifecycle, and attestation as optional frontmatter families on top of an unchanged v0.1 core. Packaging/invocation of code behind a `resource` (script, container, Skill) is out of scope — OKF fixes the interface, not the packaging.

---

## §2 Terminology

| Term | Meaning |
|---|---|
| Knowledge Bundle | directory tree of `.md` files; unit of distribution |
| Concept | one markdown file = one unit of knowledge |
| Concept ID | concept's file path, `.md` suffix removed |
| Frontmatter / Body | YAML block delimited by `---` / everything after it |
| Link | markdown link between concepts; asserts an untyped relationship (§6.1) |
| Source | a material a concept derives from, recorded in `sources` (§5.1) |
| Provenance | the set of sources a concept derives from |
| Credibility signal | objective per-source fact (`author`, `usage_count`, `last_modified`) used to infer trust — OKF stores signals, not a verdict |
| Actor | identity string: `<producer>/<version>`, `human:<id>`, or `process:<id>` (§7) |
| Trust tier | derived from `verified`: unverified / machine-confirmed / human-reviewed (§5.3) |
| Attested Computation | a concept (`type: Attested Computation`) carrying a sanctioned, checkable way to compute a value (§10) |
| Executor | run instructions/code that runs a computation and returns a receipt |
| Receipt | evidence a run returns, shaped by `executor.receipt`; a runtime artifact, not stored in the bundle |
| Attester | deterministic, no-LLM code that inspects a receipt and returns a verdict |

---

## §3 Bundle

- **Knowledge Bundle** — directory tree of `.md` files; unit of distribution (git repo, recommended; tarball/zip; or a subdirectory of a larger repo).
- **Concept** — one markdown file = one unit of knowledge (an asset, an abstract idea, or anything between). Its **Concept ID** is the file path minus `.md`.
- Directory layout is domain-independent. Concepts may sit at the bundle root or nest to any depth.

### §3.1 Reserved filenames

MUST NOT be used for concept documents, at any level:

| File | Purpose |
|---|---|
| `index.md` | directory listing — §8 |
| `log.md` | change history — §9 |

All other `.md` files are concepts. Tags are only a frontmatter field (§4.1); OKF defines no tag-index file format.

---

## §4 Concept document

One YAML frontmatter block (`---`-delimited, first line of file) + one markdown body.

### §4.1 Frontmatter

```yaml
---
type: <string>              # REQUIRED — non-empty, freeform (e.g. "BigQuery Table")
title: <string>             # optional — consumers MAY derive from filename
description: <sentence>     # optional — one-line summary
resource: <URI>             # optional — omit if abstract; reference (don't re-derive) Avro/Protobuf/OpenAPI schemas
tags: [<string>, ...]       # optional
# provenance / trust / lifecycle fields — §5
# Attested Computation fields — §10
# producer-defined keys allowed
---
```

- `type` is the only always-required key. A concept with just `type` is fully conformant (§11). Values are unregistered/freeform. Consumers MUST tolerate unknown types (treat as generic).
- Recommended, unchanged from v0.1: `title`, `description`, `resource`, `tags`. v0.1's `timestamp` is removed — see `generated`, §5.2.
- Extra/unknown keys are allowed. Consumers SHOULD preserve them. Consumers MUST NOT reject a document for having them.

### §4.2 Body

Standard markdown. SHOULD favor structure (headings, lists, tables, fenced code) over prose. No section is required. Conventional headings, SHOULD use when applicable:

| Heading | Purpose |
|---|---|
| `# Schema` | columns/fields of an asset |
| `# Examples` | concrete usage, often fenced code |
| `# Computation` | the sanctioned computation of an Attested Computation — §10 |

Per-claim attribution to external sources uses a markdown footnote keyed to a `sources[].id` (§5.1) — not a body `# Citations` list. That was v0.1; still parseable as a legacy fallback when `sources` is absent.

---

## §5 Provenance, trust, lifecycle

All fields in this section are optional frontmatter. Absence is meaningful (e.g. unverified) but never grounds for rejection (§11). Producers SHOULD follow the shapes below when using them.

### §5.1 `sources` — provenance

```yaml
sources:
  - id: ga4-schema                # optional — stable key for footnote attribution; SHOULD be set if cited
    resource: <URI-or-scope>      # REQUIRED per entry — followable path/URL, or unfollowable scope text
    title: <string>               # optional
    author: <actor>               # optional signal — §7
    usage_count: <int>            # optional signal — exercises over usage_window
    last_modified: <YYYY-MM-DD>   # optional signal — when source itself last changed
usage_window: { from: <date>, to: <date> }   # optional sibling of sources — dates frame usage_count; an entry MAY override it
```

- `author` / `usage_count` / `last_modified` are credibility signals, not a stored score. Credibility is inferred from them — same inference principle as trust tiers (§5.3). `usage_count` is coarse: read as liveness/trend, not precise cross-source ranking.
- Lineage is expressed via links, not a field. If `resource` points at another OKF concept, a consumer MAY recurse into that concept's own `sources`.
- Per-claim attribution — a markdown footnote whose label is a `sources[].id`:
  ```markdown
  The `events_` table is sharded daily.[^ga4-schema]

  [^ga4-schema]: GA4 BigQuery Export schema
  ```
  Consumers MUST join a footnote to its `sources` entry via `id`. Consumers MUST NOT join positionally (e.g. `sources[0]`) — list order is not stable.
- v0.1 fallback: consumers MAY still parse a legacy body `# Citations` list when `sources` is absent.

### §5.2 `generated` / `verified` — trust

```yaml
generated: { by: <actor>, at: <ISO 8601> }   # by REQUIRED — how/when current content was produced
verified: { by: <actor>, at: <ISO 8601> }    # OR a list of such mappings — independent checks accumulate
```

- `generated.at` marks the content's last meaningful change. Supersedes v0.1's `timestamp` — consumers MAY fall back to a legacy `timestamp` when `generated` is absent.
- `verified` is independent of `generated.at`. Content can change unconfirmed; facts can be reconfirmed unchanged. "Most recently verified" = latest `at` across entries.
- Consumers MUST treat a bare `{ by, at }` mapping (no list dash) as a one-element list.

### §5.3 Trust tiers

| `verified` | Trust tier |
|---|---|
| absent | unverified |
| present, non-`human:` actors only | machine-confirmed |
| present, includes a `human:<id>` actor | human-reviewed |

Lowest → highest. Advisory signal only, not access control — a concept with no trust frontmatter MUST NOT be rejected (§11).

### §5.4 `status` — lifecycle

`status: draft | stable | deprecated`. Absent ⇒ `stable` (default). `draft` = unreviewed, possibly incomplete. `deprecated` = kept for links/history, no longer current.

### §5.5 `stale_after` — lifecycle

`stale_after: <YYYY-MM-DD>` — optional, absolute date. Stale when `today >= stale_after` (plain date comparison, not a TTL relative to read time).

---

## §6 Cross-linking and paths

### §6.1 Links between concepts

Standard markdown links between concepts. **Absolute** (bundle-relative, starts with `/`) is RECOMMENDED — stable when files move within their subdirectory. **Relative** (`./other.md`) is also valid.

A link asserts an untyped relationship. Its kind (parent/child, joins-with, depends-on…) lives in surrounding prose, not the link. Consumers MUST tolerate broken links — a dead target may just be not-yet-written.

### §6.2 Path-valued fields

`resource`, `sources[].resource`, `computation`, `executor.resource`, `attester.resource` (§10) each accept:
- an absolute URL,
- a bundle-relative path (starts with `/`), or
- a relative path (`../…`).

`sources[].resource` may instead be a non-path scope descriptor (§5.1).

### §6.3 The `references/` convention

A `references/` subdirectory conventionally mirrors external material, run instructions, or code as concepts. `sources`, `executor`, and `attester` commonly point into it. Naming convention only — not a requirement.

---

## §7 Actor convention

Identity fields (`generated.by`, `verified[].by`, `sources[].author`) use exactly one of:

| Form | For | Example |
|---|---|---|
| `<producer>/<version>` | agents/tools | `reference_agent/gemini-2.5-pro` |
| `human:<id>` | people | `human:ahormati` |
| `process:<id>` | automated processes | `process:finance-nightly` |

Trust classification (§5.3) keys off the `human:` prefix. Producers MUST use it for hand-authored or human-confirmed content.

---

## §8 `index.md`

MAY appear in any directory including bundle root. No frontmatter, EXCEPT a bundle-root `index.md` MAY carry `okf_version` (§12) — its only permitted use. Body = one or more headed sections of link bullets, reusing the target's `description`:

```markdown
# Section
* [Title](relative-url) - short description
* [Subdirectory](subdir/) - short description
```

MAY be producer-generated or consumer-synthesized on the fly.

---

## §9 `log.md`

MAY appear at any level. Records that scope's history as a flat, date-grouped list, newest first. Date heading MUST be ISO 8601 `YYYY-MM-DD`. Leading bold action word is convention, not required:

```markdown
# Update Log
## 2026-05-22
* **Update**: Added [Customer Metrics](/tables/customer-metrics.md).
```

---

## §10 Attested Computation

A concept (`type: Attested Computation`) carrying a sanctioned, checkable way to compute a value. OKF specifies the contract and the check, not execution. Packaging of the code behind a `resource` (script, container, Skill) is out of scope.

### §10.2 Contract fields

```yaml
type: Attested Computation
runtime: bigquery                          # REQUIRED — e.g. bigquery, postgres, dbt, python, Looker
parameters:                                # optional — typed, named holes the agent may fill
  - { name: year, type: integer, required: true }
computation: <path>                        # optional — path to computation file; see §10.3
executor:                                  # optional
  resource: <path>                          # run instructions/code a runner follows
  receipt: [job_id, executed_sql, result]   # fields a run MUST return, for the attester to inspect
attester:                                  # optional
  resource: <path>                          # deterministic, no-LLM code; takes a receipt, returns a verdict
```

- `runtime` is the only REQUIRED field in this contract. It fixes what `parameters` mean and how `executor`/`attester` interpret them.
- `parameters`, `computation`, `executor`, `attester` are all optional at the contract level. `executor` and `attester` are needed in practice to actually run and attest the computation (§10.5).

### §10.3 The computation itself

Computation delivery is exactly one of:
- **inline** — a fenced code block in the body under `# Computation`, or
- **file** — `computation: <path>`, with no body fence.

Never both. If `computation` is absent, the body fence is the computation.

The agent MAY supply only *values* for the declared `parameters`. The agent MUST NOT author or edit the computation. A consumer binds `computation` with the parameter values into the run artifact. The attester independently re-derives that same binding and compares it to what the receipt says actually ran (the expanded/compiled artifact — e.g. `executed_sql`, not the source query). A rewritten query, a swapped computation file, or a mutated dependency fails the check.

### §10.5 Consumption flow — informative, not normative

Runtime artifacts (receipts, verdicts) are NOT stored in the bundle.

1. **Discover** — via `type: Attested Computation` (liftable into `index.md`), or by following a link.
2. **Load** — the contract from frontmatter; the computation from the body fence or the `computation` file.
3. **Parameterize** — the agent supplies parameter values.
4. **Execute** — the executor runs the bound computation, returns a receipt shaped by `executor.receipt`.
5. **Attest** — the attester checks: the computation that ran equals `computation` bound with the claimed parameters (not agent-authored code); the displayed value matches the receipt's authoritative source.
6. **Gate** — refuse on a failing attestation or when `today >= stale_after`; surface the verdict on success.

### §10.6 Verified vs. attested

| Dimension | `verified` (§5.2) | Attestation (§10) |
|---|---|---|
| Confirms | the definition matches policy | a run used the sanctioned computation |
| Granularity | doc-level | per-call |
| Speed | slow | runtime |
| Stored in bundle | yes | no |

Both required: a stale definition can still attest cleanly; a fresh definition still needs attestation on every run.

---

## §11 Conformance

A bundle is conformant if:

1. Every non-reserved `.md` file has a parseable YAML frontmatter block.
2. Every frontmatter block has a non-empty `type`.
3. Every present `index.md`/`log.md` follows its shape (§8/§9).

When trust/lifecycle/provenance/computation fields are present, producers SHOULD follow §5–§10. Consumers:
- MUST treat a bare `verified` mapping as a one-element list (§5.2).
- MUST NOT reject a concept for missing any optional family (§5.3).
- SHOULD derive trust tiers and staleness only from the fields specified here.
- SHOULD surface a failing attestation, not silently drop it (§10.5).

Beyond the above, consumers MUST NOT reject a bundle for: missing optional fields; unknown `type` values; unknown extra frontmatter keys; broken links; a missing `index.md`; or an unrecognized `okf_version` (§12) — SHOULD best-effort-consume instead of refusing. All other constraints are soft guidance.

---

## §12 Versioning

Current version: **0.2**. Format: `<major>.<minor>`. Minor = backward-compatible addition. Major = breaking change (renamed required field, changed reserved filename). Declared via `okf_version: "0.2"` in the bundle-root `index.md` frontmatter — nowhere else.

---

## Deferred

Out of scope for v0.2. Do not build these against this spec version:
- Runtime receipt/verdict wire protocol and the attestation lifecycle around a run.
- Attester ABI, portability, and sandboxing.
- Attestation caching.
- Semantic-layer (Looker/dbt) attester comparison beyond SQL equality.

---

## Migration Notes

| v0.1 | v0.2 replacement | Fallback |
|---|---|---|
| `timestamp` | `generated: { by, at }` — §5.2 | Consumers MAY read a legacy `timestamp` when `generated` is absent |
| body `# Citations` list | `sources` (§5.1) + footnotes | Consumers MAY still parse a legacy `# Citations` list when `sources` is absent |

Full migration checklist: `OKF-DELTA-0.1-to-0.2.md`.

---

## Worked example

```
bundle/
├── index.md
├── metrics/
│   └── revenue.md          # type: Metric — narrates, links the computation
└── computations/
    └── revenue.md          # type: Attested Computation
```

`metrics/revenue.md`:

```markdown
---
type: Metric
title: Revenue
description: Recognized revenue for a fiscal year.
tags: [finance, revenue]
status: stable
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-06-20T22:53:05Z }
verified: { by: human:ahormati, at: 2026-06-25T09:00:00Z }
---

# Definition

Recognized revenue, computed by [the revenue computation](../computations/revenue.md).
```

`computations/revenue.md`:

```markdown
---
type: Attested Computation
title: Revenue for fiscal year
runtime: bigquery
parameters:
  - { name: year, type: integer, required: true }
executor:
  resource: references/skills/run-on-bq.md
  receipt: [job_id, executed_sql, result]
attester:
  resource: references/attesters/revenue.py
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-06-20T22:53:05Z }
verified: { by: human:ahormati, at: 2026-06-25T09:00:00Z }
stale_after: 2026-12-31
sources:
  - id: rev-policy
    resource: https://wiki.acme/finance/revenue-recognition
    title: Revenue recognition policy
    author: team:finance-fpa
    last_modified: 2026-04-02
---

# Computation

    SELECT SUM(amount) AS revenue
    FROM finance.recognized_revenue
    WHERE fiscal_year = @year

Per the recognition policy.[^rev-policy]

[^rev-policy]: Revenue recognition policy
```
