# The assembled pilot dataset

**Task owner:** nobody — this is the seam between Annotator A's cache and Annotator C's scorer.
**Written by:** Annotator D, because scoring could not start without it.

`python3 assemble_pilot.py` writes `data/pilot_completions.json` and
`data/pilot_completions.csv`: one row per cached completion, joined to the item it
was generated from. It needs no API key and no third-party packages, so it runs in
CI and on a laptop.

## Why this file exists

Annotator A's clauses cover the harness and the cache. Annotator C's cover `score.py` and
`stats.py`. Neither covers the step in between — working out which item and
condition each cached completion belongs to — so both halves were finished and
nothing could be scored. This is only that step.

**It deliberately does not assign labels.** `assigned_label`, `value_correct`,
`extracted_value`, and `justification_span` are emitted empty, and a test asserts
they arrive that way. Filling them is Annotator C's Week 2 clause, not this file's job.

## The join is exact

`run.py` addresses the cache as `sha256(f"{model}_{item_id}_{prompt_id}_{format}")`
with `item_id = f"{seed_id}_{condition}"`, so every cell's filename is computed
from the frozen item set rather than recovered by matching note text back out of
the prompt.

That distinction is load-bearing. **The `value_conflict` and `resolvable` notes are
byte-identical by construction** — the cue lives in the question, not the note — so
a text-matching join cannot tell those two conditions apart, and confusing them
would corrupt the single comparison the study exists to make. Verified: all 423
rows carry their own note *and* their own question, and no row of either condition
carries the other's question.

## What was assembled

| Arm | Model | Prompt | Cells |
|---|---|---|---|
| `open_ended` | claude-opus-4.8 | `open_ended` | **160** — 40/40 seeds × 4 conditions |
| `neutral_exit` | claude-opus-4.8 | `neutral_exit` | **160** — 40/40 seeds × 4 conditions |
| `reasoning` | claude-opus-4.8 | `open_ended_reasoning` | 40 value-conflict cells (+3 out of scope) |
| `smoke_open` / `smoke_mcq` / `smoke_pal` | gpt-5-mini | 3 formats | 20 each — Annotator A's Week 1 harness check on 5 seeds |

**423 rows. Both pilot arms are complete.**

The smoke-test arms are a harness check, not pilot data, and `PILOT_ARMS` in the
script names the two that carry the primary comparison so they cannot be pooled by
accident.

**9 orphaned cache files are excluded and reported by name.** They are completions
for `mdrd-tr3279`, the seed retired after its creatinine turned out to belong to
the patient's grandmother rather than the patient. They match no current item.
Counting cache files rather than joined rows is exactly how they would come back,
which is why the script prints them rather than silently skipping them.

## Columns

Identity: `item_id`, `seed_id`, `case_id`, `condition`, `variant`, `arm`, `model`,
`prompt_id`, `format`, `calculator`, `calculator_id`.

Truth: `correct_action` (compute / decline / flag), `ground_truth`, `answer_unit`,
`answer_with_second`.

Model output: `completion_text`, `reasoning`, `prompt_text`, `input_tokens`,
`output_tokens`, `cost`.

To be filled by `score.py`: `assigned_label`, `justification_span`,
`extracted_value`, `value_correct`.

`variant` duplicates `condition` under the name `stats.py::generate_paper_table`
already expects, so the scored frame drops straight into it.

**`ground_truth` is `None` for `missing` and `value_conflict` by construction** —
the correct action there is to decline or flag, so any number is wrong. It is
recorded as an explicit `None` rather than an absent key so that stays an assertion
rather than an accident.

## What it guards against

`tests/test_assemble.py` (12 tests, wired into `regression.yml`):

- the key scheme still matches `run.py` — checked by computing a key and requiring
  it to hit a real cached file, because `run.py` cannot be imported to share the
  function (`from google.colab import userdata` at module level);
- a pilot arm covering 39 of 40 seeds **evenly across all four conditions** is
  rejected — balanced and short is the failure that would otherwise pass;
- the reasoning arm, which only ever owned the value-conflict cells, is *not*
  rejected for the cells it never owned;
- the scoring columns arrive empty.

## Two things to know before Week 3

**`run.py` cannot be imported outside Colab.** Line 1 is
`from google.colab import userdata`, unguarded, so any script importing it fails on
a laptop or in CI. `score.py` guards the same import with a try/except and an
`OPENROUTER_API_KEY` fallback; `run.py` should do the same. This file works around
it by not importing `run.py` at all, but the scorer will hit it.

**At full-grid scale the JSON should become a build artifact.** It carries the
completion and prompt text, which already live in `cache/`, so at 5 models × 3
formats × 8 calculators it will be large and entirely regenerable. It is committed
now because it is 2 MB and because the point of this file is that the next person
does not have to run anything to get started.
