# EU Cyber Resilience Act (CRA) Technical File & Declaration

> **Regulation (EU) 2024/2847 Compliance Overview**  
> *This document serves as the foundational Annex VII technical file and governance record for this product.*

---

## 1. Product Classification & Conformity Route (B.1, B.2, R.6)
- **Product Name**: [Insert Product Name]
- **Manufacturer / Legal Entity**: [Insert Company Name, Address, Contact]
- **Non-EU Manufacturer Authorised Representative (if applicable - F.4)**: [Representative Name & EU Address, or "N/A - Established in EU"]
- **CRA Classification**: **Default Product with Digital Elements** (Annex III / IV check: product is not categorized under Important Class I/II or Critical).
- **Conformity Assessment Route**: **Internal Control (Module A - Annex VIII)**. Self-assessment route verified.

---

## 2. Security Development Lifecycle (SDL) & Secure-by-Default (F.1-F.3, B.8, B.9)
- **SDL Policy**: All development follows secure coding practices:
  - Branch protection requiring code review before merge.
  - Automated dependency vulnerability screening in CI (`.github/workflows/cra-ci.yml`).
  - Strict default credential policy: No default passwords or hardcoded API keys; user-configured secrets required on startup.
  - Minimal attack surface: Unused ports, development debug routes, and excessive services disabled in production builds.

---

## 3. Product Support Period & End-of-Life (EOL) (R.5, A.8, A.9)
- **Initial Release Date**: [YYYY-MM-DD]
- **Declared Minimum Support Period**: 5 Years (or until [YYYY-MM-DD]).
- **Security Updates**: Security patches will be delivered free of charge for all active users during this period.
- **EOL Advance Notice**: At least 12 months' prior notification will be communicated before ending security support.

---

## 4. Software Bill of Materials (SBOM) & Dependencies (B.5, R.1, R.2, A.2)
- **Machine-Readable Format**: CycloneDX / SPDX JSON generated automatically on release.
- **Dependency Policy**: Direct and transitive dependencies are scanned continuously for known CVEs. No software is deployed with unmitigated high/critical CVEs.

---

## 5. Technical Documentation & Retention (R.9, R.10)
- All technical documentation, release checksums, SBOM versions, and risk assessments will be retained for at least **10 years** from the date the product is placed on the EU market.
