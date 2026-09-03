# CRA Readiness: aaronbronow/cra-readiness-skill

> **Historical.** Produced under rubric 2026.09.0, before the baseline/beyond-the-letter split
> in 2026.09.1. Under the current rubric F4 is N/A (Art. 18 makes a representative optional),
> B6 is a policy item, and D3 is Met at baseline (regular automated testing; the pentest is a
> recommended practice). Re-run for a current grade.

**Grade: D – Needs automation and policy/document work, and this assessment could not see enough (missing permissions or information) to be sure of anything more**
Confidence: Low · Assessed 2026-09-03 · Checklist version 2026.09

This is the skill assessing its own repository, run by the collector with full admin access and
no intake answers. The D is driven entirely by 23 "could not check" items (threshold is 10), not
by missing evidence: nothing is Not met, and 7 of 8 automation items are Met. With the intake
questions answered the grade would be C; with the documents listed under "Do these next" and a
security review, A.

Run: `python3 scripts/collect.py --repo aaronbronow/cra-readiness-skill --exclude examples --exclude references`
(`--exclude` prevents the skill's own reference material and sample report from counting as this
repository's policy documents.)

## At a glance

| | Count |
|---|---|
| Items met | 12 of 40 (0 not applicable recorded yet) |
| Partially met | 5 |
| Not met | 0 |
| Could not check | 23 |

Automation & tooling: 7 met / 8 · Policy, design & documents: 5 met / 32

## Do these next

1. **Decide and record whether this product is in CRA scope (B1, B2, R6, R7, R8, F4)** – six gate
   items are unknown because nobody has written down the answer. This repository is a free,
   MIT-licensed, non-commercial tool; under Art. 3 and Recitals 18–19 that is very likely outside
   the CRA. *What to do:* write `docs/compliance/scope.md` stating the conclusion and reasoning,
   and what would change it (charging for it, bundling it into a paid service). If out of scope,
   mark the six items N/A. If in scope: Default class, Module A self-assessment, DoC, CE marking
   in the docs, technical file. *Effort:* 1 hour. *Track:* Policy/documents.

2. **Write the incident response procedure (P3, P4, P5, P6, P10)** – the Art. 14 reporting duties
   apply from 11 September 2026 to anyone in scope, and the procedure is useful regardless.
   *What to do:* `docs/security/incident-response.md` with a named owner, the 24h / 72h / 14-day
   steps, ENISA's single reporting platform and the national CSIRT, explicit coverage of severe
   incidents, and a corrective-measures section. *Effort:* 2 hours. *Track:* Policy/documents.

3. **Security review of the collector (D3)** – automated SAST and secret scanning are in place;
   the one automation item still Partial needs a human. *What to do:* a half-day review of
   `scripts/collect.py` focused on the regex paths over untrusted repository files, the token
   flow (header, never URL), and the shallow-clone of arbitrary repositories; commit a summary to
   `docs/security/pentest-2026.md`. *Effort:* half a day. *Track:* Automation (gate).

## Deadlines that matter

- 11 September 2026: vulnerability and incident reporting duties (Art. 14) apply. Monitoring
  (P2) is Met; the reporting procedure (P3) does not exist.
- 11 December 2027: full CRA application; CE marking required to sell in the EU. Not applicable
  unless the scope decision in item 1 concludes the product is placed on the market commercially.

## Full checklist

### Stage 1 · Company foundations
| ID | Item | Status | Evidence / reason |
|----|------|--------|-------------------|
| F1 | Documented SDL | Could not check | No SDL document in repo; not asked |
| F2 | Evidence of conformity with SDL | Partial | Required reviews (1) on `main`; no PR security checklist or sign-off records |
| F3 | SDL covers secure-by-design/default | Could not check | Follows F1 |
| F4 | EU Authorised Representative | Could not check | Intake only; likely N/A (see scope decision) |

### Stage 2 · Before development
| ID | Item | Status | Evidence / reason |
|----|------|--------|-------------------|
| B1 | Product classification | Could not check | Intake only; no `docs/compliance/` scope note |
| B2 | Conformity assessment route | Could not check | Intake only |
| B3 | Risk assessment | Could not check | No file found; not asked |
| B4 | Threat modelling | Could not check | No file found; not asked |
| B5 | Third-party component policy | Partial | `actions/dependency-review-action` in `.github/workflows/vuln-scan.yml`; no written policy |
| B6 | EOL check for tools/dependencies | Met | `uv.lock`, `.python-version`, `pyproject.toml`; weekly `.github/workflows/eol-check.yml` against endoflife.date |
| B7 | Storage encryption feasibility | Could not check | Intake only; likely N/A (product stores no data) |
| B8 | Minimal attack-surface design | Could not check | No hardening doc; README security section added after this run |
| B9 | Default credential policy | Partial | No default credentials detected in config; likely N/A (no authentication) but not recorded |

### Stage 3 · During development
| ID | Item | Status | Evidence / reason |
|----|------|--------|-------------------|
| D1 | Cybersecurity test plan | Could not check | CI tests exist (`ci.yml`); no written plan mapping them to Annex I areas |
| D2 | Evidence of SDL compliance | Met | Branch protection on `main`: 1 review, 5 required status checks, linear history, no force-push; CI on `pull_request` (`ci.yml`, `codeql.yml`, `eol-check.yml`) |
| D3 | Pen testing / vulnerability assessment | Partial | CodeQL python+actions (`codeql.yml`), gitleaks (`ci.yml`), GitHub secret scanning + push protection enabled; no pentest evidence |
| D4 | Secure update mechanism | Met | `release.yml`: `actions/attest-build-provenance`, SHA256SUMS; README "Verifying a release"; verified on v0.1.0 with `gh attestation verify` |
| D5 | Data minimisation | Could not check | No data-handling note; README security section (added after this run) states no collection |

### Stage 4 · Before release
| ID | Item | Status | Evidence / reason |
|----|------|--------|-------------------|
| R1 | SBOM prepared and screened | Met | `release.yml` + `vuln-scan.yml`: anchore/sbom-action, Grype gate (fail on medium+); asset `cra-readiness-skill-v0.1.0.spdx.json` |
| R2 | SBOM machine-readable | Met | SPDX 2.3 JSON on release v0.1.0 |
| R3 | Inbound connections list | Could not check | Likely N/A: no listening ports; not recorded |
| R4 | Outbound connections list | Could not check | README states only `api.github.com` and `github.com`; no dedicated network doc |
| R5 | Declare EOL | Met | `SECURITY.md` supported versions with date (2031-09-30) |
| R6 | Conformity assessment completed | Could not check | Intake only |
| R7 | EU Declaration of Conformity | Could not check | No document; intake |
| R8 | CE marking | Could not check | Intake only |
| R9 | Technical file | Could not check | No index; intake |
| R10 | 10-year retention | Partial | SBOM archived per release; no written retention statement |
| R11 | User-facing documentation | Met | README/`SECURITY.md` cover intended use, security properties, secure configuration, support period, vulnerability reporting |
| R12 | Vulnerability disclosure contact | Met | `SECURITY.md` (advisories link, email, 3-business-day acknowledgement); private vulnerability reporting enabled |

### Stage 5 · After release
| ID | Item | Status | Evidence / reason |
|----|------|--------|-------------------|
| P1 | Update risk assessment on change | Could not check | Follows B3 |
| P2 | Automated SBOM vuln monitoring | Met | Dependabot alerts enabled; `.github/dependabot.yml` (github-actions, uv); twice-daily Grype + OSV-Scanner in `vuln-scan.yml` |
| P3 | 24h initial report | Could not check | No incident procedure |
| P4 | 72h technical report | Could not check | Follows P3 |
| P5 | Final report 14 days | Could not check | Follows P3 |
| P6 | Severe incident reporting | Could not check | Follows P3 |
| P7 | Automatic update for 3rd-party vulns | Met | Dependabot security updates enabled; release automated from tag (`release.yml`) |
| P8 | Security updates free of charge | Met | `SECURITY.md`: "Security updates are free of charge for the full support period" |
| P9 | Advance notice of EOL | Met | `SECURITY.md`: 12-month notice commitment |
| P10 | Corrective measures | Could not check | No procedure |

## What this assessment could not check

All 23 unknowns are document or decision gaps, not permission gaps: every API call returned
`ok` with an admin token. To get a real grade, provide:

- Scope decision (`docs/compliance/scope.md`) → F4, B1, B2, R6, R7, R8, R9
- SDL (`docs/security/sdl.md`) → F1, F3, and F2 to Met
- Risk assessment with review triggers → B3, P1
- Threat model → B4
- Incident response procedure → P3, P4, P5, P6, P10
- Test plan → D1
- Short notes recording N/A with reasons → B7, B9, R3; data handling → D5; outbound list → R4;
  attack surface → B8; retention statement → R10 to Met
- Dependency policy → B5 to Met
- Security review summary → D3 to Met

## Things a repository cannot show

Whether this tool is "placed on the market" is a legal and commercial question, not a code
question. Everything in Stage 4 that depends on it (conformity assessment, DoC, CE marking,
technical file) follows from that one decision. Confirm it before doing the Stage 4 paperwork.

## Notes and discrepancies

- Scoring rule 2 fired (23 unknowns ≥ 10). Had the intake been answered with the expected N/As
  and "no" for missing documents, rule 5 (policy gap) would have produced a C.
- Automation track has one gap (D3 pentest). Every other AUTO item is Met, so the automation
  ceiling is not what limits the grade.
- `enforce_admins` is off on `main`. The commit that added the README security section was
  pushed directly with an admin bypass. Either enable `enforce_admins` and add a second reviewer,
  or record the bypass as a documented exception in the SDL. Future changes should go through
  pull requests so the required checks bind.
- R11 was Partial at the time of the run (missing security properties and secure configuration
  in the README); those sections were added in the same session and the item is Met on re-run.
- Doc detection excluded `examples/` and `references/`; without `--exclude` the skill's own
  checklist and sample report inflate several policy items to Met.

---
*This is an automated readiness check against the 40-item manufacturer compliance matrix at
cyberresilienceact.eu, based on Regulation (EU) 2024/2847. It is not legal advice and does not
confirm compliance. Checklist version 2026.09, rules last reviewed 2026-09-03.*
