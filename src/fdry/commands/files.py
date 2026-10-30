"""OpenAI-protocol file uploads for training and evaluation."""

from pathlib import Path
from typing import Literal

import click

from fdry.commands._options import confirm_delete, yes_option
from fdry.core.context import Runtime, pass_runtime


@click.group("file")
def files() -> None:
    """Upload and inspect files for fine-tuning and evaluations."""


@files.command("upload")
@click.option("--path", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--purpose", type=click.Choice(["fine-tune", "evals", "assistants"]), required=True)
@pass_runtime
def file_upload(
    runtime: Runtime, path: Path, purpose: Literal["fine-tune", "evals", "assistants"]
) -> None:
    try:
        with path.open("rb") as handle:
            result = runtime.openai_client().files.create(file=handle, purpose=purpose)
    except OSError as exc:
        raise click.ClickException(f"Cannot open {path}: {exc}") from exc
    runtime.emit(result)


@files.command("list")
@pass_runtime
def file_list(runtime: Runtime) -> None:
    runtime.emit(list(runtime.openai_client().files.list()))


@files.command("show")
@click.option("--id", "file_id", required=True)
@pass_runtime
def file_show(runtime: Runtime, file_id: str) -> None:
    runtime.emit(runtime.openai_client().files.retrieve(file_id))


@files.command("delete")
@click.option("--id", "file_id", required=True)
@yes_option
@pass_runtime
def file_delete(runtime: Runtime, file_id: str, yes: bool) -> None:
    confirm_delete(f"file {file_id}", yes)
    runtime.emit(runtime.openai_client().files.delete(file_id))
