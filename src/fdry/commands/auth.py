"""Azure SDK authentication diagnostics."""

import click

from fdry.core.context import Runtime, pass_runtime


@click.group()
def auth() -> None:
    """Check Azure SDK authentication. Use az login for interactive sign-in."""


@auth.command("status")
@pass_runtime
def auth_status(runtime: Runtime) -> None:
    """Acquire a Foundry token without printing its contents."""
    token = runtime.credential().get_token("https://ai.azure.com/.default")
    runtime.emit({"authenticated": True, "expires_on": token.expires_on})
