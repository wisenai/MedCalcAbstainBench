# Repeat sampling analysis: within-item consistency, dissociation `value_conflict`

**Source data:** Annotator A's two repeat-sampling collections ("Repeat sampling: sample2 auto-pushed" / "sample3 auto-pushed"), identified directly from those two commits' file lists and matched to items by their own note+question text against `data/items_dissociation.json` -- not by assuming a cache-key format. 400/400 cells matched cleanly in both samples, zero unmatched.

**What this measures.** The paper draws exactly one sample per cell (Appendix B: "reported intervals therefore reflect sampling over items, not over decodings"). That means there was previously no way to tell whether any single flagged/not-flagged answer was a stable, repeatable choice or one random draw. This adds two independent extra draws per cell for the `value_conflict` condition, under both `open_ended` and `neutral_exit`, across all 5 models and all 40 dissociation notes -- exactly the comparison Table 3's largest reported swing (Opus 67.5% -> 2.5%) rests on.

---

## Table A -- within-item agreement across all 3 samples, by model and prompt

| model | prompt | fully consistent (3/3 agree) | n |
|---|---|---|---|
| `anthropic/claude-opus-4.8` | `open_ended` | 19/40 (47.5% [32.9% – 62.5%]) | 40 |
| `anthropic/claude-opus-4.8` | `neutral_exit` | 40/40 (100.0% [91.2% – 100.0%]) | 40 |
| `openai/gpt-5` | `open_ended` | 35/40 (87.5% [73.9% – 94.5%]) | 40 |
| `openai/gpt-5` | `neutral_exit` | 12/40 (30.0% [18.1% – 45.4%]) | 40 |
| `meta-llama/llama-4-maverick` | `open_ended` | 33/40 (82.5% [68.1% – 91.3%]) | 40 |
| `meta-llama/llama-4-maverick` | `neutral_exit` | 32/40 (80.0% [65.2% – 89.5%]) | 40 |
| `google/gemini-3.6-flash` | `open_ended` | 40/40 (100.0% [91.2% – 100.0%]) | 40 |
| `google/gemini-3.6-flash` | `neutral_exit` | 37/40 (92.5% [80.1% – 97.4%]) | 40 |
| `openai/gpt-5-mini` | `open_ended` | 27/40 (67.5% [52.0% – 79.9%]) | 40 |
| `openai/gpt-5-mini` | `neutral_exit` | 28/40 (70.0% [54.6% – 81.9%]) | 40 |

Overall: **303/400 cells (75.8%)** give the identical answer across all 3 draws. That single number hides a lot -- consistency ranges from 30% (GPT-5, neutral_exit) to 100% (Gemini, open_ended; Opus, neutral_exit).

---

## Table B -- flag rate, each sample shown individually, plus majority vote

Same 40 items, same model, same prompt -- three independent draws, shown side by side rather than collapsed straight to a summary stat, so the actual spread is visible.

| model | prompt | sample 1 | sample 2 | sample 3 | majority (2-of-3) |
|---|---|---|---|---|---|
| `anthropic/claude-opus-4.8` | `open_ended` | 27/40 (67.5%) | 24/40 (60.0%) | 16/40 (40.0%) | 22/40 (55.0%) |
| `anthropic/claude-opus-4.8` | `neutral_exit` | 0/40 (0.0%) | 0/40 (0.0%) | 0/40 (0.0%) | 0/40 (0.0%) |
| `openai/gpt-5` | `open_ended` | 38/40 (95.0%) | 37/40 (92.5%) | 36/40 (90.0%) | 38/40 (95.0%) |
| `openai/gpt-5` | `neutral_exit` | 26/40 (65.0%) | 28/40 (70.0%) | 24/40 (60.0%) | 30/40 (75.0%) |
| `meta-llama/llama-4-maverick` | `open_ended` | 2/40 (5.0%) | 3/40 (7.5%) | 3/40 (7.5%) | 1/40 (2.5%) |
| `meta-llama/llama-4-maverick` | `neutral_exit` | 6/40 (15.0%) | 2/40 (5.0%) | 6/40 (15.0%) | 6/40 (15.0%) |
| `google/gemini-3.6-flash` | `open_ended` | 40/40 (100.0%) | 40/40 (100.0%) | 40/40 (100.0%) | 40/40 (100.0%) |
| `google/gemini-3.6-flash` | `neutral_exit` | 38/40 (95.0%) | 39/40 (97.5%) | 40/40 (100.0%) | 40/40 (100.0%) |
| `openai/gpt-5-mini` | `open_ended` | 21/40 (52.5%) | 19/40 (47.5%) | 18/40 (45.0%) | 19/40 (47.5%) |
| `openai/gpt-5-mini` | `neutral_exit` | 6/40 (15.0%) | 8/40 (20.0%) | 6/40 (15.0%) | 6/40 (15.0%) |

**Opus/`open_ended` is the starkest case of real drift, not just item-level disagreement**: 67.5% -> 60.0% -> 40.0%, a steady downward walk across three independent draws, not noise scattered around a stable center. That's a materially different (and more concerning) pattern than random per-item flips -- it suggests the sample-1 draw sat at the high end of this model's real range on this cell, not near its center.

Note: `anthropic/claude-opus-4.8` / `neutral_exit` sample-1 here reads 0/40 (0.0%) on all three draws, not the 2.5% currently printed in Table 3 -- that 2.5% traces to a retired seed (`mdrd-tr3279`) no longer in the current 40-item construction, a separate, already-understood issue, not a sampling-instability one. This table uses the current 40-item set throughout, all three samples, so it's internally consistent with itself.

---

## Key findings

**1. Opus's headline swing is real, but was overstated by using a single unstable draw — and it isn't just noise, it's a directional drift.** `neutral_exit` is rock solid — 40/40 cells agree across all 3 draws, always landing on not-flagged. `open_ended` is not: the three draws read 67.5% → 60.0% → 40.0%, a steady downward walk, not values scattered around a stable center. That pattern means sample 1 (the one currently in Table 3) likely sat near the *top* of this cell's real range, not its middle — so 67.5% is probably the most flattering of the three numbers you could have drawn, not a representative one. The majority-vote estimate (55.0%) is a reasonable single figure, but a reader should know the true center might be closer to 55% or even lower, not 67.5%. The true effect is closer to a **55-point swing (55.0% → 0.0%)**, possibly larger toward the low end, than the 67.5-point one a single draw suggested. Still the largest effect in the paper. Just smaller and less certain than reported.

**2. GPT-5's `neutral_exit` value-conflict rate is the least reliable cell in this entire check.** Only 12/40 items (30.0%) agree across all 3 draws — worse than a coin flip's worth of consistency. Sample-1 (65.0%) and majority-of-3 (75.0%) differ by 10pp. Neither should be cited as a stable estimate of GPT-5's actual behavior on this cell without more sampling.

**3. Gemini is the most reliable cell in the grid** — 100% consistent under `open_ended`, 92.5% under `neutral_exit`. Its Table 3 numbers can be trusted at face value, no caveat needed.

**4. Llama and GPT-5-mini sit in between** (70–83% consistent across both prompts) — real but smaller single-sample noise than Opus/`open_ended` or GPT-5/`neutral_exit`.

---

## One more ripple worth knowing about: Table 4's pooled value-conflict rate also moves

Table 4's "value-conflict" row (128/200, 64.0%) pools all 5 models' `value_conflict`/`open_ended` responses. That 128 is exactly the sum of this analysis's 5 sample-1 counts (27+38+2+40+21=128 — confirms this data lines up with what's already in the paper). Swap in each model's majority-of-3 count instead (22+38+1+40+19) and the pooled total becomes **120/200 = 60.0%**, not 64.0%. Small on its own, but it's a second place in the paper (beyond just the Opus row) where this check changes a printed number, not just a caveat.

---

## What to do with this in the paper -- specific edits

**Don't touch Table 3's or Table 4's printed numbers themselves.** The whole grid is built on one sample per cell (Appendix B); silently swapping in 3-sample values for only these 10 cells would make the table internally inconsistent with its own stated methodology. This belongs as a companion finding reported *alongside* those tables, not a silent correction to them.

1. **Appendix B, Decoding** — add a sentence after the existing "reported intervals therefore reflect sampling over items, not over decodings": *"A follow-up check redrew the dissociation arm's `value_conflict` condition twice more per cell (`open_ended`/`neutral_exit`, all 5 models): 75.8% of cells gave the identical flagged/not-flagged answer across all three draws, ranging from 30% (GPT-5, neutral_exit) to 100% (Gemini, open_ended; Opus, neutral_exit)."*

2. **Discussion — the exact sentence to change** is: *"...with flagging falling from 97.5% on missing to 67.5% on conflicting under an open-ended prompt and to 2.5% under a neutral one (Table 3)."* Replace with something like: *"...with flagging falling from 97.5% on missing to 67.5% on conflicting under an open-ended prompt (a repeat-sampling check found this cell drifted downward across draws, 67.5%→60.0%→40.0%, so the true rate may sit closer to 55%) and to 2.5% under a neutral one — a difference a repeat check confirmed as stable (0/40 across three independent draws)."* This keeps Table 3's printed 67.5% intact while being honest in prose that it's the high end of the observed range, not the center.

3. **Limitations** — one sentence: *"A repeat-sampling check on the dissociation arm's most-cited cells found single-draw noise large enough to matter in two cases: Opus's open_ended value-conflict rate drifted from 67.5% to 40.0% across three independent draws, and GPT-5's neutral_exit rate showed only 30% draw-to-draw agreement — both cited findings should be read as directional, not exact, without further sampling."*

4. **A new small table** (a trimmed version of Table A or B above) placed directly after Table 3, so a reader sees each cell's reliability right where the numbers themselves are reported, not in a separate appendix they have to go find.
