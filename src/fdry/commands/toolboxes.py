"""Toolbox version lifecycle and publication."""

from pathlib import Path

import click

from fdry.commands._options import (
    confirm_delete,
    document_option,
    name_option,
    version_option,
    yes_option,
)
from fdry.core.context import Runtime, pass_runtime
from fdry.core.documents import load_document


@click.group()
def toolbox() -> None:
    """Create, version, publish, and delete toolboxes."""


@toolbox.command("list")
@pass_runtime
def toolbox_list(runtime: Runtime) -> None:
    runtime.emit(list(runtime.project_client().toolboxes.list()))


@toolbox.command("show")
@name_option
@click.option("--version", help="Show a specific version instead of toolbox details.")
@pass_runtime
def toolbox_show(runtime: Runtime, name: str, version: str | None) -> None:
    operations = runtime.project_client().toolboxes
    runtime.emit(operations.get_version(name, version) if version else operations.get(name))


@toolbox.command("versions")
@name_option
@pass_runtime
def toolbox_versions(runtime: Runtime, name: str) -> None:
    runtime.emit(list(runtime.project_client().toolboxes.list_versions(name)))


@toolbox.command("create")
@name_option
@document_option
@pass_runtime
def toolbox_create(runtime: Runtime, name: str, document: Path) -> None:
    """Create an immutable version. The service assigns its version number."""
    body = load_document(document)
    if not isinstance(body.get("tools"), list):
        raise click.UsageError("Toolbox body must contain a tools array.")
    runtime.emit(runtime.project_client().toolboxes.create_version(name, body))


@toolbox.command("publish")
@name_option
@version_option
@pass_runtime
def toolbox_publish(runtime: Runtime, name: str, version: str) -> None:
    """Set the toolbox's default version."""
    runtime.emit(runtime.project_client().toolboxes.update(name, default_version=version))


@toolbox.command("delete")
@name_option
@version_option
@yes_option
@pass_runtime
def toolbox_delete(runtime: Runtime, name: str, version: str, yes: bool) -> None:
    confirm_delete(f"toolbox {name} version {version}", yes)
    runtime.project_client().toolboxes.delete_version(name, version)
    runtime.emit({"deleted": name, "version": version})


@toolbox.command("delete-all")
@name_option
@yes_option
@pass_runtime
def toolbox_delete_all(runtime: Runtime, name: str, yes: bool) -> None:
    """Delete a toolbox and all its versions."""
    confirm_delete(f"toolbox {name} and all versions", yes)
    runtime.project_client().toolboxes.delete(name)
    runtime.emit({"deleted": name})
