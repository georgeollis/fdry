"""Local configuration commands; never persist authentication credentials."""

import click

from fdry.core.config import SETTING_ENV, read_config, validate_endpoint, write_config
from fdry.core.context import Runtime, pass_runtime


@click.group()
def config() -> None:
    """Manage non-secret, named configuration profiles."""


@config.command("set")
@click.argument("key", type=click.Choice(list(SETTING_ENV)))
@click.argument("value")
@pass_runtime
def config_set(runtime: Runtime, key: str, value: str) -> None:
    """Save one setting in the selected profile."""
    if not value.strip():
        raise click.BadParameter("Value must not be empty.")
    if key == "endpoint":
        value = validate_endpoint(value)
    data = read_config()
    data["profiles"].setdefault(runtime.profile, {})[key] = value
    write_config(data)
    runtime.emit({"profile": runtime.profile, "setting": key, "value": value})


@config.command("show")
@pass_runtime
def config_show(runtime: Runtime) -> None:
    """Show effective settings (flags > environment > profile)."""
    runtime.emit({"profile": runtime.profile, **runtime.settings})


@config.command("list")
@pass_runtime
def config_list(runtime: Runtime) -> None:
    """List saved profiles."""
    runtime.emit(read_config()["profiles"])


@config.command("unset")
@click.argument("key", type=click.Choice(list(SETTING_ENV)))
@pass_runtime
def config_unset(runtime: Runtime, key: str) -> None:
    """Remove a saved setting from the selected profile."""
    data = read_config()
    settings = data["profiles"].get(runtime.profile, {})
    if key not in settings:
        raise click.ClickException(f"{key} is not saved in profile {runtime.profile!r}.")
    del settings[key]
    write_config(data)
    runtime.emit({"removed": key, "profile": runtime.profile})
