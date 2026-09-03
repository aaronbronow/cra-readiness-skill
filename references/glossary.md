# Glossary (one line each, for use inside reports)

Use these definitions the first time a term appears in a report. Keep the wording.

- **CRA** – The EU Cyber Resilience Act, Regulation (EU) 2024/2847: security rules for any
  product with software or connectivity sold in the EU.
- **Manufacturer** – Under the CRA, whoever develops or has developed a product and places it
  on the EU market under their own name. That is you, the startup.
- **Product with digital elements** – Any software or hardware product, including its remote
  processing, that connects to a device or network. Pure SaaS is generally excluded.
- **Default / Important / Critical** – CRA product classes. Default products self-assess;
  Important and Critical products usually need an outside assessor (Notified Body).
- **Notified Body** – An organisation officially designated by an EU member state to assess
  products against the CRA. Booking one can take months.
- **Conformity assessment** – The procedure that checks the product meets the CRA. "Module A" is
  the self-assessment route for Default products.
- **Declaration of Conformity (DoC)** – The signed document in which you state the product
  complies with the CRA. Template is CRA Annex V.
- **CE marking** – The "CE" mark showing a product meets EU rules. From 11 December 2027 it is
  required to sell in-scope products in the EU.
- **Technical file / technical documentation** – The bundle of evidence (risk assessment,
  test results, SBOM, DoC, etc.) that authorities can ask to see. Contents are in CRA Annex VII.
- **SDL (Security Development Lifecycle)** – Your written process for building software securely:
  what security steps happen at each stage and who owns them.
- **Risk assessment** – A written analysis of what could go wrong with the product's security,
  how likely it is, how bad it would be, and what you do about it.
- **Threat model** – A structured exercise identifying how an attacker could get in and what
  defences that implies. STRIDE is a common method.
- **SBOM (Software Bill of Materials)** – A machine-readable list of every component in your
  software, like an ingredients label.
- **SPDX / CycloneDX** – The two standard file formats for an SBOM. A PDF or spreadsheet does not
  count.
- **Dependency** – A third-party library or package your code relies on.
- **Lockfile** – A file that pins exact dependency versions (e.g. `package-lock.json`,
  `poetry.lock`), so builds are reproducible and scannable.
- **EOL (End-of-Life)** – The date after which a product or component no longer gets security
  fixes. The CRA requires you to declare yours (minimum 5 years unless the product's expected
  lifetime is shorter).
- **Support period** – The time during which you commit to providing free security updates.
- **Vulnerability** – A weakness in software that an attacker could exploit.
- **Actively exploited vulnerability** – One that attackers are known to be using right now. This
  triggers the 24-hour reporting duty.
- **Coordinated vulnerability disclosure (CVD)** – A published process letting researchers
  report vulnerabilities to you privately so you can fix them before details go public.
- **SECURITY.md** – The standard file in a repository explaining how to report a vulnerability.
- **Private vulnerability reporting** – A GitHub setting that lets anyone report a vulnerability
  to you confidentially from the repository page.
- **ENISA** – The EU Agency for Cybersecurity. It runs the single reporting platform where
  manufacturers file vulnerability and incident reports.
- **CSIRT** – A national Computer Security Incident Response Team. Reports to ENISA are also
  routed to your national CSIRT.
- **SAST** – Static application security testing: tools that scan your source code for security
  bugs (e.g. CodeQL, Semgrep).
- **Secret scanning** – Tools that detect passwords and API keys accidentally committed to the
  repository.
- **Penetration test (pentest)** – A human-led attempt to break into the product, usually by a
  specialist firm, producing a report of findings.
- **Branch protection / rulesets** – Repository settings that require reviews and passing checks
  before code reaches the main branch.
- **Signed release / provenance / attestation** – Cryptographic proof of who built a release and
  from which source, so customers can verify it is genuine. Tools: Sigstore, cosign, SLSA,
  GitHub artifact attestations.
- **Dependabot / Renovate** – Bots that watch your dependencies for vulnerabilities and open
  pull requests to update them.
- **CI (continuous integration)** – Automated jobs (e.g. GitHub Actions) that run tests and
  checks whenever code changes.
- **Attack surface** – Everything an attacker could reach: open ports, APIs, login screens,
  file parsers. Smaller is safer.
- **Secure by default** – The product is safe as shipped, without the customer having to change
  settings.
- **Data minimisation** – Collecting and storing only the data the product needs.
- **Authorised representative** – An EU-based person or company a manufacturer *may* appoint,
  by written mandate, to deal with EU authorities (CRA Art. 18). Optional under the CRA.
- **Baseline vs. beyond the letter** – In this skill, "baseline" is what the CRA text requires
  and is what the grade measures; "beyond the letter" is recommended practice from sources such
  as OpenSSF Scorecard, the OSPS Baseline, NIST SSDF or ETSI EN 303 645, reported but not graded.
- **Market surveillance authority** – The national body that checks products on the market comply
  and can order withdrawals or recalls.
