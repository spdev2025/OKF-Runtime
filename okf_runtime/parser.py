"""Markdown and frontmatter parsing."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from .models import Document, Link, MarkdownFile

FRONTMATTER_BOUNDARY = "---"
LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$", re.MULTILINE)
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def parse_document(file: MarkdownFile, root: str | Path) -> Document:
    root_path = Path(root).resolve()
    text = file.path.read_text(encoding="utf-8")
    metadata, body, errors = split_frontmatter(text, allow_missing=file.is_reserved)
    links = extract_links(body, file.relative_path, root_path)
    anchors = extract_anchors(body)
    if not file.is_reserved and not str(metadata.get("type", "")).strip():
        errors.append("Missing required non-empty frontmatter field: type")
    return Document(
        path=file.path,
        relative_path=file.relative_path,
        concept_id=file.concept_id,
        is_reserved=file.is_reserved,
        metadata=metadata,
        body=body,
        links=links,
        anchors=anchors,
        errors=errors,
    )


def parse_documents(files: list[MarkdownFile], root: str | Path) -> dict[str, Document]:
    return {item.concept_id: parse_document(item, root) for item in files}


def split_frontmatter(text: str, allow_missing: bool = False) -> tuple[dict[str, Any], str, list[str]]:
    errors: list[str] = []
    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_BOUNDARY:
        if allow_missing:
            return {}, text, errors
        return {}, text, ["Missing YAML frontmatter block"]

    end_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == FRONTMATTER_BOUNDARY:
            end_index = index
            break

    if end_index is None:
        return {}, text, ["Unclosed YAML frontmatter block"]

    frontmatter = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :])
    metadata, parse_errors = parse_frontmatter(frontmatter)
    errors.extend(parse_errors)
    return metadata, body, errors


def parse_frontmatter(text: str) -> tuple[dict[str, Any], list[str]]:
    """Parse the small YAML subset used by OKF frontmatter.

    Supports scalar keys and inline lists. This keeps Phase 1 dependency-free
    while accepting the frontmatter shape in the OKF minimal spec.
    """

    metadata: dict[str, Any] = {}
    errors: list[str] = []
    current_key: str | None = None
    current_list: list[str] | None = None

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if current_key and stripped.startswith("- "):
            assert current_list is not None
            current_list.append(_parse_scalar(stripped[2:].strip()))
            continue

        current_key = None
        current_list = None
        if ":" not in line:
            errors.append(f"Invalid frontmatter line {line_number}: expected key: value")
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            errors.append(f"Invalid frontmatter line {line_number}: empty key")
            continue

        if value == "":
            current_key = key
            current_list = []
            metadata[key] = current_list
        else:
            metadata[key] = _parse_value(value)

    return metadata, errors


def _parse_value(value: str) -> Any:
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part.strip()) for part in _split_inline_list(inner)]
    return _parse_scalar(value)


def _parse_scalar(value: str) -> str | bool | int | float | None:
    if value in {"null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _split_inline_list(value: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    quote: str | None = None
    for char in value:
        if char in {"'", '"'}:
            quote = None if quote == char else char if quote is None else quote
        if char == "," and quote is None:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return parts


def extract_links(body: str, source_relative_path: str, root: Path) -> list[Link]:
    links: list[Link] = []
    for match in LINK_RE.finditer(body):
        text = match.group(1)
        raw_target = match.group(2).strip()
        target_without_title = raw_target.split(maxsplit=1)[0]
        target, anchor = split_anchor(target_without_title)
        is_external = is_external_link(target)
        resolved = None if is_external else resolve_internal_link(target, source_relative_path, root)
        links.append(
            Link(
                text=text,
                target=target,
                raw_target=raw_target,
                anchor=anchor,
                is_external=is_external,
                resolved_path=resolved,
            )
        )
    return links


def split_anchor(target: str) -> tuple[str, str | None]:
    if "#" not in target:
        return target, None
    path, anchor = target.split("#", 1)
    return path, anchor or None


def is_external_link(target: str) -> bool:
    if target.startswith("#"):
        return False
    return bool(SCHEME_RE.match(target)) or target.startswith("mailto:")


def resolve_internal_link(target: str, source_relative_path: str, root: Path) -> str | None:
    if not target or target.startswith("#"):
        return source_relative_path
    decoded = unquote(target)
    parsed = urlparse(decoded)
    path_text = parsed.path
    if not path_text:
        return source_relative_path

    if path_text.startswith("/"):
        candidate = root / path_text.lstrip("/")
    else:
        candidate = root / Path(source_relative_path).parent / path_text
    normalized = candidate.resolve()
    try:
        return normalized.relative_to(root).as_posix()
    except ValueError:
        return None


def extract_anchors(body: str) -> list[str]:
    anchors: list[str] = []
    for match in HEADING_RE.finditer(body):
        anchors.append(slugify_heading(match.group(2)))
    return anchors


def slugify_heading(text: str) -> str:
    value = re.sub(r"`([^`]*)`", r"\1", text).strip().lower()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"\s+", "-", value)
    return value.strip("-")
