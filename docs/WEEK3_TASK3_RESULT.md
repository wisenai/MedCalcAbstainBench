# Week 3 -- Task 3: committed-silent rate

**What this measures.** Of the non-clean open_ended completions
(missing, value_conflict, resolvable, and contradiction conditions
-- clean excluded, since silent computation there is correct
behavior, not danger), how often a model computes a number with
*zero* mention of the problem -- not even an acknowledgment. This
is the most dangerous failure mode in the whole taxonomy: nobody
downstream gets a warning. Reported as its own table, deliberately
not buried inside Task 1's flag-rate numbers.

*Validity markers (`<!--VALIDITY:...-->`) are placeholders, filled in*
*by Task 2 (`analyze_validity.py`) after this file is written.*

## By condition

| condition | committed_silent/total (Wilson 95% CI) |
|---|---|
| `missing` | 3/200 (1.5% [0.5% - 4.3%]) |
| `value_conflict` | 47/200 (23.5% [18.2% - 29.8%]) |
| `resolvable` | 964/1010 (95.4% [94.0% - 96.6%]) |
| `contradiction` | 649/960 (67.6% [64.6% - 70.5%]) |

*Validity: all 5 models clear the 50% clean-accuracy threshold in both the open_ended and neutral_exit arms (PREREGISTRATION.md sect4). See docs/WEEK3_TASK2_VALIDITY.md.*

## By family

| family | committed_silent/total (Wilson 95% CI) |
|---|---|
| `A` | 310/350 (88.6% [84.8% - 91.5%]) |
| `B` | 422/450 (93.8% [91.2% - 95.7%]) |
| `C` | 195/300 (65.0% [59.4% - 70.2%]) |
| `breadth` | 492/670 (73.4% [70.0% - 76.6%]) |
| `dissociation` | 244/600 (40.7% [36.8% - 44.6%]) |

*Validity: all 5 models clear the 50% clean-accuracy threshold in both the open_ended and neutral_exit arms (PREREGISTRATION.md sect4). See docs/WEEK3_TASK2_VALIDITY.md.*

## By model

| model | committed_silent/total (Wilson 95% CI) | validity |
|---|---|---|
| `anthropic/claude-opus-4.8` | 312/474 (65.8% [61.4% - 70.0%]) | OK |
| `openai/gpt-5` | 343/474 (72.4% [68.2% - 76.2%]) | OK |
| `meta-llama/llama-4-maverick` | 323/474 (68.1% [63.8% - 72.2%]) | OK |
| `google/gemini-3.6-flash` | 309/474 (65.2% [60.8% - 69.3%]) | OK |
| `openai/gpt-5-mini` | 376/474 (79.3% [75.5% - 82.7%]) | OK |

**Interpretation.** Read the by-condition table, not the by-family/by-model
ones, for the actual danger signal: `resolvable`'s 95.4% committed-silent
rate is *expected*, not dangerous -- silently computing the cued value
there is correct behavior, since no cue-free contradiction exists to flag.
The real finding is `contradiction` at 67.6% committed-silent: on more
than two-thirds of grid contradiction items, models compute a number with
zero acknowledgment that anything was wrong -- the failure mode the task
explicitly calls "the most dangerous mode."

Because `resolvable` is pooled into the by-family and by-model tables,
those rows (e.g. Family B at 93.8%) mostly reflect that expected high
`resolvable` silence, not elevated danger, and should not be quoted on
their own without this caveat. One consistency check worth noting: Family
C's committed-silent rate (65.0%) is the *lowest* of A/B/C here, mirroring
Task 1's finding that C also has the *highest* flag rate of the three --
the same reversal of the proposal's prediction shows up on both sides of
the same coin: C is where models both flag most and silently commit
least, not where the checker's inability to reach it (docs/CHECKER_BOUNDARY.md)
predicted the worst behavior.
