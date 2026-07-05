# OKF v0.1 — Minimal Spec

LLM-oriented distillation of OKF v0.1 (Draft) — every MUST/SHOULD/MAY rule kept, motivation/prose/narrative dropped (source §1, §2, §10; full spec: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md). OKF itself is a directory tree of UTF-8 markdown files with YAML frontmatter, representing knowledge about data/systems — no registry, no central authority, no required tooling. Ethos: **permissive consumption** — unfamiliar structure is best-effort, not malformed (§9).

## §3 Bundle

- **Knowledge Bundle** — a directory tree of `.md` files; the unit of distribution (git repo, recommended; tarball/zip; or a subdirectory of a larger repo).
- **Concept** — one markdown file = one unit of knowledge (an asset, an abstract idea, or anything between). Its **Concept ID** is the file path minus `.md` (`tables/users.md` → `tables/users`).
- Directory layout is domain-independent — concepts may sit at the bundle root or nest in subdirectories to any depth; organize however suits the content.

### §3.1 Reserved filenames

MUST NOT be used for concept documents, at any directory level:

| File | Purpose |
|---|---|
| `index.md` | directory listing — §6 |
| `log.md` | change history — §7 |

All other `.md` files are concepts. Tags are only a frontmatter field (§4.1) — there's no separate tag-index file format; consumers may synthesize a tag view by scanning frontmatter.

## §4 Concept document

A concept file = one YAML frontmatter block (`---`-delimited, first line of file) + one markdown body.

### §4.1 Frontmatter

```yaml
---
type: <string>          # REQUIRED, non-empty, freeform (e.g. "BigQuery Table", "Metric")
title: <string>          # recommended
description: <sentence>  # recommended
resource: <URI>          # recommended; omit for abstract/non-asset concepts
tags: [<string>, ...]    # recommended
timestamp: <ISO 8601>     # recommended, last meaningful change
# producer-defined keys also allowed
---
```

- `type` is the only hard requirement. Values are unregistered/freeform; consumers MUST tolerate unknown types (treat as generic concepts).
- Recommended fields, in priority order: `title`, `description`, `resource`, `tags`, `timestamp`.
- Extra/unknown keys are allowed; consumers SHOULD preserve them, and per §9 MUST NOT reject a document merely for having them.
- If the underlying asset already has a formal schema elsewhere (Avro, Protobuf, OpenAPI...), reference it via `resource` or a link rather than re-deriving it in OKF — OKF doesn't replace domain schemas.

### §4.2 Body

Standard markdown. SHOULD favor structure — headings, lists, tables, fenced code — over prose. No section is required. SHOULD use these conventional headings when the content fits (so consumers can reliably scan for them); other headings are equally valid:

| Heading | Purpose |
|---|---|
| `# Schema` | columns/fields of an asset |
| `# Examples` | concrete usage, often fenced code |
| `# Citations` | external sources — §8 |

## §5 Cross-linking

Standard markdown links between concepts:

- **Absolute** (bundle-relative), starting with `/`: `[customers](/tables/customers.md)` — RECOMMENDED; stable when files move within their subdirectory.
- **Relative**: `[other](./other.md)`.
- A link asserts an untyped relationship — its kind (parent/child, joins-with, depends-on...) lives in the surrounding prose, not the link itself.
- Consumers MUST tolerate broken links; a dead target may just be not-yet-written.

## §6 `index.md`

MAY appear in any directory, including bundle root — a listing of that directory's contents for progressive disclosure.

- No frontmatter, EXCEPT the bundle-root `index.md`, which MAY carry `okf_version` (§11) — the only place frontmatter is permitted in an `index.md`.
- Body = one or more headed sections of link bullets; entries SHOULD reuse the target's `description`:

```markdown
# Datasets
* [Sales](datasets/sales.md) - all sales-related tables
* [Subdirectory](subdir/) - short description
```

- MAY be producer-generated or consumer-synthesized on the fly.

## §7 `log.md`

MAY appear at any level; records that scope's change history as a flat, date-grouped list, **newest first**. Date heading MUST be ISO 8601 `YYYY-MM-DD`. A leading bold action word (`**Update**`, `**Creation**`, `**Deprecation**`) is convention, not required.

```markdown
# Update Log
## 2026-05-22
* **Update**: Added [Customer Metrics](/tables/customer-metrics.md).
```

## §8 Citations

Externally-sourced claims in a body SHOULD be listed under a `# Citations` heading, numbered:

```markdown
# Citations
[1] [Source title](https://example.com/doc)
[2] [Internal runbook](/references/quality-runbook.md)
```

Links MAY be external URLs, bundle-relative paths, or paths into a `references/` subdirectory that mirrors external material as concepts.

## §9 Conformance

A bundle is conformant if:

1. Every non-reserved `.md` file has a parseable YAML frontmatter block.
2. Every frontmatter block has a non-empty `type`.
3. Every present `index.md`/`log.md` follows its shape (§6/§7).

Consumers MUST NOT reject a bundle for: missing optional fields; unknown `type` values; unknown extra frontmatter keys; broken links; a missing `index.md`; or an unrecognized `okf_version` (§11) — SHOULD attempt best-effort consumption instead of refusal. Everything past the 3 rules above is soft guidance, by design: bundles grow, get refactored, and are partially agent-generated.

## §11 Versioning

Current version **0.1**; format `<major>.<minor>`. Minor = backward-compatible addition (new optional field/heading). Major = breaking change (renamed required field, changed reserved filename). A bundle declares its target version via `okf_version: "0.1"` in the bundle-root `index.md` frontmatter — nowhere else.

## Appendix — Worked example

```
my_bundle/
├── index.md
└── tables/
    ├── index.md
    └── orders.md
```

`tables/orders.md`:

```markdown
---
type: BigQuery Table
title: Customer Orders
description: One row per completed customer order across all channels.
resource: https://console.cloud.google.com/bigquery?p=acme&d=sales&t=orders
tags: [sales, orders, revenue]
timestamp: 2026-05-28T14:30:00Z
---

# Schema

| Column | Type | Description |
|---|---|---|
| `order_id` | STRING | Unique order identifier. |
| `customer_id` | STRING | FK to [customers](/tables/customers.md). |

# Joins

Joined with [customers](/tables/customers.md) on `customer_id`.

# Citations

[1] [BigQuery table schema](https://console.cloud.google.com/bigquery?p=acme&d=sales&t=orders)
```
