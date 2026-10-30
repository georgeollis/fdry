"""A project-scoped escape hatch for APIs without dedicated commands."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlsplit

import click
from azure.core.exceptions import HttpResponseError
from azure.core.rest import HttpRequest

from fdry.commands._options import confirm_delete, yes_option
from fdry.core.context import Runtime, pass_runtime
from fdry.core.documents import load_document, request_body


@click.command("rest")
@click.argument("path")
@click.option(
    "--method", type=click.Choice(["GET", "POST", "PUT", "PATCH", "DELETE"]), default="GET"
)
@click.option("--file", "document", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@yes_option
@pass_runtime
def rest(runtime: Runtime, path: str, method: str, document: Path | None, yes: bool) -> None:
    """Send a project-relative request, e.g. 'agents?api-version=v1'.

    Supply the API version required by the target operation. This command does
    not paginate. Absolute URLs and paths outside the configured project are rejected.
    """
    decoded = unquote(path)
    try:
        parsed = urlsplit(decoded)
    except ValueError as exc:
        raise click.BadParameter("Invalid relative URL.", param_hint="path") from exc
    if (
        parsed.scheme
        or parsed.netloc
        or decoded.startswith(("/", "\\"))
        or "\\" in decoded
        or parsed.fragment
        or any(segment in {".", ".."} for segment in parsed.path.split("/"))
        or "%" in decoded
        or not parsed.path
        or any(ord(character) < 32 for character in decoded)
    ):
        raise click.BadParameter(
            "Use a project-relative path without traversal.", param_hint="path"
        )
    if method == "DELETE":
        confirm_delete(f"project path {path}", yes)
    body = load_document(document) if document else None
    if body is not None and method == "GET":
        raise click.UsageError("--file is not supported with GET.")
    client = runtime.project_client()
    url = runtime.require("endpoint").rstrip("/") + "/" + path
    request = HttpRequest(
        method,
        url,
        headers={"Content-Type": "application/json"} if body is not None else None,
        content=request_body(body) if body is not None else None,
    )
    response = client.send_request(request)
    if response.status_code >= 400:
        raise HttpResponseError(response=response)
    if not response.content:
        runtime.emit({"status_code": response.status_code})
    else:
        try:
            result = response.json()
        except ValueError as exc:
            raise click.ClickException(
                f"HTTP {response.status_code}: response is not JSON."
            ) from exc
        runtime.emit(result)
