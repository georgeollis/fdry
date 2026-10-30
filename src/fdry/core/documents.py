"""JSON-compatible request documents and SDK wire-body adapters."""

from __future__ import annotations

import json
from collections.abc import Mapping
from io import BytesIO
from pathlib import Path
from typing import Any

import click
import yaml


def load_document(path: Path) -> dict[str, Any]:
    try:
        value: object = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
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
