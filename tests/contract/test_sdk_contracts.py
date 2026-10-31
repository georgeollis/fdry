"""Exercise real SDK serialization and paging with an offline Azure transport."""

import json
from pathlib import Path

import pytest
import yaml
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, WebSearchTool
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.cognitiveservices.models import (
    Deployment,
    DeploymentModel,
    DeploymentProperties,
    Sku,
)
from click.testing import CliRunner

from fdry.cli import cli
from fdry.core.context import Runtime
from tests.support import Credential, Transport

ENDPOINT = "https://account.services.ai.azure.com/api/projects/project"


def test_real_sdk_agent_pagination(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = Transport(
        [
            {"data": [{"id": "first", "name": "first"}], "has_more": True, "last_id": "first"},
            {"data": [{"id": "last", "name": "last"}], "has_more": False},
        ]
    )
    with AIProjectClient(ENDPOINT, Credential(), transport=transport) as client:
        monkeypatch.setattr(Runtime, "project_client", lambda self: client)
        result = CliRunner().invoke(cli, ["agent", "list"])
    assert result.exit_code == 0, result.output
    assert [item["name"] for item in json.loads(result.output)] == ["first", "last"]
    assert len(transport.requests) == 2


def test_real_sdk_prompt_definition(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = Transport([{"id": "agent:1", "name": "agent", "version": "1"}])
    with AIProjectClient(ENDPOINT, Credential(), transport=transport) as client:
        monkeypatch.setattr(Runtime, "project_client", lambda self: client)
        result = CliRunner().invoke(
            cli,
            [
                "agent",
                "create",
                "-n",
                "agent",
                "--model",
                "deployment",
                "--instructions",
                "Be helpful.",
            ],
        )
    assert result.exit_code == 0, result.output
    assert transport.bodies == [
        {
            "definition": {
                "kind": "prompt",
                "model": "deployment",
                "instructions": "Be helpful.",
            }
        }
    ]
    assert "/agents/agent/versions" in transport.requests[0].url


def test_real_management_sdk_deployment(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = Transport(
        [
            {
                "name": "deployment",
                "properties": {"provisioningState": "Succeeded"},
            }
        ]
    )
    with CognitiveServicesManagementClient(
        Credential(), "subscription", transport=transport
    ) as client:
        monkeypatch.setattr(Runtime, "management_client", lambda self: client)
        result = CliRunner().invoke(
            cli,
            [
                "--resource-group",
                "group",
                "--account",
                "account",
                "model",
                "create",
                "-n",
                "deployment",
                "--model",
                "catalog-model",
                "--model-version",
                "version",
                "--capacity",
                "2",
            ],
        )
    assert result.exit_code == 0, result.output
    assert transport.bodies == [
        {
            "sku": {"name": "GlobalStandard", "capacity": 2},
            "properties": {
                "model": {"format": "OpenAI", "name": "catalog-model", "version": "version"},
            },
        }
    ]
    assert "/accounts/account/deployments/deployment" in transport.requests[0].url


def test_agent_example_matches_sdk_request_and_is_forwarded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = Path(__file__).parents[2] / "examples" / "prompt-agent-web-search.yaml"
    expected = {
        "definition": PromptAgentDefinition(
            model="<MODEL_DEPLOYMENT>",
            instructions=(
                "Answer research questions using web search when current information is "
                "needed. Cite sources and distinguish verified facts from uncertainty."
            ),
            tools=[WebSearchTool(search_context_size="low")],
        ).as_dict(),
        "description": "Research assistant with web search.",
        "metadata": {"purpose": "research"},
    }
    assert yaml.safe_load(path.read_text(encoding="utf-8")) == expected
    transport = Transport([{"id": "agent:1", "name": "agent", "version": "1"}])
    with AIProjectClient(ENDPOINT, Credential(), transport=transport) as client:
        monkeypatch.setattr(Runtime, "project_client", lambda self: client)
        result = CliRunner().invoke(cli, ["agent", "create", "-n", "agent", "--file", str(path)])
    assert result.exit_code == 0, result.output
    assert transport.bodies == [expected]


def test_model_example_matches_sdk_wire_names_and_is_forwarded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = Path(__file__).parents[2] / "examples" / "model-deployment.json"
    expected = Deployment(
        sku=Sku(name="GlobalStandard", capacity=1),
        properties=DeploymentProperties(
            model=DeploymentModel(
                format="OpenAI", name="<CATALOG_MODEL>", version="<MODEL_VERSION>"
            ),
            version_upgrade_option="NoAutoUpgrade",
        ),
    ).serialize()
    assert json.loads(path.read_text(encoding="utf-8")) == expected
    transport = Transport(
        [{"name": "deployment", "properties": {"provisioningState": "Succeeded"}}]
    )
    with CognitiveServicesManagementClient(
        Credential(), "subscription", transport=transport
    ) as client:
        monkeypatch.setattr(Runtime, "management_client", lambda self: client)
        result = CliRunner().invoke(
            cli,
            [
                "--resource-group",
                "group",
                "--account",
                "account",
                "model",
                "create",
                "-n",
                "deployment",
                "--file",
                str(path),
            ],
        )
    assert result.exit_code == 0, result.output
    assert transport.bodies == [expected]


@pytest.mark.parametrize(
    "command,body,expected_path",
    [
        (
            ["agent", "create", "-n", "agent"],
            {
                "definition": {
                    "kind": "hosted",
                    "cpu": "1",
                    "memory": "2Gi",
                    "container_configuration": {"image": "registry.example/agent:latest"},
                    "protocol_versions": [{"protocol": "responses", "version": "v1"}],
                }
            },
            "/agents/agent/versions",
        ),
        (
            ["toolbox", "create", "-n", "tools"],
            {"tools": [{"type": "web_search", "name": "web"}]},
            "/toolboxes/tools/versions",
        ),
    ],
)
def test_real_sdk_definition_bodies(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    command: list[str],
    body: dict,
    expected_path: str,
) -> None:
    path = tmp_path / "definition.yaml"
    path.write_text(yaml.safe_dump(body))
    transport = Transport([{"id": "resource:1", "name": "resource", "version": "1"}])
    with AIProjectClient(ENDPOINT, Credential(), transport=transport) as client:
        monkeypatch.setattr(Runtime, "project_client", lambda self: client)
        result = CliRunner().invoke(cli, [*command, "--file", str(path)])
    assert result.exit_code == 0, result.output
    assert transport.bodies == [body]
    assert expected_path in transport.requests[0].url


def test_real_management_connection_body(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    body = {
        "properties": {
            "authType": "ApiKey",
            "category": "ApiKey",
            "target": "https://example.org",
            "credentials": {"key": "offline-test-value"},
        }
    }
    path = tmp_path / "connection.json"
    path.write_text(json.dumps(body))
    transport = Transport([body])
    with CognitiveServicesManagementClient(
        Credential(), "subscription", transport=transport
    ) as client:
        monkeypatch.setattr(Runtime, "management_client", lambda self: client)
        result = CliRunner().invoke(
            cli,
            [
                "--resource-group",
                "group",
                "--account",
                "account",
                "--project",
                "project",
                "connection",
                "create",
                "-n",
                "connection",
                "--file",
                str(path),
            ],
        )
    assert result.exit_code == 0, result.output
    assert transport.bodies == [body]
    assert "/projects/project/connections/connection" in transport.requests[0].url
    assert "offline-test-value" not in result.output
