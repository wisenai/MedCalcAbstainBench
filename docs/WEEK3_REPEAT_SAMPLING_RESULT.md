# Repeat sampling: within-item consistency, dissociation `value_conflict`

**What this measures.** The paper draws exactly one sample per cell (Appendix B), so there was previously no way to tell whether a given flagged/not-flagged answer was a stable choice or one random draw. This uses two additional independently-generated samples per cell (`sample2`/`sample3`, collected separately and identified here by matching each cached completion's own note+question text against `data/items_dissociation.json`, not by assuming a cache-key format) for the `value_conflict` condition under both `open_ended` and `neutral_exit`, across all 5 models and all 40 dissociation notes -- exactly the comparison Table 3's largest swings (e.g. Opus 67.5% -> 2.5%) rest on.

## Within-item agreement across all 3 samples, by model and prompt

| model | prompt | fully consistent (3/3 agree) | n |
|---|---|---|---|
| `anthropic/claude-opus-4.8` | `open_ended` | 19/40 (47.5% [32.9% - 62.5%]) | 40 |
| `anthropic/claude-opus-4.8` | `neutral_exit` | 40/40 (100.0% [91.2% - 100.0%]) | 40 |
| `openai/gpt-5` | `open_ended` | 35/40 (87.5% [73.9% - 94.5%]) | 40 |
| `openai/gpt-5` | `neutral_exit` | 12/40 (30.0% [18.1% - 45.4%]) | 40 |
| `meta-llama/llama-4-maverick` | `open_ended` | 33/40 (82.5% [68.1% - 91.3%]) | 40 |
| `meta-llama/llama-4-maverick` | `neutral_exit` | 32/40 (80.0% [65.2% - 89.5%]) | 40 |
| `google/gemini-3.6-flash` | `open_ended` | 40/40 (100.0% [91.2% - 100.0%]) | 40 |
| `google/gemini-3.6-flash` | `neutral_exit` | 37/40 (92.5% [80.1% - 97.4%]) | 40 |
| `openai/gpt-5-mini` | `open_ended` | 27/40 (67.5% [52.0% - 79.9%]) | 40 |
| `openai/gpt-5-mini` | `neutral_exit` | 28/40 (70.0% [54.6% - 81.9%]) | 40 |

## Same table, flag-rate recomputed with 3 samples instead of 1

Majority vote across the 3 samples (2-of-3), compared against the original single-sample flag rate for the same cells.

| model | prompt | flag rate (sample 1 only) | flag rate (majority of 3) |
|---|---|---|---|
| `anthropic/claude-opus-4.8` | `open_ended` | 27/40 (67.5% [52.0% - 79.9%]) | 22/40 (55.0% [39.8% - 69.3%]) |
| `anthropic/claude-opus-4.8` | `neutral_exit` | 0/40 (0.0% [0.0% - 8.8%]) | 0/40 (0.0% [0.0% - 8.8%]) |
| `openai/gpt-5` | `open_ended` | 38/40 (95.0% [83.5% - 98.6%]) | 38/40 (95.0% [83.5% - 98.6%]) |
| `openai/gpt-5` | `neutral_exit` | 26/40 (65.0% [49.5% - 77.9%]) | 30/40 (75.0% [59.8% - 85.8%]) |
| `meta-llama/llama-4-maverick` | `open_ended` | 2/40 (5.0% [1.4% - 16.5%]) | 1/40 (2.5% [0.4% - 12.9%]) |
| `meta-llama/llama-4-maverick` | `neutral_exit` | 6/40 (15.0% [7.1% - 29.1%]) | 6/40 (15.0% [7.1% - 29.1%]) |
| `google/gemini-3.6-flash` | `open_ended` | 40/40 (100.0% [91.2% - 100.0%]) | 40/40 (100.0% [91.2% - 100.0%]) |
| `google/gemini-3.6-flash` | `neutral_exit` | 38/40 (95.0% [83.5% - 98.6%]) | 40/40 (100.0% [91.2% - 100.0%]) |
| `openai/gpt-5-mini` | `open_ended` | 21/40 (52.5% [37.5% - 67.1%]) | 19/40 (47.5% [32.9% - 62.5%]) |
| `openai/gpt-5-mini` | `neutral_exit` | 6/40 (15.0% [7.1% - 29.1%]) | 6/40 (15.0% [7.1% - 29.1%]) |

**Interpretation.** 303/400 cells (75.8%) give the identical flagged/not-flagged answer across all 3 independent draws. [Fill in after reading the actual numbers above -- direction and magnitude of any disagreement, and whether it concentrates in specific models/prompts, changes what this paragraph should say.]
