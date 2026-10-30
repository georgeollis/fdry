import runpy
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

changes = runpy.run_path(str(Path(__file__).parents[2] / ".github" / "scripts" / "changes.py"))


@pytest.mark.parametrize(
    ("paths", "expected"),
    [
        (["README.md", "docs/cli.md", "docs/assets/foundry.js", "overrides/404.html"], True),
        (["mkdocs.yml", ".github/pull_request_template.md"], True),
        (["docs/cli.md", "src/fdry/cli.py"], False),
        (["pyproject.toml"], False),
        (["uv.lock"], False),
        (["packaging/fdry.spec"], False),
        (["tests/unit/test_cli.py"], False),
        ([".github/workflows/ci.yml"], False),
        ([".github/scripts/changes.py"], False),
        (["new-file"], False),
        ([], False),
    ],
)
def test_documentation_allowlist(paths: list[str], expected: bool) -> None:
    assert changes["documentation_only"](paths) is expected


@pytest.mark.parametrize(
    ("event", "ref", "base"),
    [
        ("workflow_dispatch", "refs/heads/main", "abc"),
        ("push", "refs/tags/v0.1.0", "abc"),
        ("push", "refs/heads/main", "0" * 40),
        ("push", "refs/heads/main", ""),
    ],
)
def test_full_build_events(event: str, ref: str, base: str) -> None:
    with patch("subprocess.check_output") as git:
        assert changes["runtime_required"](event, ref, base, "def")
        git.assert_not_called()


@pytest.mark.parametrize("event", ["pull_request", "push", "merge_group"])
def test_documentation_diff(event: str) -> None:
    outputs = [b"docs/cli.md\0overrides/main.html\0"]
    if event == "pull_request":
        outputs.insert(0, "merge-base\n")
    with patch("subprocess.check_output", side_effect=outputs) as git:
        assert not changes["runtime_required"](event, "refs/heads/main", "base", "head")
        command = git.call_args.args[0]
        assert "--no-renames" in command
        assert command[-3:] == [
            "merge-base" if event == "pull_request" else "base",
            "head",
            "--",
        ]


def test_runtime_file_moved_into_docs_still_requires_build() -> None:
    with patch("subprocess.check_output", return_value=b"src/fdry/cli.py\0docs/cli.py\0"):
        assert changes["runtime_required"]("push", "refs/heads/main", "base", "head")


def test_unavailable_diff_requires_full_build() -> None:
    with patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "git")):
        assert changes["runtime_required"]("pull_request", "refs/pull/4/merge", "base", "head")
