# Multi-Agent Manual Testing Log & Evaluation Runbook

This document provides structured test scripts and scorecards for manually verifying `cra-readiness-skill` across target AI agent environments.

---

## 1. Test Matrix & Protocol

### Tested Prompts
* **Prompt 1 (Initial Audit)**:
  > *"Evaluate this repository against the EU Cyber Resilience Act (Regulation EU 2024/2847). Follow the instructions in SKILL.md."*
* **Prompt 2 (Remediation)**:
  > *"Remediate the missing compliance files and workflows for this repository according to the CRA readiness recommendations."*
* **Prompt 3 (Zero-Tool / Conversational)**:
  > *"I am a software founder without terminal or tool execution enabled. Walk me through a CRA readiness audit using the guided interview protocol."*

---

## 2. Evaluation Rubric (1–5 Scale)

| Metric | Description | Score (1-5) |
| :--- | :--- | :---: |
| **Discovery & Activation** | Did the agent automatically discover `SKILL.md` or invoke the collector without confusion? | |
| **Tier Execution Flow** | Did the agent follow Tier 1 (deterministic tool) $\to$ Tier 2 (semantic inspection) $\to$ Tier 3 (targeted user interview)? | |
| **Tool Accuracy** | Were bash commands executed cleanly with correct arguments and error handling? | |
| **Conversational Fallback** | When tools were unavailable, did the agent cleanly initiate the 4-module questionnaire? | |
| **Remediation Precision** | Did generated files (`CRA.md`, `SECURITY.md`, `.github/workflows/`) use standard templates without regressions? | |

---

## 3. Session Log Template

Copy this section for each manual evaluation session:

```markdown
### Session: [Agent Name] - [Fixture: repo-grade-A | B | C]
- **Date**: YYYY-MM-DD
- **Agent Environment / Version**: (e.g., Claude Code 0.2.x, Antigravity 2.x, Cursor 0.40)
- **Model**: (e.g., Claude 3.7 Sonnet, Gemini 2.5 Pro, GPT-4o)
- **Target Fixture**: `fixtures/repo-grade-X`

#### Observations
1. **Initial Audit Output**:
   - Reported Grade: [A / B / C / D]
   - Expected Grade: [A / B / C / D]
   - Matched Expected: [Yes / No]
2. **Tier Progression**:
   - Ran `scripts/collector.py`? [Yes / No]
   - Read `SECURITY.md` / `CRA.md` semantically? [Yes / No]
   - Asked user for `NEEDS_USER_INPUT` items? [Yes / No]
3. **Remediation**:
   - Files created / modified:
   - Re-test pass post-remediation? [Yes / No]

#### Rubric Scores:
- Discovery: _ / 5
- Tier Flow: _ / 5
- Tool Accuracy: _ / 5
- Remediation Precision: _ / 5
- **Notes / Feedback**:
```
