import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

WORKFLOWS = Path(__file__).parents[2] / ".github" / "workflows"


def workflow_step(workflow: str, job: str, name: str) -> str:
    data = yaml.safe_load((WORKFLOWS / workflow).read_text(encoding="utf-8"))
    return next(step["run"] for step in data["jobs"][job]["steps"] if step.get("name") == name)


@pytest.mark.parametrize("runtime", ["true", "false"])
@pytest.mark.parametrize(
    ("job", "result"),
    [
        (None, None),
        ("changes", "failure"),
        ("quality", "failure"),
        ("quality", "cancelled"),
        ("check", "failure"),
        ("package", "failure"),
        ("audit", "failure"),
        ("audit", "success"),
        ("check", "skipped"),
    ],
)
def test_required_ci_gate(runtime: str, job: str | None, result: str | None) -> None:
    expected = "skipped" if runtime == "false" else "success"
    results = {
        name: {"result": "success" if name == "changes" else expected}
        for name in ["changes", "quality", "check", "package", "audit"]
    }
    if job is not None:
        results[job]["result"] = result
    script = workflow_step("ci.yml", "required", "Require every quality gate")
    script = "\n".join(script.splitlines()[1:-1])
    completed = subprocess.run(
        [sys.executable, "-c", script],
        env={**os.environ, "RESULTS": json.dumps(results), "RUNTIME": runtime},
        capture_output=True,
        text=True,
    )
    valid = job is None or result == ("success" if job == "changes" else expected)
    assert (completed.returncode == 0) == valid, completed.stderr


def test_release_checksums_cover_python_and_both_executables(tmp_path: Path) -> None:
    pwsh = shutil.which("pwsh")
    if pwsh is None:
        pytest.skip("PowerShell is required to exercise release asset preparation")

    def run(script: str, directory: Path) -> None:
        completed = subprocess.run(
            [pwsh, "-NoProfile", "-NonInteractive", "-Command", script],
            cwd=directory,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stderr

    release = tmp_path / "release"
    release.mkdir()
    assets = {
        "python": {
            "fdry-0.0.0-py3-none-any.whl": b"wheel",
            "fdry-0.0.0.tar.gz": b"source",
        },
        "windows-x64": {"fdry.exe": b"windows"},
        "linux-x64": {"fdry": b"linux"},
    }
    for target, files in assets.items():
        checkout = tmp_path / target
        dist = checkout / "dist"
        dist.mkdir(parents=True)
        (checkout / "LICENSE").write_text("license", encoding="utf-8")
        for name, content in files.items():
            (dist / name).write_bytes(content)
        if target == "python":
            script = workflow_step("package.yml", "package", "Prepare Python release assets")
        else:
            executable = next(iter(files))
            asset = f"fdry-{target}" + (".exe" if target == "windows-x64" else "")
            script = workflow_step("binary.yml", "build", "Prepare release assets")
            for key, value in {"target": target, "executable": executable, "asset": asset}.items():
                script = script.replace("${{ matrix." + key + " }}", value)
        run(script, checkout)
        for artifact in (dist / "release").iterdir():
            shutil.copy2(artifact, release / artifact.name)

    run(workflow_step("release.yml", "release", "Combine checksums"), tmp_path)
    checksums = (release / "SHA256SUMS").read_text(encoding="ascii").splitlines()
    expected = {
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}"
        for path in release.iterdir()
        if path.name != "LICENSE" and not path.name.startswith("SHA256SUMS")
    }
    assert len(checksums) == 4
    assert set(checksums) == expected
