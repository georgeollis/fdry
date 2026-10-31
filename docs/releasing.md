# Releases and supported platforms

## Supported platforms

The [v0.1.0 release](https://github.com/georgeollis/fdry/releases/tag/v0.1.0)
includes Windows/Linux executables, Python distributions, checksums, and
build-provenance attestations.

| Distribution | Platform | Python |
|--------------|----------|--------|
| Python package | Windows and Linux | Requires Python 3.10 or newer. |
| Windows executable | Windows x86-64 | Bundled Python 3.13. |
| Linux executable | Linux x86-64, glibc 2.35+; built on Ubuntu 22.04 | Bundled Python 3.13. |

Linux binaries need a writable/executable temporary location for PyInstaller's
one-file extraction, the relevant glibc runtime, and system CA trust.
Use the Python package where a standalone target is unsupported.

## Build and check policy

The Windows `.exe` is built and tested natively on `windows-latest`; the Linux
executable is built and tested on Ubuntu 22.04. Both bundle Python 3.13.
Build each artifact on its target operating system with PyInstaller; these are
not cross-compiled builds. Source-package CI separately tests Python 3.10,
3.13, and 3.15 on Windows and Linux.

Documentation-only changes run documentation and security checks without
rebuilding either executable or the Python distributions. Their aggregate
`Required CI` and `Required executables` checks still report after verifying
the changed paths. To generate executable artifacts, use a full build.
Mixed changes, CI/build-tooling changes, unavailable diffs, release tags,
and manual workflow runs retain full validation.
See the [contributor policy](https://github.com/georgeollis/fdry/blob/main/CONTRIBUTING.md#pull-requests-and-repository-checks)
for the documentation allowlist.

For a docs-only commit being considered for release, manually run the **CI**
and **Executables** workflows on the reviewed branch before tagging, then
inspect both platform artifacts, package installation, and results. Do not
remove protection or ignore failed tests to obtain a passing release gate.
Manual executable runs upload artifacts but do not create a GitHub release;
a matching version tag starts the release workflow.

## Before tagging a release

1. Review changes, dependency audits, bundled licenses, and CodeQL results.
2. Verify `Required CI`, `Required executables`, `CodeQL analysis`, and `Documentation site` for the
   exact commit on `main`. Check both executable artifacts and isolated wheel
   installation, not only editable-source tests. The release PR must also pass
   `Dependency review`.
3. Update `src\fdry\__init__.py`, release notes, and documentation through a
   passing PR. Use a SemVer version and a matching `v<VERSION>` tag.

## Tagged build and draft review

Push a version tag pointing at the reviewed `main` commit. The **Release**
workflow calls the reusable **CI** and **Executables** workflows for that tag.
CI runs offline/lint/type gates and dependency audits, builds wheel/source
distributions, and checks isolated wheel installation. Executables checks the
tag against the package version and builds/tests both native executables.
The publishing job only runs after both workflows succeed, then combines
their artifacts and creates build-provenance attestations. Write permissions
are limited to that publishing job.

The workflow creates a **draft**, not a public release, containing:

| Asset | Purpose |
|-------|---------|
| `fdry-windows-x64.exe` | Portable Windows executable. |
| `fdry-linux-x64` | Portable glibc-based Linux executable. |
| `fdry-<VERSION>-py3-none-any.whl` | Python wheel. |
| `fdry-<VERSION>.tar.gz` | Python source distribution, including dependency lock and source. |
| `SHA256SUMS` | SHA-256 hashes for the executables and Python distributions. |
| `LICENSE` | Project MIT license; bundled dependencies retain their own licenses. |

Review the workflow identity, commit, version output, checksums, and provenance
before publishing the draft. Publishing is a separate maintainer action. Existing tags
and published assets must not be overwritten. PyPI publishing is separate
from this workflow.

## Version 0.1.1 changes

Version 0.1.1 improves request parsing, configuration validation, output
consistency, and workflow documentation:

- JSON request files preserve scientific-notation numbers as numbers rather
  than converting them to strings. Files ending in `.json` now require JSON
  syntax; use `.yaml` or `.yml` for YAML bodies.
- Request and configuration files accept a UTF-8 byte-order mark.
- Blank saved settings are rejected without overwriting the configuration.
  Blank management context fails before SDK clients are created.
- Non-finite response values are rejected consistently for JSON, YAML, and
  table output.
- SDK-backed structured-agent and search-index examples include prerequisites,
  version verification, response handling, and focused offline CI checks.
- Installation requirements are stated separately from the Python versions
  tested in CI.

## Consumer verification

Download assets only from a reviewed release in
[`georgeollis/fdry`](https://github.com/georgeollis/fdry/releases).
Compare the asset's SHA-256 digest with its exact filename entry in `SHA256SUMS`
before execution. On Windows:

```powershell
Get-FileHash .\fdry-windows-x64.exe -Algorithm SHA256
```

On Linux, use the system's `sha256sum` against the downloaded checksum file;
if checking only a subset of release assets, ensure your checksum tool verifies
the selected file rather than treating missing assets as a successful full check.
Set the Linux executable bit with `chmod +x` after downloading.

With an authenticated GitHub CLI supporting attestations, verify the downloaded
file's build provenance, for example:

```powershell
gh attestation verify .\fdry-windows-x64.exe --repo georgeollis/fdry
```

Use the corresponding Linux filename when verifying that asset. Check that the
attestation identifies this repository's expected release workflow and commit.
Build-provenance attestations are separate from Windows Authenticode signatures.
