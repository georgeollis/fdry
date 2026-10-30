import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml
from azure.core.exceptions import HttpResponseError
from click.testing import CliRunner

from fdry import __version__
from fdry.cli import cli
from fdry.core.config import config_path
from fdry.core.context import Runtime
from fdry.core.output import plain

ENDPOINT = "https://account.services.ai.azure.com/api/projects/project"


def test_cli_name_and_version(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0, result.output
    assert result.output.startswith("Usage: fdry ")
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0, result.output
    assert result.output.strip() == f"fdry, version {__version__}"


def test_default_config_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FDRY_CONFIG")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert config_path() == tmp_path / ".fdry" / "config.json"


def test_profile_environment(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FDRY_PROFILE", "dev")
    result = runner.invoke(cli, ["config", "set", "endpoint", ENDPOINT])
    assert result.exit_code == 0, result.output
    result = runner.invoke(cli, ["config", "show"])
    assert json.loads(result.output)["endpoint"] == ENDPOINT
    result = runner.invoke(cli, ["--profile", "default", "config", "show"])
    assert result.exit_code == 0, result.output
    assert "endpoint" not in json.loads(result.output)


def test_profiles_and_precedence(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = runner.invoke(cli, ["--profile", "dev", "config", "set", "endpoint", ENDPOINT])
    assert result.exit_code == 0, result.output
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", ENDPOINT + "-environment")
    result = runner.invoke(cli, ["--profile", "dev", "config", "show"])
    assert json.loads(result.output)["endpoint"] == ENDPOINT + "-environment"
    result = runner.invoke(
        cli, ["--profile", "dev", "--endpoint", ENDPOINT + "-flag", "config", "show"]
    )
    assert json.loads(result.output)["endpoint"] == ENDPOINT + "-flag"
    stored = json.loads((tmp_path / "config.json").read_text())
    assert stored["profiles"]["dev"]["endpoint"] == ENDPOINT
    assert runner.invoke(cli, ["config", "set", "api_key", "not-a-key"]).exit_code == 2


def test_corrupt_config_is_not_overwritten(runner: CliRunner, tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text("{broken")
    result = runner.invoke(cli, ["config", "set", "account", "anything"])
    assert result.exit_code == 1
    assert "Cannot read configuration" in result.output
    assert path.read_text() == "{broken"


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://host/api/projects/project",
        "https://user:secret@host/api/projects/project",
        ENDPOINT + "?token=secret",
        "https://host/api/projects/",
        ENDPOINT + "/agents",
        "https://host/api/projects/..",
        "https://host/api/projects/%2e%2e",
        "https://host/api/projects/%252e%252e",
        "https://host/api/projects/a%2fb",
        "https://host:invalid/api/projects/project",
        "https://[invalid/api/projects/project",
        "https://host/api/projects/pro\nject",
    ],
)
def test_reject_invalid_endpoint(runner: CliRunner, endpoint: str) -> None:
    result = runner.invoke(cli, ["config", "set", "endpoint", endpoint])
    assert result.exit_code == 2


def test_missing_context_is_actionable(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["agent", "list"])
    assert result.exit_code == 2
    assert "AZURE_AI_PROJECT_ENDPOINT" in result.output
    assert "Traceback" not in result.output


def test_list_consumes_every_page(runner: CliRunner, project_client: MagicMock) -> None:
    project_client.agents.list.return_value = iter([{"name": "first"}, {"name": "last"}])
    result = runner.invoke(cli, ["agent", "list"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == [{"name": "first"}, {"name": "last"}]


def test_prompt_agent_create(runner: CliRunner, project_client: MagicMock) -> None:
    project_client.agents.create_version.return_value = {"name": "agent", "version": "1"}
    result = runner.invoke(
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
    project_client.agents.create_version.assert_called_once_with(
        "agent",
        {"definition": {"kind": "prompt", "model": "deployment", "instructions": "Be helpful."}},
    )


def test_agent_file_preserves_tools(
    runner: CliRunner, project_client: MagicMock, tmp_path: Path
) -> None:
    body = {
        "definition": {
            "kind": "hosted",
            "cpu": "1",
            "memory": "2Gi",
            "container_configuration": {"image": "registry.example/agent:latest"},
        }
    }
    path = tmp_path / "agent.yaml"
    path.write_text(yaml.safe_dump(body))
    project_client.agents.create_version.return_value = {"name": "agent"}
    result = runner.invoke(cli, ["agent", "create", "-n", "agent", "--file", str(path)])
    assert result.exit_code == 0, result.output
    project_client.agents.create_version.assert_called_once_with("agent", body)


def test_agent_invocation_reference(runner: CliRunner, openai_client: MagicMock) -> None:
    openai_client.responses.create.return_value = {"id": "response"}
    result = runner.invoke(
        cli,
        [
            "agent",
            "invoke",
            "-n",
            "agent",
            "--version",
            "2",
            "--input",
            "Hello",
            "--conversation",
            "conversation",
        ],
    )
    assert result.exit_code == 0, result.output
    openai_client.responses.create.assert_called_once_with(
        input="Hello",
        conversation="conversation",
        extra_body={
            "agent_reference": {
                "name": "agent",
                "type": "agent_reference",
                "version": "2",
            }
        },
    )


def test_delete_abort_and_confirm(runner: CliRunner, project_client: MagicMock) -> None:
    result = runner.invoke(cli, ["agent", "delete", "-n", "agent"], input="n\n")
    assert result.exit_code == 1
    project_client.agents.delete.assert_not_called()
    project_client.agents.delete_version.return_value = {"deleted": True}
    result = runner.invoke(
        cli,
        [
            "agent",
            "delete",
            "-n",
            "agent",
            "--version",
            "1",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    project_client.agents.delete_version.assert_called_once_with("agent", "1")


@pytest.mark.parametrize(
    "group,attribute",
    [
        ("toolbox", "toolboxes"),
        ("dataset", "datasets"),
        ("index", "indexes"),
    ],
)
def test_versioned_create(
    runner: CliRunner, project_client: MagicMock, tmp_path: Path, group: str, attribute: str
) -> None:
    body = {"tools": [{"type": "web_search"}]} if group == "toolbox" else {"type": "uri_file"}
    path = tmp_path / "body.json"
    path.write_text(json.dumps(body))
    operations = getattr(project_client, attribute)
    operations.create_version.return_value = {"version": "1"}
    operations.create_or_update.return_value = {"version": "1"}
    args = [group, "create", "-n", "name", "--file", str(path)]
    if group != "toolbox":
        args += ["--version", "1"]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.output
    if group == "toolbox":
        operations.create_version.assert_called_once_with("name", body)
    else:
        operations.create_or_update.assert_called_once_with("name", "1", body)


def test_toolbox_publish(runner: CliRunner, project_client: MagicMock) -> None:
    project_client.toolboxes.update.return_value = {"default_version": "2"}
    result = runner.invoke(cli, ["toolbox", "publish", "-n", "tools", "--version", "2"])
    assert result.exit_code == 0, result.output
    project_client.toolboxes.update.assert_called_once_with("tools", default_version="2")


def test_dataset_upload_file_and_folder(
    runner: CliRunner, project_client: MagicMock, tmp_path: Path
) -> None:
    path = tmp_path / "data.jsonl"
    path.write_text('{"input":"Hello"}\n')
    project_client.datasets.upload_file.return_value = {"version": "1"}
    project_client.datasets.upload_folder.return_value = {"version": "2"}
    for target, version in [(path, "1"), (tmp_path, "2")]:
        result = runner.invoke(
            cli,
            [
                "dataset",
                "upload",
                "-n",
                "data",
                "--version",
                version,
                "--path",
                str(target),
            ],
        )
        assert result.exit_code == 0, result.output
    project_client.datasets.upload_file.assert_called_once_with(
        name="data",
        version="1",
        file_path=str(path),
        connection_name=None,
    )
    project_client.datasets.upload_folder.assert_called_once_with(
        name="data",
        version="2",
        folder=str(tmp_path),
        connection_name=None,
    )


@pytest.mark.parametrize(
    "command,options,api",
    [
        ("invoke", [], "responses.create"),
        ("invoke", ["--api", "responses"], "responses.create"),
        ("invoke", ["--api", "chat"], "chat.completions.create"),
        ("embeddings", [], "embeddings.create"),
    ],
)
def test_model_invocation(
    runner: CliRunner, openai_client: MagicMock, command: str, options: list[str], api: str
) -> None:
    method = openai_client
    for segment in api.split("."):
        method = getattr(method, segment)
    method.return_value = {"id": "result"}
    result = runner.invoke(
        cli, ["model", command, "-n", "deployment", "--input", "Hello", *options]
    )
    assert result.exit_code == 0, result.output
    expected = {"model": "deployment"}
    expected["messages" if api == "chat.completions.create" else "input"] = (
        [{"role": "user", "content": "Hello"}] if api == "chat.completions.create" else "Hello"
    )
    method.assert_called_once_with(**expected)
    if api == "chat.completions.create":
        openai_client.responses.create.assert_not_called()
    elif api == "responses.create":
        openai_client.chat.completions.create.assert_not_called()


def test_connection_creation_redacts_credentials(
    runner: CliRunner, management_client: MagicMock, tmp_path: Path
) -> None:
    body = {
        "properties": {
            "category": "ApiKey",
            "authType": "ApiKey",
            "target": "https://example.org",
            "credentials": {"key": "sensitive-value"},
        }
    }
    path = tmp_path / "connection.json"
    path.write_text(json.dumps(body))
    management_client.project_connections.create.return_value = body
    result = runner.invoke(cli, ["connection", "create", "-n", "connection", "--file", str(path)])
    assert result.exit_code == 0, result.output
    args = management_client.project_connections.create.call_args.args
    assert args[:4] == ("group", "account", "project", "connection")
    assert json.load(args[4]) == body
    assert "sensitive-value" not in result.output
    assert "[REDACTED]" in result.output


def test_model_deployment_waits_for_completion(
    runner: CliRunner, management_client: MagicMock
) -> None:
    management_client.deployments.begin_create_or_update.return_value.result.return_value = {
        "name": "deployment"
    }
    result = runner.invoke(
        cli,
        [
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
    args = management_client.deployments.begin_create_or_update.call_args.args
    assert args[:3] == ("group", "account", "deployment")
    body = json.load(args[3])
    assert body["properties"]["model"]["version"] == "version"
    assert body["sku"]["capacity"] == 2
    management_client.deployments.begin_create_or_update.return_value.result.assert_called_once()


@pytest.mark.parametrize(
    "option,value",
    [
        ("--sku", "Standard"),
        ("--capacity", "2"),
        ("--format", "Other"),
    ],
)
def test_model_file_does_not_silently_ignore_deployment_options(
    runner: CliRunner,
    management_client: MagicMock,
    tmp_path: Path,
    option: str,
    value: str,
) -> None:
    path = tmp_path / "deployment.json"
    path.write_text('{"properties": {"model": {"name": "model"}}}')
    result = runner.invoke(
        cli,
        [
            "model",
            "create",
            "-n",
            "deployment",
            "--file",
            str(path),
            option,
            value,
        ],
    )
    assert result.exit_code == 2
    management_client.deployments.begin_create_or_update.assert_not_called()


def test_advanced_account_body_does_not_require_ignored_location(
    runner: CliRunner, management_client: MagicMock, tmp_path: Path
) -> None:
    body = {
        "kind": "AIServices",
        "location": "region",
        "properties": {
            "allowProjectManagement": True,
            "publicNetworkAccess": "Disabled",
        },
    }
    path = tmp_path / "account.json"
    path.write_text(json.dumps(body))
    management_client.accounts.begin_create.return_value.result.return_value = {"name": "account"}
    result = runner.invoke(cli, ["account", "create", "--file", str(path)])
    assert result.exit_code == 0, result.output
    assert json.load(management_client.accounts.begin_create.call_args.args[-1]) == body


def test_fine_tuning_preserves_foundry_fields(
    runner: CliRunner, openai_client: MagicMock, tmp_path: Path
) -> None:
    path = tmp_path / "training.json"
    path.write_text(
        json.dumps(
            {
                "model": "base-model",
                "training_file": "file-id",
                "trainingType": "GlobalStandard",
            }
        )
    )
    openai_client.fine_tuning.jobs.create.return_value = {"id": "job"}
    result = runner.invoke(cli, ["fine-tuning", "create", "--file", str(path)])
    assert result.exit_code == 0, result.output
    openai_client.fine_tuning.jobs.create.assert_called_once_with(
        model="base-model",
        training_file="file-id",
        extra_body={"trainingType": "GlobalStandard"},
    )


@pytest.mark.parametrize("command", ["account", "project"])
def test_resource_creation(runner: CliRunner, management_client: MagicMock, command: str) -> None:
    operations = getattr(management_client, command + "s")
    operations.begin_create.return_value.result.return_value = {"name": "created"}
    args = [command, "create", "--location", "region"]
    if command == "project":
        args += ["-n", "new-project"]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.output
    body = json.load(operations.begin_create.call_args.args[-1])
    assert body["identity"]["type"] == "SystemAssigned"
    if command == "account":
        assert body["properties"]["allowProjectManagement"] is True
        assert body["properties"]["disableLocalAuth"] is True


@pytest.mark.parametrize(
    "command,body",
    [
        ("evaluation", {"data_source_config": {"type": "custom"}, "testing_criteria": []}),
        ("fine-tuning", {"model": "base-model", "training_file": "file-id"}),
    ],
)
def test_openai_create(
    runner: CliRunner, openai_client: MagicMock, tmp_path: Path, command: str, body: dict
) -> None:
    path = tmp_path / "body.json"
    path.write_text(json.dumps(body))
    method = (
        openai_client.evals.create
        if command == "evaluation"
        else openai_client.fine_tuning.jobs.create
    )
    method.return_value = {"id": "job"}
    result = runner.invoke(cli, [command, "create", "--file", str(path)])
    assert result.exit_code == 0, result.output
    method.assert_called_once_with(**body)


def test_eval_run(runner: CliRunner, openai_client: MagicMock, tmp_path: Path) -> None:
    path = tmp_path / "run.json"
    body = {"data_source": {"type": "jsonl", "source": {"type": "file_id", "id": "file-id"}}}
    path.write_text(json.dumps(body))
    openai_client.evals.runs.create.return_value = {"id": "run"}
    result = runner.invoke(
        cli,
        [
            "evaluation",
            "run",
            "create",
            "--evaluation-id",
            "eval",
            "--file",
            str(path),
        ],
    )
    assert result.exit_code == 0, result.output
    openai_client.evals.runs.create.assert_called_once_with("eval", **body)


def test_service_error_has_nonzero_exit(runner: CliRunner, project_client: MagicMock) -> None:
    project_client.agents.list.side_effect = HttpResponseError(message="Permission denied")
    result = runner.invoke(cli, ["agent", "list"])
    assert result.exit_code == 1
    assert "Permission denied" in result.output
    assert "Traceback" not in result.output


@pytest.mark.parametrize(
    "content",
    [
        "- not-an-object",
        "date: 2026-10-25",
        "number: .nan",
        "tools: []\ntools: []",
        "tools: [{type: web_search, type: mcp}]",
        '{"tools": [], "tools": [{"type": "web_search"}]}',
        "tools: [{1: value}]",
    ],
)
def test_invalid_document_never_calls_sdk(
    runner: CliRunner, project_client: MagicMock, tmp_path: Path, content: str
) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(content)
    result = runner.invoke(cli, ["toolbox", "create", "-n", "tools", "--file", str(path)])
    assert result.exit_code == 2, result.output
    project_client.toolboxes.create_version.assert_not_called()


def test_yaml_merge_can_override_inherited_properties(
    runner: CliRunner, project_client: MagicMock, tmp_path: Path
) -> None:
    path = tmp_path / "tools.yaml"
    path.write_text(
        "tools:\n  - &base {type: web_search, name: first}\n  - <<: *base\n    name: second\n"
    )
    project_client.toolboxes.create_version.return_value = {"version": "1"}
    result = runner.invoke(cli, ["toolbox", "create", "-n", "tools", "--file", str(path)])
    assert result.exit_code == 0, result.output
    project_client.toolboxes.create_version.assert_called_once_with(
        "tools",
        {
            "tools": [
                {"type": "web_search", "name": "first"},
                {"type": "web_search", "name": "second"},
            ]
        },
    )


@pytest.mark.parametrize(
    "path",
    [
        "https://other.example/agents",
        "//other.example",
        "../agents",
        "%2e%2e/agents",
        "%252e%252e/agents",
        "agents/../models",
        "agents\\..\\models",
        "/agents",
        "agents#fragment",
        "//[invalid",
        "agents\n/versions",
    ],
)
def test_rest_does_not_send_credentials_outside_project(
    runner: CliRunner, project_client: MagicMock, path: str
) -> None:
    result = runner.invoke(cli, ["rest", path])
    assert result.exit_code == 2
    project_client.send_request.assert_not_called()


def test_rest_uses_project_url(runner: CliRunner, project_client: MagicMock) -> None:
    response = project_client.send_request.return_value
    response.status_code = 200
    response.content = b'{"data":[]}'
    response.json.return_value = {"data": []}
    result = runner.invoke(cli, ["--endpoint", ENDPOINT, "rest", "agents?api-version=v1"])
    assert result.exit_code == 0, result.output
    request = project_client.send_request.call_args.args[0]
    assert request.url == ENDPOINT + "/agents?api-version=v1"


@pytest.mark.parametrize("output", ["json", "yaml", "table"])
def test_output_redaction(runner: CliRunner, project_client: MagicMock, output: str) -> None:
    project_client.connections.list.return_value = [
        {
            "name": "connection",
            "credentials": {"key": "never-print"},
            "nested": {"apiKey": "never-print"},
        }
    ]
    result = runner.invoke(cli, ["-o", output, "connection", "list"])
    assert result.exit_code == 0, result.output
    assert "never-print" not in result.output
    assert "[REDACTED]" in result.output


@pytest.mark.parametrize(
    "key",
    ["clientSecret", "accessToken", "refresh_token", "sas-token", "primaryKey", "secondaryKey"],
)
def test_output_redacts_credential_key_variants(key: str) -> None:
    assert plain({"nested": [{key: "never-print"}]}) == {"nested": [{key: "[REDACTED]"}]}


@pytest.mark.parametrize("response", [{"value": float("nan")}, {"value": object()}])
def test_unserializable_response_is_actionable(
    runner: CliRunner, project_client: MagicMock, response: dict
) -> None:
    project_client.agents.get.return_value = response
    result = runner.invoke(cli, ["agent", "show", "-n", "agent"])
    assert result.exit_code == 1
    assert "Cannot serialize the service response" in result.output
    assert isinstance(result.exception, SystemExit)


def test_empty_table_object_is_visible(runner: CliRunner, project_client: MagicMock) -> None:
    project_client.agents.get.return_value = {}
    result = runner.invoke(cli, ["-o", "table", "agent", "show", "-n", "agent"])
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "{}"


def test_unsupported_output_is_not_silently_stringified() -> None:
    with pytest.raises(TypeError, match="Cannot serialize"):
        plain(object())


def test_clients_closed_on_exit(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    client = MagicMock()
    client.agents.list.return_value = []
    monkeypatch.setattr("fdry.core.context.AIProjectClient", lambda **kwargs: client)
    credential = MagicMock()
    monkeypatch.setattr("fdry.core.context.DefaultAzureCredential", lambda: credential)
    client.__enter__.return_value = client
    result = runner.invoke(cli, ["--endpoint", ENDPOINT, "agent", "list"])
    assert result.exit_code == 0, result.output
    client.__exit__.assert_called_once()
    credential.close.assert_called_once()


def test_auth_does_not_print_token(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    credential = MagicMock()
    credential.get_token.return_value.token = "never-print"
    credential.get_token.return_value.expires_on = 12345
    monkeypatch.setattr(Runtime, "credential", lambda self: credential)
    result = runner.invoke(cli, ["auth", "status"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["authenticated"] is True
    assert "never-print" not in result.output
