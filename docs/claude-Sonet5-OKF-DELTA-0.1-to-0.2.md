# OKF v0.1 → v0.2 Delta

v0.2 is a minor version bump (§12) except for two deliberate breaking changes below. A v0.1 bundle stays consumable by a v0.2 consumer via the fallbacks noted here — nothing needs to be rewritten to upgrade a bundle, only tooling that wants to *produce* v0.2 or read the new families. Companion file for the full v0.2 rule set: `OKF-Version-0.2-min.md`.

## Breaking changes

| v0.1 | v0.2 | Consumer fallback |
|------|------|-------------------|
| `timestamp: <ISO 8601>` (recommended, last meaningful change) | Superseded by `generated: { by: <actor>, at: <ISO 8601> }` | MAY fall back to legacy `timestamp` when `generated` is absent |
| Body heading `# Citations` (numbered list of external sources) | Superseded by frontmatter `sources:` list (§5.1). Per-claim attribution uses markdown footnotes keyed to `sources[].id` | SHOULD read `sources`; MAY still parse a legacy `# Citations` body list for v0.1 docs |

## Additive (all optional; absence ⇒ plain v0.1 concept)

### Frontmatter families (§5)

**Provenance — `sources`**
```yaml
sources: #
  - id: <stable-key>              # optional; used as footnote label for per-claim attribution
    resource: <URL bundle-path scope-descriptor |>  # REQUIRED within entry
    title: <string>               # optional
    author: <actor>               # credibility signal
    usage_count: <int>            # credibility signal (liveness/adoption)
    last_modified: <YYYY-MM-DD>   # credibility signal
usage_window: { from: <YYYY-MM-DD>, to: <YYYY-MM-DD> }  # sibling; frames usage_count; per-entry override allowed
```
* Credibility is *inferred* from signals; OKF stores no score.
* Lineage via links / `resource` pointing at other concepts; no dedicated `derived_from`.

**Trust — `generated` / `verified`**
```yaml
generated: { by: <actor>, at: <ISO 8601> }   # by REQUIRED within mapping
verified:                                    # list, or bare mapping (= one-element list)
  - { by: <actor>, at: <ISO 8601> } #
```
* Trust tiers (derived by consumer, advisory only): 
  * no `verified` ⇒ **unverified**
  * only non-`human:` actors ⇒ **machine-confirmed**
  * any `human:<id>` ⇒ **human-reviewed**
* Consumers MUST treat bare `verified` mapping as one-element list.
* MUST NOT reject concepts missing any optional family.

**Lifecycle**
```yaml
status: draft | stable | deprecated   # absent ⇒ stable
stale_after: <YYYY-MM-DD>             # absolute; stale when today >= date
```

### Actor convention (§7)
* `<producer>/<version>` — agents/tools (e.g. `reference_agent/gemini-2.5-pro`)
* `human:<id>` — people
* `process:<id>` — automated processes
* Trust classification keys off `human:` prefix; producers MUST use it for human-authored/confirmed content.

### New concept type + computation contract (§10)

`type: Attested Computation` — standalone concept carrying a sanctioned computation so a consumer can confirm a value was produced by the blessed path (not agent-improvised).

Contract fields (in addition to §5 families):
```yaml
runtime: <string>                 # REQUIRED for this type (e.g. bigquery, postgres, dbt, python, Looker)
parameters:                       # typed holes the agent may fill; binding semantics follow runtime
  - { name: <string>, type: <string>, required: <bool> } #
computation: <path>               # optional; path to computation file. Absent ⇒ body `# Computation` fence
executor: #
  resource: <path>                # run instructions/code
  receipt: [<field>, ...]         # fields a run must return (evidence for attester)
attester: #
  resource: <path>                # deterministic (no-LLM) code; takes receipt → verdict
```
* Computation provided either:
  * Inline: single fenced code block under body heading `# Computation`
  * File: `computation: <path>` and omit the body fence
* Agent MAY only supply *values* for declared `parameters`; MUST NOT author/edit the computation.
* Runtime artifacts (receipt, verdict) are **not** stored in the bundle.
* `verified` (doc-level definition) ≠ attestation (per-run mechanical check). Both needed.

### New conventional body heading
| Heading | Purpose |
|---------|---------|
| `# Computation` | Sanctioned computation of an Attested Computation (see §10) |

`# Citations` retired (use `sources` + footnotes). `# Schema` and `# Examples` unchanged.

### Path-valued fields expanded
`resource`, `sources[].resource`, `computation`, `executor.resource`, `attester.resource` accept: absolute URL, bundle-relative path (`/...`), or relative path. `sources[].resource` MAY instead be a non-path scope descriptor.

### `references/` convention
Subdirectory conventionally mirrors external material, run instructions, or code as first-class concepts. Naming convention only, not required.

## Unchanged (carried forward)

* Bundle structure, reserved filenames (`index.md`, `log.md`), Concept ID = path minus `.md`
* Required: only non-empty `type` in every concept frontmatter
* Recommended: `title`, `description`, `resource`, `tags`
* Cross-linking (absolute `/...` recommended; relative; untyped edges; tolerate broken links)
* `index.md` / `log.md` shapes and rules
* Extensions allowed; consumers SHOULD preserve unknown keys
* Conformance: 3 hard rules only; everything else soft. MUST NOT reject for missing optionals, unknown types/keys, broken links, missing `index.md`
* Version declaration: `okf_version: "0.2"` only in bundle-root `index.md` frontmatter
* Ethos: permissive consumption; no registry, no central authority, no required tooling

## Deferred (explicitly out of v0.2)

Full runtime protocol (receipt/verdict wire formats), attester ABI/sandboxing, attestation caching, semantic-layer templates (Looker/dbt model-and-binding equality).

## Migration checklist for an existing v0.1 tool

* [ ] **Parser**: accept (don't require) the 5 new frontmatter families; apply standard unknown-key handling to their sub-keys too[cite: 8].
* [ ] **Parser**: normalize a bare `verified: { by, at }` mapping into a one-element list before processing[cite: 8].
* [ ] **Generator**: emit `generated: { by, at }` instead of `timestamp`; emit provenance via `sources` + footnotes instead of a body `# Citations` list[cite: 8].
* [ ] **Reader**: keep a `timestamp` fallback and a legacy `# Citations`-list fallback for bundles that predate v0.2 — both are permanent parts of v0.2's own spec, not temporary shims[cite: 8].
* [ ] **Validator**: extend `type` routing to recognize `Attested Computation`; validate its extra REQUIRED field (`runtime`) and the shapes of `parameters` / `executor` / `attester`[cite: 8].
* [ ] **Validator**: implement trust-tier derivation (§5.3) and staleness (`today >= stale_after`) if the tool surfaces trust or freshness[cite: 8].
* [ ] **Attestation runner** (only if building one): implement the 6-step discover → load → parameterize → execute → attest → gate flow (§10.5) — informative, not required for base conformance, but required to actually attest anything[cite: 8].
* [ ] Everything else — bundle walking, reserved-filename handling, the core conformance check — is untouched; no changes needed there[cite: 8].

```