# CRA Readiness: acme-iot/thermostat-firmware

**Grade: C – Needs automation work and policy/document work**
Confidence: Medium · Assessed 2026-09-03 · Checklist version 2026.09

Your repository already has most of the day-to-day security hygiene a customer would expect:
dependency alerts, code scanning, a `SECURITY.md` with a contact, and tests on every pull
request. What is missing is the CRA paperwork (risk assessment, incident procedure, support
period, classification) and two automation pieces (an SBOM per release and signed releases).
Fixing the three items below and answering the two open questions would move you to B; the
remaining policy items are then mostly writing.

## At a glance

| | Count |
|---|---|
| Items met | 17 of 40 (2 not applicable) |
| Partially met | 8 |
| Not met | 9 |
| Could not check | 4 |

Automation & tooling: 4 met / 8 · Policy, design & documents: 13 met / 32

## Do these next

1. **Incident response procedure with the ENISA timeline (P3)** – from 11 September 2026 you
   must file an initial report within 24 hours when a vulnerability in your product is being
   actively exploited; there is no procedure in the repo and you answered "no".
   *What to do:* create `docs/security/incident-response.md` naming an on-call owner, the
   24h / 72h / 14-day steps, ENISA's single reporting platform and your national CSIRT, and a
   corrective-measures section. *Effort:* about 2 hours. *Track:* Policy/documents.

2. **SBOM generated and scanned on every release (R1, R2)** – the CRA requires a machine-readable
   list of every component, checked for known vulnerabilities before release. Your release
   workflow (`.github/workflows/release.yml`) builds firmware images but produces no SBOM.
   *What to do:* add `anchore/sbom-action` with `format: spdx-json` and `anchore/scan-action`
   with `fail-build: true` to `release.yml`; upload the SBOM as a release asset.
   *Effort:* 1–2 hours. *Track:* Automation.

3. **Declare the support period (R5, P8, P9)** – customers must be told, before buying, until
   when they will receive free security updates. `SECURITY.md` lists supported versions but no
   dates. *What to do:* add a "Support period" section: "Firmware 2.x receives free security
   updates until 2031-09-30. End of support will be announced at least 12 months in advance."
   Check the date against your MCU vendor's SDK end-of-life (B6). *Effort:* 1 hour.
   *Track:* Policy/documents.

## Deadlines that matter

- 11 September 2026: vulnerability and incident reporting duties (Art. 14) apply. Your
  monitoring (P2) is in place; your reporting procedure (P3) is not.
- 11 December 2027: full CRA application; CE marking required to sell in the EU. Conformity
  assessment, Declaration of Conformity, CE marking and technical file (R6–R9) are all not
  started. You indicated a possible Important Class I feature (network configuration), which
  may require a Notified Body; lead times of 4–10 months are common, so confirm classification
  this quarter.

## Full checklist

### Stage 1 · Company foundations
| ID | Item | Status | Evidence / reason |
|----|------|--------|-------------------|
| F1 | Documented SDL | Partial | `CONTRIBUTING.md` has a "Security review" paragraph; no phases or roles |
| F2 | Evidence of conformity with SDL | Partial | Required reviews (1) on `main`; no PR security checklist |
| F3 | SDL covers secure-by-design/default | Not met | No SDL section on defaults or attack surface |
| F4 | EU Authorised Representative | N/A | Company established in the EU (your answer) |

### Stage 2 · Before development
| ID | Item | Status | Evidence / reason |
|----|------|--------|-------------------|
| B1 | Product classification | Partial | Your answer: "Default, in our heads"; network-configuration feature suggests Important Class I. Confirm. |
| B2 | Conformity assessment route | Not met | Your answer: not decided |
| B3 | Risk assessment | Not met | No file found; your answer: none |
| B4 | Threat modelling | Partial | Your answer: done informally, not documented |
| B5 | Third-party component policy | Partial | `actions/dependency-review-action` in `ci.yml`; no written policy |
| B6 | EOL check for tools/dependencies | Partial | `platformio.ini` pins libraries; base image `espressif/idf:latest` in `Dockerfile`; no EOL tooling |
| B7 | Storage encryption feasibility | Met | Your answer: NVS encryption enabled (not verified) |
| B8 | Minimal attack-surface design | Partial | `docs/hardening.md` present; `Dockerfile` exposes 3 ports incl. debug 8080 |
| B9 | Default credential policy | Met | No default credentials in config; `README.md` documents first-boot pairing |

### Stage 3 · During development
| ID | Item | Status | Evidence / reason |
|----|------|--------|-------------------|
| D1 | Cybersecurity test plan | Partial | `test/` with `test_auth_*.cpp`; no written plan |
| D2 | Evidence of SDL compliance | Met | Branch protection on `main`: 1 review, status checks; CI on `pull_request` (`ci.yml`) |
| D3 | Pen testing / vulnerability assessment | Partial | CodeQL default setup: configured; secret scanning: enabled; no pentest in last 12 months (your answer) |
| D4 | Secure update mechanism | Partial | `sha256sums.txt` on release v2.3.1; no signatures or provenance; OTA verification not documented |
| D5 | Data minimisation | Met | `docs/privacy.md`: telemetry opt-in, data inventory |

### Stage 4 · Before release
| ID | Item | Status | Evidence / reason |
|----|------|--------|-------------------|
| R1 | SBOM prepared and screened | Not met | No SBOM job in `release.yml`; Dependabot alerts enabled but no release gate |
| R2 | SBOM machine-readable | Not met | Follows R1 |
| R3 | Inbound connections list | Partial | Ports visible in `Dockerfile`; not documented with justification |
| R4 | Outbound connections list | Partial | `docs/privacy.md` covers telemetry endpoint only |
| R5 | Declare EOL | Partial | `SECURITY.md` supported-versions table; no dates |
| R6 | Conformity assessment completed | Not met | Your answer: not started |
| R7 | EU Declaration of Conformity | Not met | Your answer: not started |
| R8 | CE marking | Not met | Your answer: not planned yet |
| R9 | Technical file | Not met | Your answer: not started |
| R10 | 10-year retention | Could not check | No retention doc; question skipped |
| R11 | User-facing documentation | Partial | `README.md`/docs cover intended use, security properties, secure configuration, vulnerability reporting; missing support period |
| R12 | Vulnerability disclosure contact | Met | `SECURITY.md` (security@acme-iot.example, 3-business-day acknowledgement); private vulnerability reporting: enabled |

### Stage 5 · After release
| ID | Item | Status | Evidence / reason |
|----|------|--------|-------------------|
| P1 | Update risk assessment on change | Not met | Follows B3 |
| P2 | Automated SBOM vuln monitoring | Met | Dependabot alerts enabled; `.github/dependabot.yml` (weekly) |
| P3 | 24h initial report | Not met | No incident procedure; your answer: none |
| P4 | 72h technical report | Not met | Follows P3 |
| P5 | Final report 14 days | Not met | Follows P3 |
| P6 | Severe incident reporting | Not met | Follows P3 |
| P7 | Automatic update for 3rd-party vulns | Met | Dependabot security updates enabled; `release.yml` triggers on tag |
| P8 | Security updates free of charge | Could not check | No statement in support docs; question skipped |
| P9 | Advance notice of EOL | Could not check | No statement in support docs; question skipped |
| P10 | Corrective measures | Could not check | No procedure; question skipped |

## What this assessment could not check

- 10-year retention (R10): no document found and question skipped. Answer Q2.7 or add a
  retention statement to `docs/compliance/`.
- Security updates free of charge (P8), advance EOL notice (P9): answer Q2.5 or add both
  sentences to the support section of `SECURITY.md`.
- Corrective measures (P10): answer Q2.6 or add a section to the incident procedure once it exists.

## Things a repository cannot show

The CRA is mostly about your company's process, not your code. Even an A here does not mean you
are compliant. Items that always need a human decision or a document outside the repo:
conformity assessment and Declaration of Conformity (R6, R7), CE marking (R8), product
classification (B1, B2), and whether your risk assessment actually reflects the product.
Consider a conversation with a compliance advisor or Notified Body before launch, especially
given the possible Important Class I feature.

## Notes and discrepancies

- Scoring rule 5 fired (policy gap: 9 policy items not met). Automation track has 4 gaps
  (B6, D3, D4, R1/R2), so clearing policy items alone would not reach B either.
- Your answer to Q1.4 ticked "manage or configure networks". If the thermostat only joins a
  Wi-Fi network as a client, this is probably not the Annex III category; if it configures
  other devices or the router, it may be. Worth a 15-minute check with the classification tool.
- `Dockerfile` port 8080 is labelled `# debug` and is exposed by default. This affects B8 and
  R3 and is a quick fix.

---
*This is an automated readiness check against the 40-item manufacturer compliance matrix at
cyberresilienceact.eu, based on Regulation (EU) 2024/2847. It is not legal advice and does not
confirm compliance. Checklist version 2026.09, rules last reviewed 2026-09-03.*
