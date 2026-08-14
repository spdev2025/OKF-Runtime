# OKF v0.2 — Agent Implementation Spec

**Purpose:** compact, self-contained context for coding agents implementing OKF parsers, validators, generators, indexes, and attestation runners.

**Core model:** an OKF bundle is a directory tree of UTF-8 `.md` concept files with YAML frontmatter and Markdown bodies. There is no registry, central authority, or required tooling. **Permissive consumption is mandatory:** soft violations must not cause rejection.

**Scope:** OKF defines the document/data interfaces and attestation contract. It does **not** execute computations or define packaging/invocation for executor/attester resources (script, container, Skill, etc.).

## 1. Core terms

- **Knowledge Bundle:** directory tree of `.md` files; unit of distribution.
- **Concept:** one Markdown file representing one unit of knowledge.
- **Concept ID:** concept file path with `.md` removed.
- **Frontmatter / Body:** YAML block delimited by `---` at file start / everything after it.
- **Link:** standard Markdown link between concepts; relationship is untyped.
- **Source / Provenance:** source material listed in `sources` / the set of sources a concept derives from.
- **Credibility signal:** objective source fact (`author`, `usage_count`, `last_modified`), not a stored score.
- **Actor:** `<producer>/<version>`, `human:<id>`, or `process:<id>`.
- **Trust tier:** derived from `verified`: `unverified`, `machine-confirmed`, `human-reviewed`.
- **Attested Computation:** `type: Attested Computation`; defines a sanctioned, checkable computation.
- **Executor:** run instructions/code that executes a computation and returns a receipt.
- **Receipt:** runtime evidence shaped by `executor.receipt`; not stored in the bundle.
- **Attester:** deterministic, no-LLM code that checks a receipt and returns a verdict.

## 2. Bundle and concept files

A bundle MAY be distributed as a git repository, tar/zip, or subdirectory of another repository. Directory layout is domain-independent; concepts MAY be nested at any depth.

Reserved filenames at every level:
- `index.md` — directory listing.
- `log.md` — change history.

These filenames MUST NOT be used as concept documents. Every other `.md` file is a concept.

A concept consists of exactly one YAML frontmatter block (`---` on its own line, first and closing lines) followed by a Markdown body.

### 2.1 Frontmatter

```yaml
---
type: <non-empty string>       # REQUIRED; freeform/unregistered
title: <string>                # recommended
description: <sentence>        # recommended
resource: <URI>                # recommended; canonical underlying resource
tags: [<string>, ...]          # recommended
# optional: sources/generated/verified/status/stale_after
# Attested Computation fields when type == "Attested Computation"
# producer-defined keys are allowed
---
```

`type` is the only universally required frontmatter key. A concept containing only `type` is conformant. Type values are not centrally registered; consumers MUST tolerate unknown types, normally treating them as generic.

For recommended fields:
- `title` is a display name; if absent, a consumer MAY derive one from the filename.
- `description` is a one-sentence summary useful for indexes/previews.
- `resource` identifies the underlying asset; it is not a substitute for a domain schema such as Avro/Protobuf/OpenAPI.
- `tags` is a list of strings.

Unknown/producer-defined keys are allowed. Consumers MUST NOT reject a document because of them and SHOULD preserve them when round-tripping.

The body is standard Markdown; no body section is required. Producers SHOULD prefer structured Markdown. Conventional headings are:
- `# Schema` — asset fields/columns.
- `# Examples` — concrete usage.
- `# Computation` — inline sanctioned computation for an Attested Computation.

Per-claim source attribution uses a Markdown footnote whose label matches a `sources[].id`; it is not a body `# Citations` list.

## 3. Provenance, trust, lifecycle

All fields in this section are optional. Their absence has meaning but MUST NOT cause rejection.

### 3.1 `sources`

```yaml
sources:
  - id: <string>                         # optional; stable attribution key
    resource: <URI or scope text>        # REQUIRED in each entry
    title: <string>                      # optional
    author: <actor>                      # optional credibility signal
    usage_count: <int>                   # optional credibility signal
    last_modified: <YYYY-MM-DD>          # optional credibility signal
usage_window: { from: <date>, to: <date> }  # optional; frames usage_count
```

`resource` may be a followable URL/path or an unfollowable scope descriptor (for example, all queries in a project). `id` SHOULD be present when the body cites that source.

`author`, `usage_count`, and `last_modified` are signals, not a subjective credibility score. `usage_count` is coarse: use it as liveness/trend, not as a precise cross-source ranking. `usage_window` MAY be overridden on an individual source entry.

If a source resource points to another OKF concept, lineage is represented by the normal link graph; a consumer MAY recurse into that concept's `sources` and propagate credibility.

Resolve footnote attribution by matching `id`, **never by list position** (`sources[0]`).

For v0.1 compatibility, when `sources` is absent, consumers MAY parse a legacy body `# Citations` list.

### 3.2 `generated` and `verified`

```yaml
generated: { by: <actor>, at: <ISO 8601> }   # by REQUIRED
verified:
  - { by: <actor>, at: <ISO 8601> }          # multiple checks allowed
```

`generated.at` is the time of the last meaningful content change; consumers MAY fall back to legacy `timestamp` when `generated` is absent.

`verified` is independent of `generated.at`; facts may be reconfirmed without regeneration, and content may change without reconfirmation. The latest `verified[].at` is the latest verification time.

A bare mapping is valid and MUST be treated as a one-element list:

```yaml
verified: { by: human:alice, at: 2026-06-25T09:00:00Z }
```

### 3.3 Trust tier

Derive only from `verified`:
1. absent → `unverified`
2. entries exist but none are `human:` → `machine-confirmed`
3. any `human:<id>` entry → `human-reviewed`

Trust tier is advisory, not access control. Lack of trust metadata MUST NOT cause rejection.

### 3.4 Lifecycle

```yaml
status: draft | stable | deprecated
stale_after: <YYYY-MM-DD>
```

`status` defaults to `stable` when absent. `draft` means unreviewed/possibly incomplete; `deprecated` means retained for links/history but no longer current.

`stale_after` is an absolute date; the concept is stale exactly when `today >= stale_after`.

## 4. Links and paths

Concepts MAY link with ordinary Markdown links:
- bundle-root absolute: `/path/to/concept.md` — RECOMMENDED;
- relative: `../concept.md` or `./concept.md`.

Links assert only an untyped relationship; semantic type (parent/child, joins-with, depends-on, etc.) comes from surrounding content. Consumers MUST tolerate broken links.

These fields are path-valued: `resource`, `sources[].resource`, `computation`, `executor.resource`, `attester.resource`. They accept:
1. absolute URLs,
2. bundle-relative paths beginning `/`,
3. ordinary relative paths.

A `sources[].resource` MAY instead be a non-path scope descriptor.

`references/` is only a naming convention for bundling external material, execution instructions, or deterministic code as first-class concepts.

## 5. Actor convention

Identity fields (`generated.by`, `verified[].by`, and source `author` when used as an actor) use exactly one of:

| Form | Meaning |
|---|---|
| `<producer>/<version>` | agent/tool |
| `human:<id>` | person |
| `process:<id>` | automated process |

Trust classification uses the `human:` prefix; producers MUST use that prefix for hand-authored or human-confirmed content.

## 6. `index.md`

`index.md` MAY appear at any level, including the root.

It contains no frontmatter, **except** a bundle-root `index.md` MAY contain `okf_version` (the only permitted frontmatter there). Its body contains headed groups with Markdown link bullets, e.g.:

```markdown
# Section
* [Title](relative-url) - short description
* [Subdirectory](subdir/) - short description
```

Entries SHOULD reuse target `description`. Producers MAY generate indexes; consumers MAY synthesize them when absent.

## 7. `log.md`

`log.md` MAY appear at any level and records that scope's history as a flat, date-grouped list, **newest first**.

Date headings MUST be `YYYY-MM-DD`. Any leading bold action word is only convention.

## 8. Attested Computation

A concept with `type: Attested Computation` defines a sanctioned computation whose execution can be mechanically checked. OKF defines the contract and check, not execution or resource packaging.

### 8.1 Standalone concept

A sanctioned computation is its **own concept**. Concepts needing its value link to it. Keeping it standalone makes runtime/parameter binding explicit, permits reuse by multiple consumers, and gives each computation independent trust/freshness/attestation state.

### 8.2 Contract

```yaml
type: Attested Computation
runtime: <string>                    # REQUIRED for this type
parameters:                           # optional typed, named values agent may fill
  - { name: <string>, type: <string>, required: <boolean> }
computation: <path>                   # optional; mutually exclusive with inline body fence
executor:
  resource: <path>                   # optional runner instructions/code
  receipt: [<field>, ...]            # optional expected evidence fields
attester:
  resource: <path>                   # optional deterministic validation code
```

`runtime` determines what `parameters` mean and how executor/attester interpret them. Examples: `bigquery`, `postgres`, `dbt`, `python`, `Looker`.

`computation` points to an external computation file. If absent, the computation is the fenced code block under `# Computation`.

`executor.resource` identifies run instructions/code; `executor.receipt` identifies evidence fields the run must return.

`attester.resource` identifies deterministic, no-LLM code that consumes the receipt and returns a verdict.

### 8.3 Computation source

Exactly one computation representation is used:

**Inline**
```markdown
# Computation

    SELECT ...
```

or **file-based**
```yaml
computation: references/computations/revenue.sql
```

The body fence and `computation` field are mutually exclusive.

The agent MAY supply only values for declared `parameters`; it MUST NOT author or edit the computation. The consumer binds the sanctioned computation with those values into the executable artifact. The attester independently re-derives the same binding and compares it with the expanded/compiled artifact recorded in the receipt (for example `executed_sql` or `compiled_sql`). A rewritten query, swapped computation file, or mutated dependency must therefore fail attestation.

### 8.4 Informative consumption flow

This flow is **informative, not normative**; receipts and verdicts are runtime artifacts and are not stored in the bundle:

1. **Discover** an Attested Computation by `type` or by following a concept link.
2. **Load** its contract and inline/file computation.
3. **Parameterize** using only declared parameter values.
4. **Execute** through the executor; obtain the declared receipt.
5. **Attest** the receipt, checking that the actual computation equals the sanctioned computation bound with the claimed parameters, and that the displayed value matches the receipt's authoritative source.
6. **Gate** display: do not display a failing attestation; warn or refuse when stale; on success, surface the verdict/evidence.

### 8.5 Verification vs attestation

- `verified` is document-level, stored in the bundle, and confirms the definition/content.
- Attestation is per-run, runtime, not stored in the bundle, and confirms one execution followed the sanctioned computation.

A stale definition can still attest cleanly; a freshly verified definition still needs attestation on each run.

## 9. Conformance and permissive consumption

A v0.2 bundle is conformant when:
1. every non-reserved `.md` file has parseable YAML frontmatter;
2. every frontmatter block has a non-empty `type`;
3. every present `index.md`/`log.md` follows its defined structure.

When optional families are present, producers SHOULD follow their specified shapes. Consumers:
- MUST treat bare `verified: {by, at}` as a one-element list;
- MUST NOT reject a concept for missing optional provenance/trust/lifecycle/computation fields;
- SHOULD derive trust/staleness only as specified;
- SHOULD surface, not silently drop, a failing attestation.

Consumers MUST NOT reject a bundle because of:
- missing optional fields;
- unknown `type` values;
- unknown extra frontmatter keys;
- broken links;
- missing `index.md`.

Everything outside explicit conformance/consumer MUST rules is soft guidance.

## 10. Versioning and compatibility

Current format: **0.2**. Version syntax is `<major>.<minor>`:
- minor = backward-compatible additions;
- major = potentially breaking changes.

A bundle MAY declare `okf_version: "0.2"` only in root `index.md` frontmatter. A consumer that does not understand a declared version SHOULD attempt best-effort consumption rather than refuse solely because of the version.

v0.1 compatibility:
- `timestamp` → `generated: { by, at }`; consumers MAY fall back to legacy `timestamp` if `generated` is absent.
- body `# Citations` → `sources`; consumers MAY still parse the legacy section when `sources` is absent.

## 11. Explicitly out of scope for v0.2

Do not implement these as part of the OKF v0.2 format:
- runtime receipt/verdict wire protocols and attestation lifecycle;
- attester ABI, portability, and sandboxing;
- attestation caching;
- semantic-layer attester comparisons beyond exact SQL equality (e.g. Looker/dbt model semantics).
