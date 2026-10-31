"""JSON-compatible request documents and SDK wire-body adapters."""

from __future__ import annotations

import json
from collections.abc import Hashable, Mapping
from io import BytesIO
from pathlib import Path
from typing import Any

import click
import yaml


class DocumentLoader(yaml.SafeLoader):
    def construct_mapping(self, node: yaml.Node, deep: bool = False) -> dict[Hashable, Any]:
        if not isinstance(node, yaml.MappingNode):
            raise yaml.constructor.ConstructorError(
                None, None, "Expected an object.", node.start_mark
            )
        keys: set[str] = set()
        for key_node, _ in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                continue
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise yaml.constructor.ConstructorError(
                    None, None, "Object keys must be strings.", key_node.start_mark
                )
            if key in keys:
                raise yaml.constructor.ConstructorError(
                    None, None, f"Duplicate object key: {key}.", key_node.start_mark
                )
            keys.add(key)
        return super().construct_mapping(node, deep=deep)


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate object key: {key}.")
        result[key] = value
    return result


def load_document(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8-sig")
        value: object = (
            json.loads(text, object_pairs_hook=_json_object)
            if path.suffix.lower() == ".json"
            else yaml.load(text, Loader=DocumentLoader)
        )
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
        raise click.BadParameter(f"Cannot read {path}: {exc}", param_hint="--file") from exc
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise click.BadParameter("Expected a JSON/YAML object.", param_hint="--file")
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise click.BadParameter(
            f"Request body must contain JSON-compatible values: {exc}", param_hint="--file"
        ) from exc
    return value


def request_body(document: Mapping[str, object]) -> BytesIO:
    """Preserve ARM wire names and polymorphic credentials through the management SDK."""
    return BytesIO(json.dumps(document, allow_nan=False).encode("utf-8"))


def openai_arguments(
    body: dict[str, Any], *, required: set[str], optional: set[str]
) -> dict[str, Any]:
    missing = required - body.keys()
    if missing:
        raise click.UsageError(f"Request body is missing: {', '.join(sorted(missing))}.")
    if {"extra_body", "extra_headers", "extra_query", "timeout"}.intersection(body):
        raise click.UsageError("Request body must contain API fields, not SDK transport options.")
    parameters = required | optional
    arguments = {key: value for key, value in body.items() if key in parameters}
    extra = {key: value for key, value in body.items() if key not in parameters}
    if extra:
        arguments["extra_body"] = extra
    return arguments
