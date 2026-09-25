# EU Cyber Resilience Act (CRA) Readiness Skill

> **An agent-agnostic AI skill and headless audit engine for startup founders and builders to answer:**  
> *"Give me a score based on how ready my GitHub repo is to comply with the Cyber Resilience Act."*

Evaluates software repositories against the official **40-item CRA Manufacturer Compliance Matrix** (Regulation EU 2024/2847) using a **3-tier scan control architecture**, outputting a plain-English founder letter grade ($A, B, C, D$) with drop-in remediation templates.

---

## 🎯 The Founder Grading System

Startup founders need binary clarity: *Can we ship to EU customers without regulatory penalty, or what technical work is blocking us?*

| Grade | Status | What It Means for a Founder | Fast Remediation |
| :---: | :--- | :--- | :--- |
| **🟢 A** | **Ready for EU Launch** | Both automated CI/CD guardrails and manufacturer governance/policies are established ($\ge 75\%$ each). | Maintain technical documentation for 10 years. |
| **🟡 B** | **Need Automation Work** | Policies and legal declarations exist (`SECURITY.md`, `CRA.md`, EOL), but automated CI/CD checks (SBOM generation, automated CVE screening) are missing. | Add `.github/workflows/cra-ci.yml` to generate CycloneDX SBOMs & scan dependencies. |
| **🟠 C** | **Need Automation & Policy Work** | Typical early-stage state: missing both automated CI/CD checks and statutory compliance declarations. | 1. Drop in `templates/SECURITY.md` & `templates/CRA.md`<br>2. Enable CI SBOM workflow. |
| **🔴 D** | **Incomplete Assessment / Unassessed** | Repository path could not be accessed, tool permissions were denied, or the folder is completely empty. | Grant repository read access or run conversational interview mode. |

---

## 🏗️ The 3-Tier Scan Control Architecture

To ensure deterministic reliability in headless CI while providing deep contextual analysis in conversational agents, this skill partitions the 40 obligations across three distinct tiers:

1. **Tier 1: Deterministic Tool Engine (Headless / Zero-LLM)**:
   - Evaluates concrete files, workflows, lockfiles, and container configurations.
   - If a GitHub API token is present, verifies branch protection and secret scanning; if missing, degrades gracefully without failing.
   - Outputs clear statuses: `PASS`, `FAIL`, `NEEDS_EXPLANATION` (for candidate documents), and `NEEDS_USER_INPUT` (for organizational attestations).
2. **Tier 2: Agent Semantic Explanation (`NEEDS_EXPLANATION`)**:
   - For candidate documents (`SECURITY.md`, `CRA.md`, `docs/`), an AI agent reads the text and checks semantic adherence to statutory CRA requirements (e.g. 24h CSIRT notification, 5-year free updates, Module A self-assessment).
3. **Tier 3: Guided Founder Questionnaire (`NEEDS_USER_INPUT`)**:
   - For organizational items that cannot be proven by code alone (e.g. EU Authorised Representative, internal SDL conformity), the agent asks a short, targeted plain-English questionnaire.

---

## ⚡ How to Use

### 1. Reusable GitHub Action (Headless CI/CD)
Add the audit directly to your repository's workflow (`.github/workflows/cra-audit.yml`):

```yaml
name: CRA Readiness Audit
on: [push, pull_request]

jobs:
  cra-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: aaronbronow/cra-readiness-skill@v1
        with:
          format: 'markdown'
          fail-on-grade: 'D'
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```
*Outputs a formatted audit scorecard directly into your GitHub Action Step Summary.*

### 2. Standalone Terminal CLI (Zero Dependencies)
Run offline on any local directory with stock Python 3.8+:

```bash
# Markdown report (default)
python3 scripts/collector.py /path/to/repo

# Machine-readable JSON for CI/CD gates or dashboards
python3 scripts/collector.py /path/to/repo --format json

# Summary headline
python3 scripts/collector.py /path/to/repo --format summary
```

### 3. With Any AI Agent (Claude Code, Antigravity, Cursor, Copilot)
This repository follows the open [Agent Skill specification](https://agentskills.io) (`SKILL.md`):
- **Claude Code / Cursor**: Point to or install this skill directory and prompt:
  > *"Audit this repository for CRA readiness using the instructions in SKILL.md"*
- **Zero-Tool Sandbox (Desktop chat / Web sandbox)**: The agent conducts a rapid 4-part interview using [`references/interview_guide.md`](references/interview_guide.md) without requiring filesystem access.

---

## 🛠️ One-Click Remediation Templates

Move from **Grade C $\rightarrow$ B $\rightarrow$ A** in minutes using the pre-built templates in `templates/`:

1. **[`templates/CRA.md`](templates/CRA.md)**: Drop into repo root to provide the Annex VII technical file, product classification, 5-year EOL commitment, and Module A Declaration of Conformity.
2. **[`templates/SECURITY.md`](templates/SECURITY.md)**: Drop into repo root to document your vulnerability disclosure contact and Article 14 24h/72h reporting protocols.
3. **[`templates/github-actions/cra-ci-sbom.yml`](templates/github-actions/cra-ci-sbom.yml)**: Drop into `.github/workflows/cra-ci.yml` for automated CycloneDX SBOM generation, Trivy CVE screening, and artifact archiving.

---

## 📋 License

MIT License. Copyright (c) 2026 Aaron Bronow.
