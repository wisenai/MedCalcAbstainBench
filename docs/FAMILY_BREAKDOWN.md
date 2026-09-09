# Family-level flag/silent rate -- two presentation options

**What this replaces in the paper.** Table 5 ("Family Flag Rate") and Table 8 ("Silent Committing Rate by Family") currently show a different total for the same family -- e.g. Family A is 525 in Table 5, 350 in Table 8 -- because each table uses its own scope (Table 5 pools all conditions; Table 8 excludes `clean`). Both numbers are individually correct, but showing two different totals for the same family reads as a mismatch. This doc has two options for replacing *both* Table 5 and Table 8 with something that doesn't have that problem -- pick one, below.

**To implement:** pick Option A or Option B and use its table(s) in place of the paper's current Table 5 and Table 8. Don't keep both options in the paper -- they're alternatives for the same two tables, not additions to them.

Both sections below are computed from the same underlying data (`data/scored.csv`, `open_ended` rows). They present it two different ways -- pick whichever reads more clearly.

---

# OPTION A -- single number per family, same total in both tables

Both tables use the SAME denominator per family -- every condition that family has, `clean` included (the true full picture, verified directly against the construction files: Family A really is 35 base notes x 3 conditions x 5 models = 525, with nothing left out). Committed-silent is computed over that identical 525, not a `clean`-excluded subset -- so it now reads as "how often does the model silently compute *anything*" rather than "how often does it silently compute when something was actually wrong," which is a real change in what the number means, not just cosmetic. **Trade-off:** the two tables now always agree on a family's total, but the committed-silent number now mixes in `clean`'s silence alongside the danger-relevant conditions'. In practice this barely moves most families' numbers, since a note's `clean` silence rate turns out close to its non-clean rate either way (Family A: 88.6% `clean`-excluded per the paper's current Table 8, vs. 90.9% pooled here; Family C: 65.0% vs. 66.7%) -- but the *meaning* still changes, from "how often is silence dangerous" to "how often is the model silent, period." If the team wants the danger-only reading preserved, Option B is where it still lives, broken out condition by condition.

### Flag rate by family (all conditions)

| family | flagged/total (Wilson 95% CI) |
|---|---|
| `A` | 9/525 (1.7% [0.9% - 3.2%]) |
| `B` | 17/600 (2.8% [1.8% - 4.5%]) |
| `C` | 108/450 (24.0% [20.3% - 28.2%]) |
| `breadth` | 140/1005 (13.9% [11.9% - 16.2%]) |
| `dissociation` | 329/800 (41.1% [37.8% - 44.6%]) |

### Committed-silent rate by family (all conditions, same totals as above)

| family | committed_silent/total (Wilson 95% CI) |
|---|---|
| `A` | 477/525 (90.9% [88.1% - 93.0%]) |
| `B` | 572/600 (95.3% [93.3% - 96.8%]) |
| `C` | 300/450 (66.7% [62.2% - 70.9%]) |
| `breadth` | 811/1005 (80.7% [78.1% - 83.0%]) |
| `dissociation` | 440/800 (55.0% [51.5% - 58.4%]) |

---

# OPTION B -- full condition-level breakdown, one table per family

**What this measures.** Every open_ended completion for each family (Family A, B, C, the breadth calculators, and the dissociation arm), scored under the same three-way rubric used throughout this project: `flagged` (declined), `committed_with_acknowledgment` (noticed, computed anyway), `committed_silent` (computed with no mention of the problem). Nothing is collapsed into a single total -- every condition a family actually has gets its own row, with its own total/flagged/acknowledged/silent counts, so a family's overall rate under any scope (all conditions, non-`clean`, contradiction only) can be reconstructed directly from visible rows rather than trusted as one collapsed number.

### Family `A`

| condition | total | flagged | acknowledged | silent |
|---|---|---|---|---|
| `clean` | 175 | 0 (0.0%) | 8 (4.6%) | 167 (95.4%) |
| `resolvable` | 175 | 0 (0.0%) | 0 (0.0%) | 175 (100.0%) |
| `contradiction` | 175 | 9 (5.1%) | 31 (17.7%) | 135 (77.1%) |
| **all conditions** | **525** | | | |

### Family `B`

| condition | total | flagged | acknowledged | silent |
|---|---|---|---|---|
| `clean` | 150 | 0 (0.0%) | 0 (0.0%) | 150 (100.0%) |
| `resolvable` | 150 | 0 (0.0%) | 0 (0.0%) | 150 (100.0%) |
| `contradiction` | 300 | 17 (5.7%) | 11 (3.7%) | 272 (90.7%) |
| **all conditions** | **600** | | | |

### Family `C`

| condition | total | flagged | acknowledged | silent |
|---|---|---|---|---|
| `clean` | 150 | 28 (18.7%) | 17 (11.3%) | 105 (70.0%) |
| `resolvable` | 150 | 12 (8.0%) | 14 (9.3%) | 124 (82.7%) |
| `contradiction` | 150 | 68 (45.3%) | 11 (7.3%) | 71 (47.3%) |
| **all conditions** | **450** | | | |

### Family `breadth`

| condition | total | flagged | acknowledged | silent |
|---|---|---|---|---|
| `clean` | 335 | 9 (2.7%) | 7 (2.1%) | 319 (95.2%) |
| `resolvable` | 335 | 6 (1.8%) | 8 (2.4%) | 321 (95.8%) |
| `contradiction` | 335 | 125 (37.3%) | 39 (11.6%) | 171 (51.0%) |
| **all conditions** | **1005** | | | |

### Family `dissociation`

| condition | total | flagged | acknowledged | silent |
|---|---|---|---|---|
| `clean` | 200 | 1 (0.5%) | 3 (1.5%) | 196 (98.0%) |
| `missing` | 200 | 196 (98.0%) | 1 (0.5%) | 3 (1.5%) |
| `value_conflict` | 200 | 128 (64.0%) | 25 (12.5%) | 47 (23.5%) |
| `resolvable` | 200 | 4 (2.0%) | 2 (1.0%) | 194 (97.0%) |
| **all conditions** | **800** | | | |

**Interpretation.** The `contradiction` row is where the proposal's prediction gets tested directly, and it reverses: Family C flags most (68/150, 45.3%), well above B (17/300, 5.7%) and A (9/175, 5.1%) -- the opposite of "flagging should be worst where dodging is impossible." `resolvable` behaves as the near-zero-flag control it was designed to be for A and B (0.0% each), and close to it for breadth (1.8%); C's `resolvable` flag rate (8.0%) is a little higher, consistent with C flagging more readily across the board, not just on `contradiction`.

The breakdown also surfaces a cost that stays invisible in any collapsed total: Family C false-flags 18.7% of its `clean` notes (28/150) -- nothing is wrong with these notes, and no other family comes close (A and B: 0.0%, breadth: 2.7%, dissociation: 0.5%). C's higher contradiction-detection rate does not come for free.

Dissociation's own internal split is visible here too: `missing` is flagged at 98.0% (196/200) while `value_conflict` is flagged at 64.0% (128/200) on the same 40 base notes -- the missing-vs-conflict gap the whole project's H1/H2 argument rests on.
