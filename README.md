# EU Cyber Resilience Act (CRA) Readiness Skill

Evaluates software repositories against the official **40-item CRA Manufacturer Compliance Matrix** (Regulation EU 2024/2847) using a **3-tier scan control architecture**, outputting a plain-English founder letter grade ($A, B, C, D$) with drop-in remediation templates.

> **An agent-agnostic AI skill and headless audit engine for startup founders and builders to answer:**  
> *"Give me a score based on how ready my GitHub repo is to comply with the Cyber Resilience Act."*

> 🔴 **LIVE WORKSHOP SESSION**: [👉 Click here to join the Interactive Claude Session](https://claude.ai) *(Presenter updates this URL on workshop day)*  
> *(No terminal or local code required. Works on mobile & desktop browser.)*

### How to use in Claude 

Paste this...
> please use this skill to walk me thru the CRA prompts https://github.com/aaronbronow/cra-readiness-skill

Click allow when Claude asks if it can pull the repo (aaronbronow/cra-readiness-skill)

That's it! Claude will evaluate the skill.md and start the walkthrough.

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

## 🎤 Presentation Quickstart (Workshop Day Checklist)

> **For Workshop Presenters & Hosts**: Follow these 4 steps on the day of the workshop to prepare your room, initialize the live Claude instance, and launch the hands-on session for both mobile attendees and CLI power users.

### Step 1: Pre-Workshop Room & Slides Setup
- [ ] **Display Pre-Meeting QR Code**: Put a slide on the projector with a QR code pointing directly to this GitHub repository (`https://github.com/aaronbronow/cra-readiness-skill`) so attendees can scan and bookmark it on their phones or laptops as they enter.
- [ ] **Presenter Reminder Slide**: Ensure your slide deck includes a visual reminder slide: *"SWITCH TO GITHUB REPO"* to transition from the deck into live demo mode.

### Step 2: Initialize the Claude Shared Session (10 mins before start)
- [ ] Open [Claude Web](https://claude.ai) in your browser.
- [ ] Start a new chat, copy the full contents of [`templates/workshop-mobile-copilot.md`](templates/workshop-mobile-copilot.md), and send it as the initial message.
- [ ] Claude will reply with the interactive Virtual Compliance Officer introduction.
- [ ] Click the **"Share"** button in the top-right corner of the Claude chat window to generate a public shared conversation URL (`https://claude.ai/share/...`).

### Step 3: Publish the Live Link & Push to GitHub (5 mins before start)
- [ ] Update the **Live Workshop Link** banner at the top of this README with your active URL:
  ```markdown
  > 🔴 **LIVE WORKSHOP SESSION**: [👉 Click here to join the Interactive Claude Session](https://claude.ai/share/YOUR_SESSION_ID)
  ```
- [ ] Commit and push to main:
  ```bash
  git commit -am "docs: update live workshop Claude session URL"
  git push
  ```

### Step 4: Kickoff & Participant Onboarding
- [ ] Switch your presentation screen from your slide deck to this GitHub repository page.
- [ ] Ask all attendees to **refresh the GitHub repository page** in their mobile or laptop browsers.
- [ ] Direct attendees to their preferred track:
  - **📱 Mobile / Browser Track (No terminal, private repos)**: Click the **Live Workshop Session** link above to launch their private 5-minute audit in Claude Web.
  - **💻 CLI / Local Agent Track**: Attendees with terminal setups or Claude Code can clone the skill directly:
    ```bash
    # Global Claude skills directory:
    git clone https://github.com/aaronbronow/cra-readiness-skill.git ~/.claude/skills/cra-readiness-skill
    # Or directly inside their project:
    git clone https://github.com/aaronbronow/cra-readiness-skill.git .skills/cra-readiness-skill
    ```

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
