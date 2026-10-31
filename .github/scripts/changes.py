import os
import subprocess


def documentation_only(paths: list[str]) -> bool:
    return bool(paths) and all(
        path.startswith(("docs/", "overrides/"))
        or path == "mkdocs.yml"
        or ("/" not in path and path.endswith(".md"))
        or path == ".github/pull_request_template.md"
        for path in paths
    )


def runtime_required(event: str, ref: str, base: str, head: str) -> bool:
    if (
        event not in {"pull_request", "push", "merge_group"}
        or ref.startswith("refs/tags/")
        or not base
        or not head
        or set(base) == {"0"}
    ):
        return True
    try:
        if event == "pull_request":
            base = subprocess.check_output(["git", "merge-base", base, head], text=True).strip()
        changed = subprocess.check_output(
            ["git", "diff", "--name-only", "--no-renames", "-z", base, head, "--"]
        )
    except subprocess.CalledProcessError:
        return True
    paths = changed.decode("utf-8", errors="surrogateescape").rstrip("\0").split("\0")
    return not documentation_only([path for path in paths if path])


if __name__ == "__main__":
    required = runtime_required(
        os.environ["EVENT"],
        os.environ["REF"],
        os.environ["BASE"],
        os.environ["HEAD"],
    )
    value = str(required).lower()
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"runtime={value}\n")
    print(f"Runtime builds required: {value}")
