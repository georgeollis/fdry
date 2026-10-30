"""Versioned datasets and local uploads."""

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
def dataset() -> None:
    """Manage versioned datasets and upload local files or folders."""


@dataset.command("list")
@pass_runtime
def dataset_list(runtime: Runtime) -> None:
    runtime.emit(list(runtime.project_client().datasets.list()))


@dataset.command("show")
@name_option
@version_option
@pass_runtime
def dataset_show(runtime: Runtime, name: str, version: str) -> None:
    runtime.emit(runtime.project_client().datasets.get(name, version))


@dataset.command("versions")
@name_option
@pass_runtime
def dataset_versions(runtime: Runtime, name: str) -> None:
    runtime.emit(list(runtime.project_client().datasets.list_versions(name)))


@dataset.command("create")
@name_option
@version_option
@document_option
@pass_runtime
def dataset_create(runtime: Runtime, name: str, version: str, document: Path) -> None:
    runtime.emit(
        runtime.project_client().datasets.create_or_update(name, version, load_document(document))
    )


@dataset.command("delete")
@name_option
@version_option
@yes_option
@pass_runtime
def dataset_delete(runtime: Runtime, name: str, version: str, yes: bool) -> None:
    confirm_delete(f"dataset {name} version {version}", yes)
    runtime.project_client().datasets.delete(name, version)
    runtime.emit({"deleted": name, "version": version})


@dataset.command("upload")
@name_option
@version_option
@click.option(
    "--path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Local file or folder.",
)
@click.option("--connection", help="Storage connection name.")
@pass_runtime
def dataset_upload(
    runtime: Runtime, name: str, version: str, path: Path, connection: str | None
) -> None:
    operations = runtime.project_client().datasets
    if path.is_dir():
        runtime.emit(
            operations.upload_folder(
                name=name, version=version, folder=str(path), connection_name=connection
            )
        )
    else:
        runtime.emit(
            operations.upload_file(
                name=name, version=version, file_path=str(path), connection_name=connection
            )
        )
