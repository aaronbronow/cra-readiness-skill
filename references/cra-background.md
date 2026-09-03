# CRA background for this skill

Checklist version: **2026.09** · Rules last reviewed: 2026-09-03

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

On becoming aware of an actively exploited vulnerability in the product, or a severe incident
affecting its security, the manufacturer notifies via ENISA's single reporting platform: an
early warning within 24 hours; a fuller notification within 72 hours (nature, severity,
mitigation); a final report within 14 days after a fix is available (or one month after the
incident notification for incidents). Users must also be informed and given mitigations. A
fix applied within the 24-hour window does not remove the obligation to report unless the
vulnerability was never exploitable in the field; treat the exemption as narrow.

## Support period

Manufacturers determine and declare the support period, reflecting expected use time and
"at least five years" unless the product is expected to be in use for a shorter time. Security
updates must remain available for at least 10 years after issue or the rest of the support
period, whichever is shorter. Users must be told the end date at purchase and at least 12
months before the last update where feasible.

## Documentation retention

Technical documentation and the DoC are kept for at least 10 years after the product is placed
on the market, or for the support period if longer.

## Penalties (for context, not for scaring founders)

Up to EUR 15 million or 2.5% of worldwide annual turnover for breaches of essential
requirements; up to EUR 10 million or 2% for other obligations; up to EUR 5 million or 1% for
incorrect information to authorities. Market surveillance authorities can also order
withdrawal or recall.

## Sources to cite in reports

- Regulation text: https://eur-lex.europa.eu/eli/reg/2024/2847/oj
- 40-item manufacturer matrix used by this skill: https://www.cyberresilienceact.eu/compliance-matrix.html
- Reporting explainer: https://www.cyberresilienceact.eu/reporting.html
- OpenSSF Open Source Project Security Baseline (useful control mapping for repos):
  https://baseline.openssf.org/

## Standard disclaimer (include verbatim at the end of every report)

*This is an automated readiness check against the 40-item manufacturer compliance matrix at
cyberresilienceact.eu, based on Regulation (EU) 2024/2847. It is not legal advice and does not
confirm compliance.*
