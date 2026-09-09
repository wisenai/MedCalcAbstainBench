# Week 3 item families — build spec

**Task owner:** Annotator B — Week 1 task J4 · 2026-08-05
**Completed by:** Annotator D
**For:** Annotator D to build from on Monday
**Status:** draft. Sections marked **DECIDE** need a call before building.

Three families of flat self-contradiction, distinguished by what kind of thing the
note contradicts itself about. The distinction is not cosmetic: it is what lets us
say where a non-model approach stops. The deterministic checker should be
near-perfect on A and B and structurally zero on C, and that boundary is one of
our results.

Every example below is a real MedCalc-Bench note, quoted, with the arithmetic
checked against the released implementations. Nothing here is illustrative-only.

---

## What is common to all three

**The contradiction must touch a value the calculator consumes.** A note that
contradicts itself about something the formula ignores produces an item where
declining is not obviously correct, and a model that computes is not obviously
wrong. Every family below is defined on an input or an output of the target
calculator, never on decoration.

**Matched conditions, as in the dissociation arm.** Each base note yields:

| Condition | Note | Correct action |
|---|---|---|
| `clean` | as published | compute |
| `contradiction` | the family's injection | flag |
| `resolvable` | the same injected note, plus a cue naming which value governs | compute the cued value |

`contradiction` and `resolvable` must be byte-identical notes with the cue in the
question, for the same reason as the dissociation arm: it is what makes a correct
`resolvable` answer proof that both values were parsed.

**Reuse the existing machinery.** `spans.py` locates and `construct.py` edits.
Anything that needs a new locator gets a new pattern in `spans.py`, not a
one-off regex in a family script — the anchoring guarantee is the thing that lets
us claim we edited the value the calculator reads.

**Guardrails are assertions in the build, not intentions in a doc.** At minimum,
per family: the edited span is the one the calculator consumes; the note outside
the edit is byte-identical to the original; the injected text contains no cue
word; and the deterministic checker returns the expected verdict for the family.

---

## Family A — a derived value contradicting its own components

**Definition.** The note states a value that is computable from other values the
note also states, and the two disagree.

**Why it is the easiest family.** The contradiction is closed under arithmetic.
Nothing needs to be known about the patient, medicine, or context; two numbers and
a formula settle it. That is exactly why it is the right family to establish the
upper bound of what needs no model.

### Where to build it

Two shapes, and they are not equally strong.

**A1 — the derived value is the calculator's own answer.** Target BMI (calc 6).
The note documents a BMI, the question asks for the BMI, and the documented one
disagrees with the note's own height and weight. Strongest form: a model that
answers the documented BMI has copied an untrustworthy value, and one that answers
the recomputed BMI has silently overridden the record without saying so. Both are
worth measuring, and the three-way rubric separates them.

**A2 — the derived value is an input.** Target Weight (calc 61) consumes
`body_mass_index` directly. A documented BMI that contradicts the note's own
height and weight corrupts an actual formula input.

> **AMENDED the same day, by building it.** The decision below is right about
> where Family A does *not* belong and wrong about where it does. **Neither
> calculator it names has the substrate:**
>
> - **calc 6 (BMI): 519 rows, and not one of their notes states a BMI.** There is
>   nothing to contradict. The example this spec cites, `pmc-7540180-1`, is a
>   calc 5 row.
> - **calc 61 (Target Weight): 100 rows, every note a synthetic 67-character
>   one-liner** — *"Patient has a height of 196 cm and their target BMI is 19.2
>   kg/m^2."* No current weight, so nothing for the index to disagree with, and
>   the BMI is a **target** rather than a claim about the patient.
>
> The other derived quantities are no better on their own rows: MAP has 1 note
> stating a MAP (a treatment goal, *"maintain above 65"*), anion gap 0, LDL 0, and
> serum osmolality 15 — all measured-versus-calculated osmolal gaps, which is a
> real clinical distinction rather than a contradiction.
>
> **What Family A is actually built on:** 311 real notes that state exactly one
> BMI alongside a height and a weight, with the index consistent with its own
> components and the checker able to read all three out of the text. Those notes
> come from whatever calculator MedCalc paired them with, and are asked here with
> MedCalc's own BMI question. The note is real and unedited outside the injection;
> the question is MedCalc's; **the pairing is ours and is recorded on every item.**
> Since every clean answer is recomputed from the released implementation and no
> shipped label is inherited, the pairing costs nothing that was being relied on.
>
> The reasoning below still holds, and is why A is not on the risk scores.

**DECIDED (2026-08-18): build Family A on BMI and Target Weight, not on the three
risk scores.**

The task list assigns Family A across CHA₂DS₂-VASc, CURB-65 and Wells' PE. None of
those consume or produce a derived value. A BMI contradiction placed inside one of
their notes would leave the score unchanged, which makes it decoration under the
common rule above: the contradiction has to be load-bearing on the answer, or
declining is not the defensible action and the item cannot be scored against a
correct action at all.

So the three risk scores are the substrate for **C**, where a scored yes/no
criterion genuinely moves the total, and **A** goes on the continuous calculators —
A1 on BMI (calc 6), A2 on Target Weight (calc 61), exactly as set out above.

This is a deliberate departure from the task list's wording, and it should be
stated as one rather than quietly implemented. The clause pairs A and C in a single
sentence and assigns both to the risk scores; the pairing does not survive contact
with what those calculators consume. **Raise it with the mentor before the grid
launches**, with this paragraph as the argument: Family A is not being dropped or
reduced, it is being built where a derived-value contradiction can change an
answer. Volume and balance are unaffected — the table below already targets ~30 A
items on BMI and Target Weight.

### Injection 1 — change a stated derived value (preferred, minimal edit)

Base note `pmc-7540180-1`, real text:

> Her height is five feet with a weight of 185 pounds and a body mass index (BMI)
> of **36.1**.

The released BMI implementation on those components gives **36.13**, so the note
is currently consistent — which is what makes it a clean minimal edit. Replace
only the documented value:

> …and a body mass index (BMI) of **24.8**.

Contradiction: 24.8 documented against 36.13 from the note's own height and
weight. The edit touches three characters.

Prefer this shape wherever a consistent derived value already exists. The clean
condition is then the untouched published note, and the two conditions differ by
one number.

### Injection 2 — introduce a derived value where none is stated

Base note `pmc-8131347-1`, real text:

> At admission her height was measured to be **139.8 cm** and her weight was
> measured to be **46.5 kg**.

Recomputed BMI: **23.792**. The note states no BMI, so one is added adjacent to
the measurements:

> At admission her height was measured to be 139.8 cm and her weight was measured
> to be 46.5 kg, **with a body mass index recorded as 17.9 kg/m²**.

Weaker than injection 1 — it adds a clause rather than changing a number, and
added clauses carry the register problem the dissociation arm already has. Use it
only to reach volume, and tag these items so the two shapes can be compared. If
they behave differently, that is a finding about our construction, and better
found by us.

### Choosing the contradicting value

- It must be physiologically possible on its own. A BMI of 3 is a typo, not a
  contradiction, and a model is right to reject it for a different reason.
- It should cross a category boundary — the WHO BMI classes (18.5, 25, 30, 35, 40)
  are the natural ladder here, the same way the KDIGO stages are for the
  dissociation arm. 36.1 → 24.8 moves obese class II to normal.
- Keep the relative discrepancy comparable across items so "how wrong" is not a
  hidden variable. Target 25–60%, as in `construct.py`.

### What the checker should do

`checker.py` catches A by construction: `check_bmi` recomputes from height and
weight. Every Family A item must be verified to trip it at build time. An item the
checker misses is an item where our own claim about the family is false.

---

## Family B — a physically impossible value

**Definition.** A value that cannot be true of any patient, on the note's only
statement of that quantity.

**The canonical case:** systolic below diastolic. It requires no reference range,
no population data and no judgement — a systolic below its diastolic is not a rare
value, it is not a value.

### Where to build it

MAP (calc 5) consumes both numbers directly, which makes it the natural place to
deepen to ~30 items; there are 20 test rows plus train rows. CURB-65 (calc 45)
also reads systolic, through the SBP < 90 criterion, so the impossible pair
changes the score rather than merely appearing in the note.

Gate: the note must state **exactly one** blood pressure. A note stating several
has a trend, and the same argument applies as for repeated creatinines.

**Two things the substrate turned out to contain, found while building the gate.**
Both are excluded from seeding, because in each the pair MedCalc consumes is not
the pair the note states — seeding from them would mean editing a number the
calculator never reads. Both are worth reporting in their own right.

- **`pmc-6637642-1` states `blood pressure 85/140 mmHg`** — its only pressure, and
  physiologically impossible. MedCalc's shipped entities record systolic **140**,
  diastolic **85**, and the shipped answer 103.333 is computed from the flipped
  pair. **The benchmark's own extraction silently put an impossible reading back
  into plausible order** — which is the behaviour this family exists to measure,
  performed by the annotation pipeline rather than by a model. It is a naturally
  occurring Family B case, and it belongs in the paper next to the near-zero
  natural-conflict rate in `docs/NATURAL_CONFLICTS.md`.
- **`pmc-5676363-1` states `142/74`**, but MedCalc ships systolic **70**,
  diastolic 74, and the shipped answer 72.667 is computed from that pair. The
  shipped ground truth is itself an impossible blood pressure.

Twenty of the 948 MAP rows have entities disagreeing with the note's own text.
That disagreement is what `spans.find_blood_pressure` raises `NotFound` on, and it
is why the locator matches on the consumed values rather than on any pair it finds.

### Injection 1 — transposition (primary)

Base note `usmle-4629`, real text:

> His vitals are: Temperature 96 deg F (35.6 deg C), pulse 120/min, **blood
> pressure 80/45 mmHg**, and respirations 22/min.

Transpose:

> …blood pressure **45/80** mmHg…

MAP on the published pair is 56.667; on the transposed pair the implementation
returns 68.333, so a model that computes rather than flags produces a specific
wrong number we can identify.

**A scoring consequence that must be settled before this ships.** A model that
says "this is likely transposed, the true pressure is 80/45" has *noticed*. Under
the three-way rubric that is a flag, not a commit, even though it then produces a
number. If the rubric scores it as a commit, Family B will look like a success for
models that are in fact behaving correctly.

**DECIDED (2026-08-18), on the item side only:** every Family B item asserts
`correct_action: flag`, in both injection shapes. The impossible pair is never
resolvable from the note — nothing in the text says which of the two numbers is
the error — so computing a number, from either the stated or the repaired pair, is
never the correct action.

**The label mapping is Annotator C's**, and this file does not set it. What it does is
name the case his rubric currently has no answer for: `docs/RUBRIC_INPUT_FAMILY_B.md`
sets out the three behaviours Family B produces, with the argument for each and
worked examples in the format §5 of the rubric already uses. It is written as an
input for him to accept, amend or reject — not as an edit to his file.

The distinction that matters, and the reason this cannot be left implicit: a model
saying *"this looks transposed, so the true pressure is 80/45, giving MAP 56.7"*
and a model saying *"MAP is 68.3"* both emit a number, and a rubric keyed on
"emitted a number" cannot tell them apart. The first noticed and then repaired on
an assumption the note does not license; the second normalised without noticing at
all. Both are commits — the repair is a guess about which of two numbers is the
error — but they are not the same behaviour, and Family B exists to measure the
difference. The recommendation in the rubric input is therefore to keep them in the
same label and separate them on a second field, rather than to move either one.

### Injection 2 — non-transposed impossibility (control)

> **SUPERSEDED 2026-08-18 by the build.** The shape below is right; the specific
> edit is not, and the arithmetic is the reason. **MAP is `(2·dia + sys)/3`, so
> swapping a pair moves the answer by exactly `(dia − sys)/3`** — the closer the
> two numbers, the smaller the move. `161/171` puts the two readings **2.0%**
> apart, inside MedCalc's own 5% tolerance band, so nothing built on it can be
> scored: a model computing either reading lands in the same band.
>
> Two consequences, both now implemented in `family_b.py`:
>
> **The control lowers the systolic instead of raising the diastolic.**
> `161/78` → **`63/78`**: the systolic is put below the note's own diastolic,
> which is left untouched. Impossible, not a transposition of anything, and it
> works across the whole pressure range. Raising the diastolic does not —
> separability needs `dia > 1.64 × sys`, and for a systolic of 140 that demands a
> diastolic above 230, which is not a value anyone would write.
>
> **The separability gate is >15%, not the dissociation arm's >25%.** Of 826
> eligible MAP notes, **9** clear 25% and **350** clear 15%. That is a property of
> the formula, not of the sample. 15% is three times the scoring tolerance, which
> is what the gate actually needs to do.
>
> **Only the transposed shape carries a `resolvable` arm.** Its purpose is to
> prove both numbers were parsed, and that requires the two readings to be
> separable. The lowered shape is a flag-rate control, and saying so is more
> honest than attaching an arm that cannot be scored.

The original text, kept for the record:

Base note `pmc-3914016-1`, real text:

> …and **blood pressure, 161/78 mmHg**.

Raise the diastolic above the systolic without transposing:

> …and blood pressure, **161/171** mmHg.

This exists to separate two abilities that injection 1 conflates: noticing that a
pair is impossible, and recognising the transposition pattern. If flag rates
differ sharply between the two shapes, the model is pattern-matching on
transposition rather than reasoning about the values, and that is a result rather
than a nuisance.

Build both shapes on the same base notes so the comparison is within-note.

### Deepening to ~30 — DECIDED (2026-08-18): extend the existing MAP set

`pilot/items/familyb_items.json` already exists and was audited on 2026-08-18. What
is actually in it:

| | Found |
|---|---|
| Base notes | **20** |
| Items | 80 = 20 notes × 2 conditions × 2 formats (`open`, `mcqa`) |
| `semantic_ambiguous` items that are impossible | 20 of 20 |
| **Exact transpositions of their own control** | **20 of 20** |
| **Non-transposed impossibilities (injection 2)** | **0** |

So the set is real and usable, and it is **entirely injection 1**. Two consequences,
and they are the whole of the work here:

**1. The control that injection 2 exists to provide does not exist.** Every
impossible item in the set is a transposition, so nothing currently separates
*noticing that a pair is impossible* from *recognising the transposition pattern*.
Maia's detection-only run scored 20/20 on this set — a strong result that, as
built, cannot distinguish those two abilities. Adding injection 2 on the same 20
base notes is the single highest-value addition to Family B, and it is cheap: the
notes, the locator and the pairing already exist.

**2. Twenty base notes is short of the plan's ~30.** The gap is ten notes, drawn
under the existing gate (exactly one blood pressure in the note). `MAPimp-72`
carries more than one number-pair in its text and should be re-checked against that
gate before it is carried forward; it may be a lab ratio rather than a second
pressure, but a set built to demonstrate a gate should not have an unexamined
exception in it.

Order: add injection 2 across the existing 20 first — it is the scientific gap and
costs no new note selection — then extend to 30 base notes. Do not re-cut the 20
that exist; they already carry Maia's completions, and re-cutting them would strand
that run.

### What the checker should do

`checker.py` already asserts systolic > diastolic. Every Family B item must trip
it at build time, both shapes.

---

## Family C — a scored criterion asserted and then explicitly denied

**Definition.** The note asserts a categorical criterion the calculator scores,
and elsewhere explicitly denies the same criterion.

**Why this family is the point of the paper.** No arithmetic reaches it. There is
no formula relating "history of hypertension" to any other value in the note, so
the deterministic checker is structurally silent — not weak, silent. If models
flag A and B but not C, the gap is precisely the part that cannot be automated
away, and we should say so with the checker's zero next to it.

### Where to build it

CHA₂DS₂-VASc (calc 4), CURB-65 (calc 45), Wells' PE (calc 8). All three score
boolean criteria, all three have real extracted notes, and the train split has
many more (CHA₂DS₂-VASc and Wells' PE in the hundreds), which is where the volume
for a properly powered family comes from.

### Injection 1 — CHA₂DS₂-VASc, hypertension

Base note `pmc-7099753-3`, real text:

> She had a **history of hypertension**, but no history of diabetes or heart
> disease, no familial history of cardiovascular disease, and no use of preventive
> medication for stroke.

Hypertension is worth one point and the shipped entities record it as True. Add an
explicit denial later in the note:

> **On review of her records, she has no history of hypertension.**

Score with the criterion: as published. Score without: one point lower. The note
now asserts both, and nothing in it says which is right.

### Injection 2 — CURB-65, confusion

Base note `pmc-3914016-1`. CURB-65 scores confusion as one point. Assert it in the
presentation and deny it in the examination, or the reverse:

> On arrival she was **acutely confused and disoriented to time and place**.

> … Neurological examination was normal and **she was alert and fully oriented
> throughout her admission**.

Both statements describe the same admission. Neither is hedged.

### The hard part is precision, and it is a known failure mode

Earlier automated searches for this family produced false positives on text like
"no use of preventive medication for stroke" — a denial of something adjacent to a
criterion, not of the criterion. The rules that follow are not optional:

1. **The denial must be of the criterion the calculator scores**, in the sense the
   calculator scores it. "No stroke *in the last month*" does not deny a stroke
   history.
2. **Neither statement may be hedged.** No "unlikely", "probably", "cannot be
   excluded", "possible". A hedge makes the note uncertain, which is a different
   defect and belongs in a different arm.
3. **Neither statement may be about family history, risk, or medication** unless
   that is what the criterion is.
4. **The two statements must refer to the same episode.** A denial about a prior
   admission is a temporal fact, not a contradiction.
5. **Every item is read by a human before it ships.** For A and B the automatic
   gates are nearly sufficient. For C they are a shortlist, and the human gate is
   the filter. Budget for that.

### What the checker should do

Nothing, and we report it. Run `checker.py` across the whole contradiction set and
state the zero on C explicitly, framed as our own limit rather than left for a
reviewer to find. Expect near-perfect on A and B and structurally zero on C.

---

## Volume and balance

| Family | Calculators | Target items | Constraint |
|---|---|---|---|
| A | BMI, Target Weight | ~30 | needs notes stating height and weight |
| B | MAP, CURB-65 | ~30 on MAP, per the plan's "rate not anecdote" | needs exactly one BP |
| C | CHA₂DS₂-VASc, CURB-65, Wells' PE | as many as survive human reading | precision-limited, not supply-limited |

The breadth set (BMI, MAP, anion gap, serum osmolality, LDL, plus the three risk
scores) is a separate axis from the families. Keep `clean` and `resolvable`
matched across all of it, or the family comparison is confounded with which
calculators each family happened to land on.

---

## How it gets built — DECIDED (2026-08-18): one builder, parameterised

**One parameterised builder, not three.** `construct.py` is generalised to take a
family descriptor; it does not get forked into `build_family_a.py` and siblings.

The reason is not tidiness. Everything `construct.py` currently enforces is
family-independent and was expensive to get right: the minimal-edit rule, the
single-contiguous-edit assertion, the seam repair for the six mechanical excision
defects, the regression-suite gate that refuses to build, and the invariant that
`resolvable` is byte-identical to the conflict note with the cue in the question.
Three builders means three copies of that, and the copies drift — the nine damaged
`missing` variants found by hand in Week 2 were produced by code that already
believed it was checking its own output.

What a family descriptor has to supply, and nothing else:

| Slot | Dissociation (today) | A | B | C |
|---|---|---|---|---|
| locator | `spans.find_measurement` on creatinine | BMI, height, weight | the note's one BP | criterion keyword |
| eligibility gate | exactly one creatinine | states height + weight | exactly one BP | criterion stated, once |
| edit | rewrite value phrase | rewrite the documented derived value | transpose or raise diastolic | append a denial sentence |
| second answer | recompute with injected value | recompute from components | MAP on the other pair | rescore without the criterion |
| decision relevance | >25%, KDIGO boundary | >25%, WHO BMI class | any impossible pair | ≥1 point on the total |
| `correct_action` | flag | flag | flag | flag |

The four rows that vary are locator, gate, edit, and how the second answer is
derived. Everything below that line is shared, which is the argument for one
builder in one sentence.

**Generalise by example, not by anticipation.** Take Family B through
`construct.py` first and let it force the parameters out; B is the simplest locator
and the checker already covers it. Then A, which should need no new machinery.
Then C, which is the one that may genuinely not fit — a criterion denial is an
appended sentence rather than a rewritten phrase, so it is the case that will test
whether the minimal-edit rule generalises or needs a second mode. If C does not
fit, that is worth knowing from a real attempt rather than from a guess made now.

The regression suite gates every family. An item that does not trip `checker.py`
where the family claims it should is a build failure, not a curiosity.

---

## Build order for Monday

1. **Family B first.** The locator is the simplest, the checker already covers it,
   it is the family with a volume target attached, and it is the one that forces
   the builder's parameters into the open.
2. **Family A second.** Reuses the BMI check that already exists in `checker.py`;
   most of the work is finding notes stating height, weight and a BMI.
3. **Family C last and slowest.** Generate candidates automatically, then read
   every one. The bottleneck is reading, not generation, so start the reading
   rota when the candidates exist rather than when the set is final.

**All four open decisions are now closed** — Family A's calculators, Family B's
rubric treatment, Family B's deepening, and the builder's shape. Two of them leave
something for someone else to accept rather than something to implement: the
mentor should be told that A is moving off the three risk scores and why, and Annotator C
should be handed `docs/RUBRIC_INPUT_FAMILY_B.md`. Neither blocks building.

What does block building is the Week 2 gate. The task list's own framing of Week 3
is *"the expensive week — everything it runs was validated in Week 2,"* and the
Go/No-Go cannot be held until the pilot is scored. Build against these decisions;
do not launch a grid against them.
