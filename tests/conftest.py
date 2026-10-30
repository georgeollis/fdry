from pathlib import Path
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from fdry.core.config import SETTING_ENV
from fdry.core.context import Runtime


@pytest.fixture(autouse=True)
def isolated_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FDRY_CONFIG", str(tmp_path / "config.json"))
    monkeypatch.delenv("FDRY_PROFILE", raising=False)
    for variable in SETTING_ENV.values():
        monkeypatch.delenv(variable, raising=False)


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def project_client(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    client = MagicMock()
    monkeypatch.setattr(Runtime, "project_client", lambda self: client)
    return client


@pytest.fixture
def openai_client(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    client = MagicMock()
    monkeypatch.setattr(Runtime, "openai_client", lambda self: client)
    return client


@pytest.fixture
def management_client(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    for key, value in {
        "subscription": "subscription",
        "resource_group": "group",
        "account": "account",
        "project": "project",
    }.items():
        monkeypatch.setenv(SETTING_ENV[key], value)
    client = MagicMock()
    monkeypatch.setattr(Runtime, "management_client", lambda self: client)
    return client
