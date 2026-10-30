# YAML and JSON request bodies

## Origin and scope

The six files in [`examples`](https://github.com/georgeollis/fdry/tree/main/examples) are AI-assisted, repository-authored
templates created for this CLI. They were not downloaded from Microsoft, exported
from an Azure environment, or supplied by the Foundry service. Their field names
follow the SDK/API shapes linked below. They are illustrative, not Microsoft
reference deployments or a promise that every combination works in every region.

This document covers **every field and literal in the six bundled templates**,
all CLI-generated provisioning fields, and the directly supported evaluation/
fine-tuning body parameters. Links to the authoritative service schemas cover
advanced fields and discriminated subtypes; `fdry` does not maintain a separate,
exhaustive copy of every Azure API schema.

The examples are covered by offline request/serialization checks, not a
successful live deployment of every template. Local parsing or SDK serialization
does not establish model, region, RBAC, network, or container compatibility.

## File format and validation

Every `--file` expects one JSON-compatible object, not an array or scalar.
Files are UTF-8. YAML uses a safe loader; object keys must be strings at every
level. Duplicate explicit keys are rejected instead of silently overwriting a
value, including inside nested objects. Standard YAML merge-key inheritance
can still be overridden by an explicit key.
JSON values
are strings, numbers, booleans, null, arrays, and objects. YAML-only values such
as timestamps and non-finite numbers are rejected if they cannot be serialized
as strict JSON. Quote CPU quantities and other fields whose schema requires strings.

There is **no** variable substitution, shell expansion inside files, secret
resolution, or automatic placeholder replacement.
`<MODEL_DEPLOYMENT>` and other angle-bracket strings are instructions to you,
not executable template syntax.
By contrast, `{{sample.output_text}}` and `{{item.expected}}` in the evaluation
example are actual evaluation-service expressions and should remain unchanged
unless you intentionally change the evaluation schema.

Keep the public templates unchanged and make an ignored local copy:

```powershell
Copy-Item examples\prompt-agent.yaml examples\prompt-agent.local.yaml
# Edit the local file and replace every placeholder before submitting it.
fdry agent create --name "<AGENT>" --file examples\prompt-agent.local.yaml
```

All commands use service wire keys. Agent/toolbox requests use keys such as
`container_configuration`; dataset/index requests use camelCase keys such as
`dataUri`, `connectionName`, and `indexName`. ARM requests use keys such as `authType` and
`allowProjectManagement`. Do not replace ARM wire keys with Python attribute names.
Account/project/model and connection management bodies are sent as JSON bytes,
preserving their wire names. The agent, toolbox, dataset, and index bodies go
directly to the corresponding Foundry SDK operation.

## Template index

| Template | Consumer | Prerequisites |
|----------|----------|---------------|
| [`prompt-agent.yaml`](https://github.com/georgeollis/fdry/blob/main/examples/prompt-agent.yaml) | `fdry agent create --name <AGENT> --file <PATH>` | Project endpoint and a compatible deployed model. |
| [`hosted-agent.yaml`](https://github.com/georgeollis/fdry/blob/main/examples/hosted-agent.yaml) | `fdry agent create --name <AGENT> --file <PATH>` | Project endpoint, compatible accessible image, hosted-agent support and permissions. |
| [`toolbox.yaml`](https://github.com/georgeollis/fdry/blob/main/examples/toolbox.yaml) | `fdry toolbox create --name <TOOLBOX> --file <PATH>` | Project endpoint and support for the selected tools. |
| [`connection.yaml`](https://github.com/georgeollis/fdry/blob/main/examples/connection.yaml) | `fdry connection create --name <CONNECTION> --file <PATH>` | Management settings, existing search service, appropriate permissions. |
| [`evaluation.json`](https://github.com/georgeollis/fdry/blob/main/examples/evaluation.json) | `fdry evaluation create --file <PATH>` | Project endpoint and evaluation API support. |
| [`fine-tuning.json`](https://github.com/georgeollis/fdry/blob/main/examples/fine-tuning.json) | `fdry fine-tuning create --file <PATH>` | Project endpoint, trainable model, uploaded training file and training permissions. |

The CLI resource name is supplied separately with `--name`; do not assume the
files name resources for you. Evaluation `name` is a display label; fine-tuning
`model` is a base-model identifier, not an agent name.

## Adding properties to a request file

The examples are starting points, **not an allowlist of every supported property**.
You can add fields documented by the request schema for your operation and
resource subtype. Most such additions need only a file edit, not a change to
`fdry`. An arbitrary new YAML key does not create a new service capability.

### Find the right schema first

1. Choose the command and its request-body schema using the table below.
2. Follow the source link in that template's field reference. Check the
   property's type, required fields, allowed values, nested object schema,
   mutually exclusive settings, and model/region restrictions.
3. Add the property at the documented nesting level in an ignored local copy.
   Preserve existing required fields. Use request wire names and the schema
   matching your SDK/API version, not names guessed from portal labels.
4. Review the complete body before submitting it. File bodies replace the
   convenience-generated body; they are not patches merged with CLI defaults.
   Read the created resource/version back and check the returned fields.

| File/operation | Where to add fields | Schema to consult |
|----------------|---------------------|-------------------|
| Prompt agent | Prompt settings under `definition`; individual tools under `definition.tools[]` | [Prompt fields](#prompt-agentyaml) and each tool's schema selected by `type`. |
| Hosted agent | Hosted settings under `definition`; image settings under `definition.container_configuration` | [Hosted fields](#hosted-agentyaml) and the container/protocol schemas. |
| Toolbox | Toolbox settings at the root; tool settings under `tools[]` | [Toolbox fields](#toolboxyaml) and the selected **toolbox-tool** subtype, not the similarly named agent-tool type. |
| Connection | ARM connection settings under `properties` | [Connection fields](#connectionyaml) and the subtype selected by `authType` and `category`. |
| Evaluation | Definition settings at the root; grader settings under `testing_criteria[]` | [Evaluation fields](#evaluationjson) and the grader/data-source subtype. Run bodies use a separate schema. |
| Fine-tuning | Job settings at the root; method settings under `method` | [Fine-tuning fields](#fine-tuningjson) and the chosen training method. |
| Account/project/model creation | ARM fields such as `location`, `identity`, `sku`, and `properties`, as applicable | [Provisioning schemas](#account-project-and-model-provisioning) for that resource, not a data-plane response. |
| Dataset/index creation | Version fields at the root and subtype-specific nested objects | [Dataset/index schemas](#dataset-and-index-bodies), selected by `type`. |

Microsoft Learn pages describe Python SDK attributes as well as schema concepts.
For ARM bodies, verify the wire spelling in the ARM request schema or SDK
serialization: for example, the Python attribute `auth_type` is the request
key `authType`, and `disable_local_auth` is `disableLocalAuth`.
Do not copy response-only IDs, creation timestamps, provisioning status, or
other read-only fields into a create request.

If current online documentation describes a newer SDK/API than your installation,
do not assume that property is available locally. Python users can inspect
installed dependencies with `python -m pip show azure-ai-projects azure-mgmt-cognitiveservices openai`.
The standalone executable bundles its own SDK versions; changing another Python
environment does not upgrade the executable.

### Example: add prompt sampling and a tool

Start with `prompt-agent.local.yaml` and extend it to:

```yaml
definition:
  kind: prompt
  model: <MODEL_DEPLOYMENT>
  instructions: You are a helpful assistant. Answer accurately and concisely.
  temperature: 0.2
  tools:
    - type: web_search
      search_context_size: low
```

`temperature` is a number under `definition`, not a quoted string or a root-level
property. `tools` is an array; `search_context_size` belongs to the web-search
tool object, not the agent definition. Its allowed values are `low`, `medium`,
and `high`. The chosen model must support both the sampling option and the tool;
remove unsupported settings rather than assuming every deployment accepts them.

The tool schema is [WebSearchTool](https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.models.websearchtool).
This is different from the `WebSearchToolboxTool` schema used in `toolbox.yaml`.
Defining a toolbox does not automatically attach its tools to an agent.

Submit the complete local file instead of combining it with convenience flags:

```powershell
fdry agent create --name "<AGENT>" --file examples\prompt-agent.local.yaml
fdry agent versions --name "<AGENT>"
fdry agent show --name "<AGENT>" --version "<RETURNED_VERSION>"
```

Creation makes a new immutable version, even if the agent already exists.
Use the returned version when reading back; do not assume it is `1`.

### Schema-defined properties versus free-form keys

Object fields are not all equally extensible:

| Object | Can you invent new keys? | Example |
|--------|--------------------------|---------|
| Agent `definition` or ARM `properties` | No; use documented schema properties. | `definition.temperature` is documented; a made-up `definition.creativity` is not a substitute. |
| Hosted `definition.environment_variables` | Yes, for variable names your container understands; values are strings. | `LOG_LEVEL: "INFO"` only affects an application that reads `LOG_LEVEL`. |
| Connection `properties.metadata` | User metadata is a string-to-string map; retain any provider-required entries. | Add a workload label without removing the example's `ApiType: Azure`. |
| Dataset/index `tags` or supported `metadata` maps | User-chosen string keys/values, subject to API limits. | A label identifies your workload; it does not change provisioning behavior. |
| Evaluation `item_schema.properties` | Yes, for dataset fields, using valid JSON Schema definitions. | Adding a column requires matching dataset items and updating grader/input expressions that reference it. |

For example, merge this **excerpt** into the existing hosted definition while
preserving its CPU, memory, image, and protocol settings:

```yaml
definition:
  environment_variables:
    LOG_LEVEL: "INFO"
```

This configures the hosted application, not `fdry` itself. It is not secret
resolution: `${SECRET}` would be sent literally. Never commit credentials in a
request body, metadata map, tag, or environment-variable map.

### Validation and when CLI changes are needed

An editor can check YAML/JSON syntax, but parsing does not prove a property's
schema, model compatibility, permissions, or service availability. `fdry` has
no schema-validation or dry-run command. **`create --file` submits a real
request** and can incur charges. Use an appropriately isolated Azure target
for integration testing.

If a request fails, check the exact field path and wire spelling, JSON type,
required sibling properties, discriminator (`kind`, `type`, or `authType`),
mutually exclusive settings, and SDK/API/model support. If a field is missing
from read-back output, do not assume it took effect: it could be read-only,
normalized, omitted from that response, or ignored. Confirm against the schema
and service behavior.

| Change | Edit the file only, or change the CLI? |
|--------|---------------------------------------|
| Add a documented property to an existing supported request subtype | Usually file only; SDK and service must both support it. |
| Add a service API field to an evaluation/run/fine-tuning body | Usually file only; the adapter forwards additional API fields as described [below](#advanced-fields-and-service-validation). Do not add a literal `extra_body` wrapper. |
| Add a new command-line flag, command, or saved configuration key | CLI code, help/reference updates, and focused tests are required. Adding YAML cannot register a flag or config key. |
| Use an agent kind other than `prompt` or `hosted` | CLI support is required: `agent create` currently rejects other kinds before contacting Azure. |
| Use a new API property absent from the bundled SDK, or change transport behavior | May require dependency/adapter changes and a new package/executable build; a file edit cannot upgrade the SDK or set SDK transport options. |

For contributors changing these boundaries, request parsing/forwarding lives in
[`core/documents.py`](https://github.com/georgeollis/fdry/blob/main/src/fdry/core/documents.py); operation-specific validation
and SDK calls live in [`commands`](https://github.com/georgeollis/fdry/tree/main/src/fdry/commands).
Keep example files, this field reference, and focused request-contract tests in
sync when introducing a newly supported request shape. Do not silently drop a
property or weaken validation merely to make an unsupported request pass.

## prompt-agent.yaml

| Field | Type / example value | Required and meaning |
|-------|----------------------|----------------------|
| `definition` | Object | Required by the CLI. Definition of the new agent version. |
| `definition.kind` | String: `prompt` | Required. Selects a prompt-based agent. CLI permits only `prompt` or `hosted` for agent files. |
| `definition.model` | String: `<MODEL_DEPLOYMENT>` | Required by the prompt schema. Replace with a deployment name from `fdry model list`, not a catalog model name or endpoint URL. |
| `definition.instructions` | String: `You are a helpful assistant. Answer accurately and concisely.` | Optional in the API; supplied in this template. A system/developer instruction, which you should customize. The convenience CLI form requires `--instructions`. |

Other prompt-definition fields are service-owned. Common optional fields include:

| Field under `definition` | Type / allowed values | Meaning |
|--------------------------|-----------------------|---------|
| `temperature` | Number, `0` to `2`; documented API default `1` | Sampling randomness, if the model supports it. |
| `top_p` | Number; documented API default `1` | Nucleus sampling. Usually change this or temperature, not both. |
| `tools` | Array of tool objects | Tools exposed to the model. Each tool's `type` selects its own schema. |
| `tool_choice` | String or tool-choice object | Tool selection policy according to the selected API/model. |
| `reasoning` | Object | Model-specific reasoning configuration. |
| `text` | Object | Plain-text or structured response configuration. |
| `skills` | Array of skill references | Foundry skill references; an omitted skill version is resolved by the service. |
| `harness` | Object | Managed runtime/agent-loop selection, where supported. |
| `rai_config` | Object | Responsible AI/content safety configuration. |
| `structured_inputs` | Object mapping names to input definitions | Inputs for prompt substitution or tool argument bindings. |

These are not additional `agent create` flags: put them in the body and check
the nested schemas and model support before use.

Source: [PromptAgentDefinition](https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.models.promptagentdefinition).

## hosted-agent.yaml

| Field | Type / example value | Required and meaning |
|-------|----------------------|----------------------|
| `definition` | Object | Required agent-version definition. |
| `definition.kind` | String: `hosted` | Required. Selects an agent running hosted code. |
| `definition.cpu` | String: `"1"` | Required by the schema. Requested CPU quantity; the service determines supported allocations. This is not a universal default. |
| `definition.memory` | String: `2Gi` | Required by the schema. Requested memory quantity; `Gi` denotes gibibytes. Supported CPU/memory pairs are service-defined. |
| `definition.container_configuration` | Object | Image-based deployment configuration. The service requires exactly one of this or `code_configuration`. |
| `definition.container_configuration.image` | String: `<REGISTRY_HOST>/<IMAGE>:<TAG>` | Container image reference. Replace registry host, image/repository path, and tag with an existing compatible image. Its pull access must be configured separately. |
| `definition.protocol_versions` | Array of objects | Optional ingress protocol declarations; align with the container implementation. |
| `definition.protocol_versions[].protocol` | String: `responses` | Required per protocol entry. SDK-known protocols: `activity`, `responses`, `a2a`, `mcp`, `invocations`, `voice`, `invocations_ws`. Service support varies. |
| `definition.protocol_versions[].version` | String: `v1` | Required per entry. This is an illustrative protocol version, not the CLI version or REST API version. Use the actual version supported by the container and Foundry. |

Other optional hosted-definition fields include `environment_variables`
(string-to-string object), `code_configuration` (code deployment alternative),
`rai_config`, `telemetry_config`, and `session_configuration` (nested objects).
Do not put secrets directly in committed environment-variable values.
Creating the definition does not build/push an image, provision its registry,
grant pull access, or prove that the hosted container is ready.

Sources: [HostedAgentDefinition](https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.models.hostedagentdefinition),
[ContainerConfiguration](https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.models.containerconfiguration),
[ProtocolVersionRecord](https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.models.protocolversionrecord).

## toolbox.yaml

| Field | Type / example value | Required and meaning |
|-------|----------------------|----------------------|
| `description` | String: `A toolbox with web search.` | Optional human-readable description. Customize it. |
| `tools` | Array | Required by the CLI; each item is a toolbox-tool object. |
| `tools[].type` | String: `web_search` | Required discriminator for this web-search tool. Other tool types have different schemas; do not change only the type and assume the rest is valid. |
| `tools[].name` | String: `web` | Optional user-defined tool/configuration name. It is not an Azure resource name, agent name, or toolbox name. |

For this toolbox web-search tool, optional `external_web_access` is boolean
(documented default `true`); `false` requests cache-only search.
`search_context_size` accepts `low`, `medium`, or `high` (default `medium`).
`filters`, `user_location`, and `custom_search_configuration` are nested objects.
`description` and `tool_configs` can configure the toolbox tool; `tool_configs`
maps tool names or `*` to tool configurations. These are toolbox-tool fields,
which are not identical to all prompt-agent tool schemas.

The version body can also carry `metadata` (string-to-string object), `skills`
(array), and `policies` (object) according to the SDK schema.
The service assigns the new version. Use `fdry toolbox versions` to find it and
`fdry toolbox publish --name <TOOLBOX> --version <VERSION>` to make it default.

Sources: [WebSearchToolboxTool](https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.models.websearchtoolboxtool),
[ToolboxTool types](https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.models.toolboxtool),
[Toolboxes operations](https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.operations.toolboxesoperations).

## connection.yaml

This is an **ARM project-connection body**, not a data-plane connection response.

| Field | Type / example value | Required and meaning |
|-------|----------------------|----------------------|
| `properties` | Object | Required by the CLI. Connection configuration. |
| `properties.authType` | String: `AAD` | Authentication discriminator: Microsoft Entra ID for this example. Retain the API's literal `AAD`; it is not a tenant ID. |
| `properties.category` | String: `CognitiveSearch` | Azure AI Search connection category. This is a fixed category literal, not a search service name. |
| `properties.target` | String: `https://<SEARCH_SERVICE>.search.windows.net` | Replace with the existing Azure AI Search endpoint. This does not create that service. |
| `properties.metadata` | String-to-string object | Optional connection metadata. |
| `properties.metadata.ApiType` | String: `Azure` | API-provider metadata used by this template. Keep its case; do not substitute a subscription ID or endpoint. |

Other auth-type discriminators known to the management SDK include `PAT`,
`ManagedIdentity`, `UsernamePassword`, `None`, `SAS`, `AccountKey`,
`ServicePrincipal`, `AccessKey`, `ApiKey`, `CustomKeys`, and `OAuth2`.
This is not a list of supported combinations for `CognitiveSearch`: each
authentication subtype/category has its own schema and service constraints.
The AAD subtype also exposes optional fields such as `isSharedToAll` (boolean),
`sharedUserList` (string array), `useWorkspaceManagedIdentity` (boolean), and
`peRequirement` (`Required`, `NotRequired`, or `NotApplicable`).
Use the ARM schema for their applicability and wire names.

Entra authentication does not grant authorization. Configure the relevant
identity's access to the search service separately. Prefer identity auth; if
another subtype requires credentials, keep its body in an ignored local file.

Source: [AADAuthTypeConnectionProperties](https://learn.microsoft.com/python/api/azure-mgmt-cognitiveservices/azure.mgmt.cognitiveservices.models.aadauthtypeconnectionproperties)
(Python attributes use snake_case; this file uses ARM wire names).

## evaluation.json

This file creates an evaluation **definition**, not a dataset, model deployment,
or evaluation run.

| Field | Type / example value | Required and meaning |
|-------|----------------------|----------------------|
| `name` | String: `exact-match` | Optional evaluation display name, not an Azure resource name. |
| `data_source_config` | Object | Required by the CLI/API. Describes the evaluation's data contract. |
| `data_source_config.type` | String: `custom` | Selects a custom item schema. |
| `data_source_config.item_schema` | JSON Schema object | Describes each input item. |
| `data_source_config.item_schema.type` | String: `object` | Each item must be an object. |
| `data_source_config.item_schema.properties` | Object | Defines the input fields `prompt` and `expected`. These are user-chosen dataset column names, not mandatory names for all evaluations. |
| `data_source_config.item_schema.properties.prompt` | Object: `{"type": "string"}` | Defines `prompt` as a string input. |
| `data_source_config.item_schema.properties.expected` | Object: `{"type": "string"}` | Defines `expected` as the expected answer string. |
| `data_source_config.item_schema.required` | String array: `["prompt", "expected"]` | Both fields must exist in each input item. |
| `data_source_config.include_sample_schema` | Boolean: `true` | Includes the sample schema used to access generated output. |
| `testing_criteria` | Array of grader objects | Required by the CLI/API. Defines how outputs are scored. |
| `testing_criteria[].type` | String: `string_check` | Selects the string-check grader schema. |
| `testing_criteria[].name` | String: `exact-match` | User-chosen grader label. |
| `testing_criteria[].input` | String: `{{sample.output_text}}` | Evaluation-service expression selecting generated output text. |
| `testing_criteria[].operation` | String: `eq` | Exact string equality. The string-check schema also defines `ne`, `like`, `ilike`; availability remains API-specific. |
| `testing_criteria[].reference` | String: `{{item.expected}}` | Evaluation-service expression selecting the expected answer from each item. |

Optional top-level `metadata` is a string-to-string object.
`prompt` is only declared by the definition; creating it does not automatically
run that prompt against a model. Submit a separate `evaluation run create`
body with the required `data_source` object and optional `name` and `metadata`.
The chosen data-source subtype determines where items and samples come from
and, for generation, the model/input-message configuration.
Use IDs returned by `evaluation create` and `evaluation run create` when
listing, inspecting, or cancelling runs.

Sources: [Foundry evaluation API guidance](https://learn.microsoft.com/azure/foundry-classic/openai/how-to/evaluations),
[OpenAI evaluation request types](https://github.com/openai/openai-python/blob/main/src/openai/types/eval_create_params.py),
[evaluation-run request types](https://github.com/openai/openai-python/blob/main/src/openai/types/evals/run_create_params.py).
The OpenAI SDK describes protocol shapes; Azure support can differ.

## fine-tuning.json

| Field | Type / example value | Required and meaning |
|-------|----------------------|----------------------|
| `model` | String: `<BASE_MODEL>` | Required. Replace with a fine-tuning-supported base-model identifier/version for the selected service, not an inference deployment name. |
| `training_file` | String: `<TRAINING_FILE_ID>` | Required. Replace with the ID returned by `fdry file upload --path <LOCAL_FILE> --purpose fine-tune`; not a local path. |

The CLI also directly forwards the following optional parameters:

| Field | Type | Meaning |
|-------|------|---------|
| `validation_file` | String file ID | Uploaded validation data for the chosen training method. |
| `hyperparameters` | Object | Training settings; supported keys and numeric/`auto` values depend on model/method. |
| `method` | Object | Training method and its method-specific configuration. Service/model support determines available methods. |
| `integrations` | Array of integration objects or null | External integration configuration, only where the service supports it. |
| `metadata` | String-to-string object or null | User metadata. Do not put credentials here. |
| `seed` | Integer or null | Training random seed, where supported. |
| `suffix` | String or null | Optional model-name suffix, subject to service constraints. |

Defaults, training-data format, dataset size, hyperparameter ranges, available
methods, regions, and charges come from the training service. `fdry` supplies
no defaults for omitted body fields and does not upload data implicitly.
Creating a job returns its initial state; poll with `fine-tuning show`.
It does not deploy the resulting fine-tuned model.

Sources: [Foundry fine-tuning guidance](https://learn.microsoft.com/azure/foundry/openai/how-to/fine-tuning),
[SDK job-create request](https://github.com/openai/openai-python/blob/main/src/openai/types/fine_tuning/job_create_params.py).

## Account, project, and model provisioning

These bodies are generated by convenience flags. When supplying `--file`,
you provide the full body instead; defaults are not merged into it.
Do not combine a file with the convenience options it replaces.
ARM operations use the subscription/resource-group/account from global settings;
the resource group must exist already.

### Account defaults

`fdry account create --location <REGION>` generates:

| Field | Type / generated value | Meaning |
|-------|------------------------|---------|
| `kind` | String: `AIServices` | Foundry-compatible account kind; CLI also requires this literal in file bodies. |
| `location` | String: `--location` value | Azure region identifier. |
| `sku` | Object | Account pricing tier. |
| `sku.name` | String: `S0` | Default account SKU. |
| `identity` | Object | Resource identity settings. |
| `identity.type` | String: `SystemAssigned` | Requests a system-assigned managed identity. |
| `properties` | Object | Account properties. |
| `properties.allowProjectManagement` | Boolean: `true` | Enables project management on the account. |
| `properties.customSubDomainName` | String: configured account name | Account custom subdomain; must satisfy Azure naming/uniqueness rules. |
| `properties.disableLocalAuth` | Boolean: `true` | Disables key-based authentication. |

Source: [Account model](https://learn.microsoft.com/python/api/azure-mgmt-cognitiveservices/azure.mgmt.cognitiveservices.models.account).
Advanced network settings and other ARM properties belong in a file.
Creating the identity does not assign RBAC roles.

### Project defaults

`fdry project create --name <PROJECT> --location <REGION>` generates:

| Field | Type / generated value | Meaning |
|-------|------------------------|---------|
| `location` | String: `--location` value | Parent account's Azure region. |
| `identity` | Object | Project identity settings. |
| `identity.type` | String: `SystemAssigned` | Requests a system-assigned identity. |
| `properties` | Object | Project properties. |
| `properties.displayName` | String: `--name` value | Human-readable project name. Resource name is also passed in the request URL. |

Source: [Project model](https://learn.microsoft.com/python/api/azure-mgmt-cognitiveservices/azure.mgmt.cognitiveservices.models.project).

### Model deployment defaults

`fdry model create --name <DEPLOYMENT> --model <CATALOG_MODEL> --model-version <MODEL_VERSION>`
generates:

| Field | Type / generated value | Meaning |
|-------|------------------------|---------|
| `sku` | Object | Deployment SKU settings. |
| `sku.name` | String: `--sku`, default `GlobalStandard` | Deployment type; available SKUs depend on model/region. |
| `sku.capacity` | Integer: `--capacity`, default `1`, minimum `1` | Allocated capacity in model/SKU-specific units. |
| `properties` | Object | Deployment properties. |
| `properties.model` | Object | Catalog model selection. |
| `properties.model.format` | String: `--format`, default `OpenAI` | Catalog/provider format. Not an output format. |
| `properties.model.name` | String: `--model` value | Catalog model name from `fdry model catalog`. |
| `properties.model.version` | String: `--model-version` value | Explicit catalog model version, not the deployment name. |

Source: [Deployment model](https://learn.microsoft.com/python/api/azure-mgmt-cognitiveservices/azure.mgmt.cognitiveservices.models.deployment).
The CLI does not enumerate every format or SKU or validate their compatibility.

## Dataset and index bodies

No dataset/index templates are bundled. These operations forward service wire
objects; consult the selected subtype rather than copying an SDK response with
read-only fields back into a create request.

For dataset references, `type` is `uri_file` or `uri_folder`; `dataUri` is the
existing data URI. `connectionName` identifies the storage connection and is
required by the schema when an upload has not already been initialized.
`isReference` is a boolean; when true the underlying data is retained on
dataset deletion. Optional `description` is a string and `tags` a string-to-string
object. Supply consistent resource names/versions using the CLI options.
For local content, prefer `dataset upload` rather than manually constructing
storage/upload state.

For an Azure AI Search index reference, `type` is `AzureSearch`,
`connectionName` names the project search connection, and `indexName` names
the existing search index. Optional `description`, `tags`, and `fieldMapping`
configure metadata and field mappings.
If present, `fieldMapping.contentFields` is a required string array;
`filepathField`, `titleField`, and `urlField` are optional string field names,
and `vectorFields` and `metadataFields` are optional arrays of field names.
This registers a reference; it does not create or populate the underlying index.

Sources: [DatasetVersion](https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.models.datasetversion),
[AzureAISearchIndex](https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.models.azureaisearchindex),
[FieldMapping](https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.models.fieldmapping).
Other index subtypes have their own schema.

## Advanced fields and service validation

Evaluation, evaluation-run, and fine-tuning bodies must contain the required
fields listed above. Recognized optional parameters are passed as SDK arguments;
additional API fields are passed through as `extra_body`. The CLI rejects
`extra_body`, `extra_headers`, `extra_query`, and `timeout` as top-level file
keys because they are SDK transport options, not service request fields.
There is no guarantee the service accepts additional fields.

Other `--file` commands perform only the documented structural checks before
forwarding the body. Unknown keys are not a supported extension mechanism:
the SDK/service can reject or ignore them. Use the schema matching your
installed SDK/API version, resource subtype, and region. Consult the current
schema for exhaustive nested field definitions rather than treating these
minimal examples as a complete service specification.
