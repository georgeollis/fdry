---
title: Overview
---

# Microsoft Foundry CLI documentation

`fdry` is an independent command-line interface for managing Microsoft Foundry
agents, model deployments, projects, and related resources. It uses the Microsoft
Foundry and Azure management SDKs, authenticates through Azure Identity, and
returns structured JSON, YAML, or table output.

Start with the [workflow examples](workflows.md) for complete tasks, use the
[CLI reference](cli.md) for command syntax, and consult the
[request-body reference](request-bodies.md) for SDK/API fields and serialization.
This is an independent project, not an official Microsoft product.

## Install

The Python package supports Python 3.10 or later, including 3.15, on Windows
and Linux. From a source checkout:

```powershell
python -m pip install .
fdry --help
fdry --version
```

The package is not published to PyPI. Windows x64 and Linux x64 standalone
builds bundle Python, so users of those builds do not need a Python installation.
Download binaries, Python wheel/source archives, and checksums from the
[v0.1.0 release](https://github.com/georgeollis/fdry/releases/tag/v0.1.0).
Verify checksums and build-provenance attestations before running downloaded files.
See [platform requirements and verification](releasing.md#consumer-verification).

## Configure a project

For local development, install Azure CLI separately and sign in:

```powershell
az login
fdry --profile "<PROFILE>" config set endpoint "https://<ACCOUNT>.services.ai.azure.com/api/projects/<PROJECT>"
fdry --profile "<PROFILE>" config show
fdry --profile "<PROFILE>" auth status
fdry --profile "<PROFILE>" -o table model list
```

Replace placeholders before running the commands. The final command verifies
project access and lists available model deployments. Use the same profile for
subsequent operations; environment variables can override saved settings.
Service-principal, workload-identity, and managed-identity credentials are also
supported. Azure RBAC and network access must be configured independently.
Management operations additionally require subscription, resource-group, and
account settings. See [configuration](cli.md#configuration-and-environment).

## Use the CLI

```powershell
fdry --profile "<PROFILE>" model invoke --name "<MODEL_DEPLOYMENT>" --input "Summarize this incident in one sentence: a deployment recovered after its capacity was increased." --api responses
fdry --profile "<PROFILE>" -o table agent list
```

Global options precede the resource command. `--help` is available on every
command. JSON output is the default. Use `--api chat` instead of `responses`
when required by the selected model deployment.

## Choose a workflow

| Guide | What it covers |
|-------|----------------|
| [Structured support triage](workflows.md#return-a-structured-support-classification) | Configure a response schema, pin an agent version, and parse the Responses API output safely. |
| [Research with web search](workflows.md#create-a-research-assistant-with-web-search) | Configure instructions and a web-search tool, then inspect a versioned invocation. |
| [Model deployment](workflows.md#deploy-a-model-with-an-explicit-upgrade-policy) | Select catalog model/version, SKU, capacity, and upgrade policy. |
| [Search index references](workflows.md#register-an-existing-search-index) | Register an existing search index with explicit field mappings. |
| [CLI reference](cli.md) | Every command, option, accepted CLI choice, default, and setting. |
| [Request bodies](request-bodies.md) | Every bundled YAML/JSON field, its meaning, and authoritative source schemas. |
| [Adding properties](request-bodies.md#adding-properties-to-a-request-file) | Extend a template, choose nesting/types, and distinguish schema-defined properties from free-form keys. |
| [Releases](releasing.md) | Supported platforms, builds, checksums, and provenance verification. |

Requests can create resources, modify data, and incur Azure charges.
There is no dry-run mode. Keep credentials and private prompts outside source
control, and review outputs before sharing them.
