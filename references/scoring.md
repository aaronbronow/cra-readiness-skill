# Scoring: how the A/B/C/D grade is computed

The grade is mechanical. Fill the status table first, then apply the rules below in order.
Do not adjust the grade based on impression; if the rules give a surprising result, say so in
the report's notes rather than changing the letter.

## Grade meanings (fixed wording, use verbatim in the headline)

| Grade | Headline wording |
|-------|------------------|
| **A** | Ready for EU launch (as far as this assessment can see) |
| **B** | Needs automation work |
| **C** | Needs automation work and policy/document work |
| **D** | Needs automation and policy/document work, and this assessment could not see enough (missing permissions or information) to be sure of anything more |

## Step 1 · Status per item

For each of the 40 items in `checklist.md`, assign exactly one status:

| Status | Meaning |
|--------|---------|
| `MET` | Evidence satisfies the item's MET rule (from repo, or founder attestation for intake items) |
| `PARTIAL` | Evidence satisfies the PARTIAL rule |
| `NOT_MET` | Evidence shows the item is not satisfied, or founder confirms it does not exist |
| `UNKNOWN` | Could not determine: permission denied, file/setting not readable, founder answered "don't know", or the assessment never reached the question |
| `NA` | Item does not apply to this product/company (record the reason) |

Rules for choosing:

1. Repo evidence beats intake answers when they conflict, and the conflict must be reported.
2. A founder's "yes" for an intake-only item counts as `MET` but is labelled
   "based on your answer, not verified" in the report.
3. "Don't know" is always `UNKNOWN`, never `NOT_MET`.
4. Absence of a file in the repo is `NOT_MET` only when the item is `Assess via: repo`.
   For `repo+intake` items, absence in the repo plus no intake answer is `UNKNOWN`.
5. If the repository could not be accessed at all, every `repo` item is `UNKNOWN`.

## Step 2 · Counts

Let `applicable` = all items except `NA`.

- `unknown_count` = number of `UNKNOWN` items among applicable
- `auto_gap` = true if any `AUTO`-track applicable item is `NOT_MET` or `PARTIAL`
- `policy_gap` = true if any `POLICY`-track applicable item is `NOT_MET`, or more than 3
  `POLICY`-track items are `PARTIAL`
- `gate_fail` = true if any gate item is `NOT_MET`, `PARTIAL` or `UNKNOWN`

## Step 3 · Apply rules in order (first match wins)

```
1. If the repository could not be accessed AND fewer than 10 intake answers were given
       -> D  (reason: "insufficient access and information")

2. If unknown_count >= 10  (25% of 40)
       -> D  (reason: "too many items could not be assessed"; list them)

3. If gate_fail is false AND auto_gap is false AND policy_gap is false
       -> A

4. If policy_gap is false AND auto_gap is true
       -> B

5. Otherwise
       -> C
```

Notes on the rules:

- **D is about visibility, not quality.** A D-grade repo may in reality be in good shape; we
  simply could not see. The report must say exactly which permissions or answers would move
  the assessment to a real grade. Rule 1 exists so the founder is never handed a C for a repo
  the agent was not allowed to open.
- **UNKNOWN on a gate item blocks A** (via `gate_fail`) but does not by itself cause D unless
  there are 10 or more unknowns. Between 1 and 9 unknowns the grade is B or C and the report
  lists the unknowns under "What we could not check".
- **Policy-only gaps produce C**, not B. B is reserved for "the paperwork is done, only tooling
  is missing". If the automation track is clean but policy is not, the report says so explicitly
  in the summary ("Automation is in good shape; remaining work is policy and documents").
- **PARTIAL on AUTO items is a gap.** Tooling either runs or it does not; half-configured CI is
  work to do.
- **PARTIAL on POLICY items is tolerated up to 3** because founders often have drafts. A fourth
  partial, or any NOT_MET, makes it a policy gap.

## Step 4 · Confidence label

Add one confidence label to the headline so founders know how much to trust the letter:

| Label | Condition |
|-------|-----------|
| High | unknown_count <= 2 and repo evidence was collected (script or direct inspection) |
| Medium | unknown_count 3–9, or grade relies on 5+ unverified intake answers |
| Low | Grade D, or repo not accessed |

## Step 5 · Progress counters (for the report)

Report, as plain counts, never percentages:

- `X of 40 items met` (count MET plus NA; state NA separately if > 0)
- `Y partial`, `Z not met`, `U could not be checked`

## Worked examples

**Example 1.** All 8 AUTO items MET. Policy: 30 MET (12 attested by founder), 2 PARTIAL
(B4 threat model, R4 outbound list), 0 NOT_MET, 0 UNKNOWN. F4 NA (EU company).
-> gate_fail false, auto_gap false, policy_gap false (only 2 partials) -> **A**, confidence
Medium (12 unverified attestations).

**Example 2.** SBOM missing (R1, R2 NOT_MET), branch protection PARTIAL (D2). Every policy item
MET or attested; 1 PARTIAL. -> policy_gap false, auto_gap true -> **B**.

**Example 3.** Typical startup repo: Dependabot on, CodeQL on, no SBOM, SECURITY.md present with
email, no risk assessment, no incident procedure, founder has not classified the product.
-> policy_gap true -> **C**. Report leads with the three highest-impact policy items plus the
SBOM job.

**Example 4.** Agent had read-only public access; branch protection, Dependabot alerts and
private vulnerability reporting all returned permission errors; founder skipped the intake
("just look at the repo"). Repo items assessable from files: ~14. Intake-only items (F4, B1, B2,
B7, R6, R8) UNKNOWN, plus repo+intake items with no file evidence UNKNOWN. unknown_count = 17
-> **D**, with a list of the exact settings and questions needed to re-grade.

## Tie-breakers and edge cases

- A repo that is a library (no network listener, no auth): R3 may be NA, B9 may be NA. Record
  reasons. The CRA still applies to libraries placed on the market commercially.
- Monorepos: assess the product named by the founder. If workflows live at the root, they count.
- Multiple products in one repo: grade the one the founder names; note the others are unassessed.
- Archived repositories: grade normally but add a warning that an archived repo cannot meet
  ongoing post-release obligations (P-items).
- Non-GitHub hosting (GitLab, Bitbucket): file-based evidence still applies. Settings that
  are GitHub-specific (private vulnerability reporting, Dependabot alerts) map to the host's
  equivalents where they exist; otherwise treat as UNKNOWN and say why.
