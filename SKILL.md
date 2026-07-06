---
name: okf-runtime
description: Discover, query, catalog, and compose Open Knowledge Format (OKF) bundles. Use this skill when you need to retrieve, filter, lint, or compose sub-bundles of markdown and YAML files without loading whole documents into your context window.
license: MIT
compatibility: Requires Python 3.10+
metadata:
  version: 0.1.0
  author: OKF Runtime contributors
  tags:
    - okf
    - knowledge-catalog
    - metadata-extraction
    - link-linting
    - agent-context
---

# OKF Runtime Skill

This skill provides a deterministic runtime and retrieval toolkit for Open Knowledge Format (OKF) repositories. It enables AI agents to query, traverse, and compose OKF document bundles without reading entire markdown files, preserving LLM context and reducing token usage.

## Available Command Interface

The OKF Runtime is written in Python and can be executed via the command line from the repository root:

```powershell
python -B -m okf_runtime.cli --root <bundle-or-scan-root> <command> [options]
```

*Note: Always use `-B` to avoid writing Python bytecode (`.pyc` files) to disk in restricted/containerized agent environments.*

### Global Flags
- `--root <path>`: Directory containing OKF bundles. Defaults to `.`.
- `--format <json|yaml>`: Standardize output for programmatic parsing or token-efficient agent reading. Defaults to `json`.

---

## Command Reference

### 1. `discover`
Discover all OKF bundles containing markdown files under the root.
```powershell
python -B -m okf_runtime.cli --root localdocs\samples discover
```
- **Output**: List of bundle paths and their markdown file count.

### 2. `catalog`
Extract and return parsed frontmatter records for all non-reserved documents.
```powershell
python -B -m okf_runtime.cli --root localdocs\samples --format yaml catalog
```
- **Flags**:
  - `--short`: Minimize tokens by listing only `id`, `path`, `type`, and `title`.
  - `--verbose`: Includes forward links and backlinks in each record.

### 3. `query`
Filter concepts without loading markdown bodies. Matches are exact `key=value`. For lists (e.g., `tags`), matches succeed if the value is contained within the list.
```powershell
python -B -m okf_runtime.cli --root localdocs\samples --format yaml query type="BigQuery Table" tags=posts
```

### 4. `show`
Retrieve metadata catalog record for a specific concept by its ID.
```powershell
python -B -m okf_runtime.cli --root localdocs\samples show bundles/stackoverflow/tables/posts_questions
```
- **Flags**:
  - `--body`: Includes the full markdown content of the file.

### 5. `links` and `backlinks`
Trace references in the knowledge graph.
```powershell
python -B -m okf_runtime.cli --root localdocs\samples links bundles/stackoverflow/tables/posts_questions
python -B -m okf_runtime.cli --root localdocs\samples backlinks bundles/stackoverflow/tables/posts_questions
```

### 6. `graph`
Build a deterministic neighborhood around a concept node.
```powershell
python -B -m okf_runtime.cli --root localdocs\samples graph bundles/stackoverflow/tables/posts_questions --depth 2
```

### 7. `compose`
Generate a temporary sub-bundle composed of relevant files centered on a topic or start concept, using radial graph pruning to respect token/context limits.
```powershell
python -B -m okf_runtime.cli --root localdocs\samples compose posts_questions --output-dir .cache\composed-output --depth 2
```
- Copies matched markdown files into the output directory.
- Generates `boundary.json` at the root of the composed folder to identify dangling/external links mapping to their original source bundle locations.

### 8. `lint-links`
Check for broken internal links, anchor issues, parser errors, or unreachable orphan documents.
```powershell
python -B -m okf_runtime.cli --root localdocs\samples lint-links
```

---

## Actionable Workflows for Agents

### Workflow A: Preserving Context via Compose
When a user asks a complex question about a topic (e.g., "how is StackOverflow posts schema structured"):
1. Query relevant concept IDs: `query tags=posts`.
2. Generate a sub-bundle: `compose posts_questions --output-dir .cache\posts-info`.
3. Check the `boundary.json` file in the generated folder to see what external files/links were skipped.
4. Read the copied files and referenced boundary documents only as needed to answer.

### Workflow B: Validating Bundle Quality
Before completing work on OKF markdown files:
1. Run `lint-links` on the repository root.
2. Review the list of failures under `errors` or broken links. Correct these by updating paths in markdown files.
3. Re-run `lint-links` to ensure errors are cleared.

---

## Gotchas & Limitations

- **Multiline Frontmatter:** The Phase 1 YAML frontmatter parser does not support indented multi-line scalars (such as descriptions spanning multiple lines). These will generate parsing errors in the output under `errors`.
- **Comma-Separated Lists:** YAML tags must be formatted as lists (e.g., `- posts` or `[posts]`). Comma-separated strings (e.g., `tags: legacy, posts`) are parsed as a single string and will not match list queries like `tags=posts`.
- **Cache Folder:** The tool automatically creates a `.cache/` folder under the root. This directory contains `manifest.json`, `metadata.json`, `links.json`, and `reverse_links.json`. It is safe to delete and will rebuild silently on the next command.
