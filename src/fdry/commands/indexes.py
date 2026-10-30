"""Versioned Foundry search index references."""

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
def index() -> None:
    """Manage versioned search index references."""


@index.command("list")
@pass_runtime
def index_list(runtime: Runtime) -> None:
    runtime.emit(list(runtime.project_client().indexes.list()))


@index.command("show")
@name_option
@version_option
@pass_runtime
def index_show(runtime: Runtime, name: str, version: str) -> None:
    runtime.emit(runtime.project_client().indexes.get(name, version))


@index.command("versions")
@name_option
@pass_runtime
def index_versions(runtime: Runtime, name: str) -> None:
    runtime.emit(list(runtime.project_client().indexes.list_versions(name)))


@index.command("create")
@name_option
@version_option
@document_option
@pass_runtime
def index_create(runtime: Runtime, name: str, version: str, document: Path) -> None:
    runtime.emit(
        runtime.project_client().indexes.create_or_update(name, version, load_document(document))
    )


@index.command("delete")
@name_option
@version_option
@yes_option
@pass_runtime
def index_delete(runtime: Runtime, name: str, version: str, yes: bool) -> None:
    confirm_delete(f"index {name} version {version}", yes)
    runtime.project_client().indexes.delete(name, version)
    runtime.emit({"deleted": name, "version": version})
