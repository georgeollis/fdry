"""Account quota inspection."""

import click

from fdry.core.context import Runtime, pass_runtime


@click.group()
def quota() -> None:
    """Inspect account quota and usage."""


@quota.command("list")
@pass_runtime
def quota_list(runtime: Runtime) -> None:
    args = runtime.account_args()
    runtime.emit(runtime.management_client().accounts.list_usages(*args))
