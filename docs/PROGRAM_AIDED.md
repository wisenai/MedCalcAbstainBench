# -- program_aided format: flag rate by condition, by family, and by model

**What this measures.** Every `program_aided` completion in the full grid (676 base items x 5 models = 3,380 rows), scored under the same three-way rubric used everywhere else in this project: `flagged` (declined), `committed_with_acknowledgment` (noticed, computed anyway), `committed_silent` (computed with no mention of the problem). This is a standalone companion to FLAG_RATES.md's open_ended tables -- program_aided was scored as part of that task's "score the full grid" scope but never got its own reported table; this fills that gap.

**No extracted value or accuracy check is reported here.** Unlike `open_ended`/`mcq`, the `program_aided` prompt gives no output-format instruction, so "what number did the model land on" has to be guessed from free-form code and prose rather than parsed from a fixed convention. Every extraction pattern precise enough to pick out *the* answer turned out to have a real false-positive mode on real data (worst: a markdown-bold-number pattern colliding with Python's `**` exponent operator, e.g. `height ** 2` misread as bold text starting with "2"). That problem doesn't need solving here: nothing downstream runs this code or acts on its output, so the only thing this project's question needs is whether the model committed to an answer at all versus declined -- which only requires detecting *presence* of an attempted computation (print() output, an explicit Output:/Result: section, a boxed expression), not picking out its exact value. See `scoring_program_aided.py`'s module docstring for the full investigation.

*A response with neither an attempted computation nor an abstention phrase is labeled `unparseable` and excluded from the flagged/total denominators below, so it doesn't silently count as either behavior.*

## By condition

| condition | flagged/total (Wilson 95% CI) | unparseable/total |
|---|---|---|
| `clean` | 107/793 (13.5% [11.3% - 16.0%]) | 217/1010 |
| `missing` | 89/182 (48.9% [41.7% - 56.1%]) | 18/200 |
| `value_conflict` | 12/189 (6.3% [3.7% - 10.8%]) | 11/200 |
| `resolvable` | 113/795 (14.2% [12.0% - 16.8%]) | 215/1010 |
| `contradiction` | 167/740 (22.6% [19.7% - 25.7%]) | 220/960 |

## By family

| family | flagged/total (Wilson 95% CI) | unparseable/total |
|---|---|---|
| `A` | 51/413 (12.3% [9.5% - 15.9%]) | 112/525 |
| `B` | 92/386 (23.8% [19.9% - 28.3%]) | 214/600 |
| `C` | 62/400 (15.5% [12.3% - 19.4%]) | 50/450 |
| `breadth` | 157/770 (20.4% [17.7% - 23.4%]) | 235/1005 |
| `dissociation` | 126/730 (17.3% [14.7% - 20.2%]) | 70/800 |

## By model

| model | flagged/total (Wilson 95% CI) | unparseable/total |
|---|---|---|
| `anthropic/claude-opus-4.8` | 42/654 (6.4% [4.8% - 8.6%]) | 22/676 |
| `openai/gpt-5` | 225/605 (37.2% [33.4% - 41.1%]) | 71/676 |
| `meta-llama/llama-4-maverick` | 28/371 (7.5% [5.3% - 10.7%]) | 305/676 |
| `google/gemini-3.6-flash` | 131/597 (21.9% [18.8% - 25.4%]) | 79/676 |
| `openai/gpt-5-mini` | 62/472 (13.1% [10.4% - 16.5%]) | 204/676 |

## Committed-silent rate, non-clean conditions

Same framing as SILENT_COMMIT.md: `clean` excluded, since silent computation there is correct behavior, not danger.

| condition | committed_silent/total (Wilson 95% CI) |
|---|---|
| `missing` | 10/182 (5.5% [3.0% - 9.8%]) |
| `value_conflict` | 125/189 (66.1% [59.1% - 72.5%]) |
| `resolvable` | 531/795 (66.8% [63.4% - 70.0%]) |
| `contradiction` | 403/740 (54.5% [50.9% - 58.0%]) |

**Interpretation.** 681/3380 (20.1%) of program_aided responses are `unparseable` -- no attempted computation and no abstention phrase detected -- and are excluded from every denominator above. This is expected to be higher than open_ended's near-zero unparseable rate: program_aided has no output-format instruction, so a real fraction of responses compute a value only inside unexecuted code with no restatement in text, which is honestly unrecoverable rather than a bug. The flagged/acknowledged/silent classification itself was hand-validated against real cached completions across multiple rounds (samples read directly, false positives found and fixed in `scoring_program_aided.py`), so the *labels* here carry similar confidence to `open_ended`/`mcq`'s, even though no extracted-value accuracy check accompanies them.

## Three-way comparison: open_ended vs. mcq vs. program_aided

**What this measures.** One overall test per family for whether flag rate differs across all three formats at once, rather than inferring it from two separate pairwise deltas. Cochran's Q is the paired-samples test for exactly this -- the generalization of McNemar's test from two related samples to three or more. It needs a complete row for every item (all three formats scored), so it runs on the subset where program_aided actually produced a real label -- `unparseable` rows are excluded from this test specifically, which is why its matched `n` is smaller than the family's full size, shown alongside the exclusion count in the same row rather than left implicit.

| family | flagged (open-ended) | flagged (mcq) | flagged (program_aided) | Cochran's Q | df | p | n (matched, all 3 parseable) | program_aided unparseable excluded |
|---|---|---|---|---|---|---|---|---|
| `A` | 2.2% | 17.2% | 12.3% | 52.7 | 2 | 3.6e-12 * | 413 | 112/525 |
| `B` | 3.4% | 23.1% | 23.8% | 70.3 | 2 | 5.35e-16 * | 386 | 214/600 |
| `C` | 22.8% | 48.8% | 15.5% | 152.1 | 2 | 9.6e-34 * | 400 | 50/450 |
| `breadth` | 16.8% | 24.5% | 20.4% | 19.9 | 2 | 4.82e-05 * | 770 | 235/1005 |
| `dissociation` | 41.8% | 43.2% | 17.3% | 262.0 | 2 | 1.27e-57 * | 730 | 70/800 |

**Interpretation.** Cochran's Q is significant (p < 0.01) for every family, confirming the three formats don't all produce the same flag rate -- consistent with the pairwise deltas below, which show *which* pairs differ and in which direction. The `program_aided unparseable excluded` column is the same coverage gap reported throughout this doc, shown here directly against the test it affects: for breadth, for example, 235/1005 items (23%) couldn't enter this specific test because program_aided produced no usable label for them, so the 3-way comparison for that family rests on the remaining 770.

## Open-ended vs. mcq vs. program_aided flag-rate delta

Extends the paper's Table 11 (open_ended vs. mcq) with program_aided as a third arm in the same table -- "was offering an exit enough" (mcq) alongside "does writing code instead of prose change flagging behavior" (program_aided), both measured against the same open_ended baseline, **on the same matched set of items for both comparisons** -- the same subset used by the three-way Cochran's Q table above (all three formats produced a real label; program_aided's `unparseable` rows excluded). One consequence: because that subset is smaller than the full family, `flagged (open-ended)` and `flagged (mcq)` here will not exactly match Table 11's numbers (which use the full family) -- everything in *this* doc is internally consistent with itself instead, so nothing needs a separate explanation for why two numbers in the same table differ.

| family | flagged (open-ended) | flagged (mcq) | Δ (mcq − open_ended), pp | p (McNemar) | flagged (program_aided) | Δ (program_aided − open_ended), pp | p (McNemar) | n (matched, shared) |
|---|---|---|---|---|---|---|---|---|
| `A` | 2.2% | 17.2% | +15.0 | 1.65e-15 * | 12.3% | +10.2 | 7.46e-09 * | 413 |
| `B` | 3.4% | 23.1% | +19.7 | 4.14e-17 * | 23.8% | +20.5 | 1.42e-16 * | 386 |
| `C` | 22.8% | 48.8% | +26.0 | 3.57e-20 * | 15.5% | -7.3 | 0.000767 * | 400 |
| `breadth` | 16.8% | 24.5% | +7.8 | 3.79e-09 * | 20.4% | +3.6 | 0.0535 | 770 |
| `dissociation` | 41.8% | 43.2% | +1.4 | 0.193 | 17.3% | -24.5 | 1.08e-35 * | 730 |

`n (matched, shared)` excludes `unparseable` program_aided rows from that family's full item×model count, same exclusion as the Cochran's Q table above: `A` 112/525 excluded; `B` 214/600 excluded; `C` 50/450 excluded; `breadth` 235/1005 excluded; `dissociation` 70/800 excluded.

**Interpretation.** mcq's delta is positive for every family -- offering an explicit abstain option always increased flagging. program_aided's deltas go in *both* directions: `C`/`dissociation` actually flag *less* under program_aided than under open_ended, most sharply dissociation (-24.5pp) and Family C (-7.3pp). A and B still increase under program_aided, same direction as mcq but by less. This is a real, unexpected pattern worth flagging rather than smoothing over -- writing code instead of reasoning in prose does not uniformly make models more willing to decline; for some families it appears to make them less willing, plausibly because committing to a specific value inside code reads as more binding than a plain-text final answer, though that explanation is speculative and not established by this table alone.
