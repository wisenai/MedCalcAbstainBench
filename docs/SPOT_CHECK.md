# spot-check: 20 items read by hand


The task list asks for two things: a script that verifies injection anchoring on
all 160 items, and 20 checked by hand. Both were done, and the hand check is the
one that found the problem.

---

## What the script checks

`verify_anchoring.py` reads the finished items back off disk and re-derives
everything without consulting the builder. That separation is the point:
`construct.py` already asserts anchoring while it builds, but a builder that is
wrong about which span the calculator reads will assert the wrong thing and pass.

Six checks per item — the clean answer recomputes through the released
implementation; the recorded span holds the value the calculator consumes; the
missing variant is one contiguous excision leaving no creatinine; the conflict
variant is one contiguous insertion keeping both values; both values drive the
calculator to the recorded answers; and the resolvable note is byte-identical to
the conflict note.

**All 40 seeds, 160 items, pass.** The script was also run against six
deliberately corrupted items — a moved span, an edited resolvable note, a
creatinine left in the missing variant, an altered clean answer, an altered second
value, and a removed cue — and caught all six.

## What the hand check found

**Nine of forty `missing` variants were damaged, and every automated check passed
them.** The script confirms an excision is contiguous, removes the creatinine, and
leaves the rest byte-identical. None of those questions is "does the result read".

| Seed | What the excision left |
|---|---|
| `mdrd-tr3249` | `urea 44 mg/dL [17–43] [0.51–0.95],` — orphaned reference range |
| `mdrd-tr3281` | same, with a parenthesized range carrying no "normal" label |
| `ckd_epi-30` | `Renal function test was severely disturbedshe had also` |
| `mdrd-tr3279` | `multiple cysts about 3 centimeters and. Computed tomography` |
| `mdrd-tr3320` | `hematocrit: 30% and. After an emergent fast ultrasound` |
| `mdrd-tr3359` | `hyperlipidemia and a. 4.5 g of protein are excreted` |
| `cockcroft_gault-tr1` | `hemoglobin (14.4 g/dL)), serum total cholesterol` |
| `mdrd-tr3282` | `Laboratory studies showed and blood urea nitrogen of 29 mg/dL` |
| `ckd_epi-38` | `Basic metabolic panel revealed from normal baseline` |

None of these is punctuation damage, which is all the builder's seam check looked
for. `disturbedshe` has no punctuation at all. `and.` is dangling but
punctuationally fine. `revealed from` is a missing grammatical object.

### The scan I wrote afterwards was worse than reading

Having found seven by eye in the sample of twenty, I wrote a pattern scan to
measure the rest. It found seven across all forty — but a *different* seven. It
missed `ckd_epi-30` entirely, because the lookahead in my fused-word probe was
wrong, and I only caught that because I had already seen the case by hand. The
corrected scan found nine.

That is the argument for the task list asking for both. The script scales; the
reading finds what the script was not written to look for.

## What was done about it

**Eight were repaired** by extending the excision rules, each generalizing rather
than special-casing: reference ranges in brackets and in unlabelled parentheses
now come out with the value; bracket balance is enforced when the measurement sits
inside a parenthesis it does not own; a bare conjunction on either side is
absorbed when there is no punctuation to take; and absorbing a leading space along
with an enclosing bracket now counts as the one separator, so a trailing one is
not taken as well.

**One was rejected.** `ckd_epi-38` reads *"panel revealed creatinine of 2.31 mg/dL
from normal baseline (Normal 0.6–1.3 mg/dL)"*. The trailing qualifier belongs to
the creatinine, and no general rule recovers the sentence. Recorded in
`data/hand_kills.json`; the seed list refilled from the eligible pool, so the arm
is still 40 seeds. The replacement, `ckd_epi-tr144`, was read and is clean.

**All nine are now regression tests.** `tests/test_regression.py` carries each one
with the note text that caused it, so the repairs cannot silently regress and the
rejected case cannot silently return.

**Re-scan after the repairs: 0 of 40 defective.**

---

## The twenty, as read

Sampled every second item in build order — 7 CKD-EPI, 7 MDRD, 6 Cockcroft-Gault,
spanning both the test and train splits.

| # | Seed | Verdict | Note |
|---|---|---|---|
| 1 | `ckd_epi-21` | pass | `SCr 42.0 and 126 μmol/L` inside the renal-function parenthetical |
| 2 | `mdrd-tr3204` | pass | lab list; both "normal" words attach to CBC and calcium, not the creatinine |
| 3 | `cockcroft_gault-4` | pass | space-separated lab table; the rewrite matches its register |
| 4 | `ckd_epi-28` | pass | reference range follows both values, so neither is singled out |
| 5 | `mdrd-tr3249` | **repaired** | orphaned bracketed range; now clean |
| 6 | `cockcroft_gault-10` | pass | — |
| 7 | `ckd_epi-30` | **repaired** | words fused; now clean |
| 8 | `mdrd-tr3259` | pass | — |
| 9 | `cockcroft_gault-14` | pass | — |
| 10 | `ckd_epi-35` | pass | — |
| 11 | `mdrd-tr3279` | **repaired** | dangling `and.`; now clean |
| 12 | `cockcroft_gault-17` | pass | — |
| 13 | `ckd_epi-38` | **rejected** | verb stripped of its object; hand-killed |
| 14 | `mdrd-tr3282` | **repaired** | `showed and blood urea`; now clean |
| 15 | `cockcroft_gault-tr1` | **repaired** | doubled closing bracket; now clean |
| 16 | `ckd_epi-tr138` | pass | — |
| 17 | `mdrd-tr3359` | **repaired** | dangling `and a.`; now clean |
| 18 | `cockcroft_gault-tr5` | pass | — |
| 19 | `ckd_epi-tr141` | pass | — |
| 20 | `mdrd-tr3384` | pass | — |

Two further defects (`mdrd-tr3281`, `mdrd-tr3320`) fell outside the sample and
were caught by the scan the sample prompted.

## Second signature

Not obtained. The repairs and the one rejection are one reader's calls.

| Reader | Date | Agrees with the repairs and the rejection | Notes |
|---|---|---|---|
| | | | |
