# Week 2 -- Task 1 (+ Task 3) result

Non-commitment (`flagged`) rate by condition, per arm. `clean` is a third
row in the same table as `missing`/`value_conflict` (Task 3 -- "as
prominently as the flag rate," not a separate file).

Delta and the paired McNemar test are PREREGISTRATION.md sect3's binding
definition of "the missing-vs-value-conflict difference within note" --
reported alongside the counts/Wilson-interval figures the task literally
asks for, at no extra cost.

## open_ended

| condition | task | flagged/total (Wilson 95% CI) |
|---|---|---|
| `missing` | Task 1 | 39/40 (97.5% [87.1% - 99.6%]) |
| `value_conflict` | Task 1 | 27/40 (67.5% [52.0% - 79.9%]) |
| `clean` | Task 3 | 1/40 (2.5% [0.4% - 12.9%]) |

**Task 1.** n = 40 paired notes. Delta (missing - value_conflict) = 30.0 pp. Paired McNemar exact p = 0.0004883 (significant at alpha=0.01).

## neutral_exit

| condition | task | flagged/total (Wilson 95% CI) |
|---|---|---|
| `missing` | Task 1 | 39/40 (97.5% [87.1% - 99.6%]) |
| `value_conflict` | Task 1 | 1/40 (2.5% [0.4% - 12.9%]) |
| `clean` | Task 3 | 1/40 (2.5% [0.4% - 12.9%]) |

**Task 1.** n = 40 paired notes. Delta (missing - value_conflict) = 95.0 pp. Paired McNemar exact p = 7.276e-12 (significant at alpha=0.01).
