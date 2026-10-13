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

- `scripts/collector.py` (deterministic 3-tier CRA readiness evaluation engine)
- `scripts/collect.py` (legacy matrix collector)
- `action.yml` (GitHub composite action)
- The GitHub Actions workflows under `.github/workflows/`

The markdown files (`SKILL.md`, `references/`, `templates/`) are instructions and drop-in templates for an AI agent. Reports about incorrect CRA guidance are welcome as ordinary issues, not as security reports.

## Supported versions

| Version | Security updates until |
|---------|------------------------|
| 0.x (latest release) | 2031-09-30 or 12 months after 1.0 is released, whichever is later |

Security updates are free of charge for the full support period. End of support will be
announced in this file and in the release notes at least 12 months in advance.

## Build Process & How Fixes Are Delivered

Fixes ship as a new tagged release through an automated, hermetic build pipeline:

1. **Hardened Minimal Execution (CRA Annex I.1)**:
   - Automated testing and scanner execution align with zero-CVE, hardened container baselines (Chainguard / Wolfi).
2. **Dual Machine-Readable SBOMs (CRA Annex I.2.1 / R.1, R.2)**:
   - Every release generates both CycloneDX JSON and SPDX JSON SBOMs via Syft (`dist/*.cyclonedx.json` and `dist/*.spdx.json`).
3. **Vulnerability Screening Gates (CRA Annex I.2.2 / R.1)**:
   - Automated Grype vulnerability screening against current feeds fails builds on unmitigated medium/high CVEs.
   - Continuous scheduled OSV-Scanner checks against lockfiles (`uv.lock`).
4. **Cryptographic Supply-Chain Ledger (Packablock)**:
   - Every release updates and cryptographically verifies the immutable supply-chain ledger (`packablock.yaml`), recording dependency lockfile snapshots.
5. **Signed Build Provenance & Checksums (CRA Annex I.2.1 / D.4)**:
   - Sigstore keyless build-provenance attestations are generated via GitHub Artifact Attestations (`actions/attest-build-provenance`) for all release tarballs, SBOMs, and ledger assets.
   - Releases include SHA256 checksum manifests (`SHA256SUMS.txt`).
   - Verify any release asset with:
     ```bash
     gh attestation verify <asset-file> --repo aaronbronow/cra-readiness-skill
     ```

Published advisories appear at https://github.com/aaronbronow/cra-readiness-skill/security/advisories.
