# Extraction audit: are MedCalc-Bench's extracted values in the notes?


_Generated 2026-08-16T23:27:29Z over 1047 published notes. Regenerate with `python3 audit/extraction_audit.py`._

## Why this exists

[`LABEL_AUDIT.md`](LABEL_AUDIT.md) reports 0% mismatch between the shipped labels and the shipped code. That number is worth less than it looks: those labels were *generated* by that code, and 535 of 586 shipped explanations are byte-identical to what the implementations emit today. It compares the code's output to the code's own output, and takes `Relevant Entities` on trust.

So it cannot see the error that matters most to us. If the wrong creatinine was pulled out of a note, the label reproduces the wrong answer faithfully and the audit reports agreement. This looks the other way: from the note to the extracted value.

## Result

| Outcome | Count |
|---|---|
| `verified` — label, value and unit anchored in one phrase, uniquely | 576 |
| `verified_ordinal` — matched in a paired `X/Y` or `respectively` construction, position confirmed | 7 |
| `verified_no_unit` — value attached to the label; the note states no unit | 6 |
| `ambiguous` — several candidate values for this label — extraction chose | 2 |
| `value_present_unlabelled` — the number is in the note, but no construction we recognise ties it to this label | 49 |
| `value_missing_entirely` — **the number does not appear in the note at all** | 3 |
| `unsupported_unit` — no locator for the unit — out of scope | 22 |

**589 of 643 scoreable extractions are positively confirmed against the note; 3 could not be found in it at all, and every one of those was read by hand.** `unsupported_unit` is excluded from the denominator because it measures our coverage, not MedCalc's extraction.

### By quantity

| Quantity | verified | verified ordinal | verified no unit | ambiguous | value present unlabelled | value missing entirely |
|---|---|---|---|---|---|---|
| age | 308 | 0 | 1 | 1 | 2 | 2 |
| creatinine | 94 | 3 | 4 | 1 | 7 | 0 |
| height | 78 | 2 | 0 | 0 | 24 | 0 |
| weight | 96 | 2 | 1 | 0 | 16 | 1 |

## The strong candidates, and what reading them showed

A number that is nowhere in the note is the one outcome that cannot be explained by our locator being fussy. These are the cases worth reading, and all of them were read.

**`pmc-3893835-1`** · Maintenance Fluids Calculations · weight extracted as 7 kg  
NOT an extraction error. The note says 'weight loss of seven kilos'. MedCalc read the spelled-out numeral; we only match digits.

**`pmc-2633322-1`** · Free Water Deficit · age extracted as 50 years  
NOT an extraction error. The note opens 'A fifty-year-old male'. Spelled-out numeral again.

**`pmc-2988179-1`** · CURB-65 Score for Pneumonia Severity · age extracted as 50 years  
NOT an extraction error. The note opens 'A fifty-year-old, non diabetic, hypertensive, smoker male'. Spelled-out numeral again.

**Confirmed extraction errors: 0.** All three are numerals spelled as words — *seven kilos*, *a fifty-year-old male* — which MedCalc converted correctly and we do not match. Handling spelled-out numbers is the obvious next increment and is not done here.

## What the earlier version got wrong

A first pass anchored values the way `construct.py` does — label to value across a gap containing no digits — and reported three candidate errors. All three were our own limitation, and the extended constructions added here now resolve them automatically, independently reaching the same verdicts the hand reading did:

- `pmc-4421172-1` — *'urea nitrogen and creatinine, 18.9 mmol/L and 366 umol/L, respectively'* → now `verified_ordinal`
- `pmc-6051943-1` — *'blood urea nitrogen/creatinine were 21.9/1.98mg/dL'* → now `verified_ordinal`
- `pmc-4756134-1` — a value inside a parenthetical trend list → now `ambiguous`, which is what it always was

Those patterns live in this file and not in `spans.py`. Seed selection must not see them: the seeds are frozen, the pre-registration binds `spans.py` by hash, and the item hand-check has already been redone. An audit may loosen the rules for itself; the item builder may not.

## How much to trust this

The 49 `value_present_unlabelled` cases are the soft spot. The number is in the note, so it is unlikely to be invented, but nothing here ties it to the right quantity — and a value extracted from the wrong analyte would land in exactly this bucket. Most are heights and weights stated without the words *height* or *weight*.

The `ambiguous` count of 2 still understates how often extraction faced a choice, for the same reason: a note reporting a trend in a phrasing we cannot parse lands in `value_present_unlabelled` rather than being counted as the choice it was.

## What this still cannot see

- An extraction that took the **wrong occurrence of a repeated identical number**. If a note states creatinine twice as 1.4, both are `verified` and no check distinguishes them.
- **Numbers spelled as words**, as the three candidates above show.
- **Which person a value belongs to.** This asks whether the number is in the note attached to the right *quantity*, never to the right *person*. A case report narrating a relative's illness in its own paragraph can have its creatinine extracted as the patient's, and every check here passes it. One such case reached the pilot before a reader caught it; seed selection now gates on it, but this audit still cannot.
- Any quantity `spans.py` has no locator for — this covers age, creatinine, height, weight only. Boolean criteria on the rule-based scores are not examined at all, and that is where criterion-interpretation disputes would live.
- Whether a **unit was converted** correctly, as opposed to transcribed.
