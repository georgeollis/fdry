"""Root command, global options, and SDK error presentation."""

from __future__ import annotations

from typing import Any

import click
from azure.core.exceptions import AzureError
from openai import OpenAIError

from fdry import __version__
from fdry.commands import register_commands
from fdry.core.config import SETTING_ENV, read_config
from fdry.core.context import Runtime


class FoundryGroup(click.Group):
    def invoke(self, ctx: click.Context) -> Any:
        try:
            return super().invoke(ctx)
        except (AzureError, OpenAIError) as exc:
            raise click.ClickException(str(exc)) from exc


@click.group(
    name="fdry", cls=FoundryGroup, context_settings={"help_option_names": ["-h", "--help"]}
)
@click.version_option(__version__, prog_name="fdry")
@click.option("--profile", default="default", envvar="FDRY_PROFILE", show_default=True)
@click.option("--endpoint", envvar=SETTING_ENV["endpoint"], help="Foundry project endpoint.")
@click.option("--subscription", envvar=SETTING_ENV["subscription"], help="Azure subscription ID.")
@click.option("--resource-group", envvar=SETTING_ENV["resource_group"])
@click.option("--account", envvar=SETTING_ENV["account"], help="Foundry account name.")
@click.option("--project", envvar=SETTING_ENV["project"], help="Project name for management calls.")
@click.option("-o", "--output", type=click.Choice(["json", "yaml", "table"]), default="json")
@click.option("--preview", is_flag=True, help="Opt in to SDK preview features.")
@click.pass_context
def cli(
    ctx: click.Context, /, profile: str, output: str, preview: bool, **options: str | None
) -> None:
    """Manage Microsoft Foundry resources.

    Place global options before the command. Authenticate with `az login` or
    DefaultAzureCredential environment/managed identity credentials.
    """
    settings = dict(read_config()["profiles"].get(profile, {}))
    settings.update({key: value for key, value in options.items() if value is not None})
    runtime = Runtime(profile=profile, settings=settings, output=output, preview=preview)
    ctx.obj = runtime
    ctx.call_on_close(runtime.stack.close)


register_commands(cli)


def main() -> None:
    cli()
