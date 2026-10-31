# Security policy

## Reporting a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/georgeollis/fdry/security/advisories/new).
Do not publish exploit details, credentials, subscription/resource identifiers,
or private prompts and service responses in a public issue.
Include the affected version, platform, minimal sanitized reproduction, expected
impact, and any workaround. Do not probe someone else's Azure resources.

This is an independently maintained project, not a Microsoft support channel.
There is no guaranteed response or remediation SLA.

## Support and trust boundaries

Security fixes are developed on `main` and distributed through GitHub Releases.
Consumers should review dependency updates and avoid unsupported old snapshots.

The CLI authenticates through Azure Identity and uses Azure/OpenAI SDKs.
It does not grant RBAC permissions. Resource writes, inference, uploads, and
training can incur charges. `--file` supplies real API requests, not a sandboxed
declarative deployment or a dry run. Hosted-agent images are supplied by users
and require their own provenance and security review.

Profiles contain non-secret configuration only. Keep credential-bearing bodies,
environment files, and logs outside version control. Structured-output redaction
is best-effort and does not guarantee that arbitrary service responses or error
messages contain no sensitive information.

CI runs dependency audits and CodeQL; Dependabot proposes updates. Action
commits and dependency hashes are pinned for reviewable build inputs.

Tagged builds create provenance attestations and checksums. Native executables
are not Authenticode/code-signed. Download executables from GitHub Releases
and verify their checksums and provenance before running them.
