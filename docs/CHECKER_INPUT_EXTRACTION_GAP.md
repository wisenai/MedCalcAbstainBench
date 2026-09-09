# Checker input: height and weight it cannot read

**For:** a contributor, who runs the deterministic checker and reports its catch rate.
**From:** a contributor. This is a finding, not a change — `checker.py` is untouched.

Building Family A meant screening notes on whether `checker.py` can read the
components out of the note text. It measured the checker's extraction as a side
effect, and the number is worth having before 's sweep.

## The number

Of **480** notes that state exactly one BMI and have a height and weight recorded
in MedCalc's entities, **169 (35%) are ones the checker cannot fully parse**:

| Missing | Notes |
|---|---|
| `height_cm` only | 70 |
| `weight_kg` only | 35 |
| both | 64 |
| **total** | **169 of 480** |

Those 169 are excluded from Family A, because an item the checker cannot catch
would make the family's own claim false. That keeps Family A honest. It does not
fix the measurement problem, which is yours.

## Why it matters to your clause

Your clause is to run the checker across the whole contradiction set and
*"expect near-perfect on A and B and structurally zero on C, and state that
boundary as our own limit rather than letting a reviewer find it."*

The boundary you report is currently **two things at once**: what is closed under
arithmetic, and what this particular extractor happens to parse. Family A is
closed under arithmetic in all 480 of those notes. The checker reaches 311 of
them. A reviewer who reads `checker.py` will see that the 35% gap is an extraction
limitation rather than a structural one, and the paper is stronger if we say so
first.

## The specific shapes it misses

The patterns require the label before the number, or the number followed by
`tall`:

```
weight_kg (?:body )?weigh(?:t|ed|s|ing)\b[^.\n\d]{0,25}?NUM\s{0,3}kg\b(?!\s*/)
height_cm (?:height|stature)\b[^.\n\d]{0,25}?NUM\s{0,3}cm\b
height_cm_tall NUM\s{0,3}cm[^.\n]{0,20}?\btall\b
```

Real notes it reads correctly:

- `She is 160 cm tall and weighs 104 kg` — both
- `Her weight was 99 kg and her height was 179 cm` — both
- `Height 179 cm, weight 99 kg` — both

Real note it does not:

- **`He weighs 106 kg and is 168 cm in height`** — weight yes, height no. The
 number precedes the label (`168 cm in height`), which neither height pattern
 allows: the first wants `height … 168 cm`, the second wants `168 cm … tall`.

That single shape — measurement first, label second — is the bulk of the gap.

---

# Update, 2026-08-19: I did change one thing, and here is exactly what it moved

The breadth clause needed serum osmolality, and `checker.py` had no rule for it.
Rather than assume the instrument was untouchable, I measured what adding one
would do **before committing it**, over all **454 distinct notes** in the corpus
your figures come from.

**Three notes change, each from no finding to one.** All three are the same item:

> `Osmolality-421` — `family: A`, `probe: contradiction`, `gold_answer: ABSTAIN`
> `The calculated serum osmolality is reported as 233 mOsm/kg`, against a
> recomputation of **424.28**

So this is **not a new false-positive surface**. It is three injected
contradictions the checker was blind to, and your Family A catch rate goes **up**
by three, and becomes more accurate. Nothing else in the corpus moves.

`check_osmolality` is now in `DERIVED`, with two exclusions so it does not
manufacture findings: a **measured** osmolality differing from the calculated one
is an osmolal gap — a real clinical finding in toxic alcohol ingestion, not an
arithmetic error — and **urine** osmolality is a different quantity entirely. Four
tests pin both.

**What you need to do:** if you have already run the checker sweep, re-run it, and
report the Family A number from the new version. If you have not, nothing changes
for you. Either way the +3 should be in the write-up rather than left as an
unexplained difference between two runs.

My earlier blanket position — don't touch the instrument — was too coarse. The
right test is whether a change moves a number already reported, and that is
measurable rather than a matter of principle. The height/weight gap below is still
untouched, because widening *that* would change catch rates on items you have
already measured.

---

## What I did not do, and why

I did not widen the patterns. **Your catch-rate figures (A 46%, B 90%,
C 0%, FP 0) were measured with the checker as it stands**, and changing the
instrument now would make those non-comparable to the numbers without
anyone noticing which run used which version. Moving a measuring instrument
mid-study is worse than a known gap in it.

## Suggested options, in the order I would consider them

1. **Report the gap and leave the code alone.** One sentence in the limitations:
 the checker's catch rate is a lower bound on what arithmetic can reach, with
 the 169/480 measurement behind it. Costs nothing, and it is honest.
2. **Widen the height pattern and re-run everything**, included, so both
 weeks are measured with the same instrument. A `NUM cm ... in height` variant
 mirroring the existing `tall` one is a small change; re-running is the real
 cost. Worth it if the A-family catch rate is going in a headline table.
3. **Report both**, as caught/parseable and caught/all — the same shape as your
 existing `caught/runnable` and `caught/all` columns, which already make exactly
 this distinction for a different reason. This is probably the best fit: your
 table is already built to carry it.

Whichever you choose, Family A's 30 items all trip the checker today, so nothing
in my build depends on the outcome.
