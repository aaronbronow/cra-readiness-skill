# Founder Interview Guide for CRA Readiness

> **A non-technical, plain-English questionnaire for startup founders and engineering leads.**  
> *Used by AI agents to resolve items marked `NEEDS_USER_INPUT`, or when running in zero-tool conversational environments.*

---

## 🧭 How Agents Conduct the Interview

1. **Targeted Execution**: Only ask the questions that correspond to items marked **`NEEDS_USER_INPUT`** (or where no repository file could be found). Never force the founder to answer all 40 questions if the tool already verified them.
2. **Plain English**: Never quote EU regulation article numbers directly to a non-technical founder without first explaining the practical meaning.
3. **Record Evidence**: Convert each answer into formal checklist status:
   - **"Yes / In Place"** $\rightarrow$ `PASS` (record as founder attestation).
   - **"Planned within 30 days"** $\rightarrow$ `PARTIAL` (flag as immediate pre-launch action).
   - **"No / Unsure"** $\rightarrow$ `FAIL` (provide drop-in template to resolve).
   - **"Not Applicable"** $\rightarrow$ `N/A` (e.g. EU Authorised Representative if company is in EU).

---

## 📋 The 4 Founder Interview Modules

### Module 1: Corporate Governance & Legal Representation (Stage 1)
*Covers F.2, F.4*

1. **EU Representative (F.4)**:  
   - *"Is your company legally established inside the European Union?"*
     - **Yes**: Item F.4 is marked **`N/A`** (no representative required).
     - **No**: *"Have you appointed an EU Authorised Representative with a written mandate to represent your company before European authorities?"*
2. **Internal Process Evidence (F.2)**:  
   - *"Does your team follow a repeatable security process when building features (e.g., code reviews, test requirements) and keep records of completed checks?"*

---

### Module 2: Component & Dependency Screening (Stage 2)
*Covers B.5*

3. **Third-Party Library Approval (B.5)**:  
   - *"Before your developers add new open-source packages or third-party SDKs to the app, do you have a policy or checklist to check them for known vulnerabilities and licenses?"*

---

### Module 3: Development & Review Practices (Stage 3)
*Covers D.2*

4. **Branch Protection & Peer Review (D.2)**:  
   - *"Do you enforce peer code review and require automated CI checks to pass before merging code into your main/release branch?"*

---

### Module 4: Incident Response & Operational Commitments (Stage 5)
*Fallback interview if `CRA.md` and `SECURITY.md` are missing from the repository*

5. **24-Hour Zero-Day Escalation (A.3, A.6)**:  
   - *"If a critical vulnerability in your product is actively exploited in the wild, do you have an on-call protocol to notify authorities/CSIRTs within 24 hours?"*
6. **Support Period & Free Updates (R.5, A.8)**:  
   - *"Do you commit to providing free security patches to your users for at least 5 years (or the declared lifetime of the product)?"*
7. **Declaration of Conformity (B.1, B.2, R.7)**:  
   - *"Are you prepared to sign a standard EU Declaration of Conformity (Module A self-assessment) certifying that your product complies with cybersecurity essentials?"*

---

## ⚡ Fast Remediation Strategy

If the founder answers **"No"** or **"Unsure"** to any questions in Modules 1–4:
- Do not make them draft policies from scratch.
- Point them directly to the pre-built templates in `templates/`:
  - [`templates/CRA.md`](../templates/CRA.md) for Module A, EOL, and retention declarations.
  - [`templates/SECURITY.md`](../templates/SECURITY.md) for CVD contact and 24h notification protocols.
  - [`templates/github-actions/cra-ci-sbom.yml`](../templates/github-actions/cra-ci-sbom.yml) for automated SBOM and CI security checks.
