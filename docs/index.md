---
title: fdry - Microsoft Foundry CLI
---

## Install

The Python package supports Python 3.10 or later, including 3.15, on Windows
and Linux. From a source checkout:

```powershell
python -m pip install .
fdry --help
fdry --version
```

The package is not published to PyPI yet. Windows x64 and Linux x64 standalone
builds bundle Python, so users of those builds do not need a Python installation.
Download binaries, Python wheel/source archives, and checksums from the
[v0.1.0 pre-release](https://github.com/georgeollis/fdry/releases/tag/v0.1.0).
Verify checksums/provenance before running downloaded files.
See [platform requirements and verification](releasing.md#consumer-verification).

## Configure a project

For local development, install Azure CLI separately and sign in:

```powershell
az login
fdry auth status
fdry config set endpoint "https://<ACCOUNT>.services.ai.azure.com/api/projects/<PROJECT>"
fdry agent list
fdry model list
```

Replace placeholders with your own values. Service/workload/managed identity
credentials are also supported through Azure Identity.
Authentication does not grant authorization; configure Azure RBAC separately.
Management operations also need subscription, resource-group, and account
settings. See [configuration](cli.md#configuration-and-environment).

## Use the CLI

```powershell
fdry model invoke --name "<DEPLOYMENT>" --input "Hello" --api responses
fdry model invoke --name "<DEPLOYMENT>" --input "Hello" --api chat
fdry --profile "<PROFILE>" -o table agent list
```

Global options precede the resource command. `--help` is available on every
command. JSON output is the default.

## Learn more

| Guide | What it covers |
|-------|----------------|
| [CLI reference](cli.md) | Every command, option, accepted CLI choice, default, and setting. |
| [Request bodies](request-bodies.md) | Every bundled YAML/JSON field, its meaning, and authoritative source schemas. |
| [Adding properties](request-bodies.md#adding-properties-to-a-request-file) | Extend a template, choose nesting/types, and distinguish schema-defined properties from free-form keys. |
| [Release readiness](releasing.md) | Platform support, verification, release gates, and unverified live behavior. |

Requests can create resources, modify data, and incur Azure charges.
There is no dry-run mode. Keep credentials and private prompts outside source
control, and review outputs before sharing them.

!!! note "Pre-release limitations"
    fdry is an open-source community CLI for Microsoft Foundry, not an official
    Microsoft product. The initial release remains alpha. Offline testing and
    build hardening do not establish live Azure compatibility; native binaries
    are unsigned. See [release readiness](releasing.md) for the assurance boundary.
