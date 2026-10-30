"""Agent definitions, versions, invocation, and availability."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import click

from fdry.commands._options import confirm_delete, name_option, yes_option
from fdry.core.context import Runtime, pass_runtime
from fdry.core.documents import load_document


@click.group()
def agent() -> None:
    """Create, version, inspect, invoke, and delete prompt or hosted agents."""


@agent.command("list")
@pass_runtime
def agent_list(runtime: Runtime) -> None:
    runtime.emit(list(runtime.project_client().agents.list()))


@agent.command("show")
@name_option
@click.option("--version", help="Show a specific version instead of agent details.")
@pass_runtime
def agent_show(runtime: Runtime, name: str, version: str | None) -> None:
    operations = runtime.project_client().agents
    runtime.emit(operations.get_version(name, version) if version else operations.get(name))


@agent.command("versions")
@name_option
@pass_runtime
def agent_versions(runtime: Runtime, name: str) -> None:
    runtime.emit(list(runtime.project_client().agents.list_versions(name)))


@agent.command("create")
@name_option
@click.option("--model", help="Model deployment name for a prompt agent.")
@click.option("--instructions", help="Prompt-agent instructions.")
@click.option(
    "--file",
    "document",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="JSON/YAML create-version body; required for hosted agents.",
)
@pass_runtime
def agent_create(
    runtime: Runtime, name: str, model: str | None, instructions: str | None, document: Path | None
) -> None:
    """Create an agent version, including when the agent already exists."""
    if document:
        if model is not None or instructions is not None:
            raise click.UsageError("Use --file OR --model and --instructions, not both.")
        body = load_document(document)
        definition = body.get("definition")
        if not isinstance(definition, dict) or definition.get("kind") not in {"prompt", "hosted"}:
            raise click.UsageError("--file must contain definition.kind: prompt or hosted.")
    else:
        if not model or not instructions:
            raise click.UsageError("Provide --file, or both --model and --instructions.")
        body = {"definition": {"kind": "prompt", "model": model, "instructions": instructions}}
    runtime.emit(runtime.project_client().agents.create_version(name, body))


@agent.command("delete")
@name_option
@click.option("--version", help="Delete only this version.")
@yes_option
@pass_runtime
def agent_delete(runtime: Runtime, name: str, version: str | None, yes: bool) -> None:
    confirm_delete(f"agent {name}" + (f" version {version}" if version else ""), yes)
    operations = runtime.project_client().agents
    result = operations.delete_version(name, version) if version else operations.delete(name)
    runtime.emit(result)


@agent.command("invoke")
@name_option
@click.option("--input", "prompt", required=True, help="User message.")
@click.option("--version", help="Pin an agent version.")
@click.option("--conversation", help="Continue an existing conversation ID.")
@pass_runtime
def agent_invoke(
    runtime: Runtime, name: str, prompt: str, version: str | None, conversation: str | None
) -> None:
    """Invoke an agent using the Responses API."""
    reference = {"type": "agent_reference", "name": name}
    if version:
        reference["version"] = version
    options: dict[str, Any] = {
        "input": prompt,
        "extra_body": {"agent_reference": reference},
    }
    if conversation:
        options["conversation"] = conversation
    runtime.emit(runtime.openai_client().responses.create(**options))


@agent.command("enable")
@name_option
@pass_runtime
def agent_enable(runtime: Runtime, name: str) -> None:
    runtime.project_client().agents.enable(name)
    runtime.emit({"name": name, "enabled": True})


@agent.command("disable")
@name_option
@pass_runtime
def agent_disable(runtime: Runtime, name: str) -> None:
    runtime.project_client().agents.disable(name)
    runtime.emit({"name": name, "enabled": False})
