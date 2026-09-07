# OKF Runtime - Skill Refactor Plan

Implementation handover. Run commands from `.agents/skills/okf-runtime/` unless stated otherwise.

## Scope and constraints

- Keep `okf_runtime/`, `tests/`, and `pyproject.toml` in place. Do not change package code or public APIs.
- Add only one executable helper: `scripts/okf.py`. It must only delegate to `okf_runtime.cli.main()`.
- Keep `python -B -m okf_runtime.cli` as the primary no-install invocation.
- Treat `references/` as agent-facing, on-demand material and `docs/` as maintainer documentation.
- Use file moves, not copy-and-delete, where the available tooling supports moves.
- Stop and report if a verification step fails.

## Target layout

```text
okf-runtime/
├── SKILL.md
├── README.md
├── LICENSE
├── pyproject.toml              # unchanged
├── okf_runtime/                # unchanged package
├── tests/                      # unchanged
├── scripts/
│   └── okf.py                  # new thin wrapper
└── references/                 # agent-facing, loaded only when needed
│   ├── USAGE.md
│   ├── OKFmin.SPEC.md
│   ├── OKF-Version-0.2-min.md
│   ├── OKF-SPEC-Version-0.2.md
│   ├── OKF-v0.2-SPEC-for-consumer-agent-context.md
│   ├── OKF-DELTA-0.1-to-0.2.md
│   └── SKILLminSPEC.md
└──docs/                           # maintainer-facing
    ├── ADR.md
    ├── ARCHITECTURE.md
    ├── CONTRIBUTING_GUIDE.md
    ├── IMPLEMENTATION_PLAN.md
    └── refactor.md
```

## 1. Move agent-facing references

Create `references/` and move these files from `docs/` without changing their contents:

- `USAGE.md`
- `OKF-SPEC-Version-0.2.md`
- `OKF-v0.2-SPEC-for-consumer-agent-context.md`
- `OKF-Version-0.2-min.md`
- `OKFmin.SPEC.md`
- `OKF-DELTA-0.1-to-0.2.md`
- `SKILLminSPEC.md`

Leave the five maintainer files shown under `docs/` in the target layout. This plan itself is one of those files.

**Verify:** `references/` contains 7 files and `docs/` contains 5 files. All 12 documentation files are accounted for.

## 2. Update paths and documented architecture

### `docs/ARCHITECTURE.md`

- Change `[spec.](OKFmin.SPEC.md)` to `[spec.](../references/OKFmin.SPEC.md)`.
- Replace the illustrative repository tree with the target layout above. Use the real package name `okf_runtime/`, add `references/`, and remove nonexistent `runtime/`, `examples/`, and `templates/` entries.
- Show only `scripts/okf.py`; do not advertise unimplemented `validate.py` or `compose.py` wrappers.

### `README.md`

Replace the repository structure summary with:

```text
- `okf_runtime/` - runtime library and CLI
- `scripts/` - thin agent-facing entry point
- `references/` - agent-facing usage and specification material
- `docs/` - architecture, decisions, contribution guidance, and plans
- `tests/` - runtime tests and fixtures
```

In the Documentation list:

- Keep maintainer links under `docs/`.
- Change `docs/OKFmin.SPEC.md` to `references/OKFmin.SPEC.md`.
- Change `docs/USAGE.md` to `references/USAGE.md`.

Do not change same-directory links between files moved together into `references/`.

**Verify:** search all files under the skill root for old `docs/` paths to the seven moved files. Ignore examples inside this plan; no other stale path may remain.

## 3. Correct `SKILL.md` metadata and packaging text

Replace the frontmatter with:

```yaml
---
name: okf-runtime
description: "Discover, catalog, query, traverse, lint, and compose Open Knowledge Format (OKF) markdown bundles. Use when: retrieving OKF concepts, filtering YAML frontmatter, tracing links, checking trust metadata, validating bundles, or creating context-limited sub-bundles."
version: 0.1.0
authors:
  - OKF Runtime contributors
tags:
  - okf
  - knowledge-catalog
  - metadata-extraction
  - link-linting
  - agent-context
license: MIT
compatibility: Requires Python 3.10+
---
```

This promotes recommended discovery fields to top level and no longer implies that standalone YAML files are scanned.

Replace the stale paragraph claiming the package is not distributable with:

```text
This directory is a conformant Agent Skill package: its `okf-runtime` directory matches the frontmatter `name`. The Python implementation lives in `okf_runtime/`, agent-facing material in `references/`, and maintainer documentation in `docs/`.
```

Replace the equivalent stale paragraph in the README's **Agent Skills packaging** section with the same facts.

**Verify:** frontmatter has top-level `name`, `description`, `version`, `authors`, `tags`, `license`, and `compatibility`; it has no `metadata:` or singular `author:` key. Search for `not a distributable` and expect no matches outside this plan.

## 4. Add the conventional script wrapper

Create `scripts/okf.py`:

```python
"""Thin agent-facing entry point for OKF Runtime."""

import sys

from okf_runtime.cli import main


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

Do not add parsing, path manipulation, formatting, validation logic, or other wrappers. Do not change the existing `okf` entry point in `pyproject.toml`.

The wrapper intentionally requires the package to be installed. It is additive; it does not replace the no-install module invocation.

**Verify:** `scripts/okf.py` contains only imports and delegation; `pyproject.toml` and `okf_runtime/` are unchanged.

## 5. Add progressive-loading guidance

In `SKILL.md`, immediately after the existing `-B` note, add:

```text
The module invocation is the primary no-install path. After installing the package from the skill root (`python -m pip install -e .`), `python scripts/okf.py ...` is an equivalent convenience wrapper.
```

Append this reference map to `SKILL.md`:

```markdown
## References

Load only the material needed for the task:

- `references/USAGE.md` - CLI/API syntax and examples; use for operation questions.
- `references/OKF-Version-0.2-min.md` - default implementation reference for OKF v0.2.
- `references/OKFmin.SPEC.md` - legacy OKF v0.1 rules.
- `references/OKF-DELTA-0.1-to-0.2.md` - migration and compatibility work.
- `references/OKF-v0.2-SPEC-for-consumer-agent-context.md` - expanded consumer-agent implementation context.
- `references/OKF-SPEC-Version-0.2.md` - full specification; load only for details absent from distilled references.
- `references/SKILLminSPEC.md` - Agent Skills packaging and conformance work only.
```

In `references/USAGE.md`, after its `-B` guidance, add:

```text
After installing from the skill root with `python -m pip install -e .`, the thin wrapper `python scripts/okf.py <command>` delegates to the same CLI. Prefer the module form above when installation is unnecessary.
```

## 6. Final validation

1. Inventory changes. Expected:
   - moved: the 7 reference files;
   - new: `scripts/okf.py` and this plan if it was not committed;
   - edited: `SKILL.md`, `README.md`, `docs/ARCHITECTURE.md`, and `references/USAGE.md`;
   - unchanged: `okf_runtime/`, `tests/`, and `pyproject.toml`.
2. Check every Markdown link/path affected by the moves. Do not flag literal old paths inside this implementation plan.
3. Confirm `SKILL.md` frontmatter is parseable and `name` equals the directory name.
4. Run `python -B -m okf_runtime.cli --help`; expect exit code 0.
5. Run `python -B -m pytest`; expect all tests to pass.
6. Optionally validate the installed wrapper in a disposable environment:
   - `python -m pip install -e .`
   - `python scripts/okf.py --help`
   - expect exit code 0 and the same command surface as the module invocation.
7. Remove generated build metadata such as `okf_runtime.egg-info/` if installation created it. Do not commit generated artifacts.

## Out of scope

- Renaming or relocating the Python package.
- Adding `validate.py`, `compose.py`, MCP, or semantic search.
- Rewriting the reference specifications.
- Changing the future `docs/OKFmin.SPEC.v02.md` item in `IMPLEMENTATION_PLAN.md`; it names a separate planned deliverable.