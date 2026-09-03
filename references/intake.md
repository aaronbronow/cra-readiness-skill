# Intake questionnaire

Ask these in two short batches. Use plain language, one question per line, and tell the
founder that "don't know" and "skip" are valid answers. Never ask all questions at once.
If the founder says "just look at the repo", ask only Batch 0 and proceed; every intake-only
item then becomes UNKNOWN and the report explains what that costs them.

Record every answer with the item IDs it feeds. Answers are attestations, not evidence:
the report labels them "based on your answer, not verified".

---

## Batch 0 · Access (always ask)

**Q0.1** Where is the code? Give me a GitHub URL (`https://github.com/org/repo`) or, if we are
working inside the project already, say "here".

**Q0.2** How would you like me to gather evidence? Pick one:
  1. **Run the collector script** – I run a small script (Python 3, no dependencies) that reads
     the repository and, if a GitHub token is available, a few repository settings. It only
     talks to GitHub and prints a report locally; nothing is uploaded anywhere.
  2. **Let me read the files myself** – I inspect files and, where I can, fetch public GitHub
     data. No script.
  3. **No tool access** – you paste the contents of a few files when I ask, and answer questions.

Explain the trade-off in one sentence: options 1 and 2 give a more reliable grade; option 3
usually leads to more "could not check" items.

---

## Batch 1 · Scope (5 questions) → feeds F4, B1, B2, B7, R3

**Q1.1** Do you sell, license, or otherwise make money from this product in the EU, or plan to?
(yes / no / not sure)
> If **no**: say the CRA mainly applies to products made available commercially; a purely
> non-commercial open-source project is largely out of scope. Offer to continue anyway as a
> readiness exercise.

**Q1.2** What is the product, in one sentence, and how do customers get it?
Choose the closest: installable software / library or SDK / firmware or device / mobile app /
hosted service only (SaaS) / mix.
> If **hosted service only**: explain that pure SaaS is generally outside the CRA (it falls under
> NIS2 instead) unless it is "remote data processing" that a product needs in order to work.
> Offer to continue.
> If **library or SDK**: R3 (inbound connections) and B9 (default credentials) may be NA.

**Q1.3** Is your company legally established in the EU? (yes / no / not sure) → F4, P3 (which CSIRT)
> If **no**: Have you appointed an EU authorised representative by written mandate? (yes / no /
> don't know). Say plainly: the CRA makes this **optional** (Art. 18), but it is recommended for
> non-EU companies because it decides which national CSIRT you report to and who holds your
> documents in the EU.

**Q1.4** Does the product do any of the following? Tick all that apply. → B1, B2
  - manage passwords or identities, or handle login for other systems
  - act as a VPN, firewall, intrusion detection, or network security tool
  - be a browser, operating system, hypervisor, or boot loader
  - manage or configure networks, routers, or industrial systems
  - be a smart-home security device (locks, cameras, alarms), a toy, or a wearable for children
  - be a microcontroller, microprocessor, smart card, or secure element
  - none of these
> Any tick other than "none" means the product is probably **Important** or **Critical** under
> Annex III/IV and likely needs a Notified Body. Flag this prominently; do not decide it for them.

**Q1.5** Have you already decided your product's CRA classification (Default / Important /
Critical) and how you will assess conformity (self-assessment or a Notified Body)?
(yes, written down / yes, in our heads / no / don't know) → B1, B2

**Q1.6** Does the product store customer data, and is that data encrypted at rest?
(no data stored / yes, encrypted / yes, not encrypted / don't know) → B7

---

## Batch 2 · Documents and decisions (up to 8 questions) → policy items

Preface: "These may live outside the repo (Notion, Google Drive, a lawyer's inbox). That's
fine; I just need to know they exist."

**Q2.1** Do you have a written description of how your team builds software securely (an SDL
or secure development policy)? (yes / partly / no / don't know) → F1, F2, F3

**Q2.2** Do you have a written cybersecurity risk assessment for this product? (yes, kept up to
date / yes, but old / no / don't know) → B3, P1

**Q2.3** Have you done a threat model (a structured "how would an attacker get in" exercise)?
(yes, documented / done informally / no / don't know) → B4

**Q2.4** How is the product's security tested, and how often? (automated scans on every change /
a recurring manual review / a one-off test / not at all / don't know) → D1, D3
> Follow-up, recorded as a *recommended practice*, not a requirement: has there been an
> independent penetration test in the last 12 months? (yes / no / don't know)

**Q2.5** Have you decided how long you will provide free security updates, and written it down
anywhere customers can see? (yes, with dates / decided but not published / no / don't know)
→ R5, P8, P9

**Q2.6** Do you have a written incident response procedure that says who does what when a
vulnerability is found, including notifying ENISA within 24 hours and informing affected users?
(yes, mentions ENISA / yes, but no ENISA step / no / don't know) → P3, P4, P5, P6, P10
> If yes: does it also cover what happens if the company shuts down (Art. 13(23))? → P10

**Q2.7** Have you started any of these formal steps? Tick all that apply. → R6, R7, R8, R9, R10
  - conformity assessment (self-assessment or with a Notified Body)
  - EU Declaration of Conformity drafted or signed
  - CE marking placement decided
  - technical file compiled (one bundle of all the documents)
  - 10-year document retention plan
  - none yet

**Q2.8** Do you have written lists of (a) the ports/interfaces the product listens on and
(b) the external services it talks to? (both / one / neither / don't know) → R3, R4

**Q2.9** Do you have a written policy for choosing and approving third-party and open-source
components? (yes / informal / no / don't know) → B5

**Q2.10** Is telemetry or usage data collection documented, and is it off or opt-in by default?
(no telemetry / documented and opt-in / on by default / don't know) → D5

---

## Mapping answers to statuses

| Answer style | Status |
|--------------|--------|
| "yes" / "yes, written down" / "yes, with dates" / "yes, mentions ENISA" | MET (attested) |
| "partly" / "in our heads" / "decided but not published" / "informal" / "yes, but old" / "yes, but no ENISA step" / "more than 12 months ago" | PARTIAL |
| "no" / "none yet" / "on by default" (D5) / "yes, not encrypted" (B7) | NOT_MET |
| "don't know" / "not sure" / skipped | UNKNOWN |
| Q1.2 = library/SDK for R3, B9; Q1.6 = no data for B7; Q2.10 = no telemetry for D5; F4 always unless a representative was appointed (then MET, informational) | NA (record reason) |

If a repo file contradicts an answer (e.g. founder says "no SDL" but `docs/security/sdl.md`
exists, or founder says "yes" but nothing is found for a `repo` item), prefer the repo evidence
and note the discrepancy in the report.
