# Workflow examples

These workflows demonstrate common tasks using the existing `fdry` commands
and SDK/API request bodies. Each example separates local configuration from
service operations and includes a way to verify the result.

## Prerequisites

Install the [Python package or standalone executable](index.md#install).
Replace every `<PLACEHOLDER>` with a value from your environment before running
a command or submitting a file. Commands below use PowerShell.

| Requirement | When it is needed |
|-------------|-------------------|
| Microsoft Foundry project endpoint and an authenticated identity | Agent, model inference, and index operations. |
| A compatible model deployment | Agent creation and invocation. The deployment name differs from the catalog model identifier. |
| Subscription, existing resource group, and Foundry account | Model provisioning and management-plane operations. |
| Appropriate Azure RBAC roles and network access | Every service operation; acquiring a token does not grant access to resources. |
| Confirmed model/region support and quota | Provisioning, structured outputs, and optional tools. |

Creating resources and invoking models can incur charges. `--file` submits a
real request; it is not a validation-only or dry-run operation. Keep credentials
and private inputs outside source control.

## Configure a named profile

For interactive development, sign in with Azure CLI. Then save a profile for
the project you intend to use:

```powershell
az login
fdry --profile "<PROFILE>" config set endpoint "https://<ACCOUNT>.services.ai.azure.com/api/projects/<PROJECT>"
fdry --profile "<PROFILE>" config show
fdry --profile "<PROFILE>" auth status
fdry --profile "<PROFILE>" -o table model list
```

`config show` verifies effective settings; `auth status` checks token acquisition;
`model list` confirms project access and identifies available deployment names.
Use the same explicit `--profile` for subsequent operations.

For provisioning or connection management, also set the management context:

```powershell
fdry --profile "<PROFILE>" config set subscription "<SUBSCRIPTION_ID>"
fdry --profile "<PROFILE>" config set resource_group "<RESOURCE_GROUP>"
fdry --profile "<PROFILE>" config set account "<ACCOUNT>"
fdry --profile "<PROFILE>" config set project "<PROJECT>"
```

Profiles store non-secret settings, not credentials. Environment variables
override saved values, and global flags override both. A profile does not
isolate Azure credentials or neutralize environment overrides. Review
`config show` before changing resources. See the
[configuration reference](cli.md#configuration-and-environment).

## Return a structured support classification

Use a model that supports structured outputs. The
[`prompt-agent-structured.yaml`](https://github.com/georgeollis/fdry/blob/main/examples/prompt-agent-structured.yaml)
request defines a support-triage agent with four required response fields:
`category`, `priority`, `summary`, and `next_action`.

The SDK types are `PromptAgentDefinition`,
`PromptAgentDefinitionTextOptions`, and `TextResponseFormatJsonSchema`.
The JSON Schema belongs under `definition.text.format.schema`; it is not a
CLI output-format setting. See the [field reference](request-bodies.md#prompt-agent-structuredyaml).

Create a local copy and replace `definition.model` with a compatible deployment:

```powershell
Copy-Item examples\prompt-agent-structured.yaml examples\prompt-agent-structured.local.yaml
```

After editing the file, create a version and capture the returned version number:

```powershell
$ErrorActionPreference = "Stop"
$profile = "<PROFILE>"
$agent = "<AGENT>"

$createdJson = fdry --profile $profile -o json agent create --name $agent --file examples\prompt-agent-structured.local.yaml
if ($LASTEXITCODE -ne 0) { throw "Agent creation failed." }
$created = $createdJson | ConvertFrom-Json
$version = $created.version
if (-not $version) { throw "The service did not return an agent version." }

fdry --profile $profile agent show --name $agent --version $version
if ($LASTEXITCODE -ne 0) { throw "Agent version verification failed." }

$responseJson = fdry --profile $profile -o json agent invoke --name $agent --version $version --input "A user can sign in but receives an access-denied error when opening a project. No other users are affected."
if ($LASTEXITCODE -ne 0) { throw "Agent invocation failed." }
$response = $responseJson | ConvertFrom-Json
$texts = @(
    $response.output |
        Where-Object type -eq "message" |
        ForEach-Object { $_.content } |
        Where-Object type -eq "output_text" |
        ForEach-Object { $_.text }
)
if ($response.status -ne "completed" -or $texts.Count -ne 1) {
    throw "Expected one completed text response. Inspect the response for refusal, incomplete output, or tool calls."
}
$triage = $texts[0] | ConvertFrom-Json
$triage | Format-Table category, priority, summary, next_action
```

The CLI returns the full Responses API object. The script checks the native
exit status before parsing JSON, pins the created version, and extracts the
model's text separately from the response envelope.

An illustrative model response is:

```json
{
  "category": "access",
  "priority": "normal",
  "summary": "One user cannot open the project after signing in.",
  "next_action": "Verify the user's role assignment and scope for the project."
}
```

The schema controls the response shape, not factual accuracy or authorization.
Validate application-specific rules before taking action. Safety refusals or
incomplete responses may not contain the requested JSON object.

To revise the instructions or schema, edit the local file and call
`agent create` with the same name. Foundry creates a new immutable version;
update callers deliberately rather than assuming the previous version changed.

## Create a research assistant with web search

Use
[`prompt-agent-web-search.yaml`](https://github.com/georgeollis/fdry/blob/main/examples/prompt-agent-web-search.yaml)
with a deployment that supports the web-search tool. The request combines
instructions, `WebSearchTool`, a version description, and metadata.

```powershell
Copy-Item examples\prompt-agent-web-search.yaml examples\prompt-agent-web-search.local.yaml
```

Replace the model deployment placeholder, review the instructions, and submit
the complete body:

```powershell
fdry --profile "<PROFILE>" agent create --name "<AGENT>" --file examples\prompt-agent-web-search.local.yaml
fdry --profile "<PROFILE>" agent show --name "<AGENT>" --version "<RETURNED_VERSION>"
fdry --profile "<PROFILE>" agent invoke --name "<AGENT>" --version "<RETURNED_VERSION>" --input "Find the current Microsoft Foundry documentation for agent versioning. Summarize the relevant behavior and cite the source URLs."
```

Use the version returned by creation. Inspect the response's content and
citations before using the result. Web-search availability is model/service
dependent; instructions requesting citations do not guarantee correct sources.
The CLI does not execute application-owned tools or implement a generic tool loop.

The [request-body guide](request-bodies.md#example-configure-an-agent-with-web-search)
also shows how to serialize this body directly from the SDK.

## Deploy a model with an explicit upgrade policy

Model deployment requires management context, a supported model/version and
SKU, and sufficient quota. Review the catalog and account usage first:

```powershell
fdry --profile "<PROFILE>" model catalog --location "<REGION>"
fdry --profile "<PROFILE>" quota list
Copy-Item examples\model-deployment.json examples\model-deployment.local.json
```

Edit the local file with the selected catalog model, version, SKU, and capacity.
The example requests `NoAutoUpgrade`; choose the appropriate version-upgrade
policy for your workload before submission.

```powershell
fdry --profile "<PROFILE>" model create --name "<MODEL_DEPLOYMENT>" --file examples\model-deployment.local.json
fdry --profile "<PROFILE>" model show --name "<MODEL_DEPLOYMENT>"
fdry --profile "<PROFILE>" model invoke --name "<MODEL_DEPLOYMENT>" --api responses --input "Summarize this operational note in one sentence: a deployment is healthy after its capacity was increased."
```

Creation waits for the management operation. `model show` and invocation use the
project endpoint, so its account must match the management account. Use a model
supporting Responses, or select `--api chat` for a compatible chat deployment.

This workflow deploys a catalog model; it does not train weights.
`NoAutoUpgrade` does not extend a model's availability beyond retirement.
See [deployment fields and SDK serialization](request-bodies.md#model-deploymentjson).

## Register an existing search index

Use
[`search-index.yaml`](https://github.com/georgeollis/fdry/blob/main/examples/search-index.yaml)
to register a versioned reference to an existing Azure AI Search index.
Prerequisites are a project connection, a populated search index, and an
identity with the required search permissions.

```powershell
Copy-Item examples\search-index.yaml examples\search-index.local.yaml
```

Replace the connection, index, and field placeholders with existing values.
`contentFields`, `titleField`, and `urlField` identify fields in the search
index, not paths to local files.

```powershell
fdry --profile "<PROFILE>" connection show --name "<SEARCH_CONNECTION>"
fdry --profile "<PROFILE>" index create --name "<INDEX_REFERENCE>" --version "<INDEX_VERSION>" --file examples\search-index.local.yaml
fdry --profile "<PROFILE>" index show --name "<INDEX_REFERENCE>" --version "<INDEX_VERSION>"
```

The request uses `AzureAISearchIndex` and `FieldMapping`, serialized with
`connectionName`, `indexName`, and `fieldMapping` wire names.
Registration neither creates/populates the search index nor attaches a search
tool to an agent. Configure the relevant agent tool separately.
See [search index fields](request-bodies.md#search-indexyaml).

## Configuration checklist

The workflows above use existing command and request-body support; no runtime
code changes are required. Configure each layer explicitly:

| Layer | Configuration | Verification |
|-------|---------------|--------------|
| CLI context | Named profile, project endpoint, and management settings as needed. | `config show`; check for environment overrides. |
| Authentication | Azure Identity credential source: interactive Azure CLI, service principal, workload identity, or managed identity. | `auth status`, then a resource read to verify authorization. |
| Azure authorization and network | Appropriate RBAC assignments, project/account scope, and private-network connectivity where applicable. | Read the intended resource from the machine running the CLI. |
| Resource behavior | Complete SDK/API request body, compatible model/tool/schema, region, SKU, and quota. | Inspect the created resource and version, then run a controlled invocation. |
| Automation | Explicit profile/version, native exit-code handling, and response-status validation. | Fail on unsuccessful commands, incomplete responses, or invalid application output. |

For automation, supply non-secret settings through environment variables or
an explicit profile and obtain credentials through the deployment platform.
Do not copy interactive login credentials into a pipeline or save tokens in a
request body. [Azure Identity](https://learn.microsoft.com/python/api/azure-identity/azure.identity.defaultazurecredential)
owns credential resolution.

`--preview` opts in to SDK preview features; it does not make an unsupported
API available. Request files cannot configure SDK transport options, retries,
or CLI flags. Adding those capabilities would require a separate CLI change,
not additional YAML keys.
