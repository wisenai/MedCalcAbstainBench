# Label audit: recomputing MedCalc-Bench's shipped answers

**Task owner:** Annotator D — Week 1 task S1  
**Completed by:** Annotator D

_Generated 2026-08-10T21:32:46Z from MedCalc-Bench `version-1.0` (353ded7c61), 1047 test rows. Regenerate with `python3 audit/label_audit.py`._

## What was measured

Each case's `Relevant Entities` — MedCalc-Bench's own extraction of the note, not ours — was fed to MedCalc-Bench's own released implementation for that calculator. The result was compared to the shipped `Ground Truth Answer` under MedCalc-Bench's own correctness rule (exact match for integer-output calculators, the shipped per-row tolerance band for decimal ones). No tolerance was widened and no formula was reimplemented.

A mismatch means the shipped label and the shipped code disagree on a case where the inputs are not in dispute. This audit does not adjudicate which of the two is wrong; the operational consequence is the same either way, which is that we recompute every clean answer we use and inherit no label.

## Headline

| | Primary sample | Creatinine seed pool |
|---|---|---|
| Cases run | 53 | 60 |
| Scored | 50 | 60 |
| Agree with shipped label | 50 | 60 |
| &nbsp;&nbsp;of which exact, not merely in-band | 50 | 60 |
| **Mismatch** | **0 (0.0%)** | **0 (0.0%)** |
| Implementation raised | 3 | 0 |
| Case missing a required input | 0 | 0 |
| Not drivable at v1.0 | 0 | 0 |

The exact-agreement row matters because the decimal bands are generous on some calculators; a result can sit inside the band while still differing from the shipped number. Reporting only the band would flatter the substrate.

The primary sample is drawn breadth-first — one case per calculator per pass, calculator order and within-calculator order fixed by seed 20260804. A flat random draw from 1,047 rows would concentrate in a few calculators and turn the headline into a statement about those calculators; this does not.

**53 cases were drawn to score 50.** The draw continues in that fixed order until the target number of cases have actually produced an answer, because three of the first fifty land on implementations that raise before producing one. Excluding those calculators to reach a clean fifty would be sampling on the outcome — dropping cases precisely because they fail, which is the one substantive thing this audit found. The order is unchanged and every unscored case is reported below.

The seed pool column is a census, not a sample: every Cockcroft-Gault, CKD-EPI and MDRD row in the test set. The dissociation seeds are drawn from this pool, so its mismatches are the specific rows we must not seed from.

## What the result means, and what it does not

On the calculators we can drive, the shipped labels reproduce exactly: 586 of 586 scored rows land on the shipped number itself, not merely inside its tolerance band. Whatever is wrong with MedCalc-Bench, it is not that the label disagrees with the code on these calculators.

That is a narrower claim than "the labels are correct", and the gap matters:

- **This tests label-against-code, holding the extracted inputs fixed.** It takes `Relevant Entities` as given. If MedCalc-Bench pulled the wrong creatinine out of a note, this audit reproduces the wrong answer faithfully and reports agreement. Published error rates that count extraction mistakes are measuring something this cannot see.
- **It says nothing about whether the formula is the right one.** A calculator implemented consistently but wrongly agrees with itself perfectly.
- **It covers the continuous calculators only.** The rule-based scores, which is where criterion-interpretation disputes would live, are excluded below.

The one substantive defect this did surface is not a label error at all: two released implementations raise on every row they are asked about (see below). For those, no answer can be reproduced from the released code in any sense.

Operationally none of this changes our plan, which was already not to inherit labels. It does mean we can stop treating substrate label error as an open threat to the dissociation arm: the seed pool is 60/60 exact.

## Supplementary: every drivable row

Running all 626 drivable rows rather than only the sampled 50 costs seconds, so we did it. It is reported here rather than as the headline because the 50-case sample is what we committed to.

- scored: **586**
- agree with the shipped label: **586** (586 exactly, 0 in-band only)
- mismatch: **0** (0.0%)
- the implementation itself raised: **40**
- case did not supply a required input: **0**

### Released implementations that cannot run

These are not label disputes. The shipped implementation raises before producing an answer, on inputs MedCalc-Bench itself extracted, so there is no recomputation to compare and the shipped label for these rows cannot be reproduced from the released code at all.

| Calculator | Rows affected | Failure |
|---|---|---|
| Albumin Corrected Delta Ratio | 20 | `AttributeError: module 'unit_converter_new' has no attribute 'conversions'` |
| Delta Ratio | 20 | `AttributeError: module 'unit_converter_new' has no attribute 'conversions'` |

## Primary sample: mismatching cases

None.

## Creatinine seed pool: mismatching cases

None.

## All drivable rows: mismatching cases

None.

## Primary sample: cases that could not be scored

| Row | Calculator | Status | Detail |
|---|---|---|---|
| 751 | Delta Ratio | error | AttributeError: module 'unit_converter_new' has no attribute 'conversions' |
| 756 | Delta Ratio | error | AttributeError: module 'unit_converter_new' has no attribute 'conversions' |
| 826 | Albumin Corrected Delta Ratio | error | AttributeError: module 'unit_converter_new' has no attribute 'conversions' |

## Primary sample: coverage by calculator

31 calculators, 2 case(s) each at most.

| Calculator | Scored | Mismatch |
|---|---|---|
| Adjusted Body Weight | 1 | 0 |
| Albumin Corrected Anion Gap | 2 | 0 |
| Albumin Corrected Delta Gap | 1 | 0 |
| Anion Gap | 2 | 0 |
| Body Mass Index (BMI) | 1 | 0 |
| Body Surface Area Calculator | 2 | 0 |
| CKD-EPI Equations for Glomerular Filtration Rate | 2 | 0 |
| Calcium Correction for Hypoalbuminemia | 1 | 0 |
| Creatinine Clearance (Cockcroft-Gault Equation) | 1 | 0 |
| Delta Gap | 2 | 0 |
| Estimated Due Date | 2 | 0 |
| Estimated Gestational Age | 2 | 0 |
| Estimated of Conception | 2 | 0 |
| Fibrosis-4 (FIB-4) Index for Liver Fibrosis | 1 | 0 |
| Fractional Excretion of Sodium (FENa) | 2 | 0 |
| Free Water Deficit | 1 | 0 |
| HOMA-IR (Homeostatic Model Assessment for Insulin Resistance) | 2 | 0 |
| Ideal Body Weight | 2 | 0 |
| LDL Calculated | 1 | 0 |
| MDRD GFR Equation | 2 | 0 |
| Maintenance Fluids Calculations | 1 | 0 |
| Mean Arterial Pressure (MAP) | 2 | 0 |
| QTc Bazett Calculator | 2 | 0 |
| QTc Framingham Calculator | 2 | 0 |
| QTc Fridericia Calculator | 2 | 0 |
| QTc Hodges Calculator | 1 | 0 |
| QTc Rautaharju Calculator | 2 | 0 |
| Serum Osmolality | 2 | 0 |
| Sodium Correction for Hyperglycemia | 2 | 0 |
| Steroid Conversion Calculator | 1 | 0 |
| Target weight | 1 | 0 |

## What this audit does not cover

MedCalc-Bench ships each case's inputs under human-readable keys and its implementations index internal ones, so driving the released code needs a rename layer (`audit/entities.py`). That layer is only safe for calculators with a fixed, unambiguous input set. The rule-based scores read their boolean criteria through `.get(key, default)`: a criterion we failed to map would not raise, it would read as *absent* and yield a plausible wrong score that looks exactly like a MedCalc label error. Rather than report a number contaminated that way, those calculators are left undriven:

| ID | Calculator | Excluded because |
|---|---|---|
| 4 | CHA2DS2-VASc Score for Atrial Fibrillation Stroke Risk | rule-based; boolean criteria read via .get() default to absent when unmapped |
| 8 | Wells' Criteria for Pulmonary Embolism | rule-based; boolean criteria read via .get() default to absent when unmapped |
| 15 | Child-Pugh Score for Cirrhosis Mortality | rule-based; boolean criteria read via .get() default to absent when unmapped |
| 16 | Wells' Criteria for DVT | rule-based; boolean criteria read via .get() default to absent when unmapped |
| 17 | Revised Cardiac Risk Index for Pre-Operative Risk | rule-based; boolean criteria read via .get() default to absent when unmapped |
| 18 | HEART Score for Major Cardiac Events | rule-based; boolean criteria read via .get() default to absent when unmapped |
| 20 | Centor Score (Modified/McIsaac) for Strep Pharyngitis | rule-based; boolean criteria read via .get() default to absent when unmapped |
| 21 | Glasgow Coma Score (GCS) | rule-based; boolean criteria read via .get() default to absent when unmapped |
| 23 | MELD Na (UNOS/OPTN) | rule-based; boolean criteria read via .get() default to absent when unmapped |
| 25 | HAS-BLED Score for Major Bleeding Risk | rule-based; boolean criteria read via .get() default to absent when unmapped |
| 27 | Glasgow-Blatchford Bleeding Score (GBS) | rule-based; boolean criteria read via .get() default to absent when unmapped |
| 28 | APACHE II Score | rule-based; boolean criteria read via .get() default to absent when unmapped |
| 29 | PSI Score: Pneumonia Severity Index for CAP | no implementation file at the version-1.0 tag |
| 32 | Charlson Comorbidity Index (CCI) | rule-based; boolean criteria read via .get() default to absent when unmapped |
| 33 | FeverPAIN Score for Strep Pharyngitis | rule-based; boolean criteria read via .get() default to absent when unmapped |
| 36 | Caprini Score for Venous Thromboembolism (2005) | rule-based; boolean criteria read via .get() default to absent when unmapped |
| 43 | Sequential Organ Failure Assessment (SOFA) Score | rule-based; boolean criteria read via .get() default to absent when unmapped |
| 45 | CURB-65 Score for Pneumonia Severity | rule-based; boolean criteria read via .get() default to absent when unmapped |
| 46 | Framingham Risk Score for Hard Coronary Heart Disease | rule-based; boolean criteria read via .get() default to absent when unmapped |
| 48 | PERC Rule for Pulmonary Embolism | rule-based; boolean criteria read via .get() default to absent when unmapped |
| 49 | Morphine Milligram Equivalents (MME) Calculator | dose table keyed by opioid name; not a fixed input set |
| 51 | SIRS Criteria | rule-based; boolean criteria read via .get() default to absent when unmapped |

So the headline covers 33 of 55 calculators in the test set — the continuous ones, which is where our own items live. Extending it to the rule-based scores means hand-mapping their criteria, which is Week 3 work for the Family C set and not a Week 1 blocker.

## What we do about it

1. Every clean answer in our item set is recomputed from the released code at build time. No shipped label is copied forward. This was the plan before the audit came back clean and stays the plan after, because it also covers the extraction question this audit cannot see.
2. Seeds are drawn only from rows where the recomputation agrees with the shipped label. On the creatinine pool that constraint currently excludes nobody, but it is enforced in `construct.py` rather than assumed.
3. Calculators whose released implementation raises are not eligible as substrate. That rules out Delta Ratio and Albumin Corrected Delta Ratio.
4. On the missing and value-conflict conditions the correct action is to decline or flag, which depends on no label at all — those conditions were never exposed to this risk.
