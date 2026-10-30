"""Execute every leaf command and verify its SDK HTTP contract without Azure."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import Mock
from urllib.parse import urlsplit

import httpx2
import pytest
from azure.ai.projects import AIProjectClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from click.testing import CliRunner
from openai import DefaultHttpxClient

from fdry.cli import cli
from fdry.core.config import config_path
from fdry.core.context import Runtime
from tests.support import Credential, Transport, leaf_commands

ENDPOINT = "https://account.services.ai.azure.com/api/projects/project"
ARM = (
    "/subscriptions/subscription/resourceGroups/group/providers/"
    "Microsoft.CognitiveServices/accounts/account"
)
RESOURCE = {"id": "resource", "name": "resource", "version": "1"}
ACCOUNT = {
    "name": "account",
    "kind": "AIServices",
    "properties": {"provisioningState": "Succeeded"},
}
NAME = ("--name", "resource")
VERSION = ("--version", "1")
YES = ("--yes",)
DOCUMENT = ("--file", "{document}")
IDENTIFIER = ("--id", "resource")
EVALUATION = ("--evaluation-id", "evaluation")


@dataclass
class Case:
    command: str
    options: tuple[str, ...] = ()
    plane: str = "project"
    method: str = "GET"
    route: str = ""
    response: dict = field(default_factory=lambda: dict(RESOURCE))
    document: dict | None = None
    request: dict | None = None
    status: int = 200

    @property
    def label(self) -> str:
        return self.command + (" " + " ".join(self.options) if self.options else "")


def versioned_cases(group: str, plural: str) -> list[Case]:
    body = {"type": "uri_file", "dataUri": "https://example.org/data.jsonl"}
    if group == "index":
        body = {"type": "AzureSearch", "connectionName": "search", "indexName": "search-index"}
    route = f"/{plural}/resource/versions/1"
    return [
        Case(f"{group} list", route=f"/{plural}", response={"value": [RESOURCE]}),
        Case(f"{group} show", NAME + VERSION, route=route),
        Case(
            f"{group} versions",
            NAME,
            route=f"/{plural}/resource/versions",
            response={"value": [RESOURCE]},
        ),
        Case(
            f"{group} create",
            NAME + VERSION + DOCUMENT,
            method="PATCH",
            route=route,
            document=body,
            request=body,
        ),
        Case(f"{group} delete", NAME + VERSION + YES, method="DELETE", route=route, status=204),
    ]


CASES = [
    Case(
        "account list",
        plane="management",
        route=ARM.rsplit("/account", 1)[0],
        response={"value": [ACCOUNT]},
    ),
    Case("account show", plane="management", route=ARM, response=ACCOUNT),
    Case(
        "account create",
        ("--location", "region"),
        plane="management",
        method="PUT",
        route=ARM,
        response=ACCOUNT,
        request={
            "kind": "AIServices",
            "location": "region",
            "sku": {"name": "S0"},
            "identity": {"type": "SystemAssigned"},
            "properties": {
                "allowProjectManagement": True,
                "customSubDomainName": "account",
                "disableLocalAuth": True,
            },
        },
    ),
    Case("account delete", YES, plane="management", method="DELETE", route=ARM, response={}),
    Case(
        "project list", plane="management", route=ARM + "/projects", response={"value": [RESOURCE]}
    ),
    Case("project show", NAME, plane="management", route=ARM + "/projects/resource"),
    Case(
        "project create",
        NAME + ("--location", "region"),
        plane="management",
        method="PUT",
        route=ARM + "/projects/resource",
        response={
            **RESOURCE,
            "properties": {"provisioningState": "Succeeded"},
        },
        request={
            "location": "region",
            "identity": {"type": "SystemAssigned"},
            "properties": {"displayName": "resource"},
        },
    ),
    Case(
        "project delete",
        NAME + YES,
        plane="management",
        method="DELETE",
        route=ARM + "/projects/resource",
        response={},
    ),
    Case(
        "model catalog", plane="management", route=ARM + "/models", response={"value": [RESOURCE]}
    ),
    Case(
        "model catalog",
        ("--location", "region"),
        plane="management",
        route="/subscriptions/subscription/providers/Microsoft.CognitiveServices/locations/region/models",
        response={"value": [RESOURCE]},
    ),
    Case("model list", route="/deployments", response={"value": [RESOURCE]}),
    Case("model show", NAME, route="/deployments/resource"),
    Case(
        "model create",
        NAME + ("--model", "base", "--model-version", "1"),
        plane="management",
        method="PUT",
        route=ARM + "/deployments/resource",
        response={**RESOURCE, "properties": {"provisioningState": "Succeeded"}},
        request={
            "sku": {"name": "GlobalStandard", "capacity": 1},
            "properties": {"model": {"format": "OpenAI", "name": "base", "version": "1"}},
        },
    ),
    Case(
        "model delete",
        NAME + YES,
        plane="management",
        method="DELETE",
        route=ARM + "/deployments/resource",
        response={},
    ),
    Case(
        "model invoke",
        NAME + ("--input", "Hello"),
        plane="openai",
        method="POST",
        route="/responses",
        request={"model": "resource", "input": "Hello"},
    ),
    Case(
        "model invoke",
        NAME + ("--input", "Hello", "--api", "chat"),
        plane="openai",
        method="POST",
        route="/chat/completions",
        request={"model": "resource", "messages": [{"role": "user", "content": "Hello"}]},
    ),
    Case(
        "model embeddings",
        NAME + ("--input", "Hello"),
        plane="openai",
        method="POST",
        route="/embeddings",
        response={
            "object": "list",
            "data": [{"object": "embedding", "index": 0, "embedding": [0.1]}],
            "model": "resource",
            "usage": {"prompt_tokens": 1, "total_tokens": 1},
        },
        request={"model": "resource", "input": "Hello", "encoding_format": "base64"},
    ),
    Case("agent list", route="/agents", response={"data": [RESOURCE]}),
    Case("agent show", NAME, route="/agents/resource"),
    Case("agent show", NAME + VERSION, route="/agents/resource/versions/1"),
    Case("agent versions", NAME, route="/agents/resource/versions", response={"data": [RESOURCE]}),
    Case(
        "agent create",
        NAME + ("--model", "deployment", "--instructions", "Be helpful."),
        method="POST",
        route="/agents/resource/versions",
        request={
            "definition": {"kind": "prompt", "model": "deployment", "instructions": "Be helpful."},
        },
    ),
    Case(
        "agent invoke",
        NAME + ("--input", "Hello"),
        plane="openai",
        method="POST",
        route="/responses",
        request={
            "input": "Hello",
            "agent_reference": {
                "type": "agent_reference",
                "name": "resource",
            },
        },
    ),
    Case("agent enable", NAME, method="POST", route="/agents/resource:enable", status=204),
    Case("agent disable", NAME, method="POST", route="/agents/resource:disable", status=204),
    Case("agent delete", NAME + YES, method="DELETE", route="/agents/resource"),
    Case(
        "agent delete", NAME + VERSION + YES, method="DELETE", route="/agents/resource/versions/1"
    ),
    Case("connection list", route="/connections", response={"value": [RESOURCE]}),
    Case("connection show", NAME, route="/connections/resource"),
    Case(
        "connection create",
        NAME + DOCUMENT,
        plane="management",
        method="PUT",
        route=ARM + "/projects/project/connections/resource",
        document={
            "properties": {
                "authType": "AAD",
                "category": "CognitiveSearch",
                "target": "https://example.org",
            }
        },
        request={
            "properties": {
                "authType": "AAD",
                "category": "CognitiveSearch",
                "target": "https://example.org",
            }
        },
    ),
    Case(
        "connection delete",
        NAME + YES,
        plane="management",
        method="DELETE",
        route=ARM + "/projects/project/connections/resource",
        response={},
    ),
    *versioned_cases("dataset", "datasets"),
    Case("dataset upload", NAME + VERSION + ("--path", "{upload}"), plane="upload"),
    *versioned_cases("index", "indexes"),
    Case("toolbox list", route="/toolboxes", response={"data": [RESOURCE]}),
    Case("toolbox show", NAME, route="/toolboxes/resource"),
    Case("toolbox show", NAME + VERSION, route="/toolboxes/resource/versions/1"),
    Case(
        "toolbox versions",
        NAME,
        route="/toolboxes/resource/versions",
        response={"data": [RESOURCE]},
    ),
    Case(
        "toolbox create",
        NAME + DOCUMENT,
        method="POST",
        route="/toolboxes/resource/versions",
        document={"tools": [{"type": "web_search"}]},
        request={"tools": [{"type": "web_search"}]},
    ),
    Case(
        "toolbox publish",
        NAME + VERSION,
        method="PATCH",
        route="/toolboxes/resource",
        request={"default_version": "1"},
    ),
    Case(
        "toolbox delete",
        NAME + VERSION + YES,
        method="DELETE",
        route="/toolboxes/resource/versions/1",
        status=204,
    ),
    Case(
        "toolbox delete-all", NAME + YES, method="DELETE", route="/toolboxes/resource", status=204
    ),
    Case(
        "evaluation list",
        plane="openai",
        route="/evals",
        response={"data": [RESOURCE], "has_more": False},
    ),
    Case("evaluation show", IDENTIFIER, plane="openai", route="/evals/resource"),
    Case(
        "evaluation create",
        DOCUMENT,
        plane="openai",
        method="POST",
        route="/evals",
        document={"data_source_config": {"type": "custom"}, "testing_criteria": []},
        request={"data_source_config": {"type": "custom"}, "testing_criteria": []},
    ),
    Case(
        "evaluation delete",
        IDENTIFIER + YES,
        plane="openai",
        method="DELETE",
        route="/evals/resource",
    ),
    Case(
        "evaluation run list",
        EVALUATION,
        plane="openai",
        route="/evals/evaluation/runs",
        response={"data": [RESOURCE], "has_more": False},
    ),
    Case(
        "evaluation run show",
        EVALUATION + IDENTIFIER,
        plane="openai",
        route="/evals/evaluation/runs/resource",
    ),
    Case(
        "evaluation run create",
        EVALUATION + DOCUMENT,
        plane="openai",
        method="POST",
        route="/evals/evaluation/runs",
        document={
            "data_source": {
                "type": "jsonl",
                "source": {"type": "file_id", "id": "file-id"},
            }
        },
        request={
            "data_source": {
                "type": "jsonl",
                "source": {"type": "file_id", "id": "file-id"},
            }
        },
    ),
    Case(
        "evaluation run cancel",
        EVALUATION + IDENTIFIER,
        plane="openai",
        method="POST",
        route="/evals/evaluation/runs/resource/cancel",
    ),
    Case(
        "fine-tuning list",
        plane="openai",
        route="/fine_tuning/jobs",
        response={"data": [RESOURCE], "has_more": False},
    ),
    Case("fine-tuning show", IDENTIFIER, plane="openai", route="/fine_tuning/jobs/resource"),
    Case(
        "fine-tuning create",
        DOCUMENT,
        plane="openai",
        method="POST",
        route="/fine_tuning/jobs",
        document={"model": "base", "training_file": "file-id"},
        request={"model": "base", "training_file": "file-id"},
    ),
    Case(
        "fine-tuning cancel",
        IDENTIFIER,
        plane="openai",
        method="POST",
        route="/fine_tuning/jobs/resource/cancel",
    ),
    Case(
        "file list",
        plane="openai",
        route="/files",
        response={"data": [RESOURCE], "has_more": False},
    ),
    Case("file show", IDENTIFIER, plane="openai", route="/files/resource"),
    Case(
        "file upload",
        ("--path", "{upload}", "--purpose", "fine-tune"),
        plane="openai",
        method="POST",
        route="/files",
    ),
    Case("file delete", IDENTIFIER + YES, plane="openai", method="DELETE", route="/files/resource"),
    Case("quota list", plane="management", route=ARM + "/usages", response={"value": []}),
    Case("auth status", plane="local"),
    Case("config list", plane="local"),
    Case("config show", plane="local"),
    Case("config set", ("account", "new-account"), plane="local"),
    Case("config unset", ("account",), plane="local"),
    Case("rest", ("agents?api-version=v1",), route="/agents", response={"data": [RESOURCE]}),
    Case(
        "rest",
        ("agents?api-version=v1", "--method", "POST") + DOCUMENT,
        method="POST",
        route="/agents",
        document={"name": "resource"},
        request={"name": "resource"},
    ),
    Case(
        "rest",
        ("agents/resource?api-version=v1", "--method", "DELETE", "--yes"),
        method="DELETE",
        route="/agents/resource",
        response={},
    ),
]


def test_matrix_exercises_every_registered_command() -> None:
    assert {case.command for case in CASES} == leaf_commands(cli)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.label)
def test_command_contract(case: Case, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    document = tmp_path / "body.json"
    document.write_text(json.dumps(case.document or {}))
    upload = tmp_path / "data.jsonl"
    upload.write_text('{"messages":[{"role":"user","content":"Hello"}]}\n')
    config_path().write_text(json.dumps({"profiles": {"default": {"account": "saved"}}}))
    options = [
        option.replace("{document}", str(document)).replace("{upload}", str(upload))
        for option in case.options
    ]
    project_transport = Transport([case.response], status=case.status)
    management_transport = Transport([case.response], status=case.status)
    openai_requests: list[httpx2.Request] = []

    def respond(request: httpx2.Request) -> httpx2.Response:
        openai_requests.append(request)
        assert len(openai_requests) == 1, "Unexpected extra HTTP request in a single-page case."
        return httpx2.Response(case.status, json=case.response)

    credential = Credential()
    monkeypatch.setattr(Runtime, "credential", lambda self: credential)
    with (
        AIProjectClient(ENDPOINT, credential, transport=project_transport) as project,
        CognitiveServicesManagementClient(
            credential, "subscription", transport=management_transport
        ) as management,
        project.get_openai_client(
            http_client=DefaultHttpxClient(transport=httpx2.MockTransport(respond))
        ) as openai,
    ):
        monkeypatch.setattr(Runtime, "project_client", lambda self: project)
        monkeypatch.setattr(Runtime, "management_client", lambda self: management)
        monkeypatch.setattr(Runtime, "openai_client", lambda self: openai)
        upload_method = Mock(return_value={"name": "resource", "version": "1"})
        monkeypatch.setattr(project.datasets, "upload_file", upload_method)
        result = CliRunner().invoke(
            cli,
            [
                "--endpoint",
                ENDPOINT,
                "--subscription",
                "subscription",
                "--resource-group",
                "group",
                "--account",
                "account",
                "--project",
                "project",
                *case.command.split(),
                *options,
            ],
        )

    assert result.exit_code == 0, (result.output, repr(result.exception))
    json.loads(result.output)
    if case.plane == "local":
        assert not project_transport.requests and not management_transport.requests
        assert not openai_requests
        if case.command == "config unset":
            assert "account" not in json.loads(config_path().read_text())["profiles"]["default"]
        elif case.command == "config set":
            assert (
                json.loads(config_path().read_text())["profiles"]["default"]["account"]
                == "new-account"
            )
    elif case.plane == "upload":
        upload_method.assert_called_once_with(
            name="resource", version="1", file_path=str(upload), connection_name=None
        )
    elif case.plane == "openai":
        assert not project_transport.requests and not management_transport.requests
        assert len(openai_requests) == 1
        request = openai_requests[0]
        assert request.method == case.method
        assert request.url.path == "/api/projects/project/openai/v1" + case.route
        if case.command == "file upload":
            assert b'filename="data.jsonl"' in request.content
            assert b"fine-tune" in request.content
            assert upload.read_bytes() in request.content
        elif case.request is not None:
            assert json.loads(request.content) == case.request
    else:
        selected = management_transport if case.plane == "management" else project_transport
        other = project_transport if case.plane == "management" else management_transport
        assert not other.requests and not openai_requests
        assert len(selected.requests) == 1
        request = selected.requests[0]
        assert request.method == case.method
        expected = (
            case.route if case.plane == "management" else "/api/projects/project" + case.route
        )
        assert urlsplit(request.url).path == expected
        if case.request is not None:
            assert selected.bodies == [case.request]
