# OKF v0.1 → v0.2 Delta

v0.2 is a minor version bump (§12) except for two deliberate breaking changes below. A v0.1 bundle stays consumable by a v0.2 consumer via the fallbacks noted here — nothing needs to be rewritten to upgrade a bundle, only tooling that wants to *produce* v0.2 or read the new families. Companion file for the full v0.2 rule set: `OKF-Version-0.2-min.md`.

## Breaking changes (2)

| v0.1 | v0.2 replacement | Legacy fallback |
|---|---|---|
| `timestamp` (frontmatter) | `generated: { by, at }` (§5.2) — `by` is now REQUIRED, an actor (§7) | Consumers MAY read a legacy `timestamp` when `generated` is absent |
| body `# Citations` list | `sources` frontmatter (§5.1) + markdown footnotes keyed to `sources[].id` | Consumers MAY still parse a legacy `# Citations` list when `sources` is absent |

**Implementer impact**: anything keyed to `timestamp` or a body `# Citations` heading needs a new code path for `generated`/`sources`. Keep the old path only as a fallback for documents that lack the new fields — don't delete it.

## Additive changes — fully backward-compatible, absence ⇒ plain v0.1 concept

- **New frontmatter families** (§5): `sources` (with per-entry signals `author` / `usage_count` / `last_modified`, plus the sibling `usage_window`), `generated`, `verified`, `status`, `stale_after`.
- **New concept type**: `Attested Computation` (§10), with contract fields `runtime` (REQUIRED for this type), `parameters`, `computation`, `executor`, `attester`.
- **New conventional body heading**: `# Computation` (§4.2), for an Attested Computation's inline computation.
- **New identity convention** (§7): `<producer>/<version>` / `human:<id>` / `process:<id>` for `generated.by` and `verified[].by`; trust classification keys off the `human:` prefix.
- **New Conformance rules** (§11), scoped to the families above: MUST treat a bare `verified` mapping as a one-element list; MUST NOT reject a concept for a missing optional family; SHOULD derive trust/staleness only from the specified fields; SHOULD surface (not silently drop) a failing attestation.

## Unchanged

Bundle structure, reserved filenames (`index.md` / `log.md`), the required `type` field, recommended `title` / `description` / `resource` / `tags`, cross-linking mechanics, index-file and log-file formats, the base 3-rule conformance test, and the 5-item "MUST NOT reject a bundle for…" permissive list all carry forward verbatim.

## Minor clarification (not itemized in the spec's own §13, but confirmed by direct comparison)

v0.1's Extensions clause (§4.1) said consumers "SHOULD NOT reject documents with unrecognized fields" — softer than what v0.1's own Conformance section already mandated ("MUST NOT reject… unknown additional frontmatter keys"). v0.2's §4.1 now says **MUST NOT** directly, closing that internal inconsistency. No behavior change for a spec-compliant consumer (Conformance already required it) — but if a v0.1 implementation's frontmatter-validation logic was keyed to the softer §4.1 wording specifically, tighten it to match.

## Migration checklist for an existing v0.1 tool

- [ ] **Parser**: accept (don't require) the 5 new frontmatter families; apply standard unknown-key handling to their sub-keys too.
- [ ] **Parser**: normalize a bare `verified: { by, at }` mapping into a one-element list before processing.
- [ ] **Generator**: emit `generated: { by, at }` instead of `timestamp`; emit provenance via `sources` + footnotes instead of a body `# Citations` list.
- [ ] **Reader**: keep a `timestamp` fallback and a legacy `# Citations`-list fallback for bundles that predate v0.2 — both are permanent parts of v0.2's own spec, not temporary shims.
- [ ] **Validator**: extend `type` routing to recognize `Attested Computation`; validate its extra REQUIRED field (`runtime`) and the shapes of `parameters` / `executor` / `attester`.
- [ ] **Validator**: implement trust-tier derivation (§5.3) and staleness (`today >= stale_after`) if the tool surfaces trust or freshness.
- [ ] **Attestation runner** (only if building one): implement the 6-step discover → load → parameterize → execute → attest → gate flow (§10.5) — informative, not required for base conformance, but required to actually attest anything.
- [ ] Everything else — bundle walking, reserved-filename handling, the core conformance check — is untouched; no changes needed there.
