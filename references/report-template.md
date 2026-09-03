# Report template

Produce the report in exactly this order and with these headings. Keep sentences short.
No jargon without a one-line explanation (see `glossary.md`). No percentages.
Every repo-based finding must name the file, workflow, release or setting it came from.

---

```markdown
# CRA Readiness: <owner/repo>

**Grade: <A|B|C|D> – <fixed headline wording from scoring.md>**
Confidence: <High|Medium|Low> · Assessed <YYYY-MM-DD> · Checklist version <from cra-background.md>

<Two or three sentences in plain English: what the grade means for this founder, the single
biggest reason for the grade, and how far they are from the next grade up.>

## At a glance

| | Count |
|---|---|
| Items met | X of 40 (N not applicable) |
| Partially met | Y |
| Not met | Z |
| Could not check | U |

Automation & tooling: <n met / 8> · Policy, design & documents: <n met / 32>

## Do these next

<Exactly three items, ordered by impact on the grade then by effort. For each:>

1. **<Item plain-English name> (<ID>)** – <why it matters in one sentence>.
   *What to do:* <concrete steps from checklist.md, adapted to what was seen in the repo>.
   *Effort:* <estimate>. *Track:* <Automation | Policy/documents>.

2. ...

3. ...

## Deadlines that matter

- 11 September 2026: vulnerability and incident reporting duties (Art. 14) apply. <one line on
  whether P2/P3 are met>
- 11 December 2027: full CRA application; CE marking required to sell in the EU. <one line on
  R6–R9 status>

## Full checklist

### Stage 1 · Company foundations
| ID | Item | Status | Evidence / reason |
|----|------|--------|-------------------|
| F1 | Documented SDL | MET | `docs/security/sdl.md` |
| ... | | | |

### Stage 2 · Before development
...

### Stage 3 · During development
...

### Stage 4 · Before release
...

### Stage 5 · After release
...

<Status column uses the words: Met · Partial · Not met · Could not check · N/A.
Evidence column: file path, workflow name, setting name, release tag, or
"Your answer (not verified)", or "Permission denied: <setting>", or "No file found".>

## What this assessment could not check

<Bullet list of every UNKNOWN item with the exact reason and what would resolve it, e.g.:>
- Branch protection (D2): token lacks admin permission on the repository. Re-run with an admin
  token, or check Settings > Branches and tell me what is there.
- Product classification (B1): question skipped.

<If grade is D, also add:> To get a real grade, provide: <the shortest list of permissions or
answers that would bring "could not check" below 10>.

## Things a repository cannot show

The CRA is mostly about your company's process, not your code. Even an A here does not mean you
are compliant. Items that always need a human decision or a document outside the repo:
conformity assessment and Declaration of Conformity (R6, R7), CE marking (R8), product
classification (B1, B2), and whether your risk assessment actually reflects the product.
Consider a conversation with a compliance advisor or Notified Body before launch.

## Notes and discrepancies

<Optional. Conflicts between answers and repo evidence; items marked N/A and why; anything
the rules produced that seems surprising.>

---
*This is an automated readiness check against the 40-item manufacturer compliance matrix at
cyberresilienceact.eu, based on Regulation (EU) 2024/2847. It is not legal advice and does not
confirm compliance. Checklist version <x>, rules last reviewed <date>.*
```

---

## Writing rules

- Lead with the grade and the reason. Founders read the first five lines.
- "Do these next" is always exactly three items. Prefer gate items, then items that flip the
  grade, then cheapest wins. If the grade is D, the three items are the access/answers needed.
- Use "you/your" for the founder, "the product" for the software, "the repo" for the repository.
- Do not praise. State what is present, what is missing, what to do.
- Do not invent evidence. If the collector output or your inspection did not show it, it is
  Not met or Could not check.
- When repo evidence and an intake answer disagree, say so in the Evidence column and again
  under Notes.
