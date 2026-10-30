"""Exercise Foundry-authenticated OpenAI requests without network access."""

import json
from pathlib import Path

import httpx2
import pytest
from azure.ai.projects import AIProjectClient
from click.testing import CliRunner
from openai import DefaultHttpxClient

from fdry.cli import cli
from fdry.core.context import Runtime
from tests.support import Credential

ENDPOINT = "https://account.services.ai.azure.com/api/projects/project"


@pytest.mark.parametrize(
    "command,body,expected_path,expected_body",
    [
        (
            ["agent", "invoke", "-n", "agent", "--input", "Hello"],
            None,
            "/responses",
            {
                "input": "Hello",
                "agent_reference": {"name": "agent", "type": "agent_reference"},
            },
        ),
        (
            ["model", "invoke", "-n", "deployment", "--input", "Hello"],
            None,
            "/responses",
            {"model": "deployment", "input": "Hello"},
        ),
        (
            ["model", "invoke", "-n", "deployment", "--input", "Hello", "--api", "responses"],
            None,
            "/responses",
            {"model": "deployment", "input": "Hello"},
        ),
        (
            ["model", "invoke", "-n", "deployment", "--input", "Hello", "--api", "chat"],
            None,
            "/chat/completions",
            {"model": "deployment", "messages": [{"role": "user", "content": "Hello"}]},
        ),
        (
            ["fine-tuning", "create"],
            {"model": "base-model", "training_file": "file-id"},
            "/fine_tuning/jobs",
            {"model": "base-model", "training_file": "file-id"},
        ),
        (
            ["evaluation", "create"],
            {"data_source_config": {"type": "custom"}, "testing_criteria": []},
            "/evals",
            {"data_source_config": {"type": "custom"}, "testing_criteria": []},
        ),
    ],
)
def test_real_openai_request(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    command: list[str],
    body: dict | None,
    expected_path: str,
    expected_body: dict,
) -> None:
    captured: list[httpx2.Request] = []

    def respond(request: httpx2.Request) -> httpx2.Response:
        captured.append(request)
        return httpx2.Response(200, json={"id": "result", "object": "response", "output": []})

    if body is not None:
        path = tmp_path / "body.json"
        path.write_text(json.dumps(body))
        command = [*command, "--file", str(path)]

    with (
        AIProjectClient(ENDPOINT, Credential()) as project,
        project.get_openai_client(
            http_client=DefaultHttpxClient(transport=httpx2.MockTransport(respond))
        ) as client,
    ):
        monkeypatch.setattr(Runtime, "openai_client", lambda self: client)
        result = CliRunner().invoke(cli, command)

    assert result.exit_code == 0, result.output
    assert len(captured) == 1
    assert str(captured[0].url) == ENDPOINT + "/openai/v1" + expected_path
    assert captured[0].headers["Authorization"] == "Bearer offline-token"
    assert json.loads(captured[0].content) == expected_body
