# Agent Skills v1.0.0 — Minimal Spec

LLM-oriented distillation of the Agent Skills specification — every MUST/SHOULD/MAY rule kept, narrative dropped. A skill is a directory containing a `SKILL.md` file with YAML frontmatter + markdown body. Ethos: minimal, portable instruction bundles for agents.

## §1 Skill directory

A **skill** is a directory:

```text
skill-name/
├── SKILL.md      # REQUIRED: metadata + instructions
├── scripts/      # OPTIONAL: executable code
├── references/   # OPTIONAL: docs
├── assets/       # OPTIONAL: templates, resources
└── ...           # OPTIONAL: anything else


Consumers MUST NOT require any file except SKILL.md.

## §2 SKILL.md Structure
SKILL.md consists of:
1. YAML frontmatter (first block)
2. Markdown body

### §2.1 Frontmatter Fields
Required:
name: string
description: string

Recommended:
version: semver
authors: list
tags: list

Optional:
platforms: list
license: string
repository: URI
docs: URI
extra keys allowed

### name Constraints
- 1 to 64 characters
- must match directory name
- allowed chars: a-z, 0-9, hyphen
- must not start or end with hyphen
- must not contain double hyphens

### description Constraints
- 1 to 1024 characters
- should describe what the skill does
- should describe when to use it
- should include routing keywords

### §2.2 Body
Markdown instructions.
Should use headings, lists, tables.
Should describe actionable procedures.
May reference scripts, assets, docs.

## §3 Progressive Loading Model

### 1. Discovery Phase
- load only frontmatter
- minimize token usage

### 2. Activation Phase
- load full body when matched by description or tags
- may load referenced files on demand

### 3. Execution Phase
- agent follows body instructions
- avoid loading unnecessary files

## §4 Directory Conventions
scripts/       optional executable helpers
references/    optional markdown or text docs
assets/        optional templates or resources
no reserved filenames except SKILL.md

## §5 Conformance
A skill is conformant if:
1. SKILL.md exists
2. YAML frontmatter is parseable
3. name and description satisfy constraints

Consumers MUST NOT reject skills for:
- missing optional fields
- unknown frontmatter keys
- extra directories or files

Consumers SHOULD attempt best-effort loading.

## §6 Spec Versioning
Current spec version: 1.0
Minor version: backward-compatible additions
Major version: breaking changes
Consumers MUST tolerate unknown future fields

## Appendix — Minimal Example

Frontmatter:
name: pdf-processing
description: Extract PDF text, fill forms, merge files. Trigger when user mentions PDFs.
tags: pdf, extraction, merge

Body:
PDF Processing
Capabilities:
- extract text and tables
- fill forms
- merge PDFs

Usage:
Trigger when user references PDFs, forms, or document extraction.
