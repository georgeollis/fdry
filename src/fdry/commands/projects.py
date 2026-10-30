"""Projects under a Foundry account."""

from __future__ import annotations

from pathlib import Path

import click

from fdry.commands._options import confirm_delete, name_option, yes_option
from fdry.core.context import Runtime, pass_runtime
from fdry.core.documents import load_document, request_body


@click.group()
def project() -> None:
    """List, inspect, provision, and delete projects under a Foundry account."""


@project.command("list")
@pass_runtime
def project_list(runtime: Runtime) -> None:
    args = runtime.account_args()
    runtime.emit(list(runtime.management_client().projects.list(*args)))


@project.command("show")
@name_option
@pass_runtime
def project_show(runtime: Runtime, name: str) -> None:
    args = runtime.account_args()
    runtime.emit(runtime.management_client().projects.get(*args, name))


@project.command("create")
@name_option
@click.option("--location", help="Parent account's region. Required unless using --file.")
@click.option("--file", "document", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@pass_runtime
def project_create(
    runtime: Runtime, name: str, location: str | None, document: Path | None
) -> None:
    """Create a project."""
    if document:
        if location:
            raise click.UsageError("Use --file OR --location, not both.")
        body = load_document(document)
    else:
        if not location:
            raise click.UsageError("Provide --location or --file.")
        body = {
            "location": location,
            "identity": {"type": "SystemAssigned"},
            "properties": {"displayName": name},
        }
    args = runtime.account_args()
    runtime.emit(
        runtime.management_client().projects.begin_create(*args, name, request_body(body)).result()
    )


@project.command("delete")
@name_option
@yes_option
@pass_runtime
def project_delete(runtime: Runtime, name: str, yes: bool) -> None:
    args = runtime.account_args()
    confirm_delete(f"project {name} and its child resources", yes)
    runtime.management_client().projects.begin_delete(*args, name).result()
    runtime.emit({"deleted": name})
