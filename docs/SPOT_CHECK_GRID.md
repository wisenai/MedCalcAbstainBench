# spot-check: ten items of each new family, read by hand


The task list asks for the human spot-check protocol on the first ten items of
each new family **before the grid launches**. Thirty items read. It found five
defects across three families, in two classes, and **every automated check had
passed all five**.

That is the same result as , where the script passed all 160 items and
reading twenty found nine broken ones. The lesson repeats because it is
structural: the scripts check what we thought to ask them, and reading finds what
we did not.

---

## What was found

### Class 1 — framing written for the published value (3 items)

A clinical judgement sits beside the value. Our injection is *required* to cross a
clinical boundary. So the judgement ends up contradicting the number it describes,
and the item now contains **a second contradiction we did not build** — one a model
may reasonably flag instead of ours, which would make the flag rate mean something
other than what we claim.

| Item | Text | Why it breaks |
|---|---|---|
| `bmi-pmc-5548950-1` | `weighed 91 kg (morbid obesity, body mass index 19.3 kg/m2)` | 19.3 is normal weight, not morbid obesity |
| `bmi-pmc-7049766-1` | `moderately overweight (62.4 kg, body mass index [BMI] 14.6)` | 14.6 is underweight |
| `map-pmc-5930216-1` | `Physical examination was normal (BMI 23.0 kg/m2, blood pressure 70/125 mmHg)` | an impossible pressure is not a normal examination |

### Class 2 — the criterion word names an instrument, not the patient (2 items)

The word is genuinely present, genuinely undenied, and genuinely about this
admission. It just names the measuring instrument.

| Item | Text | Why it breaks |
|---|---|---|
| `cha2ds2_vasc-pmc-7294161-1` | `The National Institutes of Health Stroke Scale (NIHSS) score was 12` | names the scale; asserts no stroke history |
| `cha2ds2_vasc-pmc-3317869-1` | `Thrombolysis In Myocardial Infarction (TIMI) flow 3 was observed` | an angiographic grade, not an infarction |

A third, `cha2ds2_vasc-pmc-8501465-1` (`NIH Stroke Scale/Score (NIHSS) was 2`),
fell outside the first ten and was caught by the scan the reading prompted.

---

## What was done about it

**All five were fixed by generalizing, not by hand-killing.** Each became a gate,
so the same shape cannot return in or on a rebuild:

- `family_a.py` rejects a note with weight-band framing attached to the documented
 value. BMI eligibility 311 → 291; still 30 seeds.
- `family_b.py` rejects framing in the same sentence as the pressure. Eligibility
 278 → 251; still 30 seeds.
- `spans.py` rejects a criterion mention inside an instrument name, by the words
 that follow it (`scale`, `score`, `index`, `criteria`, `classification`, `grade`)
 or the instrument openers that precede it. Family C eligibility 341 → 340.

**Nine tests pin all of it**, including two that check the gates do *not* fire on
plain statements — `He has a past medical history of stroke` must still count.

**Re-scan after the fixes: 0 of 30 framed, 0 of 30 anchored on an instrument.**

### One gate is deliberately over-strict, and says so

Family B's framing gate drops notes where `normal` modifies something else in the
same sentence — in one, `The electrocardiogram showed normal sinus rhythm ... and
blood pressure values were 160/90`, where `normal` attaches to the rhythm. Deciding
which noun a modifier governs is not something a regex does reliably. Over-rejecting
costs supply we have (251 eligible for 30 items); under-rejecting ships a broken
item. Two of the six sentence-scoped hits were false positives on inspection, and
they were dropped anyway.

---

## The thirty, as read

**Family A — BMI**, items 1–10. Eight clean. Two framing defects (above), both now
gated out. The eight that passed are unremarkable in the way they should be:
`She is 160 cm (5 ft 3 in) tall and weighs 105 kg (231 lb); BMI is 22.6 kg/m2` —
one number changed, the sentence untouched around it.

**Family B — MAP**, items 1–10. Nine clean, one framing defect. Both injection
shapes read naturally inside a vitals list: `BP of 80/140 mmHg` and `BP of 65/80
mmHg` sit where `BP of 140/80 mmHg` sat.

One thing noted and accepted: the lowered shape can produce a shock-range systolic
(`55/70`) in a patient the note describes as comfortable. That is a second-order
implausibility, but any impossible pair is implausible by construction, and the
impossibility *is* the injection. Recorded rather than gated.

**Family C — criterion denial**, items 1–10. Eight clean, two instrument defects.
The clean ones are the strongest items in the week: `congestive heart failure was
treated initially with lasix IV and subsequently with lasix orally. The patient has
no history of congestive heart failure.` Being treated for a condition and having
no history of it cannot both hold, and no second reading reconciles them.

**Family A — anion gap** was read in full rather than sampled, since there are only
five items after the framing gate. All five clean.

---

## Second signature

Not obtained. The five defects and the three gates are one reader's calls.

| Reader | Date | Agrees with the five defects and the three gates | Notes |
|---|---|---|---|
| | | | |
