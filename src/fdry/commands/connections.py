"""Connection reads through Foundry and writes through Azure management."""

from pathlib import Path

import click

from fdry.commands._options import (
    confirm_delete,
    document_option,
    name_option,
    yes_option,
)
from fdry.core.context import Runtime, pass_runtime
from fdry.core.documents import load_document, request_body


@click.group()
def connection() -> None:
    """Read project connections and provision them through Azure management APIs."""


@connection.command("list")
@pass_runtime
def connection_list(runtime: Runtime) -> None:
    runtime.emit(list(runtime.project_client().connections.list()))


@connection.command("show")
@name_option
@pass_runtime
def connection_show(runtime: Runtime, name: str) -> None:
    runtime.emit(runtime.project_client().connections.get(name, include_credentials=False))


@connection.command("create")
@name_option
@document_option
@pass_runtime
def connection_create(runtime: Runtime, name: str, document: Path) -> None:
    """Create/update a project connection from an ARM connection resource body."""
    body = load_document(document)
    if not isinstance(body.get("properties"), dict):
        raise click.UsageError("Connection body must contain a properties object.")
    args = runtime.connection_args()
    runtime.emit(
        runtime.management_client().project_connections.create(*args, name, request_body(body))
    )


@connection.command("delete")
@name_option
@yes_option
@pass_runtime
def connection_delete(runtime: Runtime, name: str, yes: bool) -> None:
    args = runtime.connection_args()
    confirm_delete(f"connection {name}", yes)
    runtime.management_client().project_connections.delete(*args, name)
    runtime.emit({"deleted": name})
