# CRA Collector Evaluation Report: Claude Fable 5.1 vs. Gemini 3.8 Flash

> **Automated Comparative Audit across Synthetic Archetypes & Real Repositories**

---

## 1. Executive Summary & Benchmark Scorecard

| Target Repository | Claude Grade | Gemini Grade | Claude Passed | Gemini Passed | Claude Latency | Gemini Latency | Agreement Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Empty Repository (Fixture)` | **D** | **D** | 1/40 | 0/40 | 72.4ms | 47.3ms | **97.5%** |
| `Minimal Code (Fixture)` | **D** | **C** | 1/40 | 3/40 | 72.0ms | 54.7ms | **90.0%** |
| `Automation-Heavy (Fixture)` | **D** | **C** | 9/40 | 11/40 | 71.8ms | 59.0ms | **80.0%** |
| `Policy-Heavy (Fixture)` | **D** | **B** | 10/40 | 18/40 | 69.7ms | 51.9ms | **65.0%** |
| `Fully Compliant (Fixture)` | **D** | **A** | 19/40 | 33/40 | 76.2ms | 50.9ms | **50.0%** |
| `cra-readiness-skill (Current Repo)` | **C** | **C** | 33/40 | 17/40 | 185.8ms | 55.9ms | **55.0%** |
| `sigstore/cosign (Sample Repo)` | **D** | **C** | 13/40 | 13/40 | 273.4ms | 53.6ms | **75.0%** |
| `cra-rewrite (Gemini Directory)` | **D** | **C** | 26/40 | 5/40 | 288.5ms | 58.9ms | **42.5%** |

- **Average Item-Level Agreement**: `69.4%` across all evaluated scenarios.
- **Latency Comparison**: Total Claude runtime: `1109.7ms` vs. Total Gemini runtime: `432.2ms` (**2.6x faster**).

---

## 2. Key Behavioral & Architectural Discoveries

### A. Grading Philosophies
1. **Claude Fable 5.1 (Letter-of-the-Law Gatekeeper)**:
   - Implements 19 statutory gates (`F1, B1, B2, B3, B9, D3, D4, R1, R2, R5, R6, R7, R8, R9, R11, R12, P2, P3, P8`).
   - **Strict gate rule**: If any single gate item is unmet or partial, the repository is capped at Grade C regardless of how many other items pass.
   - Does not compute grades directly in the collector script; relies on raw evidence generation for external scoring.

2. **Gemini 3.8 Flash (Founder Launch Thresholds)**:
   - Categorizes the 40 items into Automation (9 items) and Policy/Documentation (31 items).
   - **Threshold rule**: Grade A is achieved when both Automation and Policy scores are $\ge 75\%$. Grade B requires Policy $\ge 60\%$ with Automation $< 75\%$.
   - Standalone execution computes final founder grade immediately inside `scripts/collector.py`.

### B. Signal Detection Paradigms
1. **Regex & Content Searching (Claude)**:
   - Claude inspects text inside `README.md` and repository text files for legal and technical keywords (e.g., searching for keywords like `'security'` or `'contact'` to satisfy R12).
   - Allows partial credit and captures subtle manual processes.

2. **Discrete File Signal Matching (Gemini)**:
   - Gemini matches specific file paths defined in `references/cra_matrix_40.json` (e.g. `docs/sdl-audit.md`, `Dockerfile`, `.env.example`).
   - Exceptionally fast (<50ms) and predictable, but requires repositories to match expected file path conventions.

---

## 3. Detailed Item Divergence Analysis per Repository

### 📦 Empty Repository (Fixture)
- **Overall Assessment**: Claude **Grade D** vs. Gemini **Grade D** (97.5% agreement)

| Item ID | Title | Claude Status | Gemini Status | Claude Signal/Evidence | Gemini Signal/Evidence |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **B9** (`B.9`) | Unassessed item | `PARTIAL` | `UNASSESSED` | *None / file absent* | *None / signal not matched* |

### 📦 Minimal Code (Fixture)
- **Overall Assessment**: Claude **Grade D** vs. Gemini **Grade C** (90.0% agreement)

| Item ID | Title | Claude Status | Gemini Status | Claude Signal/Evidence | Gemini Signal/Evidence |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **B5** (`B.5`) | Third-party & open-source component policy | `UNKNOWN` | `PASS` | *None / file absent* | pyproject.toml |
| **B9** (`B.9`) | Default credential policy | `PARTIAL` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **R8** (`R.8`) | Affix the CE marking | `UNKNOWN` | `PASS` | *None / file absent* | README.md |
| **R11** (`R.11`) | User-facing documentation | `NOT_MET` | `PASS` | *None / file absent* | README.md |

### 📦 Automation-Heavy (Fixture)
- **Overall Assessment**: Claude **Grade D** vs. Gemini **Grade C** (80.0% agreement)

| Item ID | Title | Claude Status | Gemini Status | Claude Signal/Evidence | Gemini Signal/Evidence |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **F2** (`F.2`) | Evidence of conformity with the SDL | `MET` | `NEEDS_USER_INPUT` | *None / file absent* | *None / signal not matched* |
| **B6** (`B.6`) | EOL check for tools and dependencies | `UNKNOWN` | `PASS` | *None / file absent* | Automated dependency review/scanner active |
| **B9** (`B.9`) | Default credential policy | `PARTIAL` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **D2** (`D.2`) | Evidence of SDL compliance | `MET` | `NEEDS_USER_INPUT` | *None / file absent* | *None / signal not matched* |
| **D4** (`D.4`) | Secure software update mechanism | `UNKNOWN` | `PASS` | *None / file absent* | Automated release pipeline in CI |
| **R8** (`R.8`) | Affix the CE marking | `UNKNOWN` | `PASS` | *None / file absent* | README.md |
| **R11** (`R.11`) | User-facing documentation | `NOT_MET` | `PASS` | *None / file absent* | README.md |
| **P7** (`A.7`) | Automatic update for third-party vulnerabilities | `NOT_MET` | `PASS` | *None / file absent* | Automated dependency review/scanner active |

### 📦 Policy-Heavy (Fixture)
- **Overall Assessment**: Claude **Grade D** vs. Gemini **Grade B** (65.0% agreement)

| Item ID | Title | Claude Status | Gemini Status | Claude Signal/Evidence | Gemini Signal/Evidence |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **B1** (`B.1`) | Determine product classification | `UNKNOWN` | `PASS` | *None / file absent* | CRA.md (Module A / DoC record) |
| **B2** (`B.2`) | Identify the conformity assessment route | `UNKNOWN` | `PASS` | *None / file absent* | CRA.md (Module A / DoC record) |
| **B3** (`B.3`) | Product-specific cybersecurity risk assessment | `UNKNOWN` | `PASS` | *None / file absent* | docs/threat-model.md |
| **B9** (`B.9`) | Default credential policy | `PARTIAL` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **D5** (`D.5`) | Data minimisation | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **R5** (`R.5`) | Declare the product End-of-Life | `UNKNOWN` | `PASS` | *None / file absent* | CRA.md / SECURITY.md (EOL & free updates declared) |
| **R6** (`R.6`) | Complete the conformity assessment | `UNKNOWN` | `PASS` | *None / file absent* | CRA.md (Module A / DoC record) |
| **R8** (`R.8`) | Affix the CE marking | `UNKNOWN` | `PASS` | *None / file absent* | README.md |
| **R9** (`R.9`) | Compile the technical file | `PARTIAL` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **P3** (`A.3`) | 24-hour initial vulnerability report | `UNKNOWN` | `PASS` | *None / file absent* | SECURITY.md / CRA.md (Art. 14 protocol) |
| **P4** (`A.4`) | 72-hour technical report | `UNKNOWN` | `PASS` | *None / file absent* | SECURITY.md / CRA.md (Art. 14 protocol) |
| **P5** (`A.5`) | Final report within 14 days of remediation | `UNKNOWN` | `PASS` | *None / file absent* | SECURITY.md / CRA.md (Art. 14 protocol) |
| **P6** (`A.6`) | Severe incident reporting | `UNKNOWN` | `PASS` | *None / file absent* | SECURITY.md / CRA.md (Art. 14 protocol) |
| **P9** (`A.9`) | Advance notice of End-of-Life | `UNKNOWN` | `PASS` | *None / file absent* | CRA.md / SECURITY.md (EOL & free updates declared) |

### 📦 Fully Compliant (Fixture)
- **Overall Assessment**: Claude **Grade D** vs. Gemini **Grade A** (50.0% agreement)

| Item ID | Title | Claude Status | Gemini Status | Claude Signal/Evidence | Gemini Signal/Evidence |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **F3** (`F.3`) | SDL covers secure-by-design and secure-by-default | `NOT_MET` | `PASS` | *None / file absent* | docs/secure-by-design.md |
| **B1** (`B.1`) | Determine product classification | `UNKNOWN` | `PASS` | *None / file absent* | CRA.md (Module A / DoC record) |
| **B2** (`B.2`) | Identify the conformity assessment route | `UNKNOWN` | `PASS` | *None / file absent* | CRA.md (Module A / DoC record) |
| **B3** (`B.3`) | Product-specific cybersecurity risk assessment | `UNKNOWN` | `PASS` | *None / file absent* | docs/threat-model.md |
| **B5** (`B.5`) | Third-party & open-source component policy | `UNKNOWN` | `PASS` | *None / file absent* | pyproject.toml |
| **B6** (`B.6`) | EOL check for tools and dependencies | `UNKNOWN` | `PASS` | *None / file absent* | Automated dependency review/scanner active |
| **B7** (`B.7`) | Storage encryption feasibility | `UNKNOWN` | `PASS` | *None / file absent* | docs/encryption.md |
| **D2** (`D.2`) | Evidence of SDL compliance | `MET` | `NEEDS_USER_INPUT` | *None / file absent* | *None / signal not matched* |
| **D4** (`D.4`) | Secure software update mechanism | `UNKNOWN` | `PASS` | *None / file absent* | Automated release pipeline in CI |
| **R4** (`R.4`) | Outbound connections list | `PARTIAL` | `NEEDS_EXPLANATION` | *None / file absent* | *None / signal not matched* |
| **R5** (`R.5`) | Declare the product End-of-Life | `UNKNOWN` | `PASS` | *None / file absent* | CRA.md / SECURITY.md (EOL & free updates declared) |
| **R6** (`R.6`) | Complete the conformity assessment | `UNKNOWN` | `PASS` | *None / file absent* | CRA.md (Module A / DoC record) |
| **R8** (`R.8`) | Affix the CE marking | `UNKNOWN` | `PASS` | *None / file absent* | README.md |
| **R9** (`R.9`) | Compile the technical file | `PARTIAL` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **P3** (`A.3`) | 24-hour initial vulnerability report | `UNKNOWN` | `PASS` | *None / file absent* | SECURITY.md / CRA.md (Art. 14 protocol) |
| **P4** (`A.4`) | 72-hour technical report | `UNKNOWN` | `PASS` | *None / file absent* | SECURITY.md / CRA.md (Art. 14 protocol) |
| **P5** (`A.5`) | Final report within 14 days of remediation | `UNKNOWN` | `PASS` | *None / file absent* | SECURITY.md / CRA.md (Art. 14 protocol) |
| **P6** (`A.6`) | Severe incident reporting | `UNKNOWN` | `PASS` | *None / file absent* | SECURITY.md / CRA.md (Art. 14 protocol) |
| **P7** (`A.7`) | Automatic update for third-party vulnerabilities | `NOT_MET` | `PASS` | *None / file absent* | Automated dependency review/scanner active |
| **P9** (`A.9`) | Advance notice of End-of-Life | `UNKNOWN` | `PASS` | *None / file absent* | CRA.md / SECURITY.md (EOL & free updates declared) |

### 📦 cra-readiness-skill (Current Repo)
- **Overall Assessment**: Claude **Grade C** vs. Gemini **Grade C** (55.0% agreement)

| Item ID | Title | Claude Status | Gemini Status | Claude Signal/Evidence | Gemini Signal/Evidence |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **F2** (`F.2`) | Evidence of conformity with the SDL | `MET` | `NEEDS_USER_INPUT` | *None / file absent* | *None / signal not matched* |
| **F3** (`F.3`) | SDL covers secure-by-design and secure-by-default | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **F4** (`F.4`) | EU Authorised Representative (non-EU manufacturers) | `MET` | `NEEDS_USER_INPUT` | *None / file absent* | *None / signal not matched* |
| **B4** (`B.4`) | Threat modelling | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **B8** (`B.8`) | Minimal attack-surface design | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **B9** (`B.9`) | Default credential policy | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **D2** (`D.2`) | Evidence of SDL compliance | `MET` | `NEEDS_USER_INPUT` | *None / file absent* | *None / signal not matched* |
| **D5** (`D.5`) | Data minimisation | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **R7** (`R.7`) | Prepare the EU Declaration of Conformity | `PARTIAL` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **R8** (`R.8`) | Affix the CE marking | `UNKNOWN` | `PASS` | *None / file absent* | README.md |
| **R9** (`R.9`) | Compile the technical file | `PARTIAL` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **R10** (`R.10`) | 10-year retention plan | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **R12** (`R.12`) | Vulnerability disclosure contact published | `MET` | `NEEDS_EXPLANATION` | *None / file absent* | SECURITY.md |
| **P3** (`A.3`) | 24-hour initial vulnerability report | `MET` | `NEEDS_EXPLANATION` | *None / file absent* | SECURITY.md |
| **P4** (`A.4`) | 72-hour technical report | `MET` | `NEEDS_EXPLANATION` | *None / file absent* | SECURITY.md |
| **P5** (`A.5`) | Final report within 14 days of remediation | `MET` | `NEEDS_EXPLANATION` | *None / file absent* | SECURITY.md |
| **P6** (`A.6`) | Severe incident reporting | `MET` | `NEEDS_EXPLANATION` | *None / file absent* | SECURITY.md |
| **P10** (`A.10`) | Corrective measures for non-compliant products | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |

### 📦 sigstore/cosign (Sample Repo)
- **Overall Assessment**: Claude **Grade D** vs. Gemini **Grade C** (75.0% agreement)

| Item ID | Title | Claude Status | Gemini Status | Claude Signal/Evidence | Gemini Signal/Evidence |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **F1** (`F.1`) | Documented Security Development Lifecycle | `UNKNOWN` | `PASS` | *None / file absent* | CONTRIBUTING.md |
| **F2** (`F.2`) | Evidence of conformity with the SDL | `MET` | `NEEDS_USER_INPUT` | *None / file absent* | *None / signal not matched* |
| **B5** (`B.5`) | Third-party & open-source component policy | `UNKNOWN` | `PASS` | *None / file absent* | go.mod |
| **B9** (`B.9`) | Default credential policy | `PARTIAL` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **D2** (`D.2`) | Evidence of SDL compliance | `MET` | `NEEDS_USER_INPUT` | *None / file absent* | CHANGELOG.md |
| **R1** (`R.1`) | SBOM prepared and vulnerability-screened | `PARTIAL` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **R2** (`R.2`) | SBOM in machine-readable format | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **R3** (`R.3`) | Inbound connections list | `UNKNOWN` | `PASS` | *None / file absent* | README.md (connection/port descriptions) |
| **R8** (`R.8`) | Affix the CE marking | `UNKNOWN` | `PASS` | *None / file absent* | README.md |
| **R11** (`R.11`) | User-facing documentation | `NOT_MET` | `PASS` | *None / file absent* | README.md |

### 📦 cra-rewrite (Gemini Directory)
- **Overall Assessment**: Claude **Grade D** vs. Gemini **Grade C** (42.5% agreement)

| Item ID | Title | Claude Status | Gemini Status | Claude Signal/Evidence | Gemini Signal/Evidence |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **F1** (`F.1`) | Documented Security Development Lifecycle | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **F2** (`F.2`) | Evidence of conformity with the SDL | `MET` | `NEEDS_USER_INPUT` | *None / file absent* | *None / signal not matched* |
| **F3** (`F.3`) | SDL covers secure-by-design and secure-by-default | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **F4** (`F.4`) | EU Authorised Representative (non-EU manufacturers) | `MET` | `NEEDS_USER_INPUT` | *None / file absent* | *None / signal not matched* |
| **B6** (`B.6`) | EOL check for tools and dependencies | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **B8** (`B.8`) | Minimal attack-surface design | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **B9** (`B.9`) | Default credential policy | `PARTIAL` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **D2** (`D.2`) | Evidence of SDL compliance | `MET` | `NEEDS_USER_INPUT` | *None / file absent* | *None / signal not matched* |
| **D3** (`D.3`) | Penetration testing / vulnerability assessment | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **D4** (`D.4`) | Secure software update mechanism | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **D5** (`D.5`) | Data minimisation | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **R1** (`R.1`) | SBOM prepared and vulnerability-screened | `PARTIAL` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **R2** (`R.2`) | SBOM in machine-readable format | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **R5** (`R.5`) | Declare the product End-of-Life | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **R7** (`R.7`) | Prepare the EU Declaration of Conformity | `PARTIAL` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **R8** (`R.8`) | Affix the CE marking | `UNKNOWN` | `PASS` | *None / file absent* | README.md |
| **R9** (`R.9`) | Compile the technical file | `PARTIAL` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **R10** (`R.10`) | 10-year retention plan | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **R12** (`R.12`) | Vulnerability disclosure contact published | `PARTIAL` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **P2** (`A.2`) | Automated SBOM vulnerability monitoring | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **P7** (`A.7`) | Automatic update for third-party vulnerabilities | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **P8** (`A.8`) | Security updates free of charge | `PARTIAL` | `FAIL` | *None / file absent* | *None / signal not matched* |
| **P9** (`A.9`) | Advance notice of End-of-Life | `MET` | `FAIL` | *None / file absent* | *None / signal not matched* |

---

## 4. Synthesis & PR Review Recommendations

1. **Hybrid Collector Opportunity**:
   - Gemini's JSON data structure (`references/cra_matrix_40.json`) is far cleaner and more maintainable than hardcoding rules in Python.
   - However, combining Gemini's external JSON model with Claude's deeper content-inspecting heuristics creates a best-of-both-worlds collector that is both fast, declarative, and robust against unconventional file names.
2. **Grading Mode Selection**:
   - Keep Gemini's direct CLI grade output with the founder-friendly A/B/C/D letter grade, while supporting an optional `--strict-gates` flag to enforce Claude's letter-of-the-law statutory gate check.
3. **Remediation Value**:
   - Gemini's `templates/` (`CRA.md`, `SECURITY.md`, `cra-ci-sbom.yml`) are essential additions that bridge the gap from audit to actionable compliance.