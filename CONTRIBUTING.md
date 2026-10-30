# Contributing

Changes go through pull requests against `main`. Keep resource behavior explicit,
preserve structured output and exit codes, and add focused tests for changed
behavior. See the [architecture](README.md#development-and-architecture) and
[request-body extension guide](docs/request-bodies.md#adding-properties-to-a-request-file).

## Reproducible development

Install Python 3.10 or later and [uv](https://docs.astral.sh/uv/getting-started/installation/).
CI uses uv 0.13.6. From a checkout:

```powershell
uv sync --locked --all-extras --python 3.13
uv run --no-sync python -m ruff check src tests
uv run --no-sync python -m ruff format --check src tests
uv run --no-sync python -m mypy src
uv run --no-sync python -m pytest -q -m "not binary"
uv run --no-sync python -m build --no-isolation
uv run --no-sync pip-audit --skip-editable
```

CI checks Windows and Linux with Python 3.10, 3.13, and 3.15, validates wheel/source
metadata, and installs the wheel outside the checkout with locked runtime
dependencies. Standalone binaries are separately built and tested on Windows
x64 and Ubuntu 22.04 x64 with Python 3.13.

`uv.lock` is the reviewed dependency snapshot, including platform/Python
markers and artifact hashes. If changing `pyproject.toml`, run `uv lock`,
include the updated lock, and rerun checks. For an intentional dependency
refresh, use `uv lock --upgrade`, then `uv sync --locked --all-extras`.
Do not hand-edit hashes or suppress audit findings to make a build green.
Pip installation is supported for users but does not consume `uv.lock`.
Audit tooling requires Python 3.11 or later: CI runs it in an isolated Python
3.13 environment against each target interpreter's installed packages. This
keeps audit-tool dependencies out of the Python 3.10 development environment
without skipping its dependency audit.

## Test boundaries

Unit tests mock SDK boundaries. Contract tests exercise real SDK request
serialization and pagination using offline transports. They do not prove Azure
accepts a request. No normal CI job creates Azure resources or runs live inference,
evaluations, storage uploads, training, or hosted compute.

Binary tests require `FDRY_EXE` pointing to an absolute executable path.
They run outside the checkout with isolated profile/home paths and credentials,
and cover every leaf command's help, configuration persistence, and offline SDK
authentication failures. Building on Linux requires a Linux host; there is no
cross-compilation from Windows.

Live testing requires explicit approval of the target, operations, data, cost
ceiling, and cleanup. Document live-validation gaps rather than treating an
offline test as a live pass.

## Pull requests and repository checks

The required gates are `Required CI`, `Required executables`, `CodeQL analysis`,
`Dependency review`, and `Documentation site`. Aggregated gates fail when any prerequisite fails or is
cancelled; do not make a required workflow silently skip paths.
Keep action references pinned to full commit SHAs. Dependabot proposes action
and uv dependency updates; review their changelogs and test results.

Main-branch policy requires a pull request, up-to-date passing checks, resolved
conversations, and linear history; force pushes and deletion are blocked.
It does not require an additional approver, so the sole maintainer can merge
their own PR after checks. `CODEOWNERS` routes review requests; it is not an
independent security boundary.

Never commit credentials, private prompts/data, or real Azure resource
identifiers. Use placeholders in documentation and ignored `*.local.json`,
`*.local.yaml`, or `*.local.yml` files for local request bodies.
Output redaction is best-effort: sanitize reproduction logs before sharing.
Report vulnerabilities through the private process in [SECURITY.md](SECURITY.md).

## Documentation site

The searchable static site uses MkDocs and the canonical Markdown under
`docs`. Build it without deploying:

```powershell
uv sync --locked --extra docs
uv run --no-sync mkdocs build --strict
```

Warnings, missing pages, and broken internal links fail the strict build.
GitHub Pages deploys only from `main`; PRs build the site without publishing it.
Do not commit the generated `site` directory.
Keep links to repository source/examples absolute so they work on both GitHub
and the hosted documentation site.
