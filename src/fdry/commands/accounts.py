"""Foundry account provisioning."""

from __future__ import annotations

from pathlib import Path

import click

from fdry.commands._options import confirm_delete, yes_option
from fdry.core.context import Runtime, pass_runtime
from fdry.core.documents import load_document, request_body


@click.group()
def account() -> None:
    """Provision and inspect Foundry (AI Services) accounts."""


@account.command("list")
@pass_runtime
def account_list(runtime: Runtime) -> None:
    operations = runtime.management_client().accounts
    group = runtime.settings.get("resource_group")
    accounts = operations.list_by_resource_group(group) if group else operations.list()
    runtime.emit([item for item in accounts if item.kind == "AIServices"])


@account.command("show")
@pass_runtime
def account_show(runtime: Runtime) -> None:
    args = runtime.account_args()
    runtime.emit(runtime.management_client().accounts.get(*args))


@account.command("create")
@click.option("--location", help="Azure region. Required unless --file supplies the body.")
@click.option("--file", "document", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@pass_runtime
def account_create(runtime: Runtime, location: str | None, document: Path | None) -> None:
    """Create an account in an existing resource group."""
    if document:
        if location:
            raise click.UsageError("Use --file OR --location, not both.")
        body = load_document(document)
    else:
        if not location:
            raise click.UsageError("Provide --location or --file.")
        body = {
            "kind": "AIServices",
            "location": location,
            "sku": {"name": "S0"},
            "identity": {"type": "SystemAssigned"},
            "properties": {
                "allowProjectManagement": True,
                "customSubDomainName": runtime.require("account"),
                "disableLocalAuth": True,
            },
        }
    if body.get("kind") != "AIServices":
        raise click.UsageError("Foundry account body must use kind: AIServices.")
    args = runtime.account_args()
    runtime.emit(
        runtime.management_client().accounts.begin_create(*args, request_body(body)).result()
    )


@account.command("delete")
@yes_option
@pass_runtime
def account_delete(runtime: Runtime, yes: bool) -> None:
    args = runtime.account_args()
    confirm_delete(f"account {args[1]} and its child resources", yes)
    runtime.management_client().accounts.begin_delete(*args).result()
    runtime.emit({"deleted": args[1]})
