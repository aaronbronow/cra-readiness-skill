# CRA Readiness Checklist (40 items) — rubric 2026.09.1

The 40 items follow the manufacturer compliance matrix at
https://www.cyberresilienceact.eu/compliance-matrix.html. Their legal content below has been
re-checked against the text of Regulation (EU) 2024/2847 (Articles and Annexes). Where the
matrix states more than the regulation does, this file says so.

## Two layers per item

Every item has two layers. Only the first one is scored.

1. **CRA baseline (scored).** What the regulation literally requires, with article/annex
   references. Status rules (MET / PARTIAL / NOT_MET) test *only* this layer. If the law can be
   satisfied by a documented manual process, a documented manual process is MET.
2. **Beyond the letter (reported, never scored).** Practices that make the baseline easier to
   evidence, harder to get wrong, or that a customer/auditor will expect. Each carries a source
   tag so founders know it is an industry convention, not a legal duty:
   `[Scorecard]` OpenSSF Scorecard · `[OSPS]` OpenSSF Open Source Project Security Baseline ·
   `[SSDF]` NIST SP 800-218 · `[SLSA]` SLSA framework · `[ETSI]` ETSI EN 303 645 ·
   `[GitHub]` platform feature · `[Matrix]` the source matrix's stricter reading · `[Practice]` common practice.

The report shows both: the grade from layer 1, and a separate "Beyond the letter" count and
suggestions from layer 2.

## Field definitions

- **Track** — nature of the *baseline* fix: `AUTO` (tooling, CI, repo settings, release pipeline)
  or `POLICY` (decisions, documents, product design, legal steps). Drives the B/C distinction.
- **Assess via** — `repo`, `intake`, or `repo+intake`.
- **Gate** — must be MET for an A. Only literal obligations are gates.
- Statuses: `MET`, `PARTIAL`, `NOT_MET`, `UNKNOWN`, `NA`. Absence in the repo is NOT_MET only for
  `repo` items; for `repo+intake` items absence with no answer is UNKNOWN.

Repo evidence must be cited (path, workflow, setting, release). Intake answers are labelled
"based on your answer, not verified".

---

## Stage 1 · Company-level foundations (F1–F4)

### F1 · Documented secure development process (SDL)
- CRA: Annex VII(2)(a),(c) (technical documentation must describe design, development and
  production processes and their monitoring/validation); Annex VIII Pt I(3); Art. 13(1).
- Track: POLICY · Assess via: repo+intake · Gate: yes
- Plain English: a written description of how the product is designed, built, produced and how
  vulnerabilities are handled. It is a required part of the technical file.
- **Baseline.** A written description of the design/development/production process and the
  vulnerability-handling process exists.
  MET = document(s) describing the development process and referencing vulnerability handling.
  PARTIAL = informal or fragmentary (a paragraph in CONTRIBUTING, no process description).
  NOT_MET = none, confirmed by founder.
- **Beyond the letter.** Named phases with roles and owners `[SSDF PO.2]`; alignment with
  IEC 62443-4-1 or ISO/IEC 27001 `[Matrix]` (note: only *harmonised* standards give a legal
  presumption of conformity under Art. 27; these do not, yet); security champion per team `[Practice]`.
- Evidence (repo): `docs/security/sdl.md`, `SECURITY.md`, `CONTRIBUTING.md`, `docs/development-process.md`.
- Fix (half a day): 2–3 pages: how features are designed, reviewed, tested, released, and how
  vulnerabilities are triaged and fixed. Commit under `docs/security/`.

### F2 · Evidence that the process is followed
- CRA: Annex VIII Pt I(3) (manufacturer takes all measures so processes ensure compliance);
  Annex VII(2)(c) (monitoring and validation of processes); Annex VII(6) (test reports); Art. 13(14).
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: records showing the process in F1 actually happens.
- **Baseline.** Some retained, recurring evidence exists (CI records, review records, release
  checklists, test reports).
  MET = at least one form of recurring evidence is retained. PARTIAL = evidence exists but is
  ad hoc or not retained. NOT_MET = none.
- **Beyond the letter.** Two independent forms of evidence `[Practice]`; PR template with a
  security checklist `[Practice]`; required reviews before merge `[Scorecard Code-Review]`.
- Evidence (repo): CI on pull requests, `.github/PULL_REQUEST_TEMPLATE.md`, `docs/security/reviews/`, branch protection.
- Fix (1 hour): make CI run on every pull request and keep release sign-off notes.

### F3 · Secure-by-design and secure-by-default are addressed
- CRA: Annex I Pt I(2)(b) (secure by default configuration, incl. reset to original state);
  Pt I(2)(j) (limit attack surfaces incl. external interfaces); Art. 13(3) (the risk assessment
  must state whether and how each Pt I(2) requirement applies and is implemented).
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: your risk assessment or design documentation explicitly covers "safe as shipped"
  and "nothing exposed that is not needed".
- **Baseline.** The risk assessment or SDL/design documentation addresses secure defaults and
  attack-surface limitation.
  MET = both addressed explicitly. PARTIAL = one, or mentioned only in passing. NOT_MET = neither.
- **Beyond the letter.** A default-configuration review step in every release `[Practice]`;
  hardening guide published `[ETSI 5.1, 5.6]`.
- Fix (1 hour): add a section to the risk assessment covering Pt I(2)(b) and (j).

### F4 · EU authorised representative
- CRA: Art. 18(1): "A manufacturer **may**, by a written mandate, appoint an authorised representative."
- Track: POLICY · Assess via: intake · Gate: no
- Plain English: an EU-based representative is **optional** under the CRA. The matrix presents it
  as mandatory for non-EU manufacturers; the regulation does not. (Other EU product laws differ.)
- **Baseline.** No obligation. Status is `NA` by default. If appointed, record `MET` for
  information; the mandate must at least cover Art. 18(3)(a)–(c) (keep DoC and technical file,
  provide information to authorities, cooperate).
- **Beyond the letter.** Non-EU manufacturers: appoint one `[Matrix]` — it simplifies keeping
  documents "at the disposal" of EU authorities and determines which CSIRT you report to under
  Art. 14(7)(a).
- Fix (days–weeks, optional): engage a representative service; sign a mandate; name them in the
  technical file and DoC (Annex V(2)).

---

## Stage 2 · Before development begins (B1–B9)

### B1 · Product classification
- CRA: Art. 7 and Annex III (important, Class I/II); Art. 8 and Annex IV (critical); Art. 32.
- Track: POLICY · Assess via: intake · Gate: yes
- Plain English: know whether your product is Default, Important (Class I or II) or Critical,
  because that decides whether you may self-assess.
- **Baseline.** The classification has been determined and recorded (it is needed to choose a
  lawful conformity assessment procedure under Art. 32).
  MET = classification stated and rationale recorded. PARTIAL = decided, not recorded.
  NOT_MET = not considered. If intake shows Annex III features and the founder says "Default",
  record PARTIAL with a warning.
- **Beyond the letter.** Written comparison against each Annex III/IV category `[Practice]`.
- Fix (1–2 hours): one-page classification note in `docs/compliance/`.

### B2 · Conformity assessment route
- CRA: Art. 32(1)–(3); Annex VIII. Default: Module A allowed. Important Class I: Module A only if
  harmonised standards/common specifications/certification at 'substantial' are fully applied,
  else B+C or H. Class II: B+C, H, or certification at 'substantial'. Critical: Art. 8.
- Track: POLICY · Assess via: intake · Gate: yes
- Plain English: pick the legally available procedure; anything above Default usually needs a
  Notified Body, with long lead times.
- **Baseline.** A route consistent with B1 has been chosen and recorded.
  MET = recorded. PARTIAL = chosen, not recorded. NOT_MET = not decided.
- **Beyond the letter.** Contact a Notified Body early even for Class I `[Practice]`.
- Fix (1 hour; months if a Notified Body is needed): `docs/compliance/conformity-route.md`.

### B3 · Cybersecurity risk assessment
- CRA: Art. 13(2)–(4): documented; based on intended purpose, reasonably foreseeable use and
  conditions of use; states whether and how each Annex I Pt I(2)(a)–(m) requirement applies and
  how it is implemented, and how Pt I(1) and Pt II are applied; justifies non-applicable
  requirements; included in the technical documentation (Annex VII(3)); updated during the support period.
- Track: POLICY · Assess via: repo+intake · Gate: yes
- Plain English: a written analysis of the product's security risks that walks through the
  thirteen Annex I requirements and says which apply and how you meet them.
- **Baseline.** MET = documented, covers intended purpose/foreseeable use/conditions of use, and
  maps to Annex I Pt I(2)(a)–(m) with applicability and implementation. PARTIAL = a risk document
  exists but lacks the Annex I mapping or the use-context analysis. NOT_MET = none.
- **Beyond the letter.** Likelihood/impact ratings `[Practice, ISO 27005]`; asset/threat/control
  table `[Practice]`; ratings reviewed per release `[Practice]`.
- Evidence (repo): `docs/security/risk-assessment*.md`, `docs/compliance/risk*`.
- Fix (1–2 days): a table with one row per Annex I Pt I(2) letter (applies? how implemented?
  justification if not), preceded by intended purpose, foreseeable use and operating environment.

### B4 · Threat analysis
- CRA: Art. 13(2)–(3) (analysis of cybersecurity risks). Threat modelling as a named method is
  **not** required by the regulation; it is how most teams produce the analysis.
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: the risk assessment should show you actually thought about how an attacker
  gets in, not just list requirements.
- **Baseline.** The risk assessment identifies the product's attack surface and threats.
  MET = threats and attack surface identified (in B3 or a separate document). PARTIAL = generic
  or incomplete. NOT_MET = none.
- **Beyond the letter.** A named methodology (STRIDE, PASTA, LINDDUN, attack trees) `[Matrix, SSDF PW.1]`;
  data-flow diagram with trust boundaries `[Practice]`.
- Evidence (repo): `THREAT_MODEL.md`, `docs/security/threat-model*`, threat section in the risk assessment.
- Fix (1 day): one STRIDE session on a data-flow diagram; write down the results.

### B5 · Third-party and open-source component due diligence
- CRA: Art. 13(5) (exercise due diligence when integrating third-party components, incl. free
  and open-source); Art. 13(6) (report vulnerabilities found in components to the maintainer and
  share fixes, where appropriate in machine-readable form); Art. 13(8) (component support periods
  inform the support period).
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: a written approach to choosing components and what you do when one turns out
  to be vulnerable, including telling the upstream maintainer.
- **Baseline.** MET = documented due-diligence approach covering selection and vulnerability
  response, including upstream reporting. PARTIAL = practice exists (e.g. an automated review
  gate) but is undocumented, or the document omits upstream reporting. NOT_MET = none.
- **Beyond the letter.** License allow-list `[OSPS]`; `dependency-review` gate on pull requests
  `[GitHub]`; minimum maintainer-activity criteria `[Scorecard Maintained]`.
- Evidence (repo): `docs/security/dependency-policy.md`, CONTRIBUTING sections, `dependency-review-action`.
- Fix (2 hours): one page: how components are chosen, who approves, how fast vulnerabilities are
  fixed, how upstream is informed.

### B6 · Component and runtime end-of-life is considered
- CRA: Art. 13(8) (support period must account for support periods of integrated third-party
  components providing core functions and availability of the operating environment);
  Annex VII(4) (information taken into account to determine the support period).
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: know when your runtimes and key libraries stop getting fixes, and record how
  that fed into your support period. Tooling is the easy way to know; the law wants the record.
- **Baseline.** MET = documented consideration of component/runtime EOL in the support-period
  reasoning, or an automated EOL check whose output is retained. PARTIAL = dependencies pinned but
  EOL never assessed/recorded. NOT_MET = none and founder confirms.
- **Beyond the letter.** Lockfiles committed `[Scorecard Pinned-Dependencies]`; runtime version
  pins; pinned base images (no `latest`) `[SLSA]`; scheduled EOL tooling (endoflife.date, xeol) `[Practice]`.
- Evidence (repo): support-period doc, lockfiles, `.python-version`/`.nvmrc`/`.tool-versions`, EOL workflow.
- Fix (1–2 hours): list runtime and top dependencies with their EOL dates in the support-period
  document; optionally add a weekly EOL check.

### B7 · Confidentiality of stored and transmitted data
- CRA: Annex I Pt I(2)(e): protect confidentiality of stored, transmitted or processed data,
  "such as by encrypting relevant data at rest or in transit by state of the art mechanisms".
  Applies "on the basis of the cybersecurity risk assessment and where applicable".
- Track: POLICY · Assess via: intake · Gate: no
- Plain English: sensitive data the product stores or sends must be protected; encryption is the
  expected means. The matrix calls encryption "mandatory"; the law makes it the named example of
  how to meet the confidentiality requirement, applied per your risk assessment.
- **Baseline.** MET = confidentiality of relevant data addressed in the risk assessment and
  implemented (encryption at rest/in transit or justified alternative). PARTIAL = implemented but
  not documented in the risk assessment. NOT_MET = sensitive data unprotected. NA = no data.
- **Beyond the letter.** Hardware-backed key storage `[ETSI 5.4]`; documented crypto inventory `[Practice]`.
- Fix (varies): document data classes and protection per class in the risk assessment.

### B8 · Minimal attack surface
- CRA: Annex I Pt I(2)(j) (limit attack surfaces incl. external interfaces); Pt I(2)(i)
  (minimise negative impact on other devices/networks).
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: unnecessary ports, services, debug endpoints and protocols are off.
- **Baseline.** MET = attack surface addressed in the risk assessment/design docs and reflected
  in shipped configuration. PARTIAL = one of the two. NOT_MET = debug/admin interfaces on by
  default with no justification.
- **Beyond the letter.** Every interface individually justified `[Matrix]`; hardening guide `[ETSI 5.6]`.
- Fix (half a day): list interfaces, disable the unneeded, record the list (feeds R3/R4).

### B9 · No universal default credentials
- CRA: Annex I Pt I(2)(b) (secure by default configuration); Pt I(2)(d) (protection from
  unauthorised access by appropriate control mechanisms). "No default passwords" is the
  established reading of secure-by-default (also ETSI EN 303 645 5.1-1, UK PSTI), not a literal phrase.
- Track: POLICY · Assess via: repo+intake · Gate: yes
- Plain English: no shared factory password. Either none, or the user must set one on first use.
- **Baseline.** MET = no universal default credentials shipped (or NA: product has no
  authentication). PARTIAL = defaults exist but a forced change on first use is enforced.
  NOT_MET = shared default credentials in shipped configuration.
- **Beyond the letter.** Secret scanning in CI `[GitHub, Scorecard]`; per-device unique credentials `[ETSI 5.1-1]`.
- Evidence (repo): config, compose, Dockerfiles, `.env.example`, seed scripts; docs on first-run setup.
- Fix (varies): remove defaults; force setup on first use.

---

## Stage 3 · During development (D1–D5)

### D1 · Security testing with retained results
- CRA: Annex I Pt II(3) (effective and regular tests and reviews of the security of the
  product); Annex VII(6) (reports of tests carried out to verify conformity with Pt I and Pt II).
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: you test the product's security regularly and keep the results. A written
  "test plan" document is how the matrix frames it; the law asks for the tests and the reports.
- **Baseline.** MET = security-relevant tests are run regularly and their results are retained
  (CI history counts). PARTIAL = tests exist but are not security-focused or results are not
  retained. NOT_MET = no testing.
- **Beyond the letter.** Written test plan covering authentication, access control, input
  validation, encryption, error handling `[Matrix, SSDF PW.8]`; coverage targets `[Practice]`.
- Evidence (repo): tests in CI, `tests/security/`, `docs/security/test-plan.md`.
- Fix (half a day): tag the tests that cover security requirements; keep CI history; optionally
  write the plan as a table.

### D2 · Process evidence generated by the repository
- CRA: Annex VIII Pt I(3); Annex VII(2)(c); Art. 13(14). No specific tooling is required.
- Track: AUTO · Assess via: repo+intake · Gate: no
- Plain English: the repo itself should leave a trail that changes were checked before release.
  Branch protection and mandatory reviews are the common way to do that, **not a legal requirement**.
- **Baseline.** MET = changes to the released branch leave retained evidence of checks (CI on
  pull requests, or equivalent records). PARTIAL = CI exists but does not run on every change, or
  records are not retained. NOT_MET = no checks and no records. UNKNOWN if none visible and not asked.
- **Beyond the letter.** Protected default branch, no force-push `[Scorecard Branch-Protection]`;
  required status checks `[Scorecard]`; at least one required review `[Scorecard Code-Review]` —
  for a solo maintainer, document an exception in the SDL rather than bypassing; signed commits
  or tags `[Scorecard Signed-Releases]`.
- Fix (30 minutes): make CI run on every pull request; optionally protect the branch.

### D3 · Regular security testing and review
- CRA: Annex I Pt II(3) ("effective and regular tests and reviews"); Annex VII(6).
- Track: AUTO · Assess via: repo+intake · Gate: yes
- Plain English: automated or manual security testing that happens regularly, not once. A
  penetration test is **not** literally required; it is the strongest form of "review".
- **Baseline.** MET = at least one form of security testing runs regularly (SAST, dependency
  scanning, DAST, or recurring manual security review) and results are retained. PARTIAL = a
  one-off test only, or testing without retained results. NOT_MET = none.
- **Beyond the letter.** SAST in CI `[Scorecard SAST]`; secret scanning `[GitHub]`; DAST `[Practice]`;
  independent penetration test within 12 months `[Matrix, Practice]`; fuzzing `[Scorecard Fuzzing]`.
- Evidence (repo): CodeQL/Semgrep/etc. workflows, scheduled scans, `docs/security/pentest*`.
- Fix (1 hour): enable CodeQL or equivalent on pull requests and a weekly schedule.

### D4 · Secure distribution of updates
- CRA: Annex I Pt II(7) (mechanisms to securely distribute updates so vulnerabilities are fixed
  or mitigated in a timely manner, automatically where applicable for security updates);
  Pt I(2)(c) (vulnerabilities addressable through security updates; where applicable automatic
  security updates enabled by default with an easy opt-out, notification of available updates,
  option to postpone); Annex II(8)(c),(e) (instructions on installing updates and turning off auto-install).
- Track: AUTO · Assess via: repo+intake · Gate: yes
- Plain English: users must be able to get updates whose authenticity and integrity they (or the
  product) can verify, and be told how to install them.
- **Baseline.** MET = update artefacts are integrity- and authenticity-protected (signatures,
  attestations, or a package registry with equivalent guarantees) **and** installation/update
  instructions exist (Annex II(8)(c)). Where the product installs updates itself, automatic
  security updates are on by default with opt-out (Pt I(2)(c)). PARTIAL = checksums only, or
  protection without instructions. NOT_MET = unsigned artefacts and no documented update path.
- **Beyond the letter.** Build provenance attestations `[SLSA L2+, Scorecard Signed-Releases]`;
  Sigstore keyless signing `[Practice]`; reproducible builds `[SLSA]`.
- Evidence (repo): release workflow signing/attestation steps, `.sig`/`.sigstore`/`.intoto` assets,
  README verification and update instructions.
- Fix (2–4 hours): sign or attest release artefacts; add "Installing updates" and "Verifying a
  release" to the docs.

### D5 · Data minimisation
- CRA: Annex I Pt I(2)(g) (process only data adequate, relevant and limited to the intended
  purpose); Pt I(2)(l) (security logging with a user opt-out).
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: collect only what the product needs, and say what that is.
- **Baseline.** MET = what data the product processes and why is documented and limited to the
  intended purpose. PARTIAL = documented but includes data not tied to the purpose, or undocumented
  but plausibly minimal. NOT_MET = undocumented collection (e.g. analytics SDKs with no disclosure).
- **Beyond the letter.** Telemetry opt-in rather than opt-out `[Practice]` (the law requires
  opt-out only for security logging); data inventory with retention periods `[Practice, GDPR]`.
- Evidence (repo): `docs/privacy.md`, data-handling notes, telemetry configuration.
- Fix (2 hours): one-page data inventory (what, why, where, how long).

---

## Stage 4 · Before product release (R1–R12)

### R1 · SBOM and no known exploitable vulnerabilities at release
- CRA: Annex I Pt II(1) (identify and document vulnerabilities and components, incl. an SBOM in a
  commonly used, machine-readable format covering at least top-level dependencies); Pt I(2)(a)
  (made available without **known exploitable** vulnerabilities); Annex VII(2)(b),(8).
- Track: AUTO · Assess via: repo · Gate: yes
- Plain English: a machine-readable list of what is in the product, and a check before release
  that nothing in it has a known exploitable vulnerability. The matrix's "any resolved CVE is a
  violation" is stricter than the text, which says *exploitable*.
- **Baseline.** MET = an SBOM exists for the released version **and** there is evidence of a
  vulnerability check before release (automated or documented manual). PARTIAL = one of the two.
  NOT_MET = neither.
- **Beyond the letter.** SBOM generated in CI for every release and attached as an asset
  `[OSPS, Practice]`; scan gate that fails the build on known vulnerabilities `[Practice]`;
  VEX statements for non-exploitable findings `[Practice]`.
- Evidence (repo): `sbom-action`/syft/cdxgen steps, SBOM release assets, grype/trivy/osv-scanner,
  Dependabot alerts, dependency graph.
- Fix (1–2 hours): generate an SBOM at release time and scan it; keep the output with the release.

### R2 · SBOM is machine-readable in a commonly used format
- CRA: Annex I Pt II(1) ("commonly used and machine-readable format"); Art. 13(24) (Commission
  may specify format by implementing act — none adopted yet).
- Track: AUTO · Assess via: repo · Gate: yes
- Plain English: SPDX or CycloneDX, as JSON or XML. Not a PDF or spreadsheet.
- **Baseline.** MET = SPDX or CycloneDX artefact for the released version. PARTIAL = another
  machine-readable format. NOT_MET = none or non-machine-readable.
- **Beyond the letter.** Include component hashes and licenses `[Practice]`; NTIA minimum elements `[Practice]`.
- Fix (15 minutes once R1 exists): set output format to `spdx-json` or `cyclonedx-json`.

### R3 · External interfaces documented (inbound)
- CRA: Annex I Pt I(2)(j) (limit attack surfaces incl. external interfaces); Annex VII(2)(a)
  (system architecture description).
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: what the product listens on and why. A per-port justification table is the
  matrix's framing; the law wants the attack surface limited and the architecture documented.
- **Baseline.** MET = listening interfaces documented in the architecture/risk documentation.
  PARTIAL = visible in configuration only. NOT_MET = undocumented listeners. NA = no listeners.
- **Beyond the letter.** Per-interface justification and default on/off `[Matrix]`.
- Fix (1 hour): table of interface, protocol, purpose, default state.

### R4 · External connections documented (outbound)
- CRA: Annex I Pt I(2)(g) (data minimisation), (i) (minimise impact on other networks), (j);
  Annex VII(2)(a).
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: what the product talks to (APIs, telemetry, update servers) and why.
- **Baseline.** MET = outbound connections documented. PARTIAL = partly (e.g. telemetry only).
  NOT_MET = none.
- **Beyond the letter.** Justify each destination and audit third-party library egress `[Matrix]`.
- Fix (1–2 hours): capture traffic from a test build; list and justify destinations.

### R5 · Support period determined and end date published
- CRA: Art. 13(8) (determine support period; at least 5 years unless the product is expected to
  be used for less; record the reasoning — Annex VII(4)); Art. 13(19) (end date, at least month
  and year, clearly specified at time of purchase); Annex II(7) (type of support and end date in
  user information).
- Track: POLICY · Assess via: repo+intake · Gate: yes
- Plain English: decide how long you will fix vulnerabilities, write down why, and tell buyers
  the end month/year before they buy.
- **Baseline.** MET = support period decided, reasoning recorded, and end date (month + year)
  published where buyers see it. PARTIAL = period decided but end date not published, or
  published without reasoning recorded. NOT_MET = none.
- **Beyond the letter.** Per-version support table `[Practice]`; period cross-checked against
  dependency EOL `[Practice]`.
- Evidence (repo): `SUPPORT.md`, `SECURITY.md` supported versions with dates, `docs/support-policy.md`.
- Fix (1 hour): "Version X receives security updates until YYYY-MM." plus a short "how we decided".

### R6 · Conformity assessment carried out
- CRA: Art. 13(12); Art. 32; Annex VIII.
- Track: POLICY · Assess via: intake · Gate: yes
- **Baseline.** MET = the applicable procedure has been carried out and recorded (Module A:
  internal control per Annex VIII Pt I; otherwise Notified Body certificate). PARTIAL = in
  progress. NOT_MET = not started.
- **Beyond the letter.** Third-party review of a Module A self-assessment `[Practice]`.
- Fix: follow the route from B2; record the outcome in the technical file.

### R7 · EU Declaration of Conformity
- CRA: Art. 28; Annex V (content); Art. 13(12), (13); Art. 13(20) (a copy or a simplified DoC
  per Annex VI accompanies the product, the simplified form giving the URL of the full DoC).
- Track: POLICY · Assess via: repo+intake · Gate: yes
- **Baseline.** MET = DoC drawn up per Annex V, signed, and provided with the product (full or
  simplified with URL). PARTIAL = drafted or not yet provided with the product. NOT_MET = none.
- **Beyond the letter.** Publish the DoC at a stable URL `[Practice]`.
- Fix (2 hours once R6 is done): fill Annex V; sign; link from the docs (Annex II(6)).

### R8 · CE marking
- CRA: Art. 29–30. For software, Art. 30(1): the CE marking is affixed **either to the EU
  declaration of conformity or on the website accompanying the software**, in a section easily
  and directly accessible to consumers.
- Track: POLICY · Assess via: intake · Gate: yes
- **Baseline.** MET = CE marking affixed per Art. 30(1) (for software: on the DoC or website).
  PARTIAL = placement decided, not yet applied. NOT_MET = not planned.
- **Beyond the letter.** Also show it in the product's about screen `[Practice]`.
- Fix (1 hour once R7 exists).

### R9 · Technical documentation compiled
- CRA: Art. 31; Annex VII(1)–(8); Art. 13(12) (drawn up before placing on the market);
  Art. 31(2) (continuously updated during the support period).
- Track: POLICY · Assess via: repo+intake · Gate: yes
- **Baseline.** MET = a technical file exists containing every Annex VII element: product
  description and versions, user information, process descriptions (incl. SBOM, CVD policy,
  contact evidence, update distribution), risk assessment, support-period reasoning, standards
  applied, test reports, copy of DoC. PARTIAL = index exists with gaps. NOT_MET = none.
- **Beyond the letter.** Version-controlled index with links `[Practice]`.
- Fix (2 hours once components exist): `docs/compliance/technical-file.md` index.

### R10 · Retention of documentation
- CRA: Art. 13(13) (technical documentation and DoC kept at the disposal of authorities for at
  least 10 years after placing on the market **or the support period, whichever is longer**);
  Art. 13(18) (user information available for the same period); Art. 13(9) (each security update
  remains available for at least 10 years or the rest of the support period, whichever is longer).
- Track: POLICY · Assess via: repo+intake · Gate: no
- **Baseline.** MET = a retention commitment covering technical file, DoC, user information and
  security updates for the required period, and storage that can honour it. PARTIAL = artefacts
  retained by default (e.g. release assets) but no commitment or no coverage of all four.
  NOT_MET = none.
- **Beyond the letter.** Archive every SBOM version `[Matrix]`; off-platform mirror `[Practice]`.
- Fix (1 hour): retention statement; ensure release assets and docs are never deleted.

### R11 · Information and instructions to the user
- CRA: Annex II(1)–(8) (minimum content); Art. 13(18) (clear, in an understandable language,
  paper or electronic, available for the retention period); Art. 13(15)–(16) (product
  identification; manufacturer name, address, digital contact on product/packaging/docs).
- Track: POLICY · Assess via: repo · Gate: yes
- Plain English: the user documentation must contain the eight Annex II points.
- **Baseline.** Annex II points (9 is optional):
  1. manufacturer name and postal address, email or digital contact, website;
  2. single point of contact for vulnerabilities and where the CVD policy is;
  3. product name, type and identification (version);
  4. intended purpose, essential functions, security properties, security environment provided;
  5. known or foreseeable circumstances that may lead to significant cybersecurity risk;
  6. URL of the EU DoC (where applicable);
  7. type of technical support and end date of the support period;
  8. instructions on: secure commissioning and use; how changes affect data security; installing
     security updates; secure decommissioning and data removal; turning off automatic updates;
     integrator information where applicable.
  MET = all applicable points present. PARTIAL = 4–7 present. NOT_MET = 0–3.
- **Beyond the letter.** A single "Security" page grouping all of it `[Practice]`; `security.txt` `[RFC 9116]`.
- Fix (2 hours): a documentation page with one heading per Annex II point.

### R12 · Single point of contact and coordinated vulnerability disclosure policy
- CRA: Art. 13(17) (single point of contact, easily identifiable, users choose the means, not
  limited to automated tools); Annex I Pt II(5) (put in place and enforce a CVD policy); Pt II(6)
  (contact address for reporting vulnerabilities); Annex II(2).
- Track: POLICY · Assess via: repo · Gate: yes
- Plain English: one published way to report a vulnerability, and a published policy saying how
  you handle reports.
- **Baseline.** MET = a contact is published **and** a CVD policy is published or referenced.
  PARTIAL = contact without a policy, or policy without a usable contact. NOT_MET = neither.
- **Beyond the letter.** Response-time commitment `[Practice, ISO 29147]`; GitHub private
  vulnerability reporting `[GitHub]`; `.well-known/security.txt` `[RFC 9116]`; PGP key `[Practice]`;
  safe-harbour statement for researchers `[Practice]`.
- Evidence (repo): `SECURITY.md` (contact + policy), org-level `SECURITY.md`, PVR setting.
- Fix (20 minutes): `SECURITY.md` with contact, what to include, how you triage and disclose.

---

## Stage 5 · After product release (P1–P10)

### P1 · Risk assessment kept current
- CRA: Art. 13(3) (updated as appropriate during the support period); Art. 13(7) (systematically
  document cybersecurity aspects incl. vulnerabilities and third-party information; update the
  risk assessment where applicable); Art. 31(2).
- Track: POLICY · Assess via: repo+intake · Gate: no
- **Baseline.** MET = the risk assessment shows update history or a documented update rule, and
  cybersecurity information (vulnerabilities, third-party reports) is recorded. PARTIAL = rule
  without history, or history without a rule. NOT_MET = never updated, no rule.
- **Beyond the letter.** Explicit triggers (major change, new threat, exploited vulnerability)
  `[Matrix]`; review at every release `[Practice]`.
- Fix (30 minutes): "Review triggers" and "Change log" sections.

### P2 · Ongoing identification of vulnerabilities in components
- CRA: Annex I Pt II(1) (identify and document vulnerabilities and components); Pt II(3)
  (regular tests and reviews); Art. 13(7). Automation is **not** required; the matrix's "manual
  monitoring is insufficient" is advice, not law.
- Track: AUTO · Assess via: repo+intake · Gate: yes
- Plain English: a regular, reliable way to learn that a component you ship has a new vulnerability.
- **Baseline.** MET = a regular vulnerability-identification process exists for shipped
  components (automated alerts, scheduled scans, or a documented recurring manual review).
  PARTIAL = ad hoc. NOT_MET = none.
- **Beyond the letter.** Automated alerts (Dependabot/Renovate) plus a scheduled scan against
  live feeds `[Matrix, OSPS]`; daily or better frequency `[Practice]`.
- Evidence (repo): Dependabot alerts, `dependabot.yml`/`renovate.json`, scheduled scan workflows.
- Fix (30 minutes): enable Dependabot alerts or a scheduled scanner.

### P3 · Actively exploited vulnerability: early warning within 24 hours
- CRA: Art. 14(1), 14(2)(a) (24h early warning to the coordinating CSIRT and ENISA via the single
  reporting platform, Art. 16); Art. 14(7) (which CSIRT); Art. 14(8) (inform impacted users, and
  where appropriate all users, with mitigations). Applies from 11 September 2026.
- Track: POLICY · Assess via: repo+intake · Gate: yes
- **Baseline.** MET = a written procedure covering: what counts as "actively exploited" (Art. 3(42)),
  who reports, the 24h early warning via the ENISA platform to the correct CSIRT, and informing
  users. PARTIAL = procedure lacks the ENISA/CSIRT route or the 24h step or user notification.
  NOT_MET = none.
- **Beyond the letter.** Named on-call owner and backup `[Practice]`; pre-registered account on
  the reporting platform `[Practice]`; report templates `[Practice]`.
- Fix (2 hours): `docs/security/incident-response.md`.

### P4 · Vulnerability notification within 72 hours
- CRA: Art. 14(2)(b).
- Track: POLICY · Assess via: repo+intake · Gate: no
- **Baseline.** MET = procedure includes the 72h notification content (product, nature of exploit
  and vulnerability, corrective/mitigating measures taken and available to users, sensitivity).
  PARTIAL = 72h step without content list. NOT_MET = absent.
- **Beyond the letter.** Template `[Practice]`.

### P5 · Final vulnerability report within 14 days of a fix
- CRA: Art. 14(2)(c) (no later than 14 days after a corrective or mitigating measure is
  available: description incl. severity and impact; information on the malicious actor where
  available; details of the update or corrective measures).
- Track: POLICY · Assess via: repo+intake · Gate: no
- **Baseline.** MET = procedure includes the 14-day final report with its content. PARTIAL = step
  without content. NOT_MET = absent.

### P6 · Severe incident reporting
- CRA: Art. 14(3)–(5): severe incidents (criteria in 14(5)) reported via the same platform: 24h
  early warning (incl. whether suspected malicious), 72h incident notification, **final report
  within one month** of the incident notification (not 14 days — that is for vulnerabilities).
- Track: POLICY · Assess via: repo+intake · Gate: no
- **Baseline.** MET = procedure covers incidents with the 14(5) severity criteria and the
  24h / 72h / one-month timeline. PARTIAL = incidents covered without criteria or with the wrong
  timeline. NOT_MET = vulnerabilities only.
- **Beyond the letter.** Tabletop exercise annually `[Practice]`.

### P7 · Remediation and delivery of security updates
- CRA: Annex I Pt II(2) (address and remediate vulnerabilities without delay, incl. security
  updates; where technically feasible security updates provided **separately from functionality
  updates**); Pt II(4) (once an update is available, publicly disclose fixed vulnerabilities:
  description, affected product identification, impact, severity, remediation guidance; delay
  allowed in justified cases until users can patch); Pt II(8) (disseminate without delay, with
  advisory messages); Art. 13(6) (remediate component vulnerabilities and share fixes upstream).
- Track: AUTO · Assess via: repo+intake · Gate: no
- Plain English: be able to ship a security fix quickly on its own, and publish an advisory when
  you do. The matrix's "automatic update system" wording conflates this with dependency bots.
- **Baseline.** MET = a release path that can ship a security-only update promptly, and a
  practice of publishing advisories for fixed vulnerabilities (e.g. GitHub Security Advisories,
  changelog security section, advisory page). PARTIAL = one of the two. NOT_MET = neither.
- **Beyond the letter.** Automated dependency update PRs with auto-merge for security patches
  `[Practice]`; release automation from tags `[Practice]`; CVE IDs requested for fixed
  vulnerabilities `[Practice]`; machine-readable advisories (CSAF/OSV) `[Practice]` — Art. 14(8)
  says "where appropriate" machine-readable for user notifications.
- Evidence (repo): release automation, published advisories, `CHANGELOG.md` security entries,
  Dependabot/Renovate config.
- Fix (1–2 hours): automate releases from tags; adopt GitHub Security Advisories.

### P8 · Security updates free of charge and kept available
- CRA: Annex I Pt II(8) (security updates free of charge, unless otherwise agreed with a business
  user for a tailor-made product); Art. 13(9) (each security update remains available for at
  least 10 years after issue or the rest of the support period, whichever is longer);
  Art. 13(10)–(11) (substantially modified versions; archives of historical versions must warn users).
- Track: POLICY · Assess via: repo+intake · Gate: yes
- **Baseline.** MET = published statement that security updates are free for the support period,
  and updates are kept available for the 13(9) period. PARTIAL = practice without statement, or
  statement without a retention plan for updates. NOT_MET = security fixes gated behind payment.
- **Beyond the letter.** State it in terms of sale as well `[Practice]`.
- Fix (15 minutes): one sentence in the support policy; keep release artefacts permanently.

### P9 · End-of-support notification
- CRA: Art. 13(19): end date (month and year) clearly specified at time of purchase; where
  technically feasible, a notification to users when the product reaches end of support.
  A **12-month advance notice is not in the regulation**; it is the matrix's recommendation.
- Track: POLICY · Assess via: repo+intake · Gate: no
- **Baseline.** MET = end date published at purchase (see R5) and a mechanism or commitment to
  notify users at end of support where feasible. PARTIAL = date published, no notification
  mechanism. NOT_MET = neither.
- **Beyond the letter.** Announce end of support at least 12 months ahead `[Matrix]`; in-product
  banner `[Practice]`.
- Fix (15 minutes): add the notification commitment to the support policy.

### P10 · Corrective measures for non-conforming products
- CRA: Art. 13(21) (immediately take corrective measures, or withdraw or recall, when the
  product or processes are not in conformity); Art. 13(22) (provide information and cooperate
  with market surveillance on request); Art. 13(23) (inform authorities and users before ceasing
  operations). Proactive notification of authorities for non-conformity is **not** in Art. 13.
- Track: POLICY · Assess via: repo+intake · Gate: no
- **Baseline.** MET = a documented procedure for corrective measures incl. withdrawal/recall
  decisions, cooperation with authorities, and a cessation-of-operations plan. PARTIAL = informal
  or missing cessation plan. NOT_MET = none.
- **Beyond the letter.** Proactively notify market surveillance of significant non-conformity
  `[Matrix]` (as other NLF regulations require); recall drill `[Practice]`.
- Fix (30 minutes): "Corrective measures" and "If we cease operations" sections in the incident
  response document.

---

## Literal obligations not in the 40-item matrix (folded into items above)

| Obligation | CRA | Folded into |
|------------|-----|-------------|
| Report vulnerabilities in components to their maintainer; share fixes | Art. 13(6) | B5, P7 |
| Product identification (type/batch/serial) and manufacturer name/address/contact on product, packaging or docs | Art. 13(15)–(16); Annex II(1),(3) | R11 |
| Copy of DoC or simplified DoC with URL accompanies the product | Art. 13(20); Annex VI | R7 |
| Inform impacted users of exploited vulnerabilities/severe incidents and mitigations | Art. 14(8) | P3 |
| Publicly disclose fixed vulnerabilities once an update is available | Annex I Pt II(4) | P7 |
| Security updates separate from feature updates where feasible | Annex I Pt II(2) | P7 |
| Each security update available ≥10 years or rest of support period | Art. 13(9) | P8, R10 |
| Archives of old versions must warn about unsupported software | Art. 13(11) | P8 |
| Inform authorities and users before ceasing operations | Art. 13(23) | P10 |
| Security logging with user opt-out; secure data removal on decommissioning | Annex I Pt I(2)(l),(m); Annex II(8)(d) | D5, R11 |

## Quick index

| ID | Item | Track | Gate | Assess via |
|----|------|-------|------|------------|
| F1 | Documented secure development process | POLICY | yes | repo+intake |
| F2 | Evidence the process is followed | POLICY | no | repo+intake |
| F3 | Secure-by-design/default addressed | POLICY | no | repo+intake |
| F4 | EU authorised representative (optional) | POLICY | no | intake |
| B1 | Product classification | POLICY | yes | intake |
| B2 | Conformity assessment route | POLICY | yes | intake |
| B3 | Risk assessment | POLICY | yes | repo+intake |
| B4 | Threat analysis | POLICY | no | repo+intake |
| B5 | Third-party component due diligence | POLICY | no | repo+intake |
| B6 | Component/runtime EOL considered | POLICY | no | repo+intake |
| B7 | Confidentiality of data | POLICY | no | intake |
| B8 | Minimal attack surface | POLICY | no | repo+intake |
| B9 | No universal default credentials | POLICY | yes | repo+intake |
| D1 | Security testing with retained results | POLICY | no | repo+intake |
| D2 | Process evidence from the repository | AUTO | no | repo+intake |
| D3 | Regular security testing and review | AUTO | yes | repo+intake |
| D4 | Secure distribution of updates | AUTO | yes | repo+intake |
| D5 | Data minimisation | POLICY | no | repo+intake |
| R1 | SBOM and no known exploitable vulns | AUTO | yes | repo |
| R2 | SBOM machine-readable | AUTO | yes | repo |
| R3 | Inbound interfaces documented | POLICY | no | repo+intake |
| R4 | Outbound connections documented | POLICY | no | repo+intake |
| R5 | Support period and end date | POLICY | yes | repo+intake |
| R6 | Conformity assessment | POLICY | yes | intake |
| R7 | EU Declaration of Conformity | POLICY | yes | repo+intake |
| R8 | CE marking | POLICY | yes | intake |
| R9 | Technical documentation | POLICY | yes | repo+intake |
| R10 | Retention | POLICY | no | repo+intake |
| R11 | Information to the user (Annex II) | POLICY | yes | repo |
| R12 | Point of contact and CVD policy | POLICY | yes | repo |
| P1 | Risk assessment kept current | POLICY | no | repo+intake |
| P2 | Ongoing vulnerability identification | AUTO | yes | repo+intake |
| P3 | 24h early warning (vulnerability) | POLICY | yes | repo+intake |
| P4 | 72h notification | POLICY | no | repo+intake |
| P5 | 14-day final report | POLICY | no | repo+intake |
| P6 | Severe incident reporting (1-month final) | POLICY | no | repo+intake |
| P7 | Remediation and delivery of updates | AUTO | no | repo+intake |
| P8 | Free updates, kept available | POLICY | yes | repo+intake |
| P9 | End-of-support notification | POLICY | no | repo+intake |
| P10 | Corrective measures | POLICY | no | repo+intake |

Totals: 40 items · 7 AUTO · 33 POLICY · 19 gate items · F4 is NA unless a representative is appointed.
