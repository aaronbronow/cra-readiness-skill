# Security Policy

## Reporting a vulnerability

Please report vulnerabilities privately. Do not open a public issue.

- Preferred: GitHub private vulnerability reporting at
  https://github.com/aaronbronow/cra-readiness-skill/security/advisories/new
- Alternative: email abronow@gmail.com with "cra-readiness-skill security" in the subject.

Include what you found, how to reproduce it, and the impact you believe it has. You will
receive an acknowledgement within 3 business days and a status update at least every
14 days until the issue is resolved. We aim to publish a fix within 90 days of a confirmed
report and will credit you in the advisory unless you prefer otherwise.

## Scope

- `scripts/collect.py` (the only executable code in this repository)
- The GitHub Actions workflows under `.github/workflows/`

The markdown files (`SKILL.md`, `references/`) are instructions for an AI agent. Reports about
incorrect CRA guidance are welcome as ordinary issues, not as security reports.

## Supported versions

| Version | Security updates until |
|---------|------------------------|
| 0.x (latest release) | 2031-09-30 or 12 months after 1.0 is released, whichever is later |

Security updates are free of charge for the full support period. End of support will be
announced in this file and in the release notes at least 12 months in advance.

## How fixes are delivered

Fixes ship as a new tagged release. Each release includes a SPDX SBOM, SHA256 checksums and a
Sigstore build-provenance attestation; see "Verifying a release" in `README.md`. Published
advisories appear at https://github.com/aaronbronow/cra-readiness-skill/security/advisories.
