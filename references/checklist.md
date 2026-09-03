# CRA Readiness Checklist (40 items)

Source of the 40 items: the manufacturer compliance matrix at
https://www.cyberresilienceact.eu/compliance-matrix.html (Regulation (EU) 2024/2847).
Item IDs, tracks, evidence rules and fixes below are this skill's own additions.

## How to read this file

Every item has:

- **ID** – stable identifier used in the report and the collector output.
- **Track** – what kind of work fixes it:
  - `AUTO` = Automation & tooling (CI jobs, repo settings, scanners, release pipeline).
  - `POLICY` = Policy, design & documents (decisions, written documents, product design changes, legal steps).
- **Assess via** – where evidence can come from:
  - `repo` = observable in the repository (files, workflows, settings, releases).
  - `intake` = only the founder can tell us (ask in the intake questionnaire).
  - `repo+intake` = repo can show partial evidence; founder confirms the rest.
- **Gate** – `yes` means the item must be MET for an A grade. Gate items are the ones a
  market-surveillance authority or customer would ask for on day one.
- **Evidence** – what counts.
- **Status rules** – how to decide MET / PARTIAL / NOT_MET.
- **Fix** – plain-language next step for a founder, with rough effort.

Statuses used everywhere: `MET`, `PARTIAL`, `NOT_MET`, `UNKNOWN`, `NA`.
`UNKNOWN` means we could not see the evidence (permissions, no access, founder said
"don't know"). `NA` means the item does not apply (e.g. EU representative for an EU company).

Repo evidence must always be quoted in the report (file path, workflow name, setting name)
so the founder can verify it. Intake answers must be labelled "based on your answer, not verified".

---

## Stage 1 · Company-level foundations (F1–F4)

### F1 · Documented Security Development Lifecycle (SDL)
- CRA: Art. 13(1); Annex I
- Track: POLICY · Assess via: repo+intake · Gate: yes
- Plain English: a written description of how your team builds software securely (who does
  what, at which stage, and what gets checked before release).
- Evidence (repo): a file such as `SECURITY.md`, `docs/security/sdl.md`, `docs/secure-development.md`,
  `SECURITY_POLICY.md`, `CONTRIBUTING.md` containing headings/keywords like "secure development",
  "SDL", "security review", "threat model", "release checklist". ISO/IEC 27001 or IEC 62443-4-1
  certificates mentioned in docs count as strong evidence.
- Status rules: MET = document exists and covers at least phases, roles and security checks
  before release (or founder attests an equivalent document exists outside the repo).
  PARTIAL = security guidance exists but is informal (a paragraph in CONTRIBUTING, no phases/roles).
  NOT_MET = nothing found and founder says none exists.
- Fix (half a day): write a 2–3 page SDL document: design review, dependency approval, code review,
  security testing, release sign-off, post-release monitoring. Name an owner per step. Commit it under
  `docs/security/sdl.md`.

### F2 · Evidence of conformity with the SDL
- CRA: Annex I Pt I
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: proof that you actually follow the SDL, not just that it exists.
- Evidence (repo): PR template with a security checklist (`.github/PULL_REQUEST_TEMPLATE.md`),
  required reviews on the default branch, release checklist files, security review records
  (`docs/security/reviews/`), CI checks that block merges.
- Status rules: MET = at least two forms of recurring evidence (e.g. PR template checklist plus
  required reviews) or founder attests records are kept. PARTIAL = one form. NOT_MET = none.
- Fix (1–2 hours): add a security checklist to the PR template and turn on required reviews.
  Keep release sign-off notes in the repo or your ticket system.

### F3 · SDL covers secure-by-design and secure-by-default
- CRA: Annex I Pt I(2), (3)
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: your SDL explicitly says the product ships with a small attack surface and
  safe settings without the customer having to configure anything.
- Evidence (repo): SDL/security docs mention "secure by default", "attack surface",
  "hardening", "least privilege", or a default-configuration review step.
- Status rules: MET = explicit section in the SDL. PARTIAL = mentioned in passing.
  NOT_MET = absent (or F1 is NOT_MET).
- Fix (1 hour): add a section to the SDL: "Every feature is reviewed for default settings,
  exposed interfaces and permissions before release."

### F4 · EU Authorised Representative (non-EU manufacturers)
- CRA: Art. 19
- Track: POLICY · Assess via: intake · Gate: yes (only when applicable)
- Plain English: if your company is not established in the EU, you must appoint an EU-based
  representative by written mandate and name them in your documentation.
- Evidence (repo, weak): compliance docs naming a representative. Primarily intake.
- Status rules: NA = company established in the EU. MET = representative appointed and named
  in the technical documentation. NOT_MET = non-EU and no representative. UNKNOWN = founder
  does not know.
- Fix (days–weeks): engage an EU authorised representative service; sign a mandate; add their
  name and address to the technical file and Declaration of Conformity.

---

## Stage 2 · Before development begins (B1–B9)

### B1 · Determine product classification
- CRA: Annex III / Annex IV
- Track: POLICY · Assess via: intake · Gate: yes
- Plain English: know whether your product is "Default", "Important (Class I or II)" or
  "Critical". This decides whether you can self-certify or need an external assessor.
- Evidence (repo): `docs/compliance/classification.md` or similar. Primarily intake.
- Status rules: MET = founder states classification and rationale is documented.
  PARTIAL = founder states a classification but nothing is written down.
  NOT_MET = never considered. If the intake answers indicate Annex III features
  (see intake.md Q5) and the founder says "Default", flag as PARTIAL with a warning.
- Fix (1–2 hours): compare the product to the Annex III/IV lists (the source site has a
  classification tool). Write a one-page note with the conclusion and reasons.

### B2 · Identify the conformity assessment route
- CRA: Art. 32; Annex VIII
- Track: POLICY · Assess via: intake · Gate: yes
- Plain English: Default products can self-assess (Module A). Important/Critical products
  usually need a Notified Body, which takes months to schedule.
- Evidence (repo): compliance docs naming the route. Primarily intake.
- Status rules: MET = route documented and consistent with B1. PARTIAL = route chosen but not
  written down. NOT_MET = not decided.
- Fix (1 hour, or months if a Notified Body is required): record the route in
  `docs/compliance/conformity-route.md`. If Important/Critical, contact a Notified Body now.

### B3 · Product-specific cybersecurity risk assessment
- CRA: Annex I Pt I(1)
- Track: POLICY · Assess via: repo+intake · Gate: yes
- Plain English: a written assessment of what could go wrong with your product's security,
  how likely and how bad, and what you do about it. Keep every version.
- Evidence (repo): `docs/security/risk-assessment*.md`, `RISK_ASSESSMENT.md`,
  `docs/compliance/risk*`, spreadsheets exported to the repo, with version history.
- Status rules: MET = document exists with identified risks, ratings and mitigations, and is
  versioned. PARTIAL = an informal list of risks without ratings or history.
  NOT_MET = none.
- Fix (1–2 days): use a simple table (asset, threat, likelihood, impact, mitigation, owner).
  Commit it and update it at each major release.

### B4 · Threat modelling
- CRA: Annex I Pt I(1)
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: a structured look at how an attacker would get in (attack surface, actors,
  vectors) and what security requirements follow. Say which method you used (e.g. STRIDE).
- Evidence (repo): `THREAT_MODEL.md`, `docs/security/threat-model*`, diagrams, mentions of
  STRIDE/PASTA/attack trees.
- Status rules: MET = document with attack surface, threats and derived requirements plus a
  named methodology. PARTIAL = partial or method unnamed. NOT_MET = none.
- Fix (1 day): run a STRIDE session on a data-flow diagram of the product; write down the results.

### B5 · Third-party & open-source component policy
- CRA: Annex I Pt II
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: written rules for choosing and approving libraries and services, including
  minimum support life and how fast vulnerabilities must be fixed.
- Evidence (repo): `docs/security/dependency-policy.md`, `docs/third-party-components.md`,
  CONTRIBUTING sections on adding dependencies, license allow-lists, `dependency-review`
  workflow with license/severity gates.
- Status rules: MET = written policy covering selection criteria, EOL and vulnerability
  response. PARTIAL = automated gates exist but no written policy, or vice versa. NOT_MET = none.
- Fix (2 hours): write a one-page policy; add the `dependency-review` action (or equivalent)
  to enforce it on pull requests.

### B6 · EOL check for tools and dependencies
- CRA: Annex I Pt II
- Track: AUTO · Assess via: repo · Gate: no
- Plain English: know when your runtimes, base images and key libraries stop receiving
  security fixes, and avoid ones that die before your product's support period ends.
- Evidence (repo): lockfiles committed (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`,
  `poetry.lock`, `uv.lock`, `Pipfile.lock`, `go.sum`, `Cargo.lock`, `Gemfile.lock`,
  `composer.lock`); pinned runtime versions (`.nvmrc`, `.python-version`, `.tool-versions`,
  `engines`, `go` directive, Dockerfile base images with explicit tags, not `latest`);
  EOL tooling in CI (endoflife.date checks, `xeol`, Renovate/Dependabot for base images).
- Status rules: MET = lockfiles and pinned runtimes and some EOL tooling or documented EOL
  review. PARTIAL = lockfiles present but runtimes unpinned or no EOL tooling.
  NOT_MET = no lockfiles, `latest` base images.
- Fix (1–2 hours): commit lockfiles, pin runtime versions, add a scheduled `xeol` or
  endoflife.date check, and record dependency EOL dates in the support policy.

### B7 · Storage encryption feasibility
- CRA: Annex I Pt I(4)(e)
- Track: POLICY · Assess via: intake · Gate: no
- Plain English: data the product stores must be encryptable at rest. For hardware products
  this can force a hardware change; for software, confirm your storage layer supports it.
- Evidence (repo): docs stating encryption-at-rest approach; config enabling it.
- Status rules: MET = encryption at rest confirmed and documented. PARTIAL = supported but not
  documented. NOT_MET = stores sensitive data unencrypted. NA = product stores no data.
- Fix (varies): document how data at rest is encrypted (database, disk, KMS) and make it the default.

### B8 · Minimal attack-surface design
- CRA: Annex I Pt I(2)(b)
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: anything not needed for the product to work (ports, services, debug
  endpoints, protocols) is off by default.
- Evidence (repo): docs on hardening; Dockerfiles with few `EXPOSE` lines; no debug flags on
  by default in shipped config; SDL section (F3).
- Status rules: MET = documented design principle and consistent config. PARTIAL = one of the two.
  NOT_MET = debug/admin interfaces on by default or nothing documented.
- Fix (half a day): list every interface and port, decide which are needed, disable the rest by
  default, write the list down (feeds R3/R4).

### B9 · Default credential policy
- CRA: Annex I Pt I(2)(c)
- Track: POLICY · Assess via: repo+intake · Gate: yes
- Plain English: no shared default passwords. Either none at all, or the user must set a
  unique one on first use.
- Evidence (repo): no hard-coded default passwords in config, compose files, Dockerfiles,
  `.env.example`, seed scripts (patterns like `admin/admin`, `password=password`,
  `changeme`); docs describing first-run credential setup.
- Status rules: MET = no default credentials found and first-run setup documented (or NA when
  the product has no authentication). PARTIAL = defaults exist but a forced change on first
  login is documented. NOT_MET = shipped default credentials.
- Fix (varies): remove default credentials; force setup on first use; add a secret scanner
  (e.g. gitleaks) to CI to keep them out.

---

## Stage 3 · During development (D1–D5)

### D1 · Cybersecurity-focused test plan
- CRA: Annex I Pt I(1)
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: a written test plan covering authentication, access control, input
  validation, encryption and error handling, kept in the technical file.
- Evidence (repo): `docs/security/test-plan.md`, test directories with security-focused tests
  (`tests/security/`, files named `*auth*`, `*authz*`, `*injection*`, `*crypto*`), CI running tests.
- Status rules: MET = written plan and matching tests run in CI. PARTIAL = tests exist but no
  plan, or plan exists without tests. NOT_MET = neither.
- Fix (half a day): write the plan as a table (area, test, automated?, owner); tag or group the
  existing tests that satisfy it.

### D2 · Evidence of SDL compliance during development
- CRA: Annex I Pt I
- Track: AUTO · Assess via: repo · Gate: no
- Plain English: the repo itself should generate proof that the process was followed: reviews
  required, checks must pass, history is protected.
- Evidence (repo): branch protection or rulesets on the default branch (required reviews,
  required status checks, no force-push), signed commits or tags, CI workflows that run on
  every pull request.
- Status rules: MET = protected default branch with required reviews and required checks, CI on
  PRs. PARTIAL = CI on PRs but branch protection missing or unknown. NOT_MET = direct pushes
  to default branch and no CI. UNKNOWN if branch protection could not be read (needs admin).
- Fix (30 minutes): Settings > Branches (or Rulesets): require a pull request, at least one
  review and passing checks before merging; block force-pushes.

### D3 · Penetration testing / vulnerability assessment
- CRA: Annex I Pt I(1)
- Track: AUTO · Assess via: repo+intake · Gate: yes
- Plain English: security testing of the product before release: automated scanning in CI
  every time, plus a human-led penetration test for a representative build.
- Evidence (repo): SAST in CI (CodeQL, Semgrep, SonarQube, Bandit, gosec, Brakeman), secret
  scanning (gitleaks, trufflehog, GitHub secret scanning), DAST (ZAP), container scanning
  (Trivy, Grype). Pentest report or summary in `docs/security/pentest*` (intake if kept private).
- Status rules: MET = SAST plus secret scanning in CI and a pentest within the last 12 months
  (attested or documented). PARTIAL = automated scanning only, or pentest only.
  NOT_MET = neither.
- Fix (1 hour for automation; budget for pentest): enable CodeQL default setup and secret
  scanning; add gitleaks to CI; book a pentest before EU launch.

### D4 · Secure software update mechanism
- CRA: Annex I Pt I(2)(f)
- Track: AUTO · Assess via: repo+intake · Gate: yes
- Plain English: customers must be able to verify updates are genuine and untampered before
  installing, and updates should be automatic where feasible.
- Evidence (repo): signed releases or artefacts (Sigstore/cosign, GPG signatures, checksums
  published with releases), build provenance attestations (`actions/attest-build-provenance`,
  SLSA generators, npm/PyPI trusted publishing with provenance), signed tags, documentation of
  how the product updates itself or how users verify downloads.
- Status rules: MET = signed artefacts or provenance on releases and documented verification /
  auto-update. PARTIAL = checksums only, or signing without documentation. NOT_MET = unsigned
  releases and no documented update path.
- Fix (2–4 hours): add `actions/attest-build-provenance` or cosign signing to the release
  workflow; publish checksums; document verification steps in the README.

### D5 · Data minimisation
- CRA: Annex I Pt I(4)(f)
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: collect and store only what the product needs to work.
- Evidence (repo): privacy or data-handling docs, telemetry documented as opt-in or off by
  default, data inventory.
- Status rules: MET = documented data inventory and telemetry off/opt-in by default.
  PARTIAL = documented but telemetry on by default, or undocumented but minimal.
  NOT_MET = undocumented telemetry/data collection.
- Fix (2 hours): write a one-page data inventory (what, why, where, how long). Make telemetry
  opt-in.

---

## Stage 4 · Before product release (R1–R12)

### R1 · SBOM prepared and vulnerability-screened
- CRA: Annex I Pt II(1)
- Track: AUTO · Assess via: repo · Gate: yes
- Plain English: a list of every component in your product, checked so that no component
  ships with a known, already-fixed vulnerability.
- Evidence (repo): SBOM generation in CI (`anchore/sbom-action`, syft, `cyclonedx-*`,
  `spdx-sbom-generator`, `cdxgen`, Trivy SBOM output), vulnerability scan of the SBOM or
  lockfiles in CI (grype, trivy, osv-scanner, snyk, Dependabot alerts), SBOM attached to
  releases, GitHub dependency graph enabled.
- Status rules: MET = SBOM generated per release and scanned in CI with a failing gate on known
  vulnerabilities. PARTIAL = one of generation or scanning. NOT_MET = neither.
- Fix (1–2 hours): add `anchore/sbom-action` plus `anchore/scan-action` (or osv-scanner) to the
  release workflow; upload the SBOM as a release asset.

### R2 · SBOM in machine-readable format
- CRA: Annex I Pt II
- Track: AUTO · Assess via: repo · Gate: yes
- Plain English: the SBOM must be SPDX or CycloneDX (JSON/XML), not a PDF or spreadsheet.
- Evidence (repo): files or release assets named `*.spdx.json`, `*.spdx`, `*.cdx.json`,
  `bom.json`, `bom.xml`, `sbom.json`; CI steps specifying `--format spdx-json` /
  `cyclonedx-json`.
- Status rules: MET = SPDX or CycloneDX artefact produced per release. PARTIAL = SBOM exists in
  another format. NOT_MET = no SBOM (follows R1).
- Fix (15 minutes once R1 exists): set the output format to `spdx-json` or `cyclonedx-json`.

### R3 · Inbound connections list
- CRA: Annex I Pt I(2)(b)
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: a list of every port/interface the product listens on, each with a reason.
- Evidence (repo): `docs/security/network.md`, `docs/architecture` sections on ports,
  Dockerfile `EXPOSE`, compose `ports:`; consistency between docs and config.
- Status rules: MET = written list with justifications. PARTIAL = ports visible in config but
  not documented. NOT_MET = neither. NA = product opens no listening ports (e.g. a library).
- Fix (1 hour): table of port, protocol, purpose, default on/off.

### R4 · Outbound connections list
- CRA: Annex I Pt I
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: a list of every external service the product calls (APIs, telemetry, update
  servers, third-party libraries phoning home), each justified.
- Evidence (repo): docs listing outbound endpoints; telemetry documentation; egress config.
- Status rules: MET = written list with justifications. PARTIAL = partial list (e.g. telemetry
  documented, others not). NOT_MET = none.
- Fix (1–2 hours): capture network traffic from a test build, list destinations, justify or remove.

### R5 · Declare the product End-of-Life
- CRA: Art. 13(8)
- Track: POLICY · Assess via: repo+intake · Gate: yes
- Plain English: state how long you will provide security updates (minimum 5 years unless the
  product's expected lifetime is shorter). It cannot outlast your key dependencies' EOL.
- Evidence (repo): `SUPPORT.md`, `SECURITY.md` "Supported versions" section with dates,
  `docs/support-policy.md`, `docs/lifecycle.md`.
- Status rules: MET = a dated support period per version/product line, published. PARTIAL =
  "supported versions" table without dates or period. NOT_MET = none.
- Fix (1 hour): add a "Support period" section: "Version X receives security updates until
  YYYY-MM-DD." Check it against dependency EOL (B6).

### R6 · Complete the conformity assessment
- CRA: Art. 32
- Track: POLICY · Assess via: intake · Gate: yes
- Plain English: actually perform the assessment procedure for your route (self-assessment
  for Default; Notified Body for Important/Critical) and document it.
- Evidence (repo): `docs/compliance/conformity-assessment*`. Primarily intake.
- Status rules: MET = completed and documented. PARTIAL = in progress. NOT_MET = not started.
- Fix (days for Module A; months for Notified Body): follow the route from B2; record the
  outcome in the technical file.

### R7 · Prepare the EU Declaration of Conformity
- CRA: Art. 28; Annex V
- Track: POLICY · Assess via: repo+intake · Gate: yes
- Plain English: a signed document stating your product meets the CRA, following the Annex V
  template. Keep it for 10 years.
- Evidence (repo): `docs/compliance/declaration-of-conformity*`, `DoC.pdf`.
- Status rules: MET = signed DoC exists. PARTIAL = drafted, unsigned. NOT_MET = none.
- Fix (2 hours once R6 is done): fill the Annex V template; have an authorised person sign.

### R8 · Affix the CE marking
- CRA: Art. 30
- Track: POLICY · Assess via: intake · Gate: yes
- Plain English: the CE mark must appear on the product, its packaging, or (for software) in
  the documentation/about screen and website. No CE mark, no EU market from 11 Dec 2027.
- Evidence (repo): CE marking in docs/about assets. Primarily intake.
- Status rules: MET = CE marking applied where required. PARTIAL = planned, placement decided.
  NOT_MET = not planned.
- Fix (1 hour once R7 is done): add CE marking to docs, download page and about screen.

### R9 · Compile the technical file
- CRA: Art. 31; Annex VII
- Track: POLICY · Assess via: repo+intake · Gate: yes
- Plain English: one bundle containing product description, risk assessment, SDL evidence,
  test results, SBOM, connection audits, DoC and EOL declaration.
- Evidence (repo): `docs/compliance/technical-file.md` (index) or a `compliance/` directory
  linking all the above.
- Status rules: MET = index exists and every referenced document is present. PARTIAL = index
  exists with gaps. NOT_MET = none.
- Fix (2 hours once components exist): create an index file linking each Annex VII element to
  its location.

### R10 · 10-year retention plan
- CRA: Art. 31(3)
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: keep all technical documentation, including every SBOM version, for at least
  10 years after the product is first sold.
- Evidence (repo): retention policy doc; SBOMs attached to every release (immutable history);
  archival workflow.
- Status rules: MET = written retention policy and SBOMs archived per release. PARTIAL = one of
  the two. NOT_MET = neither.
- Fix (1 hour): write a retention statement; ensure release assets (SBOM, DoC) are never deleted
  and are mirrored to long-term storage.

### R11 · User-facing documentation
- CRA: Annex II; Art. 13(18)
- Track: POLICY · Assess via: repo · Gate: yes
- Plain English: customer documentation must state intended use, security properties, how to
  configure security, the support period/EOL, and how to report vulnerabilities.
- Evidence (repo): README/docs covering all five: intended use, security features, secure
  configuration, support period, vulnerability reporting.
- Status rules: MET = all five present. PARTIAL = 3–4 present. NOT_MET = 0–2 present.
- Fix (2 hours): add a "Security" page to the docs with those five headings.

### R12 · Vulnerability disclosure contact published
- CRA: Art. 13(5)
- Track: POLICY · Assess via: repo · Gate: yes
- Plain English: one clearly published, monitored way for anyone to report a vulnerability.
- Evidence (repo): `SECURITY.md` with a contact (email, form, or "use GitHub private
  vulnerability reporting"), GitHub private vulnerability reporting enabled,
  `.well-known/security.txt` in the product/website.
- Status rules: MET = SECURITY.md with a contact and response expectation, plus private
  vulnerability reporting enabled (if on GitHub). PARTIAL = contact exists but no response
  expectation, or private reporting off. NOT_MET = no contact.
- Fix (20 minutes): add SECURITY.md (contact, what to include, response time); enable
  Settings > Code security > Private vulnerability reporting.

---

## Stage 5 · After product release (P1–P10)

### P1 · Update risk assessment on significant change
- CRA: Annex I Pt I(1)
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: revisit the risk assessment whenever the product changes materially, a new
  threat appears, or a vulnerability is exploited. Record why and what changed.
- Evidence (repo): risk assessment with a change log / version history; release checklist
  item "risk assessment reviewed".
- Status rules: MET = documented trigger rule and at least one recorded review (or a new
  product with the rule documented). PARTIAL = rule exists, no history. NOT_MET = none.
- Fix (30 minutes): add "Review triggers" and "Change log" sections to the risk assessment.

### P2 · Automated SBOM vulnerability monitoring
- CRA: Art. 14
- Track: AUTO · Assess via: repo · Gate: yes
- Plain English: tooling that continuously compares your components against vulnerability
  feeds, fast enough to hit the 24-hour reporting clock. Manual checking is not enough.
- Evidence (repo): Dependabot alerts enabled, `.github/dependabot.yml` or `renovate.json`,
  scheduled (cron) vulnerability-scan workflows (osv-scanner, trivy, grype, snyk), dependency
  graph enabled.
- Status rules: MET = alerts enabled plus a scheduled scan or Dependabot/Renovate config.
  PARTIAL = one mechanism. NOT_MET = none. UNKNOWN if alert settings could not be read.
- Fix (30 minutes): enable Dependabot alerts and security updates; add a daily osv-scanner or
  trivy workflow.

### P3 · 24-hour initial vulnerability report
- CRA: Art. 14(2) · applies from 11 Sep 2026
- Track: POLICY · Assess via: repo+intake · Gate: yes
- Plain English: when you learn a vulnerability in your product is being actively exploited,
  you must file an initial notification via ENISA's single reporting platform within 24 hours.
- Evidence (repo): incident response / vulnerability handling procedure that names ENISA, the
  24h/72h/14-day timeline, an on-call owner, and the national CSIRT.
- Status rules: MET = written procedure with owner and timeline. PARTIAL = procedure exists but
  does not mention ENISA/CRA timelines. NOT_MET = none.
- Fix (2 hours): write `docs/security/incident-response.md` with the Art. 14 timeline and
  named roles; register on the ENISA platform when available.

### P4 · 72-hour technical report
- CRA: Art. 14(3)
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: within 72 hours, a fuller report to ENISA and the national CSIRT with
  severity, impact and any mitigation.
- Evidence (repo): same procedure as P3, with a 72h report template.
- Status rules: follows P3; MET requires a template or checklist for the 72h report.
- Fix (30 minutes): add a report template section to the incident response doc.

### P5 · Final report within 14 days of remediation
- CRA: Art. 14(4)
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: after the fix or workaround is available, a final report within 14 days.
- Evidence (repo): same procedure, final-report step.
- Status rules: follows P3.
- Fix (15 minutes): add the final-report step to the procedure.

### P6 · Severe incident reporting
- CRA: Art. 14(2)
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: severe incidents affecting the product's security follow the same 24h/72h
  timeline, not only vulnerabilities.
- Evidence (repo): incident response doc covers incidents as well as vulnerabilities.
- Status rules: follows P3; MET requires explicit coverage of incidents.
- Fix (15 minutes): extend the procedure's scope statement.

### P7 · Automatic update for third-party vulnerabilities
- CRA: Art. 14(2)(a)
- Track: AUTO · Assess via: repo · Gate: no
- Plain English: be able to ship a fix for a vulnerable dependency quickly, ideally
  automatically. (Fixing within 24 hours exempts you from reporting, but not from fixing.)
- Evidence (repo): Dependabot security updates or Renovate with automerge for security
  patches, release automation (release-please, semantic-release, goreleaser on tag), evidence of
  regular releases.
- Status rules: MET = automated dependency PRs plus automated release pipeline. PARTIAL = one of
  the two. NOT_MET = manual dependency bumps and manual releases.
- Fix (1–2 hours): enable Dependabot security updates; automate releases from tags.

### P8 · Security updates free of charge
- CRA: Art. 13(9)
- Track: POLICY · Assess via: repo+intake · Gate: yes
- Plain English: security fixes must be free for the whole support period, for every customer.
- Evidence (repo): support policy / terms stating security updates are free; no
  "security patches only on paid tier" language.
- Status rules: MET = stated in support policy or terms. PARTIAL = practice but not stated.
  NOT_MET = security updates gated behind payment.
- Fix (15 minutes): add one sentence to the support policy.

### P9 · Advance notice of End-of-Life
- CRA: Art. 13(8)
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: tell users at least 12 months before the last security update, where feasible.
- Evidence (repo): support policy commits to 12-month notice; deprecation announcements.
- Status rules: MET = commitment documented. PARTIAL = notice practice without commitment.
  NOT_MET = none.
- Fix (15 minutes): add "We will announce end of support at least 12 months in advance" to the
  support policy.

### P10 · Corrective measures for non-compliant products
- CRA: Art. 13(14)
- Track: POLICY · Assess via: repo+intake · Gate: no
- Plain English: if you learn the product is non-compliant, you must fix, withdraw or recall
  it and tell the market surveillance authority. Doing nothing is itself a violation.
- Evidence (repo): incident response / product recall procedure with authority notification step.
- Status rules: MET = procedure covers corrective measures and authority notification.
  PARTIAL = informal. NOT_MET = none.
- Fix (30 minutes): add a "Corrective measures" section to the incident response doc.

---

## Quick index

| ID | Item | Track | Gate | Assess via |
|----|------|-------|------|------------|
| F1 | Documented SDL | POLICY | yes | repo+intake |
| F2 | Evidence of conformity with SDL | POLICY | no | repo+intake |
| F3 | SDL covers secure-by-design/default | POLICY | no | repo+intake |
| F4 | EU Authorised Representative | POLICY | yes* | intake |
| B1 | Product classification | POLICY | yes | intake |
| B2 | Conformity assessment route | POLICY | yes | intake |
| B3 | Risk assessment | POLICY | yes | repo+intake |
| B4 | Threat modelling | POLICY | no | repo+intake |
| B5 | Third-party component policy | POLICY | no | repo+intake |
| B6 | EOL check for tools/dependencies | AUTO | no | repo |
| B7 | Storage encryption feasibility | POLICY | no | intake |
| B8 | Minimal attack-surface design | POLICY | no | repo+intake |
| B9 | Default credential policy | POLICY | yes | repo+intake |
| D1 | Cybersecurity test plan | POLICY | no | repo+intake |
| D2 | Evidence of SDL compliance | AUTO | no | repo |
| D3 | Pen testing / vulnerability assessment | AUTO | yes | repo+intake |
| D4 | Secure update mechanism | AUTO | yes | repo+intake |
| D5 | Data minimisation | POLICY | no | repo+intake |
| R1 | SBOM prepared and screened | AUTO | yes | repo |
| R2 | SBOM machine-readable | AUTO | yes | repo |
| R3 | Inbound connections list | POLICY | no | repo+intake |
| R4 | Outbound connections list | POLICY | no | repo+intake |
| R5 | Declare EOL | POLICY | yes | repo+intake |
| R6 | Conformity assessment completed | POLICY | yes | intake |
| R7 | EU Declaration of Conformity | POLICY | yes | repo+intake |
| R8 | CE marking | POLICY | yes | intake |
| R9 | Technical file | POLICY | yes | repo+intake |
| R10 | 10-year retention | POLICY | no | repo+intake |
| R11 | User-facing documentation | POLICY | yes | repo |
| R12 | Vulnerability disclosure contact | POLICY | yes | repo |
| P1 | Update risk assessment on change | POLICY | no | repo+intake |
| P2 | Automated SBOM vuln monitoring | AUTO | yes | repo |
| P3 | 24h initial report | POLICY | yes | repo+intake |
| P4 | 72h technical report | POLICY | no | repo+intake |
| P5 | Final report 14 days | POLICY | no | repo+intake |
| P6 | Severe incident reporting | POLICY | no | repo+intake |
| P7 | Automatic update for 3rd-party vulns | AUTO | no | repo |
| P8 | Security updates free of charge | POLICY | yes | repo+intake |
| P9 | Advance notice of EOL | POLICY | no | repo+intake |
| P10 | Corrective measures | POLICY | no | repo+intake |

\* F4 is a gate only when the company is not established in the EU.

Totals: 40 items · 8 AUTO · 32 POLICY · 20 gate items.
