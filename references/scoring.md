# Scoring: how the A/B/C/D grade is computed — rubric 2026.09.1

The grade is mechanical and is computed **only from the CRA baseline layer** of each item in
`checklist.md`. The "Beyond the letter" layer is reported alongside the grade and never changes it.
Fill the status table first, then apply the rules in order. If a rule produces a surprising
result, say so under Notes rather than changing the letter.

## Grade meanings (fixed wording, use verbatim in the headline)

| Grade | Headline wording |
|-------|------------------|
| **A** | Ready for EU launch (as far as this assessment can see) |
| **B** | Needs automation work |
| **C** | Needs automation work and policy/document work |
| **D** | Needs automation and policy/document work, and this assessment could not see enough (missing permissions or information) to be sure of anything more |

## Step 1 · Baseline status per item

For each of the 40 items assign exactly one status **against the item's Baseline rule**:

| Status | Meaning |
|--------|---------|
| `MET` | Baseline satisfied (repo evidence, or founder attestation for intake items) |
| `PARTIAL` | Baseline PARTIAL rule matches |
| `NOT_MET` | Baseline not satisfied, or founder confirms it does not exist |
| `UNKNOWN` | Could not determine: permission denied, not readable, "don't know", never asked |
| `NA` | Item does not apply (record why). F4 is NA by default (Art. 18: optional). |

Rules:

1. A documented manual process that meets the letter is MET. Do not downgrade an item because
   it lacks tooling; tooling belongs to the "Beyond the letter" layer.
2. Repo evidence beats intake answers when they conflict; report the conflict.
3. A founder's "yes" for an intake item is MET, labelled "based on your answer, not verified".
4. "Don't know" is UNKNOWN, never NOT_MET.
5. Absence of a file is NOT_MET only for `Assess via: repo` items. For `repo+intake` items,
   absence plus no answer is UNKNOWN.
6. If the repository could not be accessed, every `repo` item is UNKNOWN.

## Step 2 · Counts

Let `applicable` = all items except `NA`.

- `unknown_count` = UNKNOWN items among applicable
- `auto_gap` = any `AUTO`-track applicable item is NOT_MET or PARTIAL
- `policy_gap` = any `POLICY`-track applicable item is NOT_MET, or more than 3 `POLICY` items are PARTIAL
- `gate_fail` = any gate item is NOT_MET, PARTIAL or UNKNOWN

AUTO items (7): D2, D3, D4, R1, R2, P2, P7. Everything else is POLICY.
Gate items (19): F1, B1, B2, B3, B9, D3, D4, R1, R2, R5, R6, R7, R8, R9, R11, R12, P2, P3, P8.

## Step 3 · Apply rules in order (first match wins)

```
1. Repository not accessed AND fewer than 10 intake answers given      -> D  ("insufficient access and information")
2. unknown_count >= 10                                                  -> D  ("too many items could not be assessed"; list them)
3. gate_fail false AND auto_gap false AND policy_gap false               -> A
4. policy_gap false AND auto_gap true                                    -> B
5. otherwise                                                             -> C
```

Notes:

- **D is about visibility, not quality.** The report must list exactly which permissions or
  answers would produce a real grade.
- **UNKNOWN on a gate item blocks A** but does not cause D unless there are 10+ unknowns.
- **Policy-only gaps produce C**, not B. B means "the paperwork is done, only tooling is missing".
  When the automation track is clean, the summary says so explicitly.
- **PARTIAL on AUTO items is a gap.** Half-configured pipelines are work to do.
- **PARTIAL on POLICY items is tolerated up to 3.** Founders often have drafts.

## Step 4 · Beyond-the-letter layer (reported, not scored)

For each item, the checklist lists recommended practices with a source tag. Record each as
`adopted`, `not adopted`, or `unknown`. Report:

- `Beyond the letter: X of Y recommended practices adopted` (count only those assessable).
- The three highest-value practices not yet adopted, chosen by: (1) practices that would make a
  currently PARTIAL baseline item easier to evidence, (2) practices a customer security
  questionnaire will ask about (SBOM in CI, signed releases, branch protection, SAST), (3) cheapest.

Never phrase a practice as a legal requirement. Use "recommended" or "customers will expect",
and keep the source tag visible so the founder can see where the expectation comes from.

## Step 5 · Confidence label

| Label | Condition |
|-------|-----------|
| High | unknown_count <= 2 and repo evidence was collected |
| Medium | unknown_count 3–9, or the grade relies on 5+ unverified intake answers |
| Low | Grade D, or repository not accessed |

## Step 6 · Progress counters

Plain counts, never percentages: `X of 40 items met (N not applicable)`, `Y partial`,
`Z not met`, `U could not be checked`.

## Worked examples

**Example 1 — solo founder, documented manual processes.** No branch protection, no required
reviews, CI runs on every PR (D2 MET at baseline). Weekly manual `pip-audit` recorded in a log
(P2 MET). SBOM produced by hand with `syft` at each release and kept with the release, plus a
recorded scan (R1/R2 MET). Signed releases with install docs (D4 MET). CodeQL on PRs (D3 MET).
Release-from-tag script and GitHub advisories used (P7 MET). All POLICY documents present; F4 NA.
-> **A**. Beyond the letter: 9 of 22 practices adopted; suggestions: branch protection, SBOM in
CI, Dependabot alerts.

**Example 2.** Same as Example 1 but no SBOM at all (R1, R2 NOT_MET). -> auto_gap true, policy
clean -> **B**.

**Example 3 — typical startup.** Dependabot on, CodeQL on, unsigned releases (D4 PARTIAL), no
SBOM (R1/R2 NOT_MET), SECURITY.md with contact but no CVD policy (R12 PARTIAL), no risk
assessment, no incident procedure, classification undecided. -> **C**.

**Example 4 — read-only access, intake skipped.** Admin-only settings unreadable, 17 unknowns.
-> **D**, with the list of settings and questions that would re-grade it.

## Edge cases

- Libraries/SDKs: R3 NA (no listeners), B9 NA (no authentication); Annex II(8)(f) integrator
  information applies to R11.
- Monorepos / multiple products: grade the product the founder names; note the rest unassessed.
- Archived repositories: grade normally; warn that post-release obligations (P-items) cannot be met.
- Non-GitHub hosting: file evidence applies; platform-specific practices are "unknown" with a reason.
- Tailor-made B2B products: Pt I(2)(b) secure-by-default and Pt II(8) free updates may be varied
  by agreement; record the agreement as evidence.
