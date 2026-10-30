# CLI reference

`fdry` is an independent CLI for Microsoft Foundry, not a Microsoft product.
This reference covers all implemented commands and CLI values. Azure resource
names, model catalogs, regions, SKUs, protocol versions, and request-body
subtypes are service-defined, not fixed enumerations maintained by `fdry`.
See [request bodies](request-bodies.md) for YAML/JSON fields and source schemas.

## Syntax and help

```text
fdry [GLOBAL_OPTIONS] COMMAND [SUBCOMMAND] [OPTIONS]
```

Global options must precede the command. Brackets mean optional values in this
reference; do not type the brackets or placeholder angle brackets literally.
All commands and groups support `--help` and `-h`.
The installed Python package also supports `python -m fdry`; the Windows
standalone executable supports the same arguments.

```powershell
fdry --help
fdry agent create --help
fdry evaluation run create --help
fdry --profile "<PROFILE>" -o table agent list
```

## Global options

| Option | Value and default | Meaning |
|--------|-------------------|---------|
| `--profile` | String; `FDRY_PROFILE`, otherwise `default` | Saved settings profile. An unknown profile starts with no saved settings. |
| `--endpoint` | HTTPS project endpoint; unset by default | Data-plane project, in the form `https://<ACCOUNT>.services.ai.azure.com/api/projects/<PROJECT>`. No query, fragment, credentials, or extra path segments. |
| `--subscription` | Azure subscription ID; unset | Subscription for management-plane operations. |
| `--resource-group` | Existing resource-group name; unset | Resource group for management operations. |
| `--account` | Foundry account name; unset | Parent account for management operations. |
| `--project` | Project name; unset | Management-plane project for connection writes/deletes. Does not override the endpoint's project. |
| `--output`, `-o` | `json`, `yaml`, or `table`; `json` | Output serialization. Table mode is a simple rendering, not a selectable column/query interface. |
| `--preview` | Flag; off | Sets the Foundry SDK's `allow_preview` option. Does not unlock permissions or guarantee API availability. |
| `--version` | Flag | Prints the CLI version and exits. On a resource command, `--version` instead identifies a resource version. |
| `--help`, `-h` | Flag | Prints help and exits. |

## Configuration and environment

Only the following five keys can be saved with `config set`. All saved values
are nonempty strings. Do not save tokens, API keys, or passwords.

| Key | Environment variable | How to obtain the value |
|-----|----------------------|-------------------------|
| `endpoint` | `AZURE_AI_PROJECT_ENDPOINT` | Copy the project endpoint from Microsoft Foundry. |
| `subscription` | `AZURE_SUBSCRIPTION_ID` | Azure subscription ID containing the management resources. |
| `resource_group` | `AZURE_RESOURCE_GROUP` | Existing Azure resource group containing the account. |
| `account` | `AZURE_AI_ACCOUNT_NAME` | Foundry account resource name, not a project name or URL. |
| `project` | `AZURE_AI_PROJECT_NAME` | Project resource name under that account. |

Effective settings resolve as **global flag > environment variable > saved profile**.
`config show` displays effective settings; `config list` displays only saved profiles.
`config unset` removes a saved value, not an environment variable or Azure resource.

| Additional variable | Value and default |
|---------------------|-------------------|
| `FDRY_PROFILE` | Profile name; `default`. Explicit `--profile` takes precedence. |
| `FDRY_CONFIG` | Config-file path; otherwise `~/.fdry/config.json`. Use an absolute path for portability. |
| `FDRY_EXE` | Developer-only path to a built standalone executable; enables binary tests. Not a runtime CLI setting. |

The renamed CLI does not read legacy `FOUNDRYCTL_*` variables or
`~/.foundryctl/config.json`. Existing users must copy their non-secret profile
data to the new location and update scripts.

```powershell
fdry --profile "<PROFILE>" config set endpoint "https://<ACCOUNT>.services.ai.azure.com/api/projects/<PROJECT>"
fdry --profile "<PROFILE>" config set subscription "<SUBSCRIPTION_ID>"
fdry --profile "<PROFILE>" config set resource_group "<RESOURCE_GROUP>"
fdry --profile "<PROFILE>" config set account "<ACCOUNT>"
fdry --profile "<PROFILE>" config set project "<PROJECT>"
fdry --profile "<PROFILE>" config show
```

The config format is:

```json
{
  "profiles": {
    "<PROFILE>": {
      "endpoint": "https://<ACCOUNT>.services.ai.azure.com/api/projects/<PROJECT>",
      "subscription": "<SUBSCRIPTION_ID>",
      "resource_group": "<RESOURCE_GROUP>",
      "account": "<ACCOUNT>",
      "project": "<PROJECT>"
    }
  }
}
```

Profile names are user-chosen strings; the five setting keys above are the only
accepted setting keys. Missing files mean no saved profiles. Invalid config
files cause an error rather than being silently overwritten.

## Authentication and required context

Authentication uses Azure Identity's `DefaultAzureCredential`. For local use,
sign in with `az login`; Azure CLI is a separate installation. Environment,
workload identity, and managed identity authentication are also supported.
For example, service-principal authentication uses `AZURE_TENANT_ID`,
`AZURE_CLIENT_ID`, and `AZURE_CLIENT_SECRET`; these are SDK credentials, not
saved `fdry` settings. Keep secrets outside this repository.
See [DefaultAzureCredential](https://learn.microsoft.com/python/api/azure-identity/azure.identity.defaultazurecredential)
for the complete SDK-owned credential chain and its environment values.

`auth status` acquires a token for `https://ai.azure.com/.default` and prints
`authenticated` and the Unix timestamp `expires_on`, never the token.
It does not prove access to a particular project or management operation.
Assign the appropriate Azure RBAC permissions separately.

| Command family | Required settings |
|----------------|-------------------|
| `config` | None; uses the selected local profile. |
| `auth status` | Credentials, but no project or subscription setting. |
| `account list` | `subscription`; optional `resource_group` narrows the list. Only `AIServices` accounts are returned. |
| Other `account`, all `project`, `model create`, `model delete`, `quota list` | `subscription`, `resource_group`, `account`. |
| `model catalog --location` | `subscription` and the location argument. |
| `model catalog` without `--location` | `subscription`, `resource_group`, `account`. |
| `connection create`, `connection delete` | `subscription`, `resource_group`, `account`, `project`. |
| Agents, model list/show/inference, connection list/show, toolboxes, datasets, indexes, evaluations, fine-tuning, files, `rest` | `endpoint`. |

## Shared command options

`--name` (`-n`) is always required where listed. It identifies the resource
within the command's scope. `--id` is a service-returned object ID, not a name.
Resource `--version` is a string returned by the service or supplied when creating
a dataset/index version; it is not the CLI or model-catalog version.

`--file` accepts an existing JSON/YAML file containing a JSON-compatible object,
using service wire-format keys. It is not a YAML deployment orchestrator,
template engine, or environment-variable interpolator. See
[request-body rules](request-bodies.md#file-format-and-validation).

`--yes` (`-y`) skips destructive-action confirmation; it defaults to false.
Deletes prompt unless it is supplied. Create, update, publish, invoke, and cancel
operations do not prompt and may incur costs or modify resources.

In the tables below, **Required** lists mandatory command arguments/options;
an em dash means none. All rows also support help.

## Accounts and projects

| Command | Required | Optional | Behavior |
|---------|----------|----------|----------|
| `fdry account list` | — | — | List Foundry accounts in the subscription or configured resource group. |
| `fdry account show` | — | — | Read the configured account. |
| `fdry account create` | `--location <REGION>` or `--file <PATH>` | — | Create in an existing resource group; the two inputs are mutually exclusive. Waits for completion. |
| `fdry account delete` | — | `--yes`, `-y` | Delete the configured account and its children; waits for completion. |
| `fdry project list` | — | — | List projects under the configured account. |
| `fdry project show` | `--name <PROJECT>` | — | Read that project. |
| `fdry project create` | `--name <PROJECT>` and either `--location <REGION>` or `--file <PATH>` | — | Create a project; location should match the parent account. Waits for completion. |
| `fdry project delete` | `--name <PROJECT>` | `--yes`, `-y` | Delete that project and its children; waits for completion. |

`<REGION>` is an Azure location identifier. Availability is service-specific.
Use [provisioning body defaults](request-bodies.md#account-project-and-model-provisioning)
to understand the identity, SKU, and authentication settings created by convenience flags.
`project --name` is independent of the global `--project` connection setting.

## Agents

| Command | Required | Optional | Behavior |
|---------|----------|----------|----------|
| `fdry agent list` | — | — | List agents in the endpoint's project. |
| `fdry agent show` | `--name <AGENT>` | `--version <VERSION>` | Read agent details, or a specific version. |
| `fdry agent versions` | `--name <AGENT>` | — | List all versions. |
| `fdry agent create` | `--name <AGENT>` and either `--file <PATH>` or both `--model <DEPLOYMENT>` and `--instructions <TEXT>` | — | Create an immutable version, including for an existing agent. File input cannot be mixed with model/instructions flags. |
| `fdry agent invoke` | `--name <AGENT>`, `--input <TEXT>` | `--version <VERSION>`, `--conversation <CONVERSATION_ID>` | Send a user message through Responses; optionally pin a version or continue a conversation. |
| `fdry agent enable` | `--name <AGENT>` | — | Enable the agent. |
| `fdry agent disable` | `--name <AGENT>` | — | Disable the agent. |
| `fdry agent delete` | `--name <AGENT>` | `--version <VERSION>`, `--yes`, `-y` | Delete one version if specified, otherwise the agent. |

`--model` is a deployment name, not a catalog model ID. Get deployments with
`fdry model list`. Hosted agents require `--file` and an already accessible
container image. `fdry` does not build/push that image or grant image-pull permissions.
External tool calls are returned to the caller; the CLI does not execute local
tools or automatically run a tool-call loop.

## Models

| Command | Required | Optional | Behavior |
|---------|----------|----------|----------|
| `fdry model list` | — | — | List deployments visible to the project. |
| `fdry model show` | `--name <DEPLOYMENT>` | — | Read a deployment. |
| `fdry model catalog` | — | `--location <REGION>` | List regional catalog models, or account-available models when location is omitted. |
| `fdry model create` | `--name <DEPLOYMENT>` and either `--file <PATH>` or both `--model <CATALOG_MODEL>` and `--model-version <MODEL_VERSION>` | `--format <FORMAT>`, `--sku <SKU>`, `--capacity <INTEGER>` | Create/update an Azure model deployment and wait for completion. |
| `fdry model invoke` | `--name <DEPLOYMENT>`, `--input <TEXT>` | `--api responses` or `--api chat` | Invoke through Responses (default) or Chat Completions. |
| `fdry model embeddings` | `--name <DEPLOYMENT>`, `--input <TEXT>` | — | Request embeddings for one input string. |
| `fdry model delete` | `--name <DEPLOYMENT>` | `--yes`, `-y` | Delete the deployment and wait for completion. |

For `model create`, `--format` defaults to `OpenAI`, `--sku` to `GlobalStandard`,
and `--capacity` to `1` (integer, minimum `1`). These are not exhaustive provider/SKU
choices: use catalog results and Azure documentation for the selected model.
Capacity units and quota depend on the model/SKU. File input cannot be combined
with any explicitly supplied model, model-version, format, SKU, or capacity flag.
Model creation deploys existing catalog weights; it is not a training operation.
Choose an inference API supported by the deployment. Full response objects,
including IDs and usage, are returned.

## Connections and toolboxes

| Command | Required | Optional | Behavior |
|---------|----------|----------|----------|
| `fdry connection list` | — | — | List project connections through the data plane. |
| `fdry connection show` | `--name <CONNECTION>` | — | Read a connection without requesting credentials. |
| `fdry connection create` | `--name <CONNECTION>`, `--file <PATH>` | — | Create/update a project connection through Azure management. Requires a `properties` object in the body. |
| `fdry connection delete` | `--name <CONNECTION>` | `--yes`, `-y` | Delete through Azure management. |
| `fdry toolbox list` | — | — | List toolboxes. |
| `fdry toolbox show` | `--name <TOOLBOX>` | `--version <VERSION>` | Read the toolbox or a specific version. |
| `fdry toolbox versions` | `--name <TOOLBOX>` | — | List versions. |
| `fdry toolbox create` | `--name <TOOLBOX>`, `--file <PATH>` | — | Create an immutable version; service assigns its version. Requires a `tools` array. |
| `fdry toolbox publish` | `--name <TOOLBOX>`, `--version <VERSION>` | — | Set the default version. |
| `fdry toolbox delete` | `--name <TOOLBOX>`, `--version <VERSION>` | `--yes`, `-y` | Delete one version. |
| `fdry toolbox delete-all` | `--name <TOOLBOX>` | `--yes`, `-y` | Delete the toolbox and all its versions. |

Keep the endpoint project and global management `--project` aligned when
reading and writing the same connection. Connections do not create the target
service or automatically assign access to it.

## Datasets and indexes

| Command | Required | Optional | Behavior |
|---------|----------|----------|----------|
| `fdry dataset list` | — | — | List datasets. |
| `fdry dataset show` | `--name <DATASET>`, `--version <VERSION>` | — | Read one version. |
| `fdry dataset versions` | `--name <DATASET>` | — | List versions. |
| `fdry dataset create` | `--name <DATASET>`, `--version <VERSION>`, `--file <PATH>` | — | Create/update a version from a request body. |
| `fdry dataset upload` | `--name <DATASET>`, `--version <VERSION>`, `--path <LOCAL_PATH>` | `--connection <STORAGE_CONNECTION>` | Upload an existing file or folder; the SDK selects storage if connection is omitted. |
| `fdry dataset delete` | `--name <DATASET>`, `--version <VERSION>` | `--yes`, `-y` | Delete one version; underlying storage behavior depends on the dataset. |
| `fdry index list` | — | — | List registered index references. |
| `fdry index show` | `--name <INDEX>`, `--version <VERSION>` | — | Read one reference version. |
| `fdry index versions` | `--name <INDEX>` | — | List reference versions. |
| `fdry index create` | `--name <INDEX>`, `--version <VERSION>`, `--file <PATH>` | — | Create/update an index reference version, not an Azure AI Search service or search index. |
| `fdry index delete` | `--name <INDEX>`, `--version <VERSION>` | `--yes`, `-y` | Delete the Foundry reference version, not the underlying search service. |

Dataset storage access requires suitable storage permissions. Use `--path` for
local upload content and `--file` for a JSON/YAML request object; they are not interchangeable.

## Evaluations

| Command | Required | Optional | Behavior |
|---------|----------|----------|----------|
| `fdry evaluation list` | — | — | List evaluation definitions. |
| `fdry evaluation show` | `--id <EVALUATION_ID>` | — | Read a definition. |
| `fdry evaluation create` | `--file <PATH>` | — | Create from `data_source_config` and `testing_criteria`; optional `name` and `metadata`. |
| `fdry evaluation delete` | `--id <EVALUATION_ID>` | `--yes`, `-y` | Delete a definition. |
| `fdry evaluation run create` | `--evaluation-id <EVALUATION_ID>`, `--file <PATH>` | — | Submit an asynchronous run; body requires `data_source`, optionally `name` and `metadata`. |
| `fdry evaluation run list` | `--evaluation-id <EVALUATION_ID>` | — | List runs for the definition. |
| `fdry evaluation run show` | `--evaluation-id <EVALUATION_ID>`, `--id <RUN_ID>` | — | Read a run and its status. |
| `fdry evaluation run cancel` | `--evaluation-id <EVALUATION_ID>`, `--id <RUN_ID>` | — | Request cancellation without a confirmation prompt. |

Use the evaluation ID returned by definition creation, and the run ID returned
by run creation. Creating a definition does not run an evaluation.
See [evaluation fields](request-bodies.md#evaluationjson) for the exact-match
example and the distinction between dataset items and generated samples.

## Fine-tuning and files

| Command | Required | Optional | Behavior |
|---------|----------|----------|----------|
| `fdry fine-tuning list` | — | — | List fine-tuning jobs. |
| `fdry fine-tuning show` | `--id <JOB_ID>` | — | Read a job and its status. |
| `fdry fine-tuning create` | `--file <PATH>` | — | Submit an asynchronous job; body requires `model` and `training_file`. |
| `fdry fine-tuning cancel` | `--id <JOB_ID>` | — | Request cancellation without a confirmation prompt. |
| `fdry file upload` | `--path <LOCAL_FILE>`, `--purpose <PURPOSE>` | — | Upload an existing file, not a directory. Purpose must be `fine-tune`, `evals`, or `assistants`. |
| `fdry file list` | — | — | List files visible through the project OpenAI client. |
| `fdry file show` | `--id <FILE_ID>` | — | Read file metadata, not content. |
| `fdry file delete` | `--id <FILE_ID>` | `--yes`, `-y` | Delete a file. |

Upload training data with purpose `fine-tune`, then place the returned file ID in
`training_file`. Model/method availability, data formats, file-size limits,
and training charges are service-defined. A successfully submitted job is not
a completed training job or a deployed model.

## Configuration, authentication, quota, and REST

| Command | Required | Optional | Behavior |
|---------|----------|----------|----------|
| `fdry config set` | Positional `KEY VALUE` | — | Save one of the five configuration keys in the selected profile. |
| `fdry config show` | — | — | Show effective settings and selected profile. |
| `fdry config list` | — | — | Show all saved profiles. |
| `fdry config unset` | Positional `KEY` | — | Remove a saved key; errors if it is not saved. |
| `fdry auth status` | — | — | Check token acquisition without exposing the token. |
| `fdry quota list` | — | — | Read account usage/quota information. |
| `fdry rest` | Positional `PATH` | `--method <METHOD>`, `--file <PATH>`, `--yes`, `-y` | Send a single project-relative request. |

REST methods are exactly `GET`, `POST`, `PUT`, `PATCH`, and `DELETE`; default `GET`.
`--file` is rejected for GET; for other methods it supplies a JSON request body.
DELETE prompts unless `--yes` is set. Paths must be project-relative, without a
leading slash, absolute URL, fragment, traversal, backslash, double encoding,
or control characters. Include the operation's required API version in the query.
This command does not paginate or configure service-specific preview headers.

```powershell
fdry rest "agents?api-version=v1"
fdry rest "<RELATIVE_API_PATH>?api-version=<API_VERSION>" --method POST --file "<BODY_FILE>"
```

## Output, errors, and safety

List commands consume SDK pagination. REST returns only one response.
Output follows SDK response shapes; common credential fields are redacted
recursively on a best-effort basis, not as a guarantee for arbitrary service data.
Inspect outputs before sharing them.

Successful commands exit `0`; service/configuration I/O failures normally exit `1`,
and missing settings, invalid input, or usage errors exit `2`. Confirmation
cancellation is nonzero. Azure and OpenAI SDK errors go to stderr.
Some invalid data is only rejected by the service; parsing a file successfully
does not validate all Azure schema constraints.

There is no dry-run, generic retry flag, output query language, automatic RBAC
assignment, or resource-group creation command. Resource provisioning and
inference/training operations can incur Azure charges. Private endpoints require
network access and working DNS from the machine running the CLI.
