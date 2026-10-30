"""Evaluation definitions and asynchronous evaluation runs."""

from pathlib import Path

import click

from fdry.commands._options import confirm_delete, document_option, yes_option
from fdry.core.context import Runtime, pass_runtime
from fdry.core.documents import load_document, openai_arguments


@click.group()
def evaluation() -> None:
    """Manage evaluations through the Foundry OpenAI API."""


@evaluation.command("list")
@pass_runtime
def evaluation_list(runtime: Runtime) -> None:
    runtime.emit(list(runtime.openai_client().evals.list()))


@evaluation.command("show")
@click.option("--id", "evaluation_id", required=True)
@pass_runtime
def evaluation_show(runtime: Runtime, evaluation_id: str) -> None:
    runtime.emit(runtime.openai_client().evals.retrieve(evaluation_id))


@evaluation.command("create")
@document_option
@pass_runtime
def evaluation_create(runtime: Runtime, document: Path) -> None:
    arguments = openai_arguments(
        load_document(document),
        required={"data_source_config", "testing_criteria"},
        optional={"metadata", "name"},
    )
    runtime.emit(runtime.openai_client().evals.create(**arguments))


@evaluation.command("delete")
@click.option("--id", "evaluation_id", required=True)
@yes_option
@pass_runtime
def evaluation_delete(runtime: Runtime, evaluation_id: str, yes: bool) -> None:
    confirm_delete(f"evaluation {evaluation_id}", yes)
    runtime.emit(runtime.openai_client().evals.delete(evaluation_id))


@evaluation.group("run")
def evaluation_run() -> None:
    """Submit and inspect evaluation runs."""


@evaluation_run.command("create")
@click.option("--evaluation-id", required=True)
@document_option
@pass_runtime
def run_create(runtime: Runtime, evaluation_id: str, document: Path) -> None:
    arguments = openai_arguments(
        load_document(document), required={"data_source"}, optional={"name", "metadata"}
    )
    runtime.emit(runtime.openai_client().evals.runs.create(evaluation_id, **arguments))


@evaluation_run.command("list")
@click.option("--evaluation-id", required=True)
@pass_runtime
def run_list(runtime: Runtime, evaluation_id: str) -> None:
    runtime.emit(list(runtime.openai_client().evals.runs.list(evaluation_id)))


@evaluation_run.command("show")
@click.option("--evaluation-id", required=True)
@click.option("--id", "run_id", required=True)
@pass_runtime
def run_show(runtime: Runtime, evaluation_id: str, run_id: str) -> None:
    runtime.emit(runtime.openai_client().evals.runs.retrieve(run_id, eval_id=evaluation_id))


@evaluation_run.command("cancel")
@click.option("--evaluation-id", required=True)
@click.option("--id", "run_id", required=True)
@pass_runtime
def run_cancel(runtime: Runtime, evaluation_id: str, run_id: str) -> None:
    runtime.emit(runtime.openai_client().evals.runs.cancel(run_id, eval_id=evaluation_id))
