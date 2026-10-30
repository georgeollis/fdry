"""Non-secret profile persistence and endpoint validation."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import TypedDict
from urllib.parse import unquote, urlsplit

import click

SETTING_ENV = {
    "endpoint": "AZURE_AI_PROJECT_ENDPOINT",
    "subscription": "AZURE_SUBSCRIPTION_ID",
    "resource_group": "AZURE_RESOURCE_GROUP",
    "account": "AZURE_AI_ACCOUNT_NAME",
    "project": "AZURE_AI_PROJECT_NAME",
}


class ConfigData(TypedDict):
    profiles: dict[str, dict[str, str]]


def config_path() -> Path:
    override = os.getenv("FDRY_CONFIG")
    return Path(override) if override else Path.home() / ".fdry" / "config.json"


def read_config() -> ConfigData:
    path = config_path()
    if not path.exists():
        return {"profiles": {}}
    try:
        value: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise click.ClickException(f"Cannot read configuration {path}: {exc}") from exc
    if not isinstance(value, dict) or not isinstance(value.get("profiles"), dict):
        raise click.ClickException(f"Invalid configuration in {path}: expected a profiles object.")
    for name, settings in value["profiles"].items():
        if not isinstance(settings, dict) or any(
            key not in SETTING_ENV or not isinstance(item, str) for key, item in settings.items()
        ):
            raise click.ClickException(f"Invalid configuration for profile {name!r}.")
    return {"profiles": value["profiles"]}


def write_config(value: ConfigData) -> None:
    path = config_path()
    temporary: str | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as handle:
            temporary = handle.name
            json.dump(value, handle, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    except OSError as exc:
        raise click.ClickException(f"Cannot save configuration {path}: {exc}") from exc
    finally:
        if temporary and Path(temporary).exists():
            Path(temporary).unlink()


def validate_endpoint(value: str) -> str:
    try:
        parsed = urlsplit(value)
        _ = parsed.port
    except ValueError as exc:
        raise click.BadParameter(
            "Endpoint contains an invalid host or port.", param_hint="--endpoint"
        ) from exc
    path = unquote(parsed.path)
    segments = path.rstrip("/").split("/")
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or len(segments) != 4
        or segments[:3] != ["", "api", "projects"]
        or segments[-1] in {"", ".", ".."}
        or "%" in path
        or "\\" in value
        or any(character.isspace() for character in value)
    ):
        raise click.BadParameter(
            "Expected https://<account>.services.ai.azure.com/api/projects/<project>.",
            param_hint="--endpoint",
        )
    return value.rstrip("/")
