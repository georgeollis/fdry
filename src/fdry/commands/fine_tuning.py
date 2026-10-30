"""Foundry fine-tuning job submission and monitoring."""

from pathlib import Path

import click

from fdry.commands._options import document_option
from fdry.core.context import Runtime, pass_runtime
from fdry.core.documents import load_document, openai_arguments


@click.group("fine-tuning")
def fine_tuning() -> None:
    """Create, inspect, and cancel fine-tuning jobs."""


@fine_tuning.command("list")
@pass_runtime
def fine_tuning_list(runtime: Runtime) -> None:
    runtime.emit(list(runtime.openai_client().fine_tuning.jobs.list()))


@fine_tuning.command("show")
@click.option("--id", "job_id", required=True)
@pass_runtime
def fine_tuning_show(runtime: Runtime, job_id: str) -> None:
    runtime.emit(runtime.openai_client().fine_tuning.jobs.retrieve(job_id))


@fine_tuning.command("create")
@document_option
@pass_runtime
def fine_tuning_create(runtime: Runtime, document: Path) -> None:
    arguments = openai_arguments(
        load_document(document),
        required={"model", "training_file"},
        optional={
            "hyperparameters",
            "integrations",
            "metadata",
            "method",
            "seed",
            "suffix",
            "validation_file",
        },
    )
    runtime.emit(runtime.openai_client().fine_tuning.jobs.create(**arguments))


@fine_tuning.command("cancel")
@click.option("--id", "job_id", required=True)
@pass_runtime
def fine_tuning_cancel(runtime: Runtime, job_id: str) -> None:
    runtime.emit(runtime.openai_client().fine_tuning.jobs.cancel(job_id))
