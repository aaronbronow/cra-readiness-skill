# CRA background for this skill

Rubric version: **2026.09.1** · Rules last reviewed: 2026-09-03 against the Articles and Annexes of Regulation (EU) 2024/2847

Read this before the first assessment in a session. It is the minimum context needed to
explain results to a founder without over- or under-stating what the CRA requires.

## What the CRA is

Regulation (EU) 2024/2847, the Cyber Resilience Act. It sets mandatory cybersecurity
requirements for "products with digital elements" placed on the EU market: hardware and
software, including the remote data processing they depend on. It entered into force on
10 December 2024.

## Key dates

| Date | What happens |
|------|--------------|
| 10 Dec 2024 | Regulation in force |
| 11 Jun 2026 | Rules on Notified Bodies apply (assessors can be designated) |
| **11 Sep 2026** | **Reporting obligations (Art. 14) apply**: 24h early warning, 72h notification, 14-day final report for actively exploited vulnerabilities and severe incidents |
| **11 Dec 2027** | **Full application.** Products placed on the EU market must meet all requirements and carry CE marking |

Products placed on the market before 11 Dec 2027 are only caught if substantially modified
afterwards, but the reporting duties from 11 Sep 2026 apply to them anyway.

## Who is a manufacturer

Anyone who develops or manufactures a product with digital elements, or has it developed, and
markets it under their own name or trademark, for payment, monetisation or any other
commercial purpose. Startups selling software, devices, apps or SDKs are manufacturers.

This skill targets manufacturers. It does not cover importers, distributors or the lighter
"open-source steward" regime (Art. 24).

## What is out of scope (say this when relevant)

- Non-commercial open-source software (developed and supplied outside a commercial activity).
- Pure SaaS / cloud services that are not "remote data processing" for a product. These are
  governed by NIS2 instead. Where a product needs a cloud back-end to function, that back-end
  is in scope as part of the product.
- Products already covered by sector rules: medical devices, civil aviation, motor vehicles,
  marine equipment, and certain national-security products.

## Product classes

- **Default** – most products. Self-assessment (Module A) is allowed.
- **Important Class I** (Annex III Pt I) – e.g. identity management, browsers, password managers,
  malware detection, VPNs, network management, SIEM, boot managers, PKI, microcontrollers with
  security functions, smart-home security, internet-connected toys, wearables for children.
  Self-assessment allowed only if a harmonised standard is fully applied; otherwise a Notified Body.
- **Important Class II** (Annex III Pt II) – e.g. hypervisors, firewalls/IDS/IPS, tamper-resistant
  microprocessors, industrial IoT. Notified Body required.
- **Critical** (Annex IV) – hardware security modules, smart meter gateways, smart cards and
  secure elements. Notified Body, possibly EU certification.

The skill flags possible Important/Critical features from intake answers but never decides
classification. That is a founder or advisor decision.

## Essential requirements in one paragraph each

**Annex I Part I (product properties)** – designed and delivered with an appropriate level of
security based on a risk assessment; no known exploitable vulnerabilities at release; secure by
default; security updates available (automatic where feasible, with user opt-out); protection
against unauthorised access; confidentiality and integrity of data; data minimisation;
availability and resilience; minimised attack surface; mitigation of exploitation impact;
security logging; and the ability to securely remove data and settings.

**Annex I Part II (vulnerability handling)** – identify and document components (SBOM); address
and remediate vulnerabilities without delay through free security updates; regular security
testing; publish information about fixed vulnerabilities; a coordinated vulnerability disclosure
policy; a contact address for reports; secure and timely distribution of updates.

**Annex II (user information)** – name and contact of the manufacturer; single point of
contact for vulnerabilities; intended purpose and security properties; known circumstances of
risk; where to find the DoC; support period end date; how to install updates securely; how to
securely decommission the product; software identifier for SBOM lookup.

## Reporting (Art. 14) in one paragraph

On becoming aware of an **actively exploited vulnerability** (Art. 3(42): reliable evidence of
exploitation without the owner's permission) or a **severe incident** (criteria in Art. 14(5)),
the manufacturer notifies the coordinating CSIRT and ENISA via the single reporting platform
(Art. 16). Vulnerabilities: early warning within 24 hours; notification within 72 hours; final
report no later than 14 days after a corrective or mitigating measure is available. Incidents:
24 hours; 72 hours; final report **within one month** of the incident notification. Impacted
users must be informed, with mitigations, where appropriate in machine-readable form (Art. 14(8)).
There is no "fix within 24 hours and skip reporting" exemption in the text; the matrix's remark
that a fast fix "exempts reporting" is not supported by Art. 14.

## Support period

Manufacturers determine the support period reflecting expected use time, taking into account
user expectations, the nature of the product, component support periods and the operating
environment; **at least five years** unless the product is expected to be used for less
(Art. 13(8)). The reasoning goes in the technical documentation (Annex VII(4)). Each security
update remains available for at least **10 years after issue or the rest of the support period,
whichever is longer** (Art. 13(9)). The end date (at least month and year) is specified at time
of purchase, and users are notified when end of support is reached where technically feasible
(Art. 13(19)). Security updates are free of charge except by agreement for tailor-made B2B
products (Annex I Pt II(8)). No advance-notice period is prescribed.

## Documentation retention

Technical documentation and the DoC are kept at the disposal of authorities for at least 10
years after placing on the market **or the support period, whichever is longer** (Art. 13(13)).
User information is available for the same period (Art. 13(18)).

## Penalties (for context, not for scaring founders)

Up to EUR 15 million or 2.5% of worldwide annual turnover for breaches of essential
requirements; up to EUR 10 million or 2% for other obligations; up to EUR 5 million or 1% for
incorrect information to authorities. Market surveillance authorities can also order
withdrawal or recall.

## Where the source matrix says more than the regulation

The 40-item matrix at cyberresilienceact.eu is a good lifecycle checklist, but several of its
summaries are stricter than the text. This skill scores the text. Tell founders when they ask.

| Matrix says | Regulation says | Skill treats as |
|-------------|-----------------|-----------------|
| Non-EU manufacturers **must** appoint an EU authorised representative (Art. 19) | Art. 18(1): a manufacturer **may** appoint one | Optional; NA by default; recommended for non-EU |
| Notify users **12 months** before end of support (Art. 13(8)) | Art. 13(19): end date at purchase; notification **when** EOL is reached, where feasible | 12 months = recommended practice |
| Automated SBOM monitoring; **manual monitoring is insufficient** (Art. 14) | Annex I Pt II(1),(3): identify vulnerabilities; regular tests and reviews. No tooling mandated | Automation = recommended practice |
| Corrective measures **and notify market surveillance** (Art. 13(14)) | Art. 13(21): corrective measures, withdraw or recall. Cooperation on request (13(22)). Notify before ceasing operations (13(23)) | Proactive notification = recommended |
| Including a resolved CVE in the SBOM is a **direct violation** | Annex I Pt I(2)(a): no **known exploitable** vulnerabilities | Exploitability matters; VEX is useful |
| Final incident report within **14 days** | Art. 14(4)(c): **one month** after the incident notification (14 days is for vulnerabilities, 14(2)(c)) | One month for incidents |
| Vulnerability contact: Art. 13(5) | Art. 13(17) single point of contact; Annex I Pt II(5),(6); Annex II(2) | Contact **and** CVD policy required |
| Security updates free: Art. 13(9) | Annex I Pt II(8) free of charge; Art. 13(9) is the 10-year availability rule | Both are baseline |
| Retention: "at least 10 years" | Art. 13(13): 10 years **or the support period, whichever is longer** | Longer of the two |
| Storage encryption is "a mandatory requirement" | Annex I Pt I(2)(e): protect confidentiality "such as by encrypting", per the risk assessment | Confidentiality required; encryption is the expected means |
| Fix within 24 hours "exempts reporting, not fixing" | Not in Art. 14 | Report regardless |

Duties in the regulation that the matrix does not list as items: Art. 13(6) report component
vulnerabilities upstream; 13(15)–(16) product identification and manufacturer contact details;
13(20) DoC copy/simplified DoC with the product; 14(8) inform users; Annex I Pt II(2) security
updates separate from feature updates where feasible; Pt II(4) publicly disclose fixed
vulnerabilities; 13(11) warn users of unsupported versions in archives; 13(23) cessation of
operations. The checklist folds each into an existing item.

## Sources to cite in reports

- Regulation text: https://eur-lex.europa.eu/eli/reg/2024/2847/oj
- 40-item manufacturer matrix used by this skill: https://www.cyberresilienceact.eu/compliance-matrix.html
- Reporting explainer: https://www.cyberresilienceact.eu/reporting.html
- OpenSSF Open Source Project Security Baseline (useful control mapping for repos):
  https://baseline.openssf.org/

## Standard disclaimer (include verbatim at the end of every report)

*This is an automated readiness check following the 40-item manufacturer compliance matrix at
cyberresilienceact.eu, graded against the text of Regulation (EU) 2024/2847. Recommended
practices are reported separately and are not legal requirements. It is not legal advice and
does not confirm compliance.*
