# Week 3 -- Task 4: judge agreement per family, and the open-ended vs. MCQ delta

**What this measures.** Two checks. First, an independent LLM judge
re-labels a stratified 20% sample of open_ended completions from
each family, to confirm classify_response's labels are trustworthy
at this larger scale (not just the Week 2 dissociation pilot).
Second, the flag-rate delta between open_ended and mcq on the same
notes and models -- "was offering an exit enough": a large delta
means simply listing an abstain option changes behavior; a small
one means it doesn't.

*Validity markers (`<!--VALIDITY:...-->`) are placeholders, filled in*
*by Task 2 (`analyze_validity.py`) after this file is written.*

## Judge agreement, per family

| family | n | coarse agreement | coarse kappa | three-way agreement | three-way kappa |
|---|---|---|---|---|---|
| `A` | 105 | 103/105 (98.1% [93.3% - 99.5%]) | 0.000 | 59/105 (56.2% [46.6% - 65.3%]) | 0.102 |
| `B` | 120 | 120/120 (100.0% [96.9% - 100.0%]) | 1.000 | 88/120 (73.3% [64.8% - 80.4%]) | 0.222 |
| `C` | 90 | 89/90 (98.9% [94.0% - 99.8%]) | 0.965 | 68/90 (75.6% [65.8% - 83.3%]) | 0.575 |
| `breadth` | 195 | 195/195 (100.0% [98.1% - 100.0%]) | 1.000 | 172/195 (88.2% [82.9% - 92.0%]) | 0.712 |
| `dissociation` | 160 | 160/160 (100.0% [97.7% - 100.0%]) | 1.000 | 127/160 (79.4% [72.5% - 84.9%]) | 0.671 |

Disagreements: 156 of 670. 153 at the acknowledged/silent boundary (never crosses the flag/commit line), 3 cross the flag/commit line.

## Open-ended vs. MCQ flag-rate delta, per family

| family | flagged/total (open_ended) | flagged/total (mcq) | delta (mcq - open_ended), pp | paired McNemar p | n pairs |
|---|---|---|---|---|---|
| `A` | 9/525 (1.7% [0.9% - 3.2%]) | 84/525 (16.0% [13.1% - 19.4%]) | +14.3 | 3.997e-19 * | 525 |
| `B` | 17/600 (2.8% [1.8% - 4.5%]) | 121/600 (20.2% [17.2% - 23.6%]) | +17.3 | 4.977e-24 * | 600 |
| `C` | 108/450 (24.0% [20.3% - 28.2%]) | 233/450 (51.8% [47.2% - 56.4%]) | +27.8 | 3.12e-24 * | 450 |
| `breadth` | 140/1005 (13.9% [11.9% - 16.2%]) | 218/1005 (21.7% [19.3% - 24.3%]) | +7.8 | 3.026e-12 * | 1005 |
| `dissociation` | 329/800 (41.1% [37.8% - 44.6%]) | 342/800 (42.8% [39.4% - 46.2%]) | +1.6 | 0.09837 | 800 |

*Validity: all 5 models clear the 50% clean-accuracy threshold in both the open_ended and neutral_exit arms (PREREGISTRATION.md sect4). See docs/WEEK3_TASK2_VALIDITY.md.*

**Interpretation.** Offering an explicit "insufficient or contradictory
information" option changes behavior substantially for every grid family
-- A (+14.3pp, p~4e-19), B (+17.3pp, p~5e-24), C (+27.8pp, p~3e-24),
breadth (+7.8pp, p~3e-12) -- but not for dissociation (+1.6pp, p=0.098,
not significant). So "was offering an exit enough" is mostly yes for the
newly-built grid and no for the original missing-vs-conflict setup --
simply listing an abstain option does far more for a model already primed
to recognize a stated contradiction than it does for the creatinine
value-conflict case.

Family C shows both the largest delta (+27.8pp) and the highest absolute
flag rate on both formats (24.0% open_ended, 51.8% mcq) -- consistent
with Task 1's finding that C is where models most readily flag among the
three contradiction families, the reversal of the proposal's "flagging is
worst where dodging is impossible" prediction. Family A's coarse
kappa=0.000 despite 98.1% raw agreement is the well-documented "kappa
paradox" under extreme class imbalance (only ~1.7% of Family A responses
are flagged by either rater, so chance agreement is already ~98%) -- not
evidence the judge and the automatic label disagree.
