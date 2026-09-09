# Results summary -- Weeks 2 and 3 (Scoring, Stats & Reliability)

This is a synthesis of every result produced so far under Annotator C's role
(the three-way rubric, the scorer, judge agreement, Wilson/McNemar, all
result tables), covering both the Week 2 dissociation pilot and the Week 3
full grid. It exists to answer one question: **what does the evidence
gathered so far actually say about the paper's central claim**, and where
does it still fall short of what the proposal committed to showing.

Every number below has been independently recomputed from the raw scored
CSVs/JSONs and confirmed to match the corresponding `.md` table exactly --
see the audit notes inline where relevant. This document does not
introduce new numbers; it only synthesizes and interprets what
`docs/WEEK2_TASK*.md` and `docs/WEEK3_TASK*.md` already report.

## The question this project asks

*When a clinical note is contradictory rather than incomplete, does a
calculator-running language model flag it and decline, or does it quietly
compute an answer anyway?* The proposal's bet: models are good at
spotting holes (missing values) and bad at spotting contradictions
(present-but-untrustworthy values) -- and if that's true, every previously
published abstention number is secretly averaging two very different
behaviors together.

## Week 2 -- the dissociation pilot (creatinine calculators, one model)

40 matched base notes, four conditions each (`clean`/`missing`/
`value_conflict`/`resolvable`), Claude Opus 4.8, two prompt arms
(`open_ended`, `neutral_exit`).

**The core claim holds, strongly, on both arms.** Non-commitment on
`missing` is near-ceiling (97.5%, both arms). Non-commitment on
`value_conflict` is far lower -- 67.5% under `open_ended`, only 2.5% under
`neutral_exit` -- giving Δ = 30.0pp (p=4.9e-4) and Δ = 95.0pp (p=7.3e-12)
respectively, both highly significant paired McNemar results. `clean`
false-flagging stays low on both arms (2.5%), so the model isn't just
declining on everything.

**The neutral-prompt control argues against H1, not for it.** The
proposal's H1 predicts the gap should shrink under an even-handed prompt
that doesn't specifically cue declining on `missing`. It grew instead --
Δ nearly tripled under `neutral_exit`. This is evidence for H2 (the
trigger is per-check, not one confidence knob), and it's evidence the
proposal itself named in advance as a falsifier test, not something found
after the fact and rationalized.

**Parsing vs. flagging: the failure is in the response, not the reading.**
Resolvable accuracy is 97.5% on both arms -- the model reliably parses and
uses both conflicting values when told which one to use. Yet under
`neutral_exit`, 38 of those 39 correctly-parsed notes still went unflagged
on the matched, uncued `value_conflict` twin. The model can read; it just
doesn't volunteer that something's wrong unless prompted to pick.

## Week 3 -- the full grid (Family A/B/C, breadth calculators, dissociation, 5 models)

676 base items across 8 item files, 5 models, `open_ended`/`mcq`/
`program_aided` fully scored (10,140 rows), `neutral_exit` scored for the
validity check. Every table below is `open_ended`-reported (the format the
project's validity/reliability machinery was built around), except the
open-ended-vs-MCQ delta, which by definition needs both.

**Validity check clears the board.** All 5 models clear the 50%
clean-accuracy threshold in both `open_ended` and `neutral_exit`
(76.2%-88.1%), and none shows the "passes in one arm, fails in the other"
pattern. Every result below is real signal, not an artifact of an
incapable model.

**The headline finding, and it's a reversal of the proposal's own
prediction.** The proposal's Key Ideas #3 states directly: flagging
should be *worst* -- lowest -- exactly where a model cannot dodge the
contradiction (Family C, an asserted-and-denied criterion with no
arithmetic to redo). Instead:

| family | flag rate (open_ended) | committed-silent rate |
|---|---|---|
| A (derived-value, dodgeable) | 1.7% | 88.6% |
| B (impossible value, one calculator) | 2.8% | 93.8% |
| C (categorical, no dodge) | **24.0%** | **65.0%** |

C is where models flag *most* and silently commit *least* of the three
families -- the opposite ordering from what was predicted. This shows up
twice, independently: once in the flag-rate table (Task 1) and once,
consistently, in the committed-silent table (Task 3). It is not an
artifact of validity (all models clear the threshold) or of construction
(A and B are exactly as easy to dodge as designed -- the deterministic
checker in `docs/CHECKER_BOUNDARY.md` catches both at ~100%, confirming
they're genuinely arithmetic-recoverable, while C is structurally
unreachable by any checker). A plausible but unconfirmed explanation: a
stated-and-denied criterion may simply be more legible to a model reading
for meaning than a numeric mismatch it has to actively recompute to
notice. This needs to be reported in the paper explicitly as a reversal
of the pre-registered prediction, with the explanation flagged as a
hypothesis for the mechanism-trace work to test, not asserted as
established.

**"Was offering an exit enough" -- mostly yes for the grid, no for
dissociation.** Every grid family shows a large, highly significant
open-ended-vs-MCQ delta: A +14.3pp (p~4e-19), B +17.3pp (p~5e-24), C
+27.8pp (p~3e-24, the largest), breadth +7.8pp (p~3e-12). Dissociation's
delta is small and not significant (+1.6pp, p=0.098). Simply listing an
abstain option does far more for a model already primed to recognize a
stated contradiction than it does for the original creatinine
value-conflict setup.

**Judge reliability holds up at the larger scale.** 670-row stratified
sample across all 5 families: coarse (flag-vs-commit) agreement is
98.1%-100% in every family except the well-understood Family A "kappa
paradox" case (98.1% raw agreement, κ=0.000 -- an artifact of extreme
class imbalance, not disagreement). Of 156 total disagreements, 153 sit at
the acknowledged/silent boundary (never touches the headline metric) and
only 3 cross the flag/commit line. The automatic labels are trustworthy at
grid scale, not just in the Week 2 pilot.

## Cross-week consistency

Week 2's dissociation pilot and Week 3's `dissociation` family share 39 of
40 seeds (one, `mdrd-tr3279`, was retired mid-project and replaced by
`mdrd-tr3399` -- documented in `PREREGISTRATION.md` Amendment 8). Opus's
numbers on the 39 shared seeds match exactly across both weeks (`missing`
39/40, `value_conflict` 27/40 in both). The one difference found (`clean`:
1/40 in Week 2 vs. 0/40 in Week 3) traces to that exact retired seed --
Opus flagged `mdrd-tr3279_clean` as a false positive, which is at least
consistent with that note having a real, if different, defect (its
creatinine value belonged to the patient's grandmother, not the patient).

## Known gaps -- not yet covered by anything delivered so far

1. **No resolvable-accuracy / parsing-vs-flagging cross-tab exists for the
   grid families.** Week 2 built this for dissociation; the proposal's
   design applies it to every family (each has its own `resolvable`
   condition), but none of Week 3's four tasks reproduce it for A/B/C/
   breadth. Task 1's by-condition table shows a pooled `resolvable` row
   (2.2%) but not the paired, per-family cross-tab the "parsing vs.
   flagging" claim needs to generalize beyond dissociation.
2. **The extended-thinking / high-reasoning-effort falsifier is untested.**
   The proposal names this explicitly as a second way to adjudicate H1 vs.
   H2 (the gap should close under more reasoning, per H1). Annotator A's
   `open_ended_extended_thinking` data exists (80% complete, missing
   entirely for one model) but nothing in Annotator C's 8 tasks across both
   weeks scores or reports on it.
3. **`program_aided` scoring is lower-confidence by design.** Its
   abstain/flag signal is genuinely heuristic (no output-format
   instruction in the prompt, phrasing varies by vendor, and a
   defensive-but-unreached code branch can look like a flag). Every
   `program_aided` row carries a `low_confidence` marker; none of it
   currently feeds a reported table (Task 1's core tables and Task 3 are
   `open_ended`-only; Task 4's delta uses `open_ended`+`mcq`), so this
   doesn't block anything already reported, but a hand-validated sample is
   still owed before `program_aided` numbers can be trusted the way the
   other two formats' can.

## What's ready for the paper right now

The core dissociation claim (Week 2), the H1-vs-H2 neutral-prompt evidence
(Week 2), the parsing-vs-flagging diagnostic for dissociation (Week 2),
the full-grid flag-rate/family/model tables (Week 3 Task 1), the
committed-silent danger-mode table (Week 3 Task 3), the validity
calibration (Week 3 Task 2), the judge-reliability confirmation at scale,
and the open-ended-vs-MCQ delta (Week 3 Task 4) -- all of it, with the
Family C reversal reported explicitly as a reversal, not smoothed over.
The three gaps above are the concrete list of what's still needed before
the paper's design is fully substantiated.
