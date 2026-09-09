# Week 2 — Clean Accuracy Validity Check

Model: anthropic/claude-opus-4.8
Threshold: 50% (pre-registered)
Tolerance: 5% relative difference from recomputed ground truth

open_ended: 38/40 - 95%
neutral_exist: 38/40 95%

Misses for both open_ended and neutral_exist

- `mdrd-tr3279_clean` — model declined (CANNOT DETERMINE). The only creatinine value in the note (180 μmol/L) appears to belong to the patient's grandmother, mentioned later in the note during her own diagnostic workup, not the patient. Recorded correct_answer (36.312) may be computed from the wrong person's value. Flagged to Annotator D for verification; excluded from interpretation pending resolution.
- `ckd_epi-tr144_clean` — model computed 108.44 vs. true answer 100.514 (7.9% off, outside tolerance). Model's arithmetic checked and is internally consistent with the CKD-EPI formula and constants it used; discrepancy likely reflects a formula-version/constant mismatch between the model's calculation and MedCalc-Bench's reference implementation, not a reasoning error. Worth Annotator D/Annotator C comparing exact constants.