"""Shared Click parameters and destructive-action confirmation."""

from pathlib import Path

import click

name_option = click.option("--name", "-n", required=True, help="Resource name.")
version_option = click.option("--version", required=True, help="Resource version.")
yes_option = click.option("--yes", "-y", is_flag=True, help="Skip delete confirmation.")
document_option = click.option(
    "--file",
    "document",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="JSON/YAML body, using service wire-format field names.",
)


def confirm_delete(resource: str, yes: bool) -> None:
    if not yes:
        click.confirm(f"Delete {resource}? This cannot be undone", abort=True, err=True)
