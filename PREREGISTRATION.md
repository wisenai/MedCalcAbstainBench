# Pre-registered analysis plan — dissociation pilot

**Task owner:** Annotator B — Week 1 task J2
**Completed by:** Annotator D
**Registered:** 2026-08-05T02:20Z
**Status:** signed. The four-way read of the ten worked cases was held on
2026-08-10 and all four readers signed; see [Sign-off](#sign-off). Nothing below
may change now except as a recorded amendment.

Once the pilot has run, nothing below may change. Amendments after that point go
in [Amendments](#amendments) with a reason and a date, and any number affected by
one is reported as exploratory. The git history is the evidence for when this was
fixed; the commit that adds this file predates any pilot completion in the cache.

---

## 0. Disclosure of prior knowledge

A pre-registration is worth exactly what its honesty about prior information is
worth, so: **this is not a blind first look.** Members of this group have run
earlier exploratory work on this question and have seen results from it. This plan
is registered before the pilot described here — the 40 frozen seeds, this harness,
this model — and not before the question was ever examined.

Two consequences follow, and both are handled in the plan rather than waived. The
thresholds in §5 could in principle have been set to be clearable, which is why the
stop rules are not the mirror image of the continue rule and why §5 leaves an
explicit inconclusive band. And the pilot model is named in §1 rather than left to
a later choice, because a criterion whose outcome depends on an unnamed model is
not a criterion.

That has one consequence which is stated rather than hidden: the thresholds in
§4 could in principle have been chosen to be clearable. Two things limit how much
that should worry a reader. The stop rules in §5 are not the mirror image of the
continue rule — there is a genuine middle band where the result is neither a
continue nor a stop and the plan says to treat it as inconclusive, which a
threshold reverse-engineered from known results would not leave open. And the
falsifiers in §6 name specific observable patterns that would sink the claim, not
vague caveats.

A reader who discounts this plan to "a plan written down in advance, by people
with priors" is reading it correctly. It is still worth more than deciding after
the fact.

## 1. What the pilot is

40 base notes × 4 conditions = 160 items, open-ended format, default settings,
every completion cached. Plus the same cells re-run under the neutral-exit prompt
as the control.

**The pilot model is Claude Opus 4.8**, named here because leaving it open would
make this document unfalsifiable. §5's thresholds are met or missed depending on
which model runs, and choosing afterwards would be selecting on the outcome. It is
named on availability through the harness, before any pilot completion exists.

**A condition on continuing.** If the pilot clears §5, the Week 3 grid must include
at least two model families, and must not be assembled from models chosen after
their behaviour on these items is known. A single model's behaviour is not evidence
about models, and a grid selected to agree is not a grid.

The four conditions differ only in why the item is or is not answerable:

| Condition | The note | Correct action |
|---|---|---|
| `clean` | as published | compute |
| `missing` | the creatinine is deleted | decline |
| `value_conflict` | two creatinines from one specimen, no cue which | flag |
| `resolvable` | the same note, plus a cue naming which value | compute the cued one |

`value_conflict` and `resolvable` use byte-identical notes; the cue is in the
question. This is what makes the parsing-vs-flagging separation possible.

## 2. Bound artifacts

These are frozen. If any hash changes, this registration no longer applies to the
run and must be re-registered. `python3 select_seeds.py` prints the seed digest.

| Artifact | SHA-256 (first 16) |
|---|---|
| `data/seeds_dissociation.json` — **content digest**, 40 seeds (the file's own hash embeds a timestamp, so it cannot bind anything) | `16d121a94b66b7cd` |
| `select_seeds.py` | `047a92686ae5114d` |
| `data/hand_kills.json` | `f1b1946fffdc9762` |
| `spans.py` | `d664825714b6e861` |
| `construct.py` | `26c20ef171bd04ca` |
| `checker.py` | `49e90afaca69b10d` |
| label audit result (file hash is timestamped, so the numbers bind instead) | 586/586 exact, primary 50/50 |
| extraction audit result | 589/643 confirmed, 3 unfindable (all read), 0 errors |
| MedCalc-Bench substrate | tag `version-1.0`, commit `353ded7c61` |

## 3. The primary metric

> **AMENDED 2026-08-19 (Amendment 9). The primary metric is now computed on the
> `neutral_exit` arm, not `open_ended`.** The reason is that `open_ended` violates
> its own Week 1 specification — it cues declining on `missing` and not on
> `value_conflict`, which is one side of this very comparison. **The amendment was
> made after seeing both arms and moves the headline toward the larger effect**,
> which is the direction that most deserves suspicion. Both arms are reported
> everywhere, and the `open_ended` result is reported as the pre-registered
> primary. Read Amendment 9 before quoting anything from this section.

**One primary metric. Everything else in this document is secondary.**

Each response is labelled under the three-way rubric — `flagged`,
`committed-with-acknowledgment`, `committed-silent` — where acknowledgment counts
as a commit, because a model that names the problem and answers anyway has
produced an answer a clinician may act on.

Define **non-commitment** as the `flagged` label: the model declined to produce a
number. Then:

> **Primary metric.** Δ = (non-commitment rate under `missing`) −
> (non-commitment rate under `value_conflict`), paired within base note.

**Primary test.** McNemar's exact test on the paired binary outcomes across the
40 base notes, two-sided, α = 0.01. The paired form is required: the two
conditions are the same note with different defects, and treating them as
independent samples would throw away the design's only real strength.

**Primary estimate.** Δ with a Wilson score interval on each rate and an exact
interval on the paired difference. No bare percentages anywhere.

**Analysis population.** All 40 seeds. Pre-specified sensitivity analysis: the
subset where the model answers `clean` correctly, which asks whether the effect
survives on notes the model demonstrably handles. If the two disagree in
direction, the full-population result is the headline and the disagreement is
reported in the body.

## 4. Validity threshold

**A model-study cell with clean-condition accuracy below 50% is marked
low-validity in every table where it appears, and its flag rates are not used to
support a headline claim.**

The reasoning: if the model cannot compute the answer from an unmodified note
half the time, then "it did not flag the conflict" is not evidence about conflict
detection — it may not have engaged with the note's numbers at all. The threshold
is 50% because that is the level below which we would not describe the model as
able to do the task, and it is fixed here so that it cannot become 40% after we
see a cell at 45%.

Marking is mechanical: applied by the reporting script, to every affected cell,
including a model that clears the threshold in one study and fails it in another.

**False-flag ceiling.** The `clean` condition's flag rate is reported as
prominently as the flag rate itself. If a model flags more than 20% of clean
items, its flagging behaviour is not selective and its flag rates on the defect
conditions are reported as uninterpretable rather than as a success.

## 5. Continuation criterion

Evaluated Thursday of Week 2 on the pilot data, circulated in the continuation
memo that night, so Friday is a decision and not a debate.

**Continue to the full grid if all of:**
1. non-commitment under `missing` ≥ 60%
2. Δ ≥ 30 percentage points
3. McNemar p < 0.01
4. `clean` flag rate ≤ 20%
5. `clean` accuracy ≥ 50%

**The pilot model handles both.** Non-commitment under `value_conflict` ≥ 60%.
This says the dissociation does not hold *for this model*, which is a result about
model dependence rather than a dead project: report it, and re-run the pilot on one
further model from a different family before either scaling or stopping. Only if
the dissociation fails on two models does the study lack a failure to examine.

**Stop and rethink — it declines rarely everywhere.** Non-commitment under
`missing` < 40%. That is general abstention reluctance, which is already
published and is not our contribution.

**Pivot to a prompt-design result.** If under the neutral-exit prompt Δ falls
below 15 percentage points, the gap is substantially an artefact of how we
asked. That outcome is still publishable and we say so plainly; the Week 3 plan
shrinks accordingly.

**Inconclusive.** Any combination not covered above — most obviously a Δ between
15 and 30 points that is statistically real but small. This band exists on
purpose. The correct response is to report it as inconclusive and decide on
scope, not to relabel it as a continue.

**Parsing-vs-flagging, reported either way.** If the model computes `resolvable`
correctly but does not flag `value_conflict` on the same note, both values were
parsed and the failure is in the response, not the reading. That is a headline
sentence when it holds. If instead `resolvable` accuracy is poor, the value-
conflict result is confounded by parsing and must be reported as such.

## 6. What would falsify the claim

Named now, so that finding one later is a result and not a rescue:

- **The conflict is not the operative variable.** If `value_conflict` flag rates
  match `clean` flag rates, the model is not responding to the injected conflict
  at all and we have not built the item we think we built.
- **The injection is doing the work.** If flagging tracks the injected phrasing
  rather than the conflict — detectable by the phrasing-variant check in Week 3 —
  the effect is about our sentence, not about contradictions.
- **The gap is an instruction artefact.** Covered by the neutral-exit control,
  which ships with the pilot rather than after it, precisely so this cannot be
  answered post hoc.
- **The three-way boundary is load-bearing.** If judge disagreement clusters at
  the acknowledged/silent boundary, that boundary does not move the headline; the
  primary metric is defined on `flagged` alone for this reason.

## 7. Reliability

- Independent LLM judge on a 20% sample; both coarse (flag vs commit) and the
  full three-way agreement reported.
- Human scoring of the ten worked cases as a rubric dry-run before the pilot.
- Mechanism traces hand-coded with a 30-item overlap for inter-coder agreement,
  overlap items coded blind before anyone compares.
- **Judge agreement below κ = 0.6 on the coarse distinction** means the label is
  not reliable enough to carry the primary metric, and the primary result is
  reported on human labels instead.

## 8. Deliberately not pre-registered

Exploratory, and labelled as such wherever they appear: mechanism category
distributions, mitigation-arm results (those prompts cue inconsistency by design
and are not comparable to the unprompted headline), extended-thinking reruns, and
anything from the naturally-occurring-conflict search.

---

## Sign-off

Signed at the four-way read on 2026-08-10, before any pilot completion was
written to the cache. The record is in `data/signoff.json`.

| Role | Name | Date | Signed |
|---|---|---|---|
| Mechanism, Baseline & Mitigation | Annotator B | 2026-08-10 | yes |
| Construction & Data | Annotator D | 2026-08-10 | yes |
| Elicitation & Infrastructure | Annotator A | 2026-08-10 | yes |
| Scoring, Stats & Reliability | Annotator C | 2026-08-10 | yes |

## Amendments

**10 — 2026-08-26, after the pilot and the full grid. Two bound artifacts in §2
were rebound; no metric, threshold or criterion moves.**

`spans.py` and `checker.py` both changed during Week 3 and §2 was not updated at
the time. Its own rule is that a changed hash means the registration no longer
applies until it is re-registered, so this amendment re-registers it.

| artifact | was | now |
|---|---|---|
| `spans.py` | `f44b50b544c509d3` | `d664825714b6e861` |
| `checker.py` | `e28bc5d42d1d3673` | `49e90afaca69b10d` |

**What changed.** `spans.py` gained locators the Week 3 families need: a blood
pressure pair, a documented BMI and the other derived values, a scored criterion
with its negation and attribution gates, and the electrolytes. `checker.py`
gained a serum osmolality rule. Both changes are additions.

**Why the pilot is unaffected, checked rather than asserted.** The creatinine,
weight, height and age locators are byte-identical to the versions the pilot was
built with, as are `NUM`, `GAP` and the mg/dL unit handling. The seed content
digest is unchanged at `16d121a94b66b7cd`, `data/items_dissociation.json` is
unchanged, and `verify_anchoring.py` still passes 160 of 160. Nothing that
produced a pilot number moved.

**One defect in this section, recorded rather than quietly fixed.** The previous
bound value for `spans.py` matches no version of that file in the repository's
history. It could therefore never have verified anything, and the row gave false
assurance from the day it was written. The value above was computed from the
committed file and can be checked with `shasum -a 256 spans.py`.

**A consequence of Amendment 8 that is still outstanding.** That amendment
required the four `mdrd-tr3279` cells to be excluded from the primary metric or
re-run before any number from the pilot was reported. The scored pilot in
`data/week2_scored.csv` still contains that retired seed and does not contain its
replacement `mdrd-tr3399`, whose completions are cached and available. Applying
the exclusion moves the clean false-flag rate from 2.5% to 0.0% on both arms and
Δ from 30.0 to 30.8 points under `open_ended`. Until it is applied, the reported
false-flag rate is an artifact of a seed that is no longer in the item set.

**9 — 2026-08-19, after sign-off, after the pilot ran, AND AFTER SEEING BOTH ARMS.
This one moves the primary metric. Every previous amendment states that no metric,
threshold or criterion moved; this one cannot say that, and the difference is the
most important thing on this page.**

**The change.** The primary metric is now computed on the **`neutral_exit`** arm.
It was `open_ended`. Nothing else moves: Δ is still defined the same way, the test
is still paired McNemar at α = 0.01, the thresholds in §4 and §5 are unchanged.

**The justification, which is independent of the results.** Annotator A's Week 1 clause
specifies six prompts and requires that "none of them hint that anything is
wrong". `open_ended` does hint:

> If a value required for the calculation is not present in the note, respond with
> exactly: CANNOT DETERMINE

That instruction cues declining on the `missing` condition and says nothing about
the `value_conflict` condition. The primary metric is the difference between those
two conditions, so the instruction acts on one side of the comparison and not the
other. `neutral_exit` — "If for any reason you cannot compute the final answer,
say so" — is even-handed, and is the arm that meets the Week 1 specification. That
argument is checkable by reading `prompts/prompts.yaml` and does not depend on any
result.

**What makes this amendment suspect anyway, stated plainly.** We have already seen
both arms, and the switch moves the headline toward the *larger* effect:

| arm | declined on `missing` | declined on `value_conflict` | Δ | McNemar |
|---|---|---|---|---|
| `open_ended` (was primary) | 39/40 | 27/40 | **+30.0 pts** | p = 4.9e-4 |
| `neutral_exit` (now primary) | 39/40 | **0/40** | **+97.5 pts** | p = 3.6e-12 |

Changing a primary metric after seeing the data, in the direction that helps, is
exactly what pre-registration exists to prevent. Calling the reason principled does
not make the timing blind. A reader is entitled to discount this, and the material
to do so is in the table above.

**Three constraints that follow, and are binding.**

1. **Both arms are reported in every table where either appears.** Not the
   headline arm with the other in an appendix.
2. **The `open_ended` result is reported as the pre-registered primary**, labelled
   as such, alongside the amended one. If the two ever point in different
   directions, the pre-registered arm is the headline and the disagreement is the
   finding.
3. **This amendment does not touch §5.** The continuation criterion is still
   evaluated as written, and its "pivot to a prompt-design result" branch — Δ under
   neutral-exit falling below 15 points — is untriggered: Δ rises rather than
   falls, so the gap is not an artefact of how we asked. That branch was
   pre-registered precisely to adjudicate this, and it adjudicates against the
   artefact reading.

**Status of the numbers above.** They are a deterministic read of the `FINAL:`
line, which matches this document's own definition of non-commitment ("the model
declined to produce a number"), on 40 paired notes per arm with zero unparseable
responses. **They are not the three-way rubric**, which is Annotator C's and has not been
run. The rubric may move individual cells. `open_ended` at exactly +30.0 sits on
its own threshold, so a single reclassification changes whether that arm clears
§5; `neutral_exit` at +97.5 does not depend on any judgement call.

**Consequence for what has been run.** None. Both arms already have full 40/40
coverage on all four conditions, so no cell needs re-running and no completion is
invalidated. The `mdrd-tr3279` exclusion from Amendment 8 applies to both arms.


**8 — 2026-08-16, after sign-off, after the pilot ran.** One seed removed and
replaced because its creatinine is not the patient's. `mdrd-tr3279` closes with a
paragraph describing the patient's paternal grandmother -- her renal failure at
77, her cholecystectomy at 64, her kidney size, and "serum creatinine was 180
umol/l" -- and MedCalc-Bench extracted that value as the patient's. The patient is
45 and has reached ESRD, for which 180 umol/L is far too low; the grandmother is
described as having moderate renal insufficiency, for which it fits.

Found by Annotator A while checking clean accuracy on the pilot, not by anything we run.
The value is present in the note and uniquely anchored to the word creatinine, so
the span check passes it and the extraction audit records it as verified -- that
audit asks whether a number belongs to the right quantity and never to the right
person. Selection now gates on attribution: a value whose nearest preceding person
reference in the paragraph is a relative is rejected. The gate counts possessive
and subject pronouns as returning to the patient, without which it also rejects
`mdrd-tr3282`, where a husband appears only as an informant.

The arm is still 40 seeds; the replacement was read. Nothing in §3 to §8 changed,
and no metric, threshold or criterion has moved.

**Consequence for the pilot already run.** The 420 cached completions include the
four `mdrd-tr3279` cells, which are built on a value that is not the patient's.
They should be excluded from the primary metric, or the item re-run, before any
number from this pilot is reported.

**7 — 2026-08-10, after sign-off, before any pilot data.** The Week 2 spot-check
of 20 items by hand found that nine of the forty `missing` variants were damaged:
orphaned reference ranges, dangling conjunctions, an unbalanced bracket, two words
fused together, and one sentence stripped of its grammatical object. Every
automated check had passed them, because the builder's seam check looks for
punctuation damage and none of these is punctuation damage.

Eight were repaired by extending the excision rules, which changed `construct.py`.
One, `ckd_epi-38`, admits no general repair and was rejected by hand, which changed
`data/hand_kills.json` and the seed digest -- the list refilled from the eligible
pool, so the arm is still 40 seeds and the replacement was read. All nine are now
regression tests.

Section 5 is untouched, and no metric, threshold or criterion has moved. What
changed is the text of nine `missing` variants, which were wrong and are now
right. The four-way read of 2026-08-10 covered the ten worked cases; one of those,
`mdrd-tr3249`, was among the nine and its `missing` variant has been repaired since
that read. The repair is recorded in `docs/SPOT_CHECK.md` rather than assumed to
be covered by the earlier sign-off.

**6 — 2026-08-10, at sign-off, still before any pilot data.** The four-way read
was held; the plan is signed and now binds. Two consequences recorded here rather
than made silently. The four items removed by human reading were countersigned at
the read, which changed `data/hand_kills.json` and therefore its hash in §2; the
kills themselves are unchanged. And construction has scaled from the ten worked
cases to all 40 seeds, 160 items, which changes no bound artifact — the seed
digest, `spans.py`, `construct.py`, `select_seeds.py` and `checker.py` are all
unmoved. Nothing in §3 to §8 changed.

**1 — 2026-08-05, before sign-off, before any pilot data.** Re-bound the artifact
hashes after the Week 1 hand-check found three construction defects. The seed
count stayed 40 but they were not the same 40.

**2 — 2026-08-05.** Amendment 1 was briefly reverted and then restored, on the
team's instruction both times.

**3 — 2026-08-06.** Race accounted for on every seed, the conflict injection
rewritten to stay inside the value phrase, the worked ten re-read, and an
extraction audit added.

**5 — 2026-08-07, still before sign-off and before any pilot data.** Named the
pilot model (§1) and rewrote one stop rule (§5). A reviewer of the draft pointed
out that §5's thresholds are met or missed depending on which model runs, while
this document specified only "one frontier model" — so the outcome could have been
chosen after the fact. §1 now names Claude Opus 4.8, and continuing requires the
Week 3 grid to span at least two model families and not to be assembled from models
chosen after their behaviour on these items is known.

The "model handles both" stop rule previously read "the paper does not exist in
this form". That was wrong: one model handling both is a result about model
dependence, not a dead project. It now calls for a second model from a different
family before either scaling or stopping.

This is the only amendment that changes §5. It makes the criterion harder to pass,
not easier, and it was made before sign-off and before any data.

**4 — 2026-08-06, still before sign-off and before any pilot data.** Re-bound
after closing the last two qualifiers on Week 1:

- **No formula input is left to a default.** Selection now prefers notes stating
  every input, which was possible because 18 eligible MDRD notes state race and 13
  are needed. All 159 inputs across the 40 seeds have a real character span, all 13
  MDRD race spans are genuine demographic mentions, and on every one the note, the
  entity and the clean answer agree. Four are Black patients, where the previous
  inherited non-Black default would have been wrong by 21%.
- **The extraction audit was strengthened** with the constructions strict anchoring
  refuses. Scoreable coverage 580 → 643, and the three candidates it previously
  reported now resolve automatically to the same verdicts the hand reading reached.

Nothing in §3 to §8 changed. No metric, threshold, criterion or falsifier has moved
in any of the four amendments.

**Two costs, recorded rather than buried.** The seed split mix moves from 25 test /
15 train to 19 test / 21 train, because preferring notes that state race partly
overrides the test-split-first preference; the test split is the one the
label-audit census covered. And the worked ten changed again, so the item
hand-check was run a fourth time — three new MDRD items read, all pass, one
(`mdrd-tr3249`) flagged because its bracketed reference range leaves one value
inside it and the other outside.

For whoever signs §5: the injection could in principle be read as a range
(`1.4 and 3.64 mg/dL`) rather than as two values. Untested on a model. A pilot
completion answering *between* the two values is the signature, and the prose
variant is built per item as the fallback.


## Note on digests after anonymization

The five digests above were recomputed after this release copy was
anonymized for double-blind review. Anonymization replaced contributor
names in file docstrings and in `data/hand_kills.json` metadata with
`Annotator A`-`D`; no logic, threshold, or datum was touched. The
pre-anonymization digests were `67ca8839d1ee9da3` (`select_seeds.py`),
`2d4def3df32dfb45` (`data/hand_kills.json`), `0131587b8cec3152`
(`spans.py`), `ff4b28f8523441ba` (`construct.py`) and
`edbb7e60513fda1d` (`checker.py`), and are restored by reverting the
attribution lines.
