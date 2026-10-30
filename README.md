# fdry

An independent, open-source Python command-line interface for **Microsoft Foundry**.
Built on the Microsoft Foundry Python SDK and Azure management SDK. Not an official
Microsoft product.

**Status:** initial implementation. This is not yet full Foundry portal parity.
Preview APIs, model availability, quota, and hosted-agent support depend on the
selected region, subscription, and service rollout.

## Documentation

[CLI reference](docs/cli.md) covers every command, option, default, accepted
CLI choice, and configuration value.
[Request-body reference](docs/request-bodies.md) explains every field in the
bundled YAML/JSON examples, provisioning defaults, and advanced schema references.

The files in `examples` are AI-assisted templates authored for this project,
not official Microsoft samples or exports from an Azure environment. They use
the SDK/API request formats linked in the request-body reference. Replace all
placeholders before submitting them; service support and permissions still apply.

## Install

### Windows executable

The standalone x64 build bundles Python and its dependencies; users do **not**
need to install Python. It is a portable executable, not an MSI installer.
Once a GitHub release is published, download `fdry-windows-x64.exe` and
`SHA256SUMS` from that release. Compare the hash, then rename the executable:

```powershell
Get-FileHash .\fdry-windows-x64.exe -Algorithm SHA256
Rename-Item .\fdry-windows-x64.exe fdry.exe
.\fdry.exe --help
```

Add the executable's directory to `PATH` to use `fdry` from any directory.
The executable has the same commands and configuration as the Python package.
Azure CLI is not bundled: install it separately for `az login`, or use supported
environment/workload/managed identity credentials.

No executable release has been published yet. Builds are currently unsigned;
code signing and installer/package-manager distribution are not configured.

### From source

Requires Python 3.10 or later. From a checkout:

```powershell
python -m pip install .
fdry --help
```

The package is not yet published to PyPI. Installing from source creates the
`fdry` executable; `python -m fdry` also works.

## Authenticate and configure

For local development, install Azure CLI and sign in:

```powershell
az login
fdry auth status
fdry config set endpoint "https://<ACCOUNT>.services.ai.azure.com/api/projects/<PROJECT>"
```

Authentication uses `DefaultAzureCredential`, so environment-based service
principals, workload identities, and managed identities are supported too.
`fdry` does not store access tokens or API keys.
Authentication success does not imply authorization: assign the appropriate
Foundry data-plane roles and Azure resource-management permissions separately.

Management commands need additional context:

```powershell
fdry config set subscription "<SUBSCRIPTION_ID>"
fdry config set resource_group "<RESOURCE_GROUP>"
fdry config set account "<ACCOUNT>"
fdry config set project "<PROJECT>"
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

```powershell
fdry agent list
fdry model list
fdry project list
fdry agent create --name "<AGENT>" --model "<DEPLOYMENT>" --instructions "You are a helpful assistant."
fdry agent invoke --name "<AGENT>" --input "Hello"
fdry model invoke --name "<DEPLOYMENT>" --input "Hello" --api responses
fdry model invoke --name "<DEPLOYMENT>" --input "Hello" --api chat
fdry model embeddings --name "<EMBEDDING_DEPLOYMENT>" --input "Some text"
```

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
fdry account create --location "<REGION>"
fdry project create --name "<PROJECT>" --location "<REGION>"
fdry model catalog --location "<REGION>"
fdry model create --name "<DEPLOYMENT>" --model "<CATALOG_MODEL>" --model-version "<MODEL_VERSION>" --sku "<SKU>" --capacity 1
```

`account create` defaults to an AI Services account with project management,
system-assigned identity, and key-based authentication disabled. `project create`
defaults to a system-assigned identity. Supply `--file` **instead of** convenience
options to send an advanced ARM request body, including network settings.
Provisioning waits for the management SDK's long-running operation to complete.
Quota and billing units for `--capacity` depend on the model and SKU.

`model create` deploys a catalog model through the Cognitive Services deployment
API; it does not train model weights or cover every serverless/managed-compute
offering in the wider model catalog.

### Definitions, connections, and toolboxes

Copy examples to ignored `*.local.yaml` or `*.local.json` files and replace
placeholders before using them. See the [field reference](docs/request-bodies.md)
for types, required values, and where to obtain each value. The following
commands show which command consumes each template:

```powershell
fdry agent create --name "<AGENT>" --file examples\prompt-agent.yaml
fdry agent create --name "<HOSTED_AGENT>" --file examples\hosted-agent.yaml
fdry connection create --name "<CONNECTION>" --file examples\connection.yaml
fdry toolbox create --name "<TOOLBOX>" --file examples\toolbox.yaml
fdry toolbox publish --name "<TOOLBOX>" --version "<VERSION>"
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
fdry dataset upload --name "<DATASET>" --version "<VERSION>" --path "<LOCAL_FILE>"
fdry evaluation create --file examples\evaluation.json
fdry file upload --path "<TRAINING_JSONL>" --purpose fine-tune
fdry fine-tuning create --file examples\fine-tuning.json
fdry fine-tuning show --id "<JOB_ID>"
```

Use the uploaded file ID in the fine-tuning definition. Fine-tuning and
evaluation runs are asynchronous: creation returns the job/run, not a completed
training/evaluation result. Check status with `show`. Training formats, methods,
supported graders, regional availability, and permissions remain service-specific.
Dataset upload may require a storage connection with the appropriate RBAC roles.
Index commands register references; they do not provision Azure AI Search services
or build the underlying search index.

### Other APIs

```powershell
fdry rest "agents?api-version=v1"
```

Use `--method POST --file <BODY_FILE>` for request bodies. Paths must remain
relative to the configured project; external URLs and traversal are rejected.
Supply the API version required by the operation. Use `--preview` to opt in to
preview features supported by the SDK; preview routes can also require
service-specific feature headers, which this REST command does not configure.
Skills, routines, memory stores, red-team scans, tracing, networking, RBAC
management, and hosted-agent build/deploy orchestration do not yet have dedicated
command groups. `rest` is not a substitute for all Azure management APIs.

## Safety and errors

Delete commands prompt for confirmation; `--yes` bypasses it for automation.
Account/project deletion also removes their child resources.
Create/update/publish/invoke commands do not prompt and may overwrite mutable
resources or incur charges. Do not run them against production without review.

Service failures return a nonzero exit status and an error on stderr. Missing
settings, invalid documents, and invalid arguments are reported as usage errors.
Keep credential-bearing definition files outside source control; use Entra
authentication where possible. `*.local.json` and `*.local.yaml` are ignored.
Private endpoints require execution from a network with access and correct DNS.

## Development and architecture

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src
python -m pip wheel --no-deps . --wheel-dir dist
```

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

Dependency direction is `cli -> commands -> core -> SDK`. Resource modules do not
import each other. There is no custom HTTP/authentication stack, generic resource
dispatcher, or extra service layer that simply mirrors SDK methods. Add one only
when a real cross-command domain workflow justifies it.

Tests never create Azure resources. Contract tests exercise the installed Azure
SDKs against an offline transport; they are not live-service integration tests.
CI runs on Windows and Linux with Python 3.10 and 3.13. Live Azure validation is
still required before treating a release as production-ready.

Contributions should keep resource behavior explicit, preserve structured output
and failure exit codes, and include focused behavior or SDK-contract tests.
Run the commands above before opening a pull request.

### Build and release the Windows executable

Build on Windows with Python 3.13 x64; PyInstaller does not cross-compile.

```powershell
python -m pip install -e ".[dev,binary]"
python -m PyInstaller --noconfirm --clean --log-level WARN packaging\fdry.spec
$env:FDRY_EXE = (Resolve-Path dist\fdry.exe).Path
python -m pytest -q tests\binary
```

The output is `dist\fdry.exe`. The executable is built from the same entry
point as the Python package. SDK modules loaded dynamically are included by the
build specification. Binary checks run from an unrelated directory with Python
environment overrides removed, no Python executable on the Windows search path,
and no Azure credentials configured. The default
test suite skips them unless `FDRY_EXE` is set.

The **Windows executable** GitHub Actions workflow builds and exercises the
artifact on pull requests affecting binary inputs, on manual dispatch, and on
`v*` tags. A tag must match the package version, for example `v0.1.0`.
Tagged builds create a **draft GitHub release** with the Windows x64 executable,
its SHA-256 checksum, and the MIT license; maintainers review and publish the
draft separately. Manual runs upload workflow artifacts without creating a release.
No GitHub release is created by running a local build.

## License

[MIT](LICENSE).
