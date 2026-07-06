"""Metadata catalogs and indexes."""

from __future__ import annotations

from typing import Any

from .models import Document


def build_metadata_index(documents: dict[str, Document]) -> dict[str, dict[str, Any]]:
    return {
        concept_id: document.to_catalog_record()
        for concept_id, document in sorted(documents.items())
        if not document.is_reserved
    }


def build_tag_index(metadata_index: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for concept_id, record in metadata_index.items():
        tags = record["metadata"].get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        if not isinstance(tags, list):
            continue
        for tag in tags:
            index.setdefault(str(tag), []).append(concept_id)
    return {key: sorted(value) for key, value in sorted(index.items())}


def build_type_index(metadata_index: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for concept_id, record in metadata_index.items():
        doc_type = record["metadata"].get("type")
        if doc_type is None:
            continue
        index.setdefault(str(doc_type), []).append(concept_id)
    return {key: sorted(value) for key, value in sorted(index.items())}


def query_metadata(metadata_index: dict[str, dict[str, Any]], filters: dict[str, str]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for record in metadata_index.values():
        metadata = record["metadata"]
        if all(_matches(metadata, key, value) for key, value in filters.items()):
            matches.append(record)
    return sorted(matches, key=lambda item: str(item["id"]))


def _matches(metadata: dict[str, Any], key: str, expected: str) -> bool:
    value = metadata.get(key)
    if isinstance(value, list):
        return expected in {str(item) for item in value}
    return str(value) == expected
