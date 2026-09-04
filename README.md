# EU Cyber Resilience Act (CRA) Readiness Skill

> **An agent-agnostic AI skill and audit toolkit for startup founders to answer:**  
> *"Give me a score based on how ready my GitHub repo is to comply with the Cyber Resilience Act."*

Evaluates software repositories against the official **40-item CRA Manufacturer Compliance Matrix** (Regulation EU 2024/2847) and outputs a founder-level letter grade ($A, B, C, D$) with drop-in remediation templates.

---

## 🎯 The Founder Grading System

Startup founders need plain-English certainty: *Can we ship to EU customers without regulatory penalties, or what technical work is blocking us?*

| Grade | Status | Plain-English Meaning | Fast Remediation |
| :---: | :--- | :--- | :--- |
| **🟢 A** | **Ready for EU Launch** | Both automated CI/CD guardrails and required manufacturer governance/policies are established. | Maintain compliance records for 10 years. |
| **🟡 B** | **Need Automation Work** | Policies and disclosures exist (`SECURITY.md`, EOL, DoC), but automated CI/CD checks (SBOM generation, automated CVE screening) are missing. | Add `.github/workflows/cra-ci.yml` to generate CycloneDX SBOMs & scan dependencies. |
| **🟠 C** | **Need Automation & Policy Work** | Typical early-stage state: missing both technical CI/CD automation and essential regulatory declarations. | 1. Drop in `SECURITY.md` & `CRA.md`<br>2. Enable CI SBOM workflow. |
| **🔴 D** | **Incomplete Assessment & Gaps** | Needs both B and C, **and** the assessment could not be completed reliably due to lack of tool/repository permissions or insufficient project information. | Grant read access or complete the 4-question conversational interview. |

---

## ⚡ How to Use

### 1. With Any AI Agent (Agent-Agnostic)
This repository follows the open Agent Skill specification (`SKILL.md`). You can use it in:
- **Gemini CLI / Antigravity**: Point the agent to or install this directory.
- **Claude Code**: Add as an agent tool or skill directory.
- **Cursor / GitHub Copilot**: Reference `@SKILL.md` in chat:
  > *"Audit this repository for CRA readiness using the instructions in SKILL.md"*

### 2. Standalone Terminal CLI (Zero Dependencies)
If you prefer running a direct audit without sending repository context to an external LLM:

```bash
# Markdown report (default)
python3 scripts/collector.py /path/to/your/repo

# Structured JSON export (for CI/CD gates or downstream dashboards)
python3 scripts/collector.py /path/to/your/repo --format json
```

### 3. Zero-Tool Conversational Mode (Privacy-Preserving)
For users who do not want to grant tool/filesystem access, the skill includes a rapid 4-part interview covering:
1. Automated SBOM generation & dependency screening (B.6, R.1, R.2, A.2).
2. Vulnerability disclosure contact & Article 14 24h notification policy (R.12, A.3-A.6).
3. 5-year End-of-Life support commitment (R.5, A.8, A.9).
4. Module A Declaration of Conformity and technical file retention (B.1, B.2, R.7, R.10).

---

## 📦 Project Structure

```text
cra-readiness-skill/
├── SKILL.md                             # Universal AI agent skill instructions
├── README.md                            # Quickstart & user documentation
├── scripts/
│   └── collector.py                     # Zero-dependency Python inspection script
├── references/
│   ├── cra_matrix_40.json               # Authoritative 40-item CRA matrix database
│   └── scoring_guide.md                 # Detailed scoring rubric & lifecycle breakdown
└── templates/
    ├── SECURITY.md                      # CRA-compliant vulnerability disclosure policy
    ├── CRA.md                           # Manufacturer technical file & Module A DoC
    └── github-actions/
        └── cra-ci-sbom.yml              # Drop-in GitHub Action for CycloneDX SBOM + Trivy
```

---

## 🚀 Fast-Track: From Grade C to Grade A in 15 Minutes

1. **Add Vulnerability Disclosure**:
   Copy [`templates/SECURITY.md`](templates/SECURITY.md) to your repository root. Update `security@yourcompany.com`.
2. **Add Manufacturer Technical File**:
   Copy [`templates/CRA.md`](templates/CRA.md) to your repository root. Confirm product name and declared 5-year support period.
3. **Add SBOM & Vulnerability Automation**:
   Copy [`templates/github-actions/cra-ci-sbom.yml`](templates/github-actions/cra-ci-sbom.yml) to `.github/workflows/cra-ci.yml`.
4. **Re-run the audit**:
   Your repository will now satisfy the core requirements and achieve **Grade A** readiness for the EU market.

---

## ⚖️ Legal Disclaimer
*This skill and collector provide technical readiness indicators and gap analysis based on EU Regulation 2024/2847. It does not constitute formal legal counsel or official conformity certification by a notified body.*
