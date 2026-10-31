# fdry

`fdry` is an independent, open-source command-line interface for **Microsoft Foundry**.
Manage agents, model deployments, projects, and related resources through the
Microsoft Foundry and Azure management SDKs. Available as a Python package or
standalone Windows/Linux executable. This is not an official Microsoft product.

[![CI](https://github.com/georgeollis/fdry/actions/workflows/ci.yml/badge.svg)](https://github.com/georgeollis/fdry/actions/workflows/ci.yml)
[![Executables](https://github.com/georgeollis/fdry/actions/workflows/binary.yml/badge.svg)](https://github.com/georgeollis/fdry/actions/workflows/binary.yml)
[![Documentation](https://github.com/georgeollis/fdry/actions/workflows/pages.yml/badge.svg)](https://github.com/georgeollis/fdry/actions/workflows/pages.yml)
[![Security](https://github.com/georgeollis/fdry/actions/workflows/security.yml/badge.svg)](https://github.com/georgeollis/fdry/actions/workflows/security.yml)

## Documentation

Documentation is available at **[georgeollis.github.io/fdry](https://georgeollis.github.io/fdry/)**.

| Guide | Purpose |
|-------|---------|
| [Workflow examples](docs/workflows.md) | Complete workflows for structured agent responses, web research, model deployment, and search index references. |
| [CLI reference](docs/cli.md) | Commands, options, defaults, output formats, and configuration precedence. |
| [Request-body reference](docs/request-bodies.md) | SDK/API schemas, bundled example fields, and request-model serialization. |
| [Release guide](docs/releasing.md) | Platform requirements, installation artifacts, and checksum/provenance verification. |

The files in `examples` use SDK/API request field names. The
[request-body reference](docs/request-bodies.md#sdkapi-request-bodies) documents
their schemas and shows how to serialize SDK request models.

## Support and repository safeguards

| Distribution | Supported/tested target |
|--------------|-------------------------|
| Python package | Windows and Linux; CI tests Python **3.10, 3.13, and 3.15**. Python 3.10+ is required. |
| Windows executable | x86-64; bundles Python 3.13. No Python installation is needed. |
| Linux executable | x86-64, built on Ubuntu 22.04; glibc 2.35+ and an executable temporary directory are required. |
| Other standalone targets | No macOS, ARM64, or Alpine/musl binaries are supplied. |

See [SECURITY.md](SECURITY.md) for security reporting,
[CONTRIBUTING.md](CONTRIBUTING.md) for development and repository checks, and the
[release guide](docs/releasing.md) for builds and artifact verification.

## Install

**[Download v0.1.0](https://github.com/georgeollis/fdry/releases/tag/v0.1.0)**
provides Windows/Linux executables, Python wheel/source archives, checksums, and
build-provenance attestations.

### Windows executable

The standalone x64 build bundles Python and its dependencies; users do **not**
need to install Python. It is a portable executable, not an MSI installer.
Download `fdry-windows-x64.exe` and `SHA256SUMS` from the
[release](https://github.com/georgeollis/fdry/releases/tag/v0.1.0).
Compare the hash, then rename the executable:

```powershell
Get-FileHash .\fdry-windows-x64.exe -Algorithm SHA256
Rename-Item .\fdry-windows-x64.exe fdry.exe
.\fdry.exe --help
```

Add the executable's directory to `PATH` to use `fdry` from any directory.
The executable has the same commands and configuration as the Python package.
Azure CLI is not bundled: install it separately for `az login`, or use supported
environment/workload/managed identity credentials.

The Windows executable is unsigned. Windows may display a SmartScreen prompt.

### From source

Requires Python 3.10 or later. From a checkout:

```powershell
python -m pip install .
fdry --help
```

The package is not published to PyPI. Installing from source creates the
`fdry` executable; `python -m fdry` also works.

### Linux executable

The Linux x86-64 build bundles Python and dependencies. It is built on Ubuntu
22.04 and targets glibc 2.35 or later. Alpine/musl, ARM64, and macOS binaries
are not supplied. The executable needs a writable/executable temporary directory
for PyInstaller extraction and a working system CA trust store.

Download `fdry-linux-x64` and `SHA256SUMS` from the release.
Check its SHA-256 hash against the matching entry before running it, then grant
execute permission and rename it to `fdry` if desired. Linux users can use
`sha256sum` to verify the hash and `chmod +x` to grant execute permission.
Add its directory to `PATH`, or invoke it by its full path. Azure CLI remains
a separate installation for interactive authentication.

Releases include SHA-256 checksums and GitHub build-provenance attestations.
Verification instructions are in the [release guide](docs/releasing.md).

## Authenticate and configure

For local development, install Azure CLI and sign in:

```powershell
az login
fdry --profile "<PROFILE>" config set endpoint "https://<ACCOUNT>.services.ai.azure.com/api/projects/<PROJECT>"
fdry --profile "<PROFILE>" config show
fdry --profile "<PROFILE>" auth status
fdry --profile "<PROFILE>" -o table model list
```

Authentication uses `DefaultAzureCredential`, so environment-based service
principals, workload identities, and managed identities are supported too.
`fdry` does not store access tokens or API keys.
Authentication success does not imply authorization: assign the appropriate
Foundry data-plane roles and Azure resource-management permissions separately.

Management commands need additional context:

```powershell
fdry --profile "<PROFILE>" config set subscription "<SUBSCRIPTION_ID>"
fdry --profile "<PROFILE>" config set resource_group "<RESOURCE_GROUP>"
fdry --profile "<PROFILE>" config set account "<ACCOUNT>"
fdry --profile "<PROFILE>" config set project "<PROJECT>"
```

Profiles are stored in `~/.fdry/config.json`. Use `--profile <PROFILE>` or
`FDRY_PROFILE` to select one; `FDRY_CONFIG` overrides the config-file path.
Global flags must appear **before** the resource command.

Settings resolve in this order: **command-line flag > environment variable > saved profile**.

| Setting | Global flag | Environment variable |
|---------|-------------|----------------------|
| Project endpoint | `--endpoint` | `AZURE_AI_PROJECT_ENDPOINT` |
| Subscription | `--subscription` | `AZURE_SUBSCRIPTION_ID` |
| Resource group | `--resource-group` | `AZURE_RESOURCE_GROUP` |
| Account | `--account` | `AZURE_AI_ACCOUNT_NAME` |
| Management project | `--project` | `AZURE_AI_PROJECT_NAME` |

The endpoint selects the project for data-plane operations. `--project` selects
the project for management-plane connection writes; keep them aligned when
working with one project. Project CRUD instead uses its command's `--name`.

Use the same explicit profile for a workflow. Profiles isolate saved resource
settings, not credentials or environment variables; check effective settings
before modifying resources.

## Commands

| Group | Supported operations |
|-------|----------------------|
| `account` | List, show, create, delete Foundry accounts |
| `project` | List, show, create, delete projects within an account |
| `agent` | List, show, create prompt/hosted versions, list versions, invoke, enable, disable, delete |
| `model` | List/show deployments, discover catalog models, create deployments, Responses/chat/embeddings invocation, delete |
| `connection` | List, show, create/update, delete project connections |
| `toolbox` | List, show, create versions, list versions, publish default version, delete versions/all |
| `dataset` | List, show, create/update versions, list versions, upload files/folders, delete |
| `index` | List, show, create/update versions, list versions, delete index references |
| `evaluation` | List, show, create, delete evaluation definitions |
| `evaluation run` | Create, list, show, cancel runs |
| `fine-tuning` | Create, list, show, cancel jobs |
| `file` | Upload, list, show, delete training/evaluation files |
| `quota` | Inspect account usage |
| `config` | Set, show, list profiles, unset settings |
| `auth` | Check SDK authentication |
| `rest` | Send authenticated, project-relative requests to other data-plane APIs |

List commands consume SDK pagination. `rest` returns one response and does not
paginate. JSON is the default output; use `-o yaml` or `-o table`.
Output retains the SDK response shape, with common credential fields redacted.
Redaction is best-effort, not a guarantee that arbitrary service data is non-sensitive.

### Agents and models

With an existing model deployment, create a focused agent and use the returned
version for reproducible invocation:

```powershell
fdry --profile "<PROFILE>" agent create --name "<AGENT>" --model "<MODEL_DEPLOYMENT>" --instructions "Summarize operational incidents. Separate observed facts from hypotheses and recommend one next diagnostic step."
fdry --profile "<PROFILE>" agent show --name "<AGENT>" --version "<RETURNED_VERSION>"
fdry --profile "<PROFILE>" agent invoke --name "<AGENT>" --version "<RETURNED_VERSION>" --input "Requests began returning rate-limit errors immediately after traffic doubled. Summarize the incident and recommend the next check."
fdry --profile "<PROFILE>" model invoke --name "<MODEL_DEPLOYMENT>" --input "Explain the difference between model deployment capacity and per-request token limits." --api responses
```

For application integration, the [structured support-triage example](docs/workflows.md#return-a-structured-support-classification)
defines a JSON response schema and demonstrates exit-code handling, version
pinning, and response parsing.

`model invoke` selects the protocol with `--api responses|chat`; Responses is the
default when the flag is omitted. Choose a protocol supported by your deployment.
Embeddings use the embeddings API. Foundry agent invocation uses Responses.
Invocation returns the full response object, including IDs and usage.
External tool calls requiring application execution are returned to the caller;
the CLI does not run arbitrary local tools or automatically complete tool-call loops.

Use `agent invoke --version <VERSION>` to pin a version or
`--conversation <CONVERSATION_ID>` to continue an existing conversation.
Agent `create` also updates an existing agent by creating a new immutable version.

### Provision resources

**These commands create billable Azure resources.** The resource group must
already exist. Resource creation does not assign RBAC roles automatically.

```powershell
fdry --profile "<PROFILE>" account create --location "<REGION>"
fdry --profile "<PROFILE>" project create --name "<PROJECT>" --location "<REGION>"
fdry --profile "<PROFILE>" model catalog --location "<REGION>"
fdry --profile "<PROFILE>" model create --name "<DEPLOYMENT>" --model "<CATALOG_MODEL>" --model-version "<MODEL_VERSION>" --sku "<SKU>" --capacity 1
```

`account create` defaults to an AI Services account with project management,
system-assigned identity, and key-based authentication disabled. `project create`
defaults to a system-assigned identity. Supply `--file` **instead of** convenience
options to send an advanced ARM request body, including network settings.
Provisioning waits for the management SDK's long-running operation to complete.
Quota and billing units for `--capacity` depend on the model and SKU.

`model create` provisions a catalog-model deployment through the Cognitive
Services management API. See the [deployment workflow](docs/workflows.md#deploy-a-model-with-an-explicit-upgrade-policy)
for model selection, capacity, and upgrade-policy configuration.

### Definitions, connections, and toolboxes

Copy examples to ignored `*.local.yaml` or `*.local.json` files and replace
placeholders before using them. See the [field reference](docs/request-bodies.md)
for field types and required values.

```powershell
Copy-Item examples\prompt-agent-web-search.yaml examples\prompt-agent-web-search.local.yaml
Copy-Item examples\model-deployment.json examples\model-deployment.local.json
# Replace placeholders and review settings in both local files before submitting.
fdry --profile "<PROFILE>" model create --name "<MODEL_DEPLOYMENT>" --file examples\model-deployment.local.json
fdry --profile "<PROFILE>" agent create --name "<AGENT>" --file examples\prompt-agent-web-search.local.yaml
fdry --profile "<PROFILE>" agent versions --name "<AGENT>"
```

The model body configures catalog model/version, SKU, capacity, and version
upgrade policy. The agent body configures instructions, web search, description,
and metadata; set `definition.model` to the model **deployment** name, not its
catalog identifier. See [agent configuration](docs/request-bodies.md#example-configure-an-agent-with-web-search)
and [model configuration](docs/request-bodies.md#model-deploymentjson) for exact
SDK models and serialization examples. Use `prompt-agent.yaml` for an agent
without tools.

Other complete bodies can be submitted the same way after creating and editing
local copies of the corresponding examples:

```powershell
fdry --profile "<PROFILE>" agent create --name "<HOSTED_AGENT>" --file examples\hosted-agent.local.yaml
fdry --profile "<PROFILE>" connection create --name "<CONNECTION>" --file examples\connection.local.yaml
fdry --profile "<PROFILE>" toolbox create --name "<TOOLBOX>" --file examples\toolbox.local.yaml
fdry --profile "<PROFILE>" toolbox publish --name "<TOOLBOX>" --version "<VERSION>"
```

Hosted-agent creation registers an image-based agent version. It does **not**
build/push an image, create a registry, grant image-pull permissions, or implement
a local agent runtime. Provide an accessible image that implements the declared
Foundry protocol and has the required identity/network configuration.

Toolbox version numbers are assigned by Foundry. Publish explicitly to change
the default version. JSON/YAML input uses service wire field names: agent/toolbox
data-plane bodies use fields such as `container_configuration`; ARM bodies use
fields such as `authType`. See the
[Foundry SDK reference](https://learn.microsoft.com/python/api/azure-ai-projects/)
and [Azure management SDK reference](https://learn.microsoft.com/python/api/azure-mgmt-cognitiveservices/)
for full request schemas.

### Datasets, evaluations, and fine-tuning

```powershell
fdry --profile "<PROFILE>" dataset upload --name "<DATASET>" --version "<VERSION>" --path "<LOCAL_FILE>"
fdry --profile "<PROFILE>" evaluation create --file examples\evaluation.local.json
fdry --profile "<PROFILE>" file upload --path "<TRAINING_JSONL>" --purpose fine-tune
fdry --profile "<PROFILE>" fine-tuning create --file examples\fine-tuning.local.json
fdry --profile "<PROFILE>" fine-tuning show --id "<JOB_ID>"
```

Create and edit local copies of the evaluation and fine-tuning examples.
Use the uploaded file ID in the fine-tuning definition. Fine-tuning and
evaluation runs are asynchronous: creation returns the job/run, not a completed
training/evaluation result. Check status with `show`. Training formats, methods,
supported graders, regional availability, and permissions remain service-specific.
Dataset upload may require a storage connection with the appropriate RBAC roles.
Index commands register references; they do not provision Azure AI Search services
or build the underlying search index.

### Other APIs

```powershell
fdry --profile "<PROFILE>" rest "agents?api-version=v1"
```

Use `--method POST --file <BODY_FILE>` for request bodies. Paths must remain
relative to the configured project; external URLs and traversal are rejected.
Supply the API version required by the operation. Use `--preview` to opt in to
preview features supported by the SDK; preview routes can also require
service-specific feature headers, which this REST command does not configure.

## Safety and errors

Delete commands prompt for confirmation; `--yes` bypasses it for automation.
Account/project deletion also removes their child resources.
Create/update/publish/invoke commands do not prompt and may overwrite mutable
resources or incur charges. Review the target and request before running them.

Service failures return a nonzero exit status and an error on stderr. Missing
settings, invalid documents, and invalid arguments are reported as usage errors.
Keep credential-bearing definition files outside source control; use Entra
authentication where possible. `*.local.json` and `*.local.yaml` are ignored.
Private endpoints require execution from a network with access and correct DNS.

## Development and architecture

```powershell
uv sync --locked --all-extras --python 3.13
uv run --no-sync python -m pytest -q -m "not binary"
uv run --no-sync python -m ruff check src tests .github\scripts
uv run --no-sync python -m ruff format --check src tests .github\scripts
uv run --no-sync python -m mypy src .github\scripts
uv run --no-sync python -m build --no-isolation
uv run --no-sync pip-audit --skip-editable
```

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) first.
CI pins uv and uses the committed `uv.lock` for platform-specific dependency
versions and hashes. End-user source installation still supports pip, but pip
resolves the package's declared dependency ranges rather than consuming this lock.
See [CONTRIBUTING.md](CONTRIBUTING.md) for the development and pull-request workflow.
For documentation-only edits, use the
[documentation-site checks](CONTRIBUTING.md#documentation-site) instead of the
package and executable build commands.

```text
src\fdry\
  cli.py                 Root options, registration, and error boundary
  commands\              One module per resource; explicit SDK operations
    _options.py          Shared Click options and delete confirmation
  core\
    config.py            Profile validation and atomic persistence
    context.py           Typed, lazy SDK clients and invocation lifetime
    documents.py         Input validation and wire-format adapters
    output.py            Serialization, redaction, and output rendering
tests\
  unit\                  CLI behavior with isolated SDK boundaries
  contract\              Real SDK serialization/pagination, offline transport
  binary\                Black-box checks against the standalone executable
packaging\               Standalone executable build specification
examples\                Placeholder-only resource definitions
```

Dependency direction is `cli -> commands -> core -> SDK`. Resource command
modules call the corresponding SDK operations; shared modules handle profile
persistence, client lifetimes, request documents, and output serialization.

Contract tests cover SDK request serialization and pagination.
CI runs on Windows and Linux with Python 3.10, 3.13, and 3.15.

See [contribution requirements](CONTRIBUTING.md) for validation and review guidance.

### Build and release standalone executables

Build on the target OS with Python 3.13 x64; PyInstaller does not cross-compile.
For Windows:

```powershell
uv sync --locked --all-extras --python 3.13
uv run --no-sync python -m PyInstaller --noconfirm --clean --log-level WARN packaging\fdry.spec
$env:FDRY_EXE = (Resolve-Path dist\fdry.exe).Path
uv run --no-sync python -m pytest -q tests\binary
```

The Windows output is `dist\fdry.exe`; the Linux output is named `fdry` in `dist`.
Both executables are built from the same entry
point as the Python package. SDK modules loaded dynamically are included by the
build specification. Binary checks run from an unrelated directory with Python
environment overrides removed, no Python executable on the Windows search path,
and no Azure credentials configured. The default
test suite skips them unless `FDRY_EXE` is set.

The **Executables** GitHub Actions workflow builds and exercises both platforms
on runtime-changing pull requests and pushes to `main`, manual dispatch, and
`v*` tags. Documentation-only changes do not rebuild either executable.
A tag must match the package version, for example `v0.1.0`.
Tagged builds create a **draft GitHub release** with Windows/Linux x64 executables,
Python wheel/source distributions, SHA-256 checksums, and the MIT license.
Maintainers review and publish drafts separately. Runtime-changing pull requests
and manual runs upload workflow artifacts without creating a release. No release
is created by a local build. See the [release checklist](docs/releasing.md) before
tagging.

## License

[MIT](LICENSE).
