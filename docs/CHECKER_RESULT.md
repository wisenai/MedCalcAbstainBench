# The deterministic checker: the number, extracted

**Task owner:** Annotator D — mentor revision 2, "you say arithmetic alone solves families A and B,
can you write the checker and give me that number? No model calls needed."

The checker was already written. `checker.py` (387 lines) recomputes every stated derived value
from its own components and asserts systolic > diastolic. `checker_boundary.py` runs it across all
676 built conditions and writes `docs/CHECKER_BOUNDARY.md`. No model, no prompt, no API key,
reproducible in seconds. This file extracts the answer to the question asked.

```
python3 checker_boundary.py
```

---

## The number

**Family A: 35/35. Family B: 60/60. Both exactly 100%.**

| family | condition | caught | rate |
|---|---|---|---|
| A — stated derived value vs its own components | contradiction | 35/35 | 100.0% [90.1% – 100.0%] |
| B — systolic below diastolic | contradiction | 60/60 | 100.0% [94.0% – 100.0%] |
| C — criterion asserted then denied | contradiction | 0/30 | 0.0% [0.0% – 11.4%] |
| breadth | contradiction | 0/67 | 0.0% [0.0% – 5.4%] |
| dissociation | value_conflict | 0/40 | 0.0% [0.0% – 8.8%] |

Across all 232 contradiction conditions the checker catches 95.

**False positives on clean notes: 0/202 (0.0% [0.0% – 1.9%]).** It never fires on a note that is
not broken, so this upper bound is free rather than bought with false alarms.

The paper currently says arithmetic recovers the two numeric families "almost completely." That
understates it. The correct claim is 100% on both, with no false positives.

---

## The two zeros are not the same kind of zero

Reporting a single figure — the checker misses 137 of 232 — would overstate our own limit in the
direction that flatters the paper. Two different things are happening.

**30 items are structurally invisible.** Family C asserts a criterion and later denies it: "history
of diabetes ... no history of diabetes." No number disagrees with another number, so no arithmetic
exists to run. No version of this tool, however good, could catch these. This is the real boundary,
and it is where a language model is genuinely required.

**107 items are missed for an implementation reason.** The dissociation and breadth arms state two
values for one input, as in `creatinine 1.4 and 3.64 mg/dL`. `checker.py` reads quantities with
label-anchored patterns, so the second value falls outside the match. A duplicate-value detector
would catch all 107, and the change is local to `read()`.

So the honest claim is narrower than "the checker cannot reach these":

> Arithmetic alone already solves Families A and B. A modestly better arithmetic tool would also
> solve the dissociation and breadth arms. Family C, 30 items, is the only part of this corpus
> where a language model is not merely convenient but necessary.

---

## The cost side, which belongs in the same sentence

The checker fires on **65/202 resolvable notes** — every Family A and Family B resolvable item.

A resolvable item is the contradictory note plus a cue *in the question* naming which value
governs. The checker reads notes only and never sees the question, so a pipeline gated on it would
refuse notes that are perfectly answerable. Anyone quoting the 100% should quote this alongside it.

| family | fires on resolvable |
|---|---|
| A | 35/35 |
| B | 30/30 |
| C | 0/30 |
| breadth | 0/67 |
| dissociation | 0/40 |

---

## For the paper

One sentence, replacing "almost completely":

> A deterministic checker that recomputes stated derived values and compares systolic against
> diastolic catches 35/35 of Family A and 60/60 of Family B with no false positives on clean notes,
> and 0/30 of Family C, where no arithmetic exists to run.

Full detail, including why the other zeros differ, is in `docs/CHECKER_BOUNDARY.md`.

**Note on reproducing.** Re-running `checker_boundary.py` on a machine without the statistics
dependency regenerates the tables without their confidence intervals. The counts are unaffected.
Check `requirements.txt` is satisfied before regenerating.
