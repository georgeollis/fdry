# Release readiness and supported platforms

## Current assurance

The repository is hardened for reviewed changes, locked dependency installation,
offline contract testing, and gated Linux and Wine-based Windows builds. That is **not**
certification of production behavior against Azure. The package remains marked
alpha until maintainers have evidence for a stable support commitment.

The [v0.1.0 pre-release](https://github.com/georgeollis/fdry/releases/tag/v0.1.0)
provides the initial Windows/Linux executables and Python distributions.
Its offline-only validation and unsigned-native-code limitations remain in effect.
That release's Windows executable was built natively with Python 3.13; the
Linux/Wine workflow below applies to subsequent builds, not the existing assets.

| Area | Coverage / limitation |
|------|-----------------------|
| Python package | Windows/Linux CI on Python 3.10, 3.13, and 3.15; wheel and source distribution build/metadata checks; isolated wheel-install smoke test. |
| Windows executable | x86-64 standalone build on Ubuntu 24.04 using Windows Python 3.15.2 and PyInstaller under Wine 11; all command-help paths, config persistence, and offline SDK imports/auth failures run under Wine. No native Windows executable validation, MSI, or ARM64 build. Native Windows source tests are separate from artifact validation. |
| Linux executable | x86-64 build on Ubuntu 22.04, Python 3.13; same black-box checks. Targets glibc 2.35+. No Alpine/musl, ARM64, or macOS binary support. Other Linux distributions are not individually certified. |
| Dependencies | `uv.lock` pins resolved inputs/hashes; audits run in CI and weekly. Python-version/platform markers can select different locked versions. Public pip installs still resolve declared ranges. |
| Code and repository | Ruff, formatting, strict mypy, CodeQL, dependency review, pinned actions, strict documentation-site builds, required PR/check gates, protected linear history. |
| Azure behavior | Current hardening validation is offline only. Resource provisioning, RBAC, regional/model availability, hosted readiness, inference, uploads, evaluations, and training still need explicitly authorized live validation for the release. |
| Distribution trust | Tagged builds prepare checksums and GitHub build-provenance attestations. No native code-signing certificate or package-manager/PyPI publishing is configured. |

Linux binaries need a writable/executable temporary location for PyInstaller's
one-file extraction, the relevant glibc runtime, and system CA trust.
Checks on Ubuntu do not establish compatibility with every glibc distribution.
Use the Python package where a standalone target is unsupported.

## Building the Windows executable on Linux

PyInstaller is [not a native cross-compiler](https://pyinstaller.org/en/stable/).
The Windows job instead runs Windows Python and Windows dependencies inside
Wine. It does not use a Windows runner or a third-party container image.

Use Ubuntu 24.04 x86-64 with WineHQ stable **11.0.0.0~noble-1**, `xvfb`, `xauth`,
`curl`, `file`, and uv **0.13.6**. The workflow installs Wine from its signed
official apt repository and verifies the signing-key file's SHA-256 digest.
From a checkout, with those tools installed:

```bash
export RUNNER_TEMP="$(mktemp -d)"
export WINEPREFIX="$RUNNER_TEMP/fdry-wine"
xvfb-run --auto-servernum bash packaging/build-windows.sh
```

The script downloads the official Windows Python **3.15.2** x64 installer,
verifies its SHA-256 digest, and installs it into the isolated Wine prefix.
It exports the reviewed `uv.lock`, requires dependency hashes and Windows
wheels, audits that environment, runs offline source tests, packages the
Windows PE executable, and runs all executable checks with Windows Python
under Wine. The output is `dist/fdry.exe`; CI publishes it as
`fdry-windows-x64.exe` with checksums.

Update the reviewed installer URL/hash together when changing Python. Update
the Wine version and signing-key hash deliberately when upgrading that toolchain.
Do not replace a failed locked dependency with an unpinned installation.
Wine is a compatibility layer: passing these checks does **not** prove the
artifact works on real Windows. Validate the downloaded executable on the
intended Windows versions before making native Windows support assurances.
The separate Windows source-test matrix does not close that artifact-testing gap.

## Before tagging a release

1. Review changes, dependency/audit results, compatibility, licenses of bundled
   dependencies, and outstanding CodeQL findings. Do not bypass failing gates
   or publish with unresolved material findings.
2. Verify `Required CI`, `Required executables`, `CodeQL analysis`, and `Documentation site` for the
   exact commit on `main`. Check both executable artifacts and isolated wheel
   installation, not only editable-source tests. The release PR must also pass
   `Dependency review`.
3. Run separately authorized Azure integration tests against representative
   projects/models and permissions. Include failure/cleanup behavior. Record
   sanitized evidence, supported regions/models/APIs, costs, and any exclusions.
   Never start billable tests as an implicit CI/release step.
4. Verify the supported-platform matrix and evaluate signing/distribution
   requirements for the intended production audience. Unsigned native builds
   and unverified live paths must remain explicit release limitations.
5. Update `src\fdry\__init__.py`, package classifiers when justified, release
   notes, and docs through a passing PR. Use a SemVer version and a matching
   `v<VERSION>` tag. Do not mark the first version stable merely because CI passes.

## Tagged build and draft review

Push a version tag pointing at the reviewed `main` commit. The **Executables**
workflow checks the tag against the package version, audits dependencies, runs
offline/lint/type gates, builds/tests both executables, and builds wheel/source
distributions. The release job only runs after platform checks succeed.

The workflow creates a **draft**, not a public release, containing:

| Asset | Purpose |
|-------|---------|
| `fdry-windows-x64.exe` | Portable Windows executable. |
| `fdry-linux-x64` | Portable glibc-based Linux executable. |
| `fdry-<VERSION>-py3-none-any.whl` | Python wheel. |
| `fdry-<VERSION>.tar.gz` | Python source distribution, including dependency lock and source. |
| `SHA256SUMS` | SHA-256 hashes for the executables and Python distributions. |
| `LICENSE` | Project MIT license; bundled dependencies retain their own licenses. |

Review the workflow identity/commit and all artifacts before publishing the
draft. Confirm version output, platform behavior, hash entries, and provenance.
No stable release is automatically published to GitHub or PyPI.
Rerunning a tag does not authorize replacing an existing release; resolve a
failed draft deliberately and never silently overwrite published assets/tags.

The lock makes dependency selection reviewable and repeatable. OS images,
Python patch versions, build timestamps, and native tooling are not fully
hermetic; byte-for-byte reproducibility is not claimed.

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
Attestations establish an artifact's build identity, not its functional safety,
Azure compatibility, or a Windows code-signing trust chain.
