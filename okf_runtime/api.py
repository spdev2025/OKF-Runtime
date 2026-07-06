"""Stable library-first API for OKF Runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import cache, metadata as metadata_module, scanner
from .compose import compose_bundle
from .graph import neighborhood
from .links import lint_links as lint_link_index


def discover(root: str | Path = ".") -> list[dict[str, object]]:
    return scanner.discover_bundles(root)


def catalog(root: str | Path = ".", include_links: bool = False) -> list[dict[str, Any]]:
    index = cache.load_or_rebuild(root)
    records = list(index.metadata_index.values())
    if include_links:
        for record in records:
            concept_id = str(record["id"])
            record["links"] = index.forward_links.get(concept_id, [])
            record["backlinks"] = index.reverse_links.get(concept_id, [])
    return sorted(records, key=lambda item: str(item["id"]))


def query(root: str | Path = ".", **filters: str) -> list[dict[str, Any]]:
    index = cache.load_or_rebuild(root)
    return metadata_module.query_metadata(index.metadata_index, filters)


def show(root: str | Path, concept_id: str, include_body: bool = False) -> dict[str, Any]:
    index = cache.load_or_rebuild(root)
    normalized = concept_id.removesuffix(".md")
    record = index.metadata_index.get(normalized)
    if record is None:
        raise KeyError(f"Unknown concept: {concept_id}")
    result = dict(record)
    if include_body:
        result["body"] = index.documents[normalized].body
    return result


def links(root: str | Path = ".", concept_id: str | None = None) -> dict[str, list[dict[str, Any]]] | list[dict[str, Any]]:
    index = cache.load_or_rebuild(root)
    if concept_id is None:
        return index.forward_links
    return index.forward_links.get(concept_id.removesuffix(".md"), [])


def backlinks(root: str | Path = ".", concept_id: str | None = None) -> dict[str, list[dict[str, Any]]] | list[dict[str, Any]]:
    index = cache.load_or_rebuild(root)
    if concept_id is None:
        return index.reverse_links
    return index.reverse_links.get(concept_id.removesuffix(".md"), [])


def graph(root: str | Path, concept_id: str, depth: int = 1) -> dict[str, Any]:
    index = cache.load_or_rebuild(root)
    normalized = concept_id.removesuffix(".md")
    if normalized not in index.metadata_index:
        raise KeyError(f"Unknown concept: {concept_id}")
    return neighborhood(normalized, index.forward_links, index.reverse_links, depth=depth)


def compose(root: str | Path, topic: str, output_dir: str | Path | None = None, depth: int = 1) -> dict[str, Any]:
    index = cache.load_or_rebuild(root)
    return compose_bundle(index, topic, output_dir=output_dir, depth=depth)


def lint_links(root: str | Path = ".") -> list[dict[str, Any]]:
    index = cache.load_or_rebuild(root)
    return lint_link_index(index.documents, index.forward_links, index.reverse_links)
