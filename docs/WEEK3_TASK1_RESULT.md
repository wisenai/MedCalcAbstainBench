# Week 3 -- Task 1: flag rate by condition, by family, and by model

**What this measures.** Every open_ended completion in the full grid
(Family A, B, C, the breadth calculators, and the dissociation arm --
676 base items x 5 models) scored under the same three-way rubric
used throughout this project: `flagged` (declined), `committed_with_
acknowledgment` (noticed, computed anyway), `committed_silent`
(computed with no mention of the problem). These three tables are
the headline view of that scoring -- how often each model flags,
broken down three ways. `mcq` and `program_aided` completions are
also scored (10,140 rows total, satisfying "score the full grid"),
but feed Task 4's delta rather than these tables -- see
PREREGISTRATION.md sect1/sect4 for why open_ended is the reporting format
here: it's the format the project's whole validity/reliability
machinery was built around.

Condition labels are kept exactly as constructed, not merged --
`missing`/`value_conflict` (dissociation arm) and `contradiction`
(grid) are related but not identical defects, so collapsing them
into one label would hide that distinction.

*Validity markers (`<!--VALIDITY:...-->`) are placeholders, filled in*
*by Task 2 (`analyze_validity.py`) after this file is written.*

## By condition

| condition | flagged/total (Wilson 95% CI) |
|---|---|
| `clean` | 38/1010 (3.8% [2.8% - 5.1%]) |
| `missing` | 196/200 (98.0% [95.0% - 99.2%]) |
| `value_conflict` | 128/200 (64.0% [57.1% - 70.3%]) |
| `resolvable` | 22/1010 (2.2% [1.4% - 3.3%]) |
| `contradiction` | 219/960 (22.8% [20.3% - 25.6%]) |

*Validity: all 5 models clear the 50% clean-accuracy threshold in both the open_ended and neutral_exit arms (PREREGISTRATION.md sect4). See docs/WEEK3_TASK2_VALIDITY.md.*

## By family

| family | flagged/total (Wilson 95% CI) |
|---|---|
| `A` | 9/525 (1.7% [0.9% - 3.2%]) |
| `B` | 17/600 (2.8% [1.8% - 4.5%]) |
| `C` | 108/450 (24.0% [20.3% - 28.2%]) |
| `breadth` | 140/1005 (13.9% [11.9% - 16.2%]) |
| `dissociation` | 329/800 (41.1% [37.8% - 44.6%]) |

*Validity: all 5 models clear the 50% clean-accuracy threshold in both the open_ended and neutral_exit arms (PREREGISTRATION.md sect4). See docs/WEEK3_TASK2_VALIDITY.md.*

## By model

| model | flagged/total (Wilson 95% CI) | validity |
|---|---|---|
| `anthropic/claude-opus-4.8` | 120/676 (17.8% [15.1% - 20.8%]) | OK |
| `openai/gpt-5` | 138/676 (20.4% [17.5% - 23.6%]) | OK |
| `meta-llama/llama-4-maverick` | 65/676 (9.6% [7.6% - 12.1%]) | OK |
| `google/gemini-3.6-flash` | 179/676 (26.5% [23.3% - 29.9%]) | OK |
| `openai/gpt-5-mini` | 101/676 (14.9% [12.5% - 17.8%]) | OK |

**Interpretation.** Flag rate is highest on `missing` (98.0%) and lowest on
`resolvable` (2.2%) and `clean` (3.8%) -- the model declines readily on a
structural gap and rarely false-flags a normal note. Among the semantic
defects, `value_conflict` (64.0%) is flagged far more than `contradiction`
(22.8%).

**By family, the ordering across A/B/C reverses what the proposal
predicted.** Key Ideas #3 of the proposal states the prediction directly:
flagging should be *worst* -- lowest -- exactly where dodging the
contradiction is impossible (Family C), since a model that cannot
recompute around the problem should just guess rather than decline.
Instead, C shows the *highest* flag rate of the three (24.0%), well above
A (1.7%) and B (2.8%) -- both of which a model can quietly sidestep, by
recomputing a derived value (A) or by using the note's one available
blood-pressure pair regardless of which is which (B). This is a reversal
of the pre-registered prediction and should be reported as one, not folded
into the results as if it were expected. A plausible explanation, not yet
confirmed: a stated-and-denied criterion may be more legible to a model
reading for meaning than a numeric mismatch it has to actively recompute
to notice -- but that is a hypothesis for future work (e.g. the mechanism
trace coding), not a finding this table can establish on its own.

Dissociation's family-level rate (41.1%) averages together a near-ceiling
`missing` response and a middling `value_conflict` one; the by-condition
table above is the one that isolates that distinction, not this row.
