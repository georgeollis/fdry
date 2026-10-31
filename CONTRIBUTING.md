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
uv run --no-sync python -m ruff check src tests .github\scripts
uv run --no-sync python -m ruff format --check src tests .github\scripts
uv run --no-sync python -m mypy src .github\scripts
uv run --no-sync python -m pytest -q -m "not binary"
uv run --no-sync python -m build --no-isolation
uv run --no-sync pip-audit --skip-editable
```

CI checks Windows and Linux with Python 3.10, 3.13, and 3.15, validates wheel/source
metadata, and installs the wheel outside the checkout with locked runtime
dependencies. Standalone binaries are separately built and tested on Windows
x64 and Ubuntu 22.04 x64 with Python 3.13.

`ci.yml` orchestrates reusable code-quality, test-matrix, package-installation,
and dependency-audit workflows. Lint, formatting, and type checks run once on
Python 3.13 rather than in every test and executable job. Interpreter-specific
dependency audits stay with the test matrix; the all-extras audit is shared with
scheduled security checks. `binary.yml` builds and exercises standalone
executables. `release.yml` handles version tags, requires both CI and executable
validation, then attests artifacts and creates a draft release. Build and test
jobs have read-only permissions; release write permissions are limited to the
publishing job. Reusable workflows exchange artifacts within the same run.
Python distributions come from the package workflow, not the executable builds.

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

Unit tests isolate SDK boundaries. Contract tests cover SDK request
serialization and pagination. Run both with `pytest -q -m "not binary"`.

Binary tests require `FDRY_EXE` pointing to an absolute executable path.
They run outside the checkout with isolated profile/home paths and credentials,
and cover every leaf command's help, configuration persistence, and offline SDK
authentication failures. Building on Linux requires a Linux host; there is no
cross-compilation from Windows.

Live testing requires explicit approval of the target, operations, data, cost
ceiling, and cleanup.

## Pull requests and repository checks

The required gates are `Required CI`, `Required executables`, `CodeQL analysis`,
`Dependency review`, and `Documentation site`. Documentation-only changes (root
Markdown, `docs/`, `overrides/`, `mkdocs.yml`, or the PR template) run the strict
documentation build, focused offline example tests, and security checks without
the runtime test matrix, package installation, dependency audits, or native executable builds.
The required CI and executable gates still report success after confirming
that only those documentation paths changed. Mixed or unrecognized changes,
workflow changes, release tags, manual runs, and unavailable diffs use full
validation. Aggregated gates fail when detection or a required job fails or
is cancelled; do not silently skip required workflows with trigger-level filters.
The allowlist is maintained in `.github/scripts/changes.py`; its focused tests
are in `tests/unit/test_ci_changes.py`. Keep it limited to documentation inputs.
Deleted and renamed files must be classified too, so moving a runtime file into
`docs/` cannot bypass its checks. An empty diff also uses full validation.
Passing docs-only aggregate gates does not produce fresh executable artifacts.
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
`docs`. Validate the examples and build the site without deploying:

```powershell
uv sync --locked --extra docs --extra dev
uv run --no-sync python -m pytest -q tests\contract\test_sdk_contracts.py tests\unit\test_documentation_examples.py
uv run --no-sync mkdocs build --strict
```

Markdown warnings, missing pages, broken internal links, and missing heading
anchors fail the strict build. Navigation links generated by templates also
need browser checks. Example tests compare request files with installed SDK
serialization and exercise the documented PowerShell response-handling script
with offline responses, including incomplete output, refusal, and command failure.
The documentation workflow runs these checks for docs-only changes too.
For documentation-only edits, use the documentation checks
rather than building packages or native executables. If changing site
JavaScript, also run:

```powershell
node --check docs\assets\foundry.js
node --check overrides\js\darkmode.js
```

GitHub Pages deploys only from `main`; PRs build the site without publishing it.
Do not commit the generated `site` directory.
Keep links to repository source/examples absolute so they work on both GitHub
and the hosted documentation site.

The documentation-first layout extends MkDocs' built-in theme through `overrides`.
It uses text-only identity, persistent section navigation, and on-page contents,
with light mode by default and optional dark/system modes. Styles and interaction
code live in `docs/assets`; no logos, external fonts, theme CDN, or additional
theme dependency are required.
For design changes, also check narrow screens, both color modes, search,
keyboard navigation, and code-copy controls. Respect reduced-motion settings
and keep the independent-project notice visible.
