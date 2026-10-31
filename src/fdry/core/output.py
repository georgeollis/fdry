"""Consistent SDK serialization and secret redaction across output formats."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from datetime import date, datetime
from enum import Enum
from typing import Any

import click
import yaml

SECRET_KEYS = {
    "authorization",
    "headers",
    "credentials",
    "apikey",
    "key",
    "token",
    "accesstoken",
    "refreshtoken",
    "sastoken",
    "primarykey",
    "secondarykey",
    "password",
    "secret",
    "clientsecret",
    "connectionstring",
    "environmentvariables",
}


def plain(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return plain(value.model_dump(mode="json"))
    if hasattr(value, "as_dict"):
        return plain(value.as_dict())
    if isinstance(value, Mapping):
        return {
            str(key): (
                "[REDACTED]"
                if str(key).lower().replace("_", "").replace("-", "") in SECRET_KEYS
                else plain(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Enum):
        return plain(value.value)
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Non-finite numbers are not valid response values.")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def emit(value: Any, output: str) -> None:
    try:
        data = plain(value)
        if output == "yaml":
            click.echo(yaml.safe_dump(data, sort_keys=False).rstrip())
        elif output == "table":
            _table(data)
        else:
            click.echo(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False))
    except (TypeError, ValueError, yaml.YAMLError) as exc:
        raise click.ClickException("Cannot serialize the service response.") from exc


def _table(data: Any) -> None:
    rows = data if isinstance(data, list) else [data]
    if not rows:
        click.echo("(no results)")
        return
    if not all(isinstance(row, dict) for row in rows):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return
    columns = list(dict.fromkeys(key for row in rows for key in row))
    if not columns:
        click.echo(json.dumps(data))
        return
    rendered = [[json.dumps(row.get(key), ensure_ascii=False) for key in columns] for row in rows]
    widths = [
        max(len(key), *(len(row[index]) for row in rendered)) for index, key in enumerate(columns)
    ]
    click.echo("  ".join(key.ljust(width) for key, width in zip(columns, widths, strict=True)))
    click.echo("  ".join("-" * width for width in widths))
    for row in rendered:
        click.echo("  ".join(item.ljust(width) for item, width in zip(row, widths, strict=True)))
