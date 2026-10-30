"""Model discovery, Azure deployment, and inference."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import click

from fdry.commands._options import confirm_delete, name_option, yes_option
from fdry.core.context import Runtime, pass_runtime
from fdry.core.documents import load_document, request_body


@click.group()
def model() -> None:
    """Discover, deploy, invoke, and delete models.

    Creating a model means deploying a catalog model, not training new model weights.
    """


@model.command("list")
@pass_runtime
def model_list(runtime: Runtime) -> None:
    """List deployments visible to the selected project."""
    runtime.emit(list(runtime.project_client().deployments.list()))


@model.command("show")
@name_option
@pass_runtime
def model_show(runtime: Runtime, name: str) -> None:
    runtime.emit(runtime.project_client().deployments.get(name))


@model.command("catalog")
@click.option("--location", help="List regional models; otherwise list account-available models.")
@pass_runtime
def model_catalog(runtime: Runtime, location: str | None) -> None:
    if location:
        runtime.emit(list(runtime.management_client().models.list(location)))
    else:
        args = runtime.account_args()
        runtime.emit(list(runtime.management_client().accounts.list_models(*args)))


@model.command("create")
@name_option
@click.option("--model", "model_name", help="Catalog model name.")
@click.option("--model-version", help="Explicit catalog model version.")
@click.option("--format", "model_format", default="OpenAI", show_default=True)
@click.option("--sku", default="GlobalStandard", show_default=True)
@click.option("--capacity", type=click.IntRange(min=1), default=1, show_default=True)
@click.option("--file", "document", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@pass_runtime
def model_create(
    runtime: Runtime,
    name: str,
    model_name: str | None,
    model_version: str | None,
    model_format: str,
    sku: str,
    capacity: int,
    document: Path | None,
) -> None:
    """Deploy a model. Advanced/provider-specific deployment bodies use --file."""
    if document:
        ctx = click.get_current_context()
        conflicting = [
            option
            for option in ("model_name", "model_version", "model_format", "sku", "capacity")
            if ctx.get_parameter_source(option) == click.core.ParameterSource.COMMANDLINE
        ]
        if conflicting:
            raise click.UsageError("Use --file OR model deployment options, not both.")
        body = load_document(document)
    else:
        if not model_name or not model_version:
            raise click.UsageError("Provide --file, or both --model and --model-version.")
        body = {
            "sku": {"name": sku, "capacity": capacity},
            "properties": {
                "model": {"format": model_format, "name": model_name, "version": model_version}
            },
        }
    args = runtime.account_args()
    runtime.emit(
        runtime.management_client()
        .deployments.begin_create_or_update(*args, name, request_body(body))
        .result()
    )


@model.command("invoke")
@name_option
@click.option("--input", "prompt", required=True)
@click.option(
    "--api",
    type=click.Choice(["responses", "chat"]),
    default="responses",
    show_default=True,
    help="Model inference API.",
)
@pass_runtime
def model_invoke(
    runtime: Runtime, name: str, prompt: str, api: Literal["responses", "chat"]
) -> None:
    """Invoke a model using Responses or Chat Completions."""
    client = runtime.openai_client()
    if api == "chat":
        runtime.emit(
            client.chat.completions.create(
                model=name, messages=[{"role": "user", "content": prompt}]
            )
        )
    else:
        runtime.emit(client.responses.create(model=name, input=prompt))


@model.command("embeddings")
@name_option
@click.option("--input", "text", required=True)
@pass_runtime
def model_embeddings(runtime: Runtime, name: str, text: str) -> None:
    """Invoke an embeddings model deployment."""
    runtime.emit(runtime.openai_client().embeddings.create(model=name, input=text))


@model.command("delete")
@name_option
@yes_option
@pass_runtime
def model_delete(runtime: Runtime, name: str, yes: bool) -> None:
    args = runtime.account_args()
    confirm_delete(f"model deployment {name}", yes)
    runtime.management_client().deployments.begin_delete(*args, name).result()
    runtime.emit({"deleted": name})
