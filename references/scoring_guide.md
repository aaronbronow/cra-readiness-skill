# CRA Manufacturer Scoring Guide for Startup Founders

This guide defines how the CRA Readiness Skill evaluates a GitHub repository against the **40-item EU Cyber Resilience Act (CRA) Manufacturer Compliance Matrix** (Regulation EU 2024/2847).

---

## 1. The 4-Tier Founder Grading System

Startup founders need binary clarity: *“Can we ship to EU customers without regulatory penalty, or what is blocking us?”*

| Grade | Status | Plain-English Founder Meaning | What Is Present | What Is Missing |
| :---: | :--- | :--- | :--- | :--- |
| **A** | **Ready for EU Launch** | Your repository has the necessary policies, legal declarations, and automated CI/CD security checks to meet CRA manufacturer requirements. | Both Automation AND Policy/Documentation requirements are documented and satisfied. | Nothing critical. Routine maintenance required. |
| **B** | **Need Automation Work** | Your governance, policies, and disclosures are in place, but your codebase lacks automated CI/CD guardrails (SBOM generation, automated CVE monitoring, dependency screening). | Policies, disclosures, and risk documentation exist (`SECURITY.md`, DoC, EOL declaration). | Machine-readable SBOMs (CycloneDX/SPDX), CI security scans, or automated patching workflows. |
| **C** | **Need Automation Work & Policy/Document Work** | Typical early-stage state. You have code, but neither the required legal/policy artifacts nor automated compliance pipelines are configured. | Working application code or basic README. | Both technical automation (SBOMs, scanners) AND required regulatory documents (CVD contact, SDL, EOL, risk assessment). |
| **D** | **Incomplete Assessment & Gaps** | The assessment could not be completed reliably due to lack of repository tool permissions, private submodule barriers, or missing architectural details, AND both B and C are needed. | Unknown / partial signals. | Skill could not inspect files/CI, or critical information was withheld/inaccessible, requiring manual interview. |

---

## 2. Classification of the 40 Matrix Items

The 40 items across the 5 lifecycle stages are categorized into three core buckets:

### 1. Automation Items (Technical CI/CD & Pipeline)
These require automated scripts, GitHub Actions, or machine-readable outputs:
- **B.6**: EOL check for tools and dependencies (Dependabot/Renovate/Dependency Review)
- **B.8**: Minimal attack surface design (Container/infra least privilege)
- **D.1**: Cybersecurity-focused test plan (CI automated test suite)
- **D.3**: Penetration testing / SAST / DAST vulnerability screening (CodeQL/Semgrep/Snyk)
- **D.4**: Secure software update mechanism (Signed release pipeline/Goreleaser)
- **R.1**: SBOM prepared & vulnerability-screened
- **R.2**: Machine-readable SBOM (SPDX/CycloneDX JSON)
- **A.2**: Automated continuous SBOM vulnerability monitoring (OSV/NVD/EUVD sync)
- **A.7**: Automatic update mechanism for 3rd-party vulnerabilities

### 2. Policy & Documentation Items (Governance & Declarations)
These require written files, public notices, and signed declarations in the repository:
- **F.1 - F.3**: Documented Security Development Lifecycle (SDL) & secure-by-default design
- **F.4**: EU Authorised Representative designation (for non-EU startups selling into EU)
- **B.1 - B.2**: Product classification & conformity assessment route identification (Module A)
- **B.3 - B.4**: Product-specific cybersecurity risk assessment & threat model
- **B.5**: Third-party & open-source component selection policy
- **B.7**: Storage encryption feasibility document
- **B.9**: Default credential policy (zero default passwords)
- **D.2**: Evidence of SDL compliance in PRs/builds
- **D.5**: Data minimisation policy
- **R.3 - R.4**: Inbound & Outbound connection/port justifications
- **R.5 & A.9**: Declared End-of-Life (EOL) date (minimum 5-year support or expected lifetime)
- **R.6 - R.7**: Conformity assessment record & signed EU Declaration of Conformity (DoC)
- **R.8**: CE marking plan & placement
- **R.9 - R.10**: Annex VII Technical File compilation & 10-year retention policy
- **R.11**: User-facing security instructions
- **R.12**: Single vulnerability disclosure point of contact (`SECURITY.md`)
- **A.1**: Risk reassessment trigger on significant changes
- **A.3 - A.6**: Incident & 24h / 72h / 14-day vulnerability reporting procedure
- **A.8**: Commitment to free security updates during support period
- **A.10**: Corrective measures & recall protocol

### 3. Unassessed / Insufficient Info Flags (Triggers Grade D)
A grade **D** is assigned if:
1. Tool permissions were denied or unavailable to read `.github/workflows/`, repo root files, or manifests.
2. The user answers "Not applicable / Don't know" to fundamental classification questions.
3. The repo is empty, private and inaccessible, or lacks codebase context.

---

## 3. Fast Remediation Path for Startups (C -> B -> A)

```mermaid
graph LR
    D[Grade D: Incomplete Assessment] -->|Grant inspect tool or answer guided questions| C[Grade C: Need Policy & Automation]
    C -->|Drop in templates: SECURITY.md, CRA.md| B[Grade B: Need Automation]
    B -->|Activate GitHub Actions: SBOM + CodeQL + Dependabot| A[Grade A: Ready for EU Launch]
```

1. **Step 1 (Resolve Grade C Policies in 15 mins)**:
   - Copy `templates/SECURITY.md` to repository root (covers CVD, reporting contact, 24/72h notification).
   - Copy `templates/CRA.md` to repository root (covers classification, Module A DoC, EOL commitment, SDL summary).
2. **Step 2 (Resolve Grade B Automation in 10 mins)**:
   - Copy `templates/github-actions/cra-ci-sbom.yml` to `.github/workflows/cra-ci.yml`.
   - Enable Dependabot / Renovate for automated dependency security screening.
