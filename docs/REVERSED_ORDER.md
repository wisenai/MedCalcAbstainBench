# Reversed contradictory-value order -- dissociation arm

**What this measures.** A subset of the dissociation arm's `value_conflict` and `resolvable` notes (40 base notes, both creatinine-dissociation conditions), re-run with the two conflicting values' order reversed in the note text -- the value that appeared first now appears second and vice versa -- to test whether *order*, not just which two values conflict, affects flagging. Run under both `open_ended` and `neutral_exit` prompts, same as the original dissociation pilot. Scored with the same three-way rubric used throughout this project, via `score.py`'s classification logic reimplemented standalone here for local computation.

## Flag rate, flipped order

| condition | prompt | flagged/total (Wilson 95% CI) |
|---|---|---|
| `value_conflict_flipped` | `open_ended` | 109/200 (54.5% [47.6% - 61.3%]) |
| `value_conflict_flipped` | `neutral_exit` | 68/200 (34.0% [27.8% - 40.8%]) |
| `resolvable_flipped` | `open_ended` | 0/200 (0.0% [0.0% - 1.9%]) |
| `resolvable_flipped` | `neutral_exit` | 0/200 (0.0% [0.0% - 1.9%]) |

## Order effect: original vs. flipped, paired per item

Same 40 seed notes, same models, same prompts -- only the stated order of the two conflicting values differs. Paired McNemar test per condition per prompt; significance at alpha=0.01 (matching this project's standard McNemar threshold, stricter than the 0.05 used for Wilson CIs).

| condition | prompt | flagged (original) | flagged (flipped) | Δ (flipped − original), pp | p (McNemar) | n pairs |
|---|---|---|---|---|---|---|
| `value_conflict` | `open_ended` | 64.0% | 54.5% | -9.5 | 0.00256 * | 200 |
| `value_conflict` | `neutral_exit` | 38.0% | 34.0% | -4.0 | 0.256 | 200 |
| `resolvable` | `open_ended` | 2.0% | 0.0% | -2.0 | 0.125 | 200 |
| `resolvable` | `neutral_exit` | 0.0% | 0.0% | +0.0 | 1 | 200 |

**Interpretation.** Order has a statistically significant effect on flag rate in 1 of 4 condition-prompt pairs tested: `value_conflict`/`open_ended` (-9.5pp, p=0.00256). This means which value the model reads first is not a neutral framing choice -- it measurably changes whether the model notices and flags the conflict, independent of which two values are actually in conflict.
