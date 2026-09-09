# Week 1 hand-check of the worked cases

**Task owner:** Annotator B — Week 1 task J3 · 2026-08-05
**Completed by:** Annotator D
**Second signature:** confirmed at the four-way read, 2026-08-10

The plan asks three questions of each worked case: is the contradiction real, does
the note still read coherently, and does any second reading make the item
consistent after all. Below is what reading them actually turned up, what was
changed as a result, and what is left for the four-way read to decide.

This is a record of a first pass by one person. It is not the four-way read and
does not substitute for it.

---

## Summary

Reading the first batch of ten found **four defects, three of them systematic**.
All four are fixed; the fixes changed the seed list, so the ten worked cases in
`docs/WORKED_CASES.md` are not the ten I started with.

The items were then rebuilt a second time, when the conflict injection changed
from an appended clause to a rewrite of the value phrase. That changed the text of
every value-conflict item, so the ten were read a **third** time against what
actually exists now. All ten pass.

| | |
|---|---|
| Cases read | 33 (ten, ten after the fixes, ten after the injection changed, three new MDRD items after race was resolved) |
| Systematic defects found | 3 |
| Items killed by hand | 4 |
| Seeds lost to the new automatic gates | 21 of 60 test-split candidates |
| Earlier flags resolved by the new injection form | 2 |
| Formula inputs left to a default | 0 (was 13) |
| Worked cases crossing a CKD stage boundary | 10 / 10 (was 9) |
| Current worked ten passing all three questions | 10 / 10 |

The seed count held at 40 only because the pool was widened to MedCalc-Bench's
train split. On the test split alone the new gates leave 25, which is short of
what Week 2 needs. That is recorded in [What this cost](#what-this-cost).

---

## Defect 1 — a stated eGFR re-states the creatinine

**Found in:** `cockcroft_gault-8`, and on inspection six more seeds.

The note reads:

> On the other hand, impaired renal function [i.e., serum creatinine: 1.42 mg/dL;
> eGFR: 49.1 mL/min/1.73 m2] was observed after admission.

This breaks both defect conditions at once, and it took reading the note to see it:

- Under `missing`, deleting the creatinine does not make the item unanswerable.
  The eGFR is still there and it is a function of the creatinine, so the value is
  recoverable. A model that declines here is arguably wrong, and a model that
  computes is arguably right — the exact opposite of what the condition asserts.
- Under `value_conflict`, a reader can check which of the two creatinines is
  consistent with an eGFR of 49.1 and keep that one. That is precisely the "second
  reading makes the item consistent after all" failure the plan says to kill for.

**Fixed** as gate 4 in `select_seeds.py`: a seed is rejected if its note states
eGFR, GFR, creatinine clearance, or MELD. Cost across the widened pool: 46 rows.

## Defect 2 — the note characterises the creatinine

**Found in:** `mdrd-143`, `ckd_epi-32`, `mdrd-151`, `mdrd-142`, `ckd_epi-33`,
`mdrd-159`, and, in a form the first fix missed, `cockcroft_gault-6`.

Two shapes, one problem. The note has already told the reader what kind of value
this is, so an injected value of the other kind is the one the reader discards.

> After decompression, the patient had an improvement in renal function with serum
> creatinine **decreasing to** 1.6 mg/dL.

A note that says the value changed has invited "use the one after decompression",
which is the same trend escape hatch the injection wording exists to close.

> In kidney panel, serum urea (155.8 mg/dL) and serum creatinine levels (8.9 mg/dL)
> were **highly increased** suggesting severe form of disease.

Injecting a normal creatinine here contradicts the note's own clinical reading
rather than contradicting the other value.

**Fixed** as gate 5, in two strengths, because attribution is genuinely hard.
Framing that attaches to the creatinine grammatically is rejected automatically.
Framing merely present in the same sentence is recorded as a review flag, because
it usually describes a neighbour: `creatinine level of 0.9 mg/dL and an elevated
hematocrit of 0.6` is about the hematocrit, and `Urinalysis is within normal
limits` at the end of a lab table is about the urinalysis. A first cut that
rejected on sentence-level presence threw out fifteen seeds, about a third of them
good ones.

The nine flagged seeds were then read by hand. Four were killed, five kept, all
recorded with reasons in `data/hand_kills.json`, which `select_seeds.py` applies
as its final gate — so the decision is enforced by the build rather than living in
a document nobody re-reads.

| Seed | Verdict | Why |
|---|---|---|
| `cockcroft_gault-6` | **killed** | sentence opens "results were within the normal ranges, as follows:" and lists the creatinine among them |
| `ckd_epi-32` | **killed** | "creatinine levels (8.9 mg/dL) were highly increased suggesting severe form of disease" |
| `ckd_epi-37` | **killed** | "revealed elevated PR3-ANCA, blood urea nitrogen, and serum creatinine levels" — the adjective distributes over the list |
| `mdrd-144` | **killed** | "an elevation of blood urea nitrogen 23.8 mg/dl, creatinine 1.14 mg/dl" — same shape |
| `cockcroft_gault-4` | kept | "within normal limits" describes the urinalysis |
| `cockcroft_gault-14` | kept | "high"/"low" come from high- and low-density lipoprotein |
| `cockcroft_gault-20` | kept | "her acetone was elevated" describes the acetone |
| `ckd_epi-28` | kept | a reference range says what is typical, not which measurement is real |
| `mdrd-154` | kept | "normal range" attaches to a different analyte later in the block |

## Defect 3 — my own seam check could be fooled

**Found in:** `mdrd-143`, while checking that its excision was clean.

The `missing` variant read:

> the patient had an improvement in renal function with .

which is broken, and the build had passed it. The check compared the *count* of
punctuation defects before and after the excision, and this excision traded one
defect for another: the original ended `... 1.6 mg/dL ().` with a stray empty
bracket pair, and removing the measurement left `renal function with.` — one
defect before, one after, badly broken in between.

**Fixed** by comparing the defect multiset rather than the count, so a swap is
caught. `mdrd-143` now fails the build, which is correct; it is also killed by
gate 5 independently.

Worth saying plainly: this was a bug in the checking, not in the construction. A
guardrail that can be satisfied by a trade is not a guardrail, and the only reason
it surfaced is that someone read the output instead of trusting the green light.

## Defect 4 — the worked ten were all one calculator

**Found in:** the worked-case set itself, not in any individual item.

The seeds are frozen in calculator order, and the worked ten were the first ten,
which made them ten Cockcroft-Gault cases. The four-way read would then have
approved a construction that had never been looked at on CKD-EPI or MDRD — and
those differ in which inputs the formula consumes. MDRD reads race; CKD-EPI does
not read weight or height.

**Fixed:** `construct.py` now picks the worked ten round-robin across the three
calculators. The current set is 4 CKD-EPI, 3 Cockcroft-Gault, 3 MDRD.

---

## Second pass — after the injection form changed

The conflict is no longer injected by appending a clause. It now rewrites the
value phrase itself:

> creatinine, 1.4 mg/dL  →  creatinine, **1.4 and 3.64 mg/dL**

Every value-conflict item therefore carries different text from the one I checked
in the first pass, so the first pass no longer describes what exists. All ten were
re-read against the new text. **All ten pass**, and two things I had flagged are
resolved by the change rather than by argument:

- **`cockcroft_gault-4`'s register mismatch is gone.** That note is a
  space-separated laboratory table, and a narrative clause dropped into it read
  badly. `Creatinine 0.8 and 2.08 mg/dL` matches the table's own style.
- **`ckd_epi-28`'s reference-range asymmetry is gone.** The note states
  `(normal range 0.6-1.2 mg/dL)`. Under the old form the range attached to the
  published value only; under the rewrite it follows both, and both are above it.
  Neither value is singled out as the abnormal one.

| # | Seed | Verdict | Observation |
|---|---|---|---|
| 1 | `ckd_epi-21` | pass | `SCr 42.0 and 126 μmol/L`. The unit is stated once, after both values — standard notation, but it is the item where that is least obvious. |
| 2 | `cockcroft_gault-1` | pass | — |
| 3 | `mdrd-145` | pass | — |
| 4 | `ckd_epi-26` | pass | — |
| 5 | `cockcroft_gault-4` | pass | register mismatch resolved (above) |
| 6 | `mdrd-148` | pass, flagged | the only item whose two answers share a CKD stage (3.6 vs 6.0 mL/min/1.73m², both stage 5). The conflict is real; the *decision* is not obviously different. Unchanged from the first pass. |
| 7 | `ckd_epi-28` | pass | range asymmetry resolved (above) |
| 8 | `cockcroft_gault-7` | pass | — |
| 9 | `mdrd-154` | pass | — |
| 10 | `ckd_epi-29` | pass | creatinine is 11.3 mg/dl and the prothrombin time is 11.3 sec. Cosmetic; anchoring is on label and unit. |

### Third pass — after MDRD's race was resolved

The seed list changed once more. Where a note does not state race, MDRD's released
implementation reads the patient as non-Black and the clean answer inherits a
1.212 coefficient nobody chose; 18 eligible MDRD notes *do* state race and only 13
are needed, so selection now prefers notes that state every formula input. All 13
MDRD seeds are new, three of them are in the worked ten, and those three were read.

**All ten still pass.** Two things improved without being aimed at:

- **Every one of the 159 formula inputs now has a real character span.** No input
  is left to a default. All 13 race spans are genuine demographic mentions — *"A
  73-year-old Caucasian male"*, *"A 50-year-old black woman"* — and on all 13 the
  note, MedCalc's entity and the clean answer agree. Four are Black patients, where
  the old default would have been wrong by 21%.
- **All ten worked cases now cross a CKD stage boundary**, up from nine.
  `mdrd-148`, the one item whose two answers shared a stage, is no longer among them.

| # | Seed | Verdict | Observation |
|---|---|---|---|
| 3 | `mdrd-tr3204` | pass | The lab list opens *"normal complete blood count (CBC), normal serum calcium value, creatinine 1.4 and 3.08 mg/dL"*. Both "normal"s attach to the CBC and the calcium; the creatinine is stated flatly. Watch this one — it is the closest any item comes to a framing word landing near the creatinine. |
| 6 | `mdrd-tr3225` | pass | Space-separated lab table. Reads as the table's own style. |
| 9 | `mdrd-tr3249` | pass, flagged | The note carries bracketed reference ranges: *"creatinine 0.62 and 1.36 mg/dL [0.51–0.95]"*. The range covers both values, but **0.62 falls inside it and 1.36 outside** — the only item where the two values differ in whether they look normal. Compare `ckd_epi-28`, where both fall outside and the asymmetry does not arise. It does not resolve the conflict — an out-of-range creatinine is an ordinary measurement, not a wrong one — but it is the item most open to the argument that it does. |

The seven remaining seeds are unchanged from the previous pass and were not re-read.

**Cost of this change**, recorded because it is a real trade: the split mix moves
from 25 test / 15 train to 19 test / 21 train. Preferring notes that state race
partly overrides the test-split-first preference, and the test split is the one the
label-audit census covered. Judgement: an input the note actually states beats the
weaker assurance of a census that only ever tested label-against-code.

### The in-phrase form introduces one risk the old one did not

`1.4 and 3.64 mg/dL` could conceivably be read as a **range** rather than as two
values. I judge it unlikely — a range is written with "to" or a dash, not "and",
and no item here uses a dash — but it is a new failure mode created by this
change, and nobody has tested it on a model yet. It is the specific thing to look
for in the first pilot completions: if a model answers with something between the
two values, it read a range.

The prose form is still built for every item, so if the range reading turns out to
be real, the comparison to fall back on already exists.

### One change came out of the first re-read

Six of the original ten had two answers that crossed no decision boundary, because
the boundary was a single 60 mL/min cut-off and those notes describe patients whose
creatinine is already 7–13 mg/dL. No plausible second value lifts such a patient
above 60, so every advanced-CKD item scored as decision-irrelevant.

That was the wrong test rather than a bad set of items: moving a patient between
CKD stage 4 and stage 5 is exactly the decision that changes management.
`construct.py` now scores against the KDIGO stage ladder (15, 30, 45, 60, 90).
Across all 40 seeds, 39 cross a stage boundary; `mdrd-148` above is the one that
does not.

## What this cost

The gates added here reject 21 of the 60 creatinine rows in the test split, which
leaves 25 — below the ~40 the plan calls for. Rather than relax a gate that was
added for a reason, the candidate pool was widened to MedCalc-Bench's train split,
which holds 928 further real extracted notes across the same three calculators.
417 rows now pass every gate, and 40 are selected by a fixed, documented rule:
balanced across calculators, test-split rows before train-split rows, ascending
row number.

Two consequences the group should be aware of rather than discover later:

- **Most seeds are now train-split rows.** They are real PMC case-report notes of
  the same kind, but the label audit covered the test split as a census and did
  not cover these. The per-seed label check still runs on every one of them, so no
  seed carries a label the released code disagrees with; what is missing is the
  broader assurance the census gave.
- **We are now selecting 40 from 417 rather than taking everything that passes.**
  The rule is fixed and deterministic and touches nothing we will later measure,
  but it is a choice where previously there was none, and it should be in the
  methods section rather than in this file only.

---

## Second signature

The plan asks for a second signature from whoever is free. Nothing below is
signed yet.

What a second reader should check, in the order that would catch the most:

1. The four hand-kills in `data/hand_kills.json`. Read each note and say whether
   you agree the framing covers the creatinine. Two of them (`ckd_epi-37`,
   `mdrd-144`) rest on an adjective distributing over a list, which is a reading,
   not a fact.
2. The five kept-despite-a-flag decisions in the same file, particularly
   `ckd_epi-28` — a reference range is arguably more resolving than I judged it.
3. `mdrd-148`, the one item whose two answers share a CKD stage.
4. Whether widening to the train split is acceptable at all, or whether the arm
   should be 25 test-split seeds instead.

| Reader | Date | Agrees with the kills | Notes |
|---|---|---|---|
| Annotator A, Annotator C, Annotator B | 2026-08-10 | yes | Confirmed at the four-way read; no further items killed |

_Entered by Annotator D from the group read rather than typed individually; see
`data/signoff.json` for the record._
