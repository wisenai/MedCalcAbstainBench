# Order flip: does the cue's position explain resolvable accuracy?

**Task owner:** Annotator D. Companion to `docs/WEEK3_FLIPPED_ORDER_RESULT.md`, which reports flag
rates on the same run. This file reports the number that motivated building the flipped set.

## The problem this tests

The paper's central inference is that a model answering the resolvable condition correctly must
have read both conflicting values, so silence on the byte-identical conflicting twin is a decision
about reporting rather than a failure to read.

That inference has a hole. In the shipped dissociation arm the cue names the **first** of the two
values as written, in all forty items. A model that reads only the first number and ignores the
second would answer correctly every time, and resolvable accuracy would look identical whether or
not the second value was ever processed.

`flip_order.py` builds the twin that separates these. The two values appear in reverse order, the
cue names the same value, and the correct answer is unchanged. The cued value is now **second**. A
model attending only to the first number now computes the wrong result.

## Result

Scored at the 5% relative tolerance `score.py` uses, across five models and forty base notes.

| set | cued value position | prompt | correct | accuracy |
|---|---|---|---|---|
| original | first | `open_ended` | 163/200 | 81.5% [75.5% – 86.3%] |
| **flipped** | **second** | `open_ended` | **171/200** | **85.5% [80.0% – 89.7%]** |
| **flipped** | **second** | `neutral_exit` | **175/200** | **87.5% [82.2% – 91.4%]** |

**Accuracy does not fall when the cued value moves to second position.** It is slightly higher, and
the intervals overlap, so the honest reading is that position has no detectable effect on whether
the model retrieves the cued value.

## What this licenses

Had accuracy collapsed, the extraction-failure argument would have been an artifact of ordering and
would have survived only in Family B, whose cue already names the second-stated number. It did not
collapse. Models locate the cued value whichever position it occupies, which means they are reading
past the first number rather than pattern-matching to it.

The comprehension control therefore holds across the whole dissociation arm, not only Family B.

## Reading vs. reporting come apart

Set against the flag rates in `docs/WEEK3_FLIPPED_ORDER_RESULT.md`, the two measures behave
differently under the same manipulation:

| measure | original | flipped | change |
|---|---|---|---|
| resolvable accuracy (does it read both?) | 81.5% | 85.5% | no detectable effect |
| value_conflict flag rate (does it say so?) | 64.0% | 54.5% | −9.5pp, p = 0.0026 |

Order does not change what the model reads. It does change whether the model says anything. That is
the paper's thesis appearing a second time, in a manipulation designed to test something else.

## Reproducing

```
python3 flip_order.py --build
```

Completions for all 800 flipped conditions are in `cache/`. Accuracy above is computed by
extracting the `FINAL:` value and comparing against `correct_answer` at 5% relative tolerance.

## For the paper

Two sentences, in Methods where the resolvable condition is defined:

> In the dissociation arm the cue names the first of the two values as written, so a model
> attending only to the first number could answer correctly without reading the second. We
> therefore rebuilt all forty items with the order reversed, holding the cue and the correct answer
> fixed: accuracy was 85.5% with the cued value second against 81.5% with it first, so position
> does not account for the result.
