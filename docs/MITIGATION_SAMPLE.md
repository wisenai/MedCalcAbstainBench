# Mitigation sample — handoff

**For:** Maia, Week 3 mitigation arm.
**From:** Annotator D. Regenerate with `python3 mitigation_sample.py`.

Your clause is to run the mitigation arm *"on the family-balanced sample plus
consistent controls: inline consistency instruction vs. a separate verifier pass
placed before the calculator"*, and to *"report false-flagging on consistent notes
as the cost side of both"*. Both halves are here.

## What you have

`data/mitigation_sample.json` — **72 items**, notes and questions only.
`data/mitigation_key.json` — which are defective, the correct action, and the pairing.

| Family | Defects | Controls | Balanced across |
|---|---|---|---|
| A — derived value vs its components | 12 | 12 | BMI 7, anion gap 5 |
| B — impossible blood pressure | 12 | 12 | transposed 6, lowered 6 |
| C — criterion asserted then denied | 12 | 12 | 10 criteria, 3 calculators |

## The controls are matched, and that is the point

**Every defect is paired with the `clean` condition of its own base note** — same
patient, same prose, same question, differing only in the defect removed. An
unmatched set of clean notes would confound your cost side with everything else
that differs between notes, and false-flagging is exactly the number where that
would matter.

`pairs_with` in the key gives you the partner for a within-note comparison.

## The key is separate on purpose

The sample carries `mitigation_id`, `family`, `calculator`, `note`, `question` and
**nothing else**. No arm, no correct action, no answer, no pairing.

Identifiers are opaque (`mit-001` …) and ordered by a digest of the note text, so
defects and controls interleave — only 2 of 36 pairs land adjacent, against 36 of
36 in the first version I built, which numbered them `…-control` and gave the whole
thing away. Same reason the repo already keeps `pilot/items/_coding_key.json` out
of its sample.

**One honest limit.** The blind stops casual label-reading; it cannot stop a
determined diff. Defect and control share a base note by design, so anyone
comparing all 72 notes will find 36 near-identical pairs and can read the injection
off directly. That is inherent to a matched-pair design, not something the
identifiers can fix. It matters only if a human codes these; it does not affect a
model run at all.

## Two things worth knowing before you run

**Family B has two shapes and they are the comparison.** `transposed` is the note's
own pair swapped (`140/80` → `80/140`); `lowered` puts the systolic below the note's
own diastolic without swapping (`161/78` → `63/78`). If flag rates differ sharply
between them, the model is pattern-matching on transposition rather than reasoning
about the values — which is a result, not a nuisance. The sample is 6 and 6 so that
comparison is available.

**Family A's controls are genuinely clean, and were checked.** Their published
derived value agrees with the note's own components within 5%, and `checker.py`
stays silent on every one. If your verifier pass flags them, that is false-flagging
and not a disagreement about the item.

## Related

- `docs/SPOT_CHECK_WEEK3.md` — the hand read of these families, and the five defects
  it found that every script had passed. All five are gated out of what you have.
- `docs/CHECKER_INPUT_EXTRACTION_GAP.md` — the checker's height/weight blind spot,
  which bears on your catch-rate numbers.
- `docs/RUBRIC_INPUT_FAMILY_B.md` — the labelling case Family B raises, for Annotator C.
