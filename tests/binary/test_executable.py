"""Black-box checks for the actual frozen artifact, without Azure access."""

import json
import os
import subprocess
from pathlib import Path

import pytest

from fdry import __version__
from fdry.cli import cli
from tests.support import leaf_commands

pytestmark = pytest.mark.binary


@pytest.fixture
def executable() -> Path:
    configured = os.environ.get("FDRY_EXE")
    if not configured:
        pytest.skip("Set FDRY_EXE to run standalone executable checks.")
    path = Path(configured).resolve()
    assert path.is_file(), f"Executable does not exist: {path}"
    return path


@pytest.fixture
def environment(tmp_path: Path) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("AZURE_", "FDRY_", "PYTHON"))
    }
    env["FDRY_CONFIG"] = str(tmp_path / "config.json")
    env["AZURE_TOKEN_CREDENTIALS"] = "EnvironmentCredential"
    if os.name == "nt":
        system_root = Path(os.environ["SystemRoot"])
        env["PATH"] = os.pathsep.join([str(system_root / "System32"), str(system_root)])
    else:
        env["PATH"] = os.defpath
    return env


def run(
    executable: Path, environment: dict[str, str], tmp_path: Path, *arguments: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(executable), *arguments],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )


def test_frozen_config_round_trip(
    executable: Path, environment: dict[str, str], tmp_path: Path
) -> None:
    result = run(executable, environment, tmp_path, "config", "set", "account", "offline-account")
    assert result.returncode == 0, result.stderr
    result = run(executable, environment, tmp_path, "config", "show")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["account"] == "offline-account"
    result = run(executable, environment, tmp_path, "config", "list")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["default"]["account"] == "offline-account"
    result = run(executable, environment, tmp_path, "config", "unset", "account")
    assert result.returncode == 0, result.stderr
    result = run(executable, environment, tmp_path, "config", "show")
    assert result.returncode == 0, result.stderr
    assert "account" not in json.loads(result.stdout)


@pytest.mark.parametrize("command", sorted(leaf_commands(cli)))
def test_frozen_command_help(
    executable: Path, environment: dict[str, str], tmp_path: Path, command: str
) -> None:
    result = run(executable, environment, tmp_path, *command.split(), "--help")
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("Usage:")


@pytest.mark.parametrize("api", ["responses", "chat"])
def test_frozen_sdk_imports_before_offline_authentication_failure(
    executable: Path, environment: dict[str, str], tmp_path: Path, api: str
) -> None:
    result = run(
        executable,
        environment,
        tmp_path,
        "--endpoint",
        "https://account.services.ai.azure.com/api/projects/project",
        "model",
        "invoke",
        "--name",
        "deployment",
        "--input",
        "Hello",
        "--api",
        api,
    )
    assert result.returncode == 1, result.stderr
    assert "EnvironmentCredential" in result.stderr
    assert "Traceback" not in result.stderr
    assert "ModuleNotFoundError" not in result.stderr


def test_frozen_help_and_version(
    executable: Path, environment: dict[str, str], tmp_path: Path
) -> None:
    for arguments in [("--version",), ("--help",), ("model", "invoke", "--help")]:
        result = run(executable, environment, tmp_path, *arguments)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip()
        if arguments == ("--version",):
            assert result.stdout.strip() == f"fdry, version {__version__}"
