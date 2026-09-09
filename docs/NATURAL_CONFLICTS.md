# Naturally occurring intra-note conflicts

**Task owner:** Annotator D — Week 2  
**Completed by:** Annotator D

_Generated 2026-08-10T22:48:08Z over 7642 unique published notes across both released splits. Regenerate with `python3 natural_conflicts.py`._

## The question, and why the answer matters either way

Every contradiction we test is one we injected. A reviewer is entitled to ask whether real notes contain them already — if they are common, a constructed benchmark is unnecessary; if they are absent, the construction is doing work no corpus could do for us. The plan predicted near-zero and mostly temporal trends, and a predicted null is only worth anything if the search could have found something, so this looks four ways rather than one.

## Result

| Signal | Notes |
|---|---|
| Arithmetic contradiction (derived value vs. components, or an impossible value) | **30** (0.4%) |
| One analyte stated with differing values | 924 |
| …every mention carrying a temporal marker | 853 |
| …at least one carrying none | 71 |
| Condition asserted and denied | 32 |
| Sex referred to inconsistently | 51 |

**Only the first row is decisive on its own.** Arithmetic either contradicts itself or does not, and that check is the same instrument used on our constructed items. The other three surface candidates that a person has to read, and they are reported as candidates rather than counted as conflicts.

### Every arithmetic candidate, read

The count above is what the checker flagged. It is not the number of contradictions, and reporting it as one would repeat a mistake this project has already made once. Three rounds of tuning removed false-positive modes before this list settled — a blood product abbreviated MAP, a BMI read from the height inside its own parenthetical, a pH read as an anion gap — and what survived still had to be read.

| Verdict | Notes |
|---|---|
| genuine | 13 |
| note typo | 4 |
| marginal | 8 |
| artifact | 5 |

**Genuine** — The note's own numbers disagree, and no reading reconciles them.

- `pmc-7461646-1` (test) — weight 39.5 kg, height 146 cm, stated BMI 17.6
- `pmc-8547566-1` (train) — height 125 cm, weight 25 kg, stated BMI 14.2
- `pmc-5438001-1` (train) — Na 128, Cl 99, HCO3 11 give 18; note states 20
- `pmc-6637642-1` (train) — blood pressure 85/140 -- systolic below diastolic
- `usmle-524` (train) — 175 cm, 64 kg, stated BMI 22 (gives 20.9)
- `pmc-3799273-1` (train) — 163 cm, 55 kg, stated BMI 22.3 (gives 20.7)
- `pmc-8451257-1` (train) — blood pressure 11/64 -- systolic of 11
- `pmc-4766327-1` (train) — 160 cm, 60.8 kg, stated BMI 38.0 (gives 23.7)
- `pmc-3060377-2` (train) — 158 cm, 62 kg, stated BMI 30 (gives 24.8)
- `pmc-6525427-1` (train) — 172 cm, 120 kg, stated BMI 37 (gives 40.6)
- `pmc-4839905-1` (train) — 132 cm, 19.5 kg, stated BMI 17.7 (gives 11.2)
- `pmc-8133044-6` (train) — 173 cm, 70 kg, stated BMI 25 (gives 23.4)
- `pmc-2852807-1` (train) — Na 133, Cl 102, HCO3 4.5 give 26.5; note states 19.3

**Note Typo** — A unit is wrong in the source — height in metres labelled cm. Real, but a transcription error rather than a contradiction between two claims.

- `pmc-7407036-1` (train) — 'height 1.72 cm' -- the note's unit is wrong
- `pmc-7745487-1` (train) — 'height: 1.65 cm'
- `pmc-8716636-1` (train) — 'height 1.7 cm'
- `pmc-5433413-1` (train) — 'height, 1.65 cm'

**Marginal** — A small discrepancy with an innocent explanation: a directly assayed LDL rather than a Friedewald estimate, or a MAP taken from a monitor rather than computed.

- `pmc-4691631-1` (test) — bicarbonate 19.9 falling to 16.0 over days; the stated gap fits neither
- `pmc-8122131-1` (train) — Friedewald LDL vs a directly measured one; HDL of 218 is itself odd
- `pmc-6287602-1` (train) — Friedewald 138.8 vs stated 167; direct LDL assay is common
- `pmc-4295136-1` (train) — Friedewald 135.6 vs stated 151
- `pmc-8241635-1` (train) — MAP 88 stated for 125/80; formula gives 95
- `pmc-7571607-1` (train) — MAP 58 stated for 85/51; formula gives 62.3
- `pmc-3150201-1` (train) — Friedewald 103.8 vs stated 116.7
- `pmc-6286717-1` (train) — 205 cm, 58 kg, stated 14.5 vs 13.8 -- just outside the band

**Artifact** — Ours, not the corpus's. Values from different timepoints, a third party's measurement, or a target rather than an observation.

- `pmc-4397714-1` (train) — BP 125/57 on admission, MAP 69 after deterioration -- different timepoints
- `pmc-8111402-1` (train) — 104.3 kg / 155.4 cm gives exactly the stated 43.2; another weight was parsed
- `pmc-8187023-1` (train) — 'maintained on a mean arterial pressure of 60-80 mmHg' is a target
- `pmc-6447649-1` (train) — 'his twin brother was 170 cm tall' -- a third party's height
- `pmc-4766314-1` (train) — MAP 70 and MAP 106 at different points in the operation

## What the repeated-analyte candidates actually are

924 notes state one analyte with more than one value. In 853 of them every mention sits beside a temporal marker — a day, a repeat draw, a word like *decreased* or *follow-up* — which makes them trends rather than contradictions. That is exactly the prediction, and it is also why our own seed selection requires a note to state its creatinine exactly once.

A trend is not a contradiction, and treating it as one would be the error this project is trying to avoid. Clinical convention endorses using the most recent value, so a note reporting a creatinine rising over three days is internally consistent and correctly answerable. We exclude that case from the study by design, not because it is rare.

## What this search could not have found

- **Contradictions between prose and a value that is not restated.** A note describing a patient as anuric while reporting normal renal function is self-contradictory, and nothing here reads for that.
- **Clinical implausibility as opposed to impossibility.** A creatinine of 12 mg/dL in a patient described as well is suspicious, not contradictory, and no rule separates the two without a clinician.
- **Anything outside the four analytes and nine conditions listed in the source.** The categorical search in particular is deliberately narrow, because a loose denial pattern produces candidates faster than anyone can read them.

## What this means for the study

The null is the useful result. Real notes in this corpus almost never contradict themselves in a way that arithmetic can catch, and the repeated values that do occur are overwhelmingly trends with the timing stated. A benchmark that waited for natural contradictions would have almost nothing to measure, which is the case for constructing them — and for constructing them in the one form clinical convention does not already resolve.
