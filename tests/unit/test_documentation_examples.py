import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("status", "content", "exit_code", "succeeds"),
    [
        (
            "completed",
            [
                {
                    "type": "output_text",
                    "text": json.dumps(
                        {
                            "category": "access",
                            "priority": "normal",
                            "summary": "One user cannot open a project.",
                            "next_action": "Verify the role assignment.",
                        }
                    ),
                }
            ],
            "0",
            True,
        ),
        ("incomplete", [{"type": "output_text", "text": "{}"}], "0", False),
        ("completed", [{"type": "refusal", "refusal": "Cannot process this request."}], "0", False),
        ("completed", [], "1", False),
    ],
)
def test_documented_agent_workflow_checks_status_and_pins_version(
    status: str, content: list[dict[str, str]], exit_code: str, succeeds: bool
) -> None:
    pwsh = shutil.which("pwsh")
    if pwsh is None:
        pytest.skip("PowerShell is required to exercise the documented workflow")
    document = Path(__file__).parents[2] / "docs" / "workflows.md"
    snippets = re.findall(r"```powershell\n(.*?)```", document.read_text(encoding="utf-8"), re.S)
    script = next(snippet for snippet in snippets if "$createdJson =" in snippet)
    mock = """
function fdry {
    $global:LASTEXITCODE = 0
    if ($args -contains 'create') {
        '{"name":"agent","version":"7"}'
    } else {
        $position = [Array]::IndexOf($args, '--version')
        if ($position -lt 0 -or $args[$position + 1] -ne '7') {
            throw 'Invocation must pin the version returned by creation.'
        }
        if ($args -contains 'invoke') {
            $global:LASTEXITCODE = [int]$env:FDRY_TEST_EXIT
            $env:FDRY_TEST_RESPONSE
        } else {
            '{"name":"agent","version":"7"}'
        }
    }
}
"""
    response = {"status": status, "output": [{"type": "message", "content": content}]}
    completed = subprocess.run(
        [pwsh, "-NoProfile", "-NonInteractive", "-Command", mock + script],
        env={
            **os.environ,
            "FDRY_TEST_RESPONSE": json.dumps(response),
            "FDRY_TEST_EXIT": exit_code,
        },
        capture_output=True,
        text=True,
    )
    assert (completed.returncode == 0) == succeeds, completed.stderr
    if succeeds:
        assert "access" in completed.stdout
        assert "normal" in completed.stdout
