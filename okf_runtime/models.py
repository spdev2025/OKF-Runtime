"""Shared data models for the OKF runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


RESERVED_FILENAMES = {"index.md", "log.md"}


@dataclass(frozen=True)
class MarkdownFile:
    """A markdown file discovered in a bundle."""

    path: Path
    relative_path: str
    mtime: float
    size: int

    @property
    def is_reserved(self) -> bool:
        return Path(self.relative_path).name in RESERVED_FILENAMES

    @property
    def concept_id(self) -> str:
        rel = self.relative_path.replace("\\", "/")
        return rel[:-3] if rel.endswith(".md") else rel


@dataclass(frozen=True)
class Link:
    """A markdown link found in a document."""

    text: str
    target: str
    raw_target: str
    anchor: str | None = None
    is_external: bool = False
    resolved_path: str | None = None


@dataclass
class Document:
    """A parsed markdown document."""

    path: Path
    relative_path: str
    concept_id: str
    is_reserved: bool
    metadata: dict[str, Any]
    body: str
    links: list[Link] = field(default_factory=list)
    anchors: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def title(self) -> str | None:
        value = self.metadata.get("title")
        return str(value) if value is not None else None

    @property
    def type(self) -> str | None:
        value = self.metadata.get("type")
        return str(value) if value is not None else None

    def to_catalog_record(self) -> dict[str, Any]:
        return {
            "id": self.concept_id,
            "path": self.relative_path,
            "reserved": self.is_reserved,
            "metadata": self.metadata,
            "errors": self.errors,
        }


@dataclass
class RuntimeIndex:
    """Derived runtime state for a bundle."""

    root: Path
    documents: dict[str, Document]
    forward_links: dict[str, list[dict[str, Any]]]
    reverse_links: dict[str, list[dict[str, Any]]]
    metadata_index: dict[str, dict[str, Any]]
    tag_index: dict[str, list[str]]
    type_index: dict[str, list[str]]
    stale_rebuilt: bool = False

    def concept_ids(self) -> list[str]:
        return sorted(self.metadata_index)
