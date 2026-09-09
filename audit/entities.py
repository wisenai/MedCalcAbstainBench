#!/usr/bin/env python3
"""Translate MedCalc-Bench's `Relevant Entities` keys into the names its own code reads.

Task owner: Annotator D -- Week 1 task S1.
Completed by Annotator D.

MedCalc-Bench ships each case's extracted inputs under human-readable keys
("Systolic Blood Pressure"), while its calculator implementations index internal
ones (`sys_bp`). The two were never wired together upstream: the implementations
were used offline to write the ground-truth explanations, and the shipped
evaluation only ever compares a model's final number to a stored label. Driving
the released code from the released entities therefore needs this layer.

Two design choices matter for the audit's honesty:

1. Only calculators whose entire input set maps unambiguously are registered.
   The rule-based scores (CHA2DS2-VASc, CURB-65, Wells', HAS-BLED, ...) read
   dozens of boolean criteria through `.get(key, default)`, so a key we failed to
   map does not raise — it silently reads as "criterion absent" and produces a
   plausible wrong score. That would show up as a MedCalc label error when it is
   really our mapping error. They are excluded, and the audit says so.

2. Even inside a registered calculator, a case missing a required input is
   reported as `unmapped_input` rather than scored. A mismatch we cannot attribute
   is not evidence about the label.
"""

# Display key in the shipped CSV -> parameter name the released code indexes.
# Misspellings on the right-hand side (`total_cholestrol`) are upstream's, kept
# verbatim because they are what the implementation actually reads.
ALIASES = {
    "Systolic Blood Pressure": "sys_bp",
    "Diastolic Blood Pressure": "dia_bp",
    "Heart Rate or Pulse": "heart_rate",
    "QT interval": "qt_interval",
    "Sodium": "sodium",
    "Chloride": "chloride",
    "Bicarbonate": "bicarbonate",
    "Albumin": "albumin",
    "Calcium": "calcium",
    "Glucose": "glucose",
    "Insulin": "insulin",
    "Blood Urea Nitrogen (BUN)": "bun",
    "Total cholesterol": "total_cholestrol",
    "high-density lipoprotein cholesterol": "hdl_cholestrol",
    "Triglycerides": "triglycerides",
    "Urine creatinine": "urine_creatinine",
    "Urine sodium": "urine_sodium",
    "Alanine aminotransferase": "alt",
    "Aspartate aminotransferase": "ast",
    "Platelet count": "platelet_count",
    "Body Mass Index (BMI)": "body_mass_index",
    "Race": "race",
    "Last menstrual date": "menstrual_date",
    "Current Date": "current_date",
    "cycle length": "cycle_length",
    # already internal in the shipped CSV, listed so the table is the whole story
    "age": "age",
    "sex": "sex",
    "height": "height",
    "weight": "weight",
    "creatinine": "creatinine",
    "input steroid": "input steroid",
    "target steroid": "target steroid",
    # Week 3, Family C. Continuous inputs of the rule-based scores; the boolean
    # criteria are mapped separately in CRITERIA below.
    "respiratory rate": "respiratory_rate",
}

# --- Week 3: the rule-based scores, mapped criterion by criterion ------------
#
# These three are what the exclusion note above is about, and Family C needs them:
# a criterion asserted and later denied is only a contradiction if the criterion
# is one the score actually reads. Mapping them is therefore a prerequisite, and
# the danger the note describes is unchanged -- `.get()` and `'x' in params` both
# read an unmapped key as "criterion absent" and return a plausible wrong score.
#
# So the mapping is not trusted on inspection. `verify_criteria.py` flips every
# criterion below on a real case and requires the score to move. A criterion that
# can be flipped without changing the total is either mapped wrong or not scored,
# and either way it cannot carry an item.
#
# Display key in the shipped CSV -> the name the implementation indexes.
CRITERIA = {
    4: {   # CHA2DS2-VASc  (cha2ds2_vasc_score.py)
        "Congestive Heart Faliure": "chf",          # misspelling is upstream's
        "Hypertension history": "hypertension",
        "Stroke": "stroke",
        "Transient Ischemic Attacks History": "tia",
        "Thromboembolism history": "thromboembolism",
        "Vascular disease history": "vascular_disease",
        "Diabetes history": "diabetes",
    },
    45: {  # CURB-65  (curb-65.py)
        "Confusion": "confusion",
    },
    8: {   # Wells' PE  (wells_criteria_pe.py)
        "Clinical signs and symptoms of Deep Vein Thrombosis": "clinical_dvt",
        "Pulmonary Embolism is #1 diagnosis OR equally likely": "pe_number_one",
        "Immobilization for at least 3 days": "immobilization_for_3days",
        "Surgery in the previous 4 weeks": "surgery_in_past4weeks",
        "Previously documented Deep Vein Thrombosis": "previous_dvt",
        "Previously Documented Pulmonary Embolism": "previous_pe",
        "Malignancy with treatment within 6 months or palliative": "malignancy_with_treatment",
        "Hemoptysis": "hemoptysis",
    },
}

# The non-boolean inputs each rule-based score also needs, mapped through ALIASES.
RULE_BASED_REQUIRED = {
    4:  ["age", "sex"],
    45: ["age", "sys_bp", "dia_bp", "bun", "respiratory_rate"],
    8:  ["heart_rate"],
}

# Deliberately NOT added to REQUIRED below. REQUIRED defines the population of
# the Week 1 label audit, whose result (0% mismatch on 50 scored, 586/586 census)
# is already reported and pre-registered. Widening that population now would
# change a published number for reasons unrelated to the question it answers, and
# nobody reading the two versions could tell which instrument produced which.
# Family C drives these three through CRITERIA instead. If we ever want them in
# the audit, that is a re-run of the whole audit, reported as one.

# calc_id -> inputs the implementation must find. Registered calculators only.
# `height` appears under Cockcroft-Gault because its code routes through BMI.
REQUIRED = {
    2:  ["age", "sex", "weight", "height", "creatinine"],   # Cockcroft-Gault
    3:  ["age", "sex", "creatinine"],                       # CKD-EPI 2021
    5:  ["sys_bp", "dia_bp"],                               # MAP
    6:  ["height", "weight"],                               # BMI
    7:  ["albumin", "calcium"],                             # calcium correction
    9:  ["age", "sex", "creatinine"],                       # MDRD
    10: ["height", "sex"],                                  # ideal body weight
    11: ["heart_rate", "qt_interval"],                      # QTc Bazett
    13: ["menstrual_date", "cycle_length"],                 # estimated due date
    19: ["age", "alt", "ast", "platelet_count"],            # FIB-4
    22: ["weight"],                                         # maintenance fluids
    24: ["input steroid", "target steroid"],                # steroid conversion
    26: ["sodium", "glucose"],                              # Na correction
    30: ["sodium", "bun", "glucose"],                       # serum osmolality
    31: ["glucose", "insulin"],                             # HOMA-IR
    38: ["age", "sex", "weight", "sodium"],                 # free water deficit
    39: ["sodium", "chloride", "bicarbonate"],              # anion gap
    40: ["creatinine", "sodium", "urine_creatinine", "urine_sodium"],  # FeNa
    44: ["total_cholestrol", "hdl_cholestrol", "triglycerides"],       # LDL
    56: ["heart_rate", "qt_interval"],                      # QTc Fridericia
    57: ["heart_rate", "qt_interval"],                      # QTc Framingham
    58: ["heart_rate", "qt_interval"],                      # QTc Hodges
    59: ["heart_rate", "qt_interval"],                      # QTc Rautaharju
    60: ["height", "weight"],                               # BSA
    61: ["body_mass_index", "height"],                      # target weight
    62: ["weight", "height", "sex"],                        # adjusted body weight
    63: ["sodium", "chloride", "bicarbonate"],              # delta gap
    64: ["sodium", "chloride", "bicarbonate"],              # delta ratio
    65: ["sodium", "chloride", "bicarbonate", "albumin"],   # alb-corr anion gap
    66: ["sodium", "chloride", "bicarbonate", "albumin"],   # alb-corr delta gap
    67: ["sodium", "chloride", "bicarbonate", "albumin"],   # alb-corr delta ratio
    68: ["menstrual_date", "cycle_length"],                 # estimated conception
    69: ["menstrual_date", "current_date"],                 # gestational age
}

# Calculators we deliberately do not drive, and why. Surfaced in the report so the
# coverage limit is stated by us rather than found by a reviewer.
UNREGISTERED_REASON = {
    4:  "rule-based; boolean criteria read via .get() default to absent when unmapped",
    8:  "rule-based; boolean criteria read via .get() default to absent when unmapped",
    15: "rule-based; boolean criteria read via .get() default to absent when unmapped",
    16: "rule-based; boolean criteria read via .get() default to absent when unmapped",
    17: "rule-based; boolean criteria read via .get() default to absent when unmapped",
    18: "rule-based; boolean criteria read via .get() default to absent when unmapped",
    20: "rule-based; boolean criteria read via .get() default to absent when unmapped",
    21: "rule-based; boolean criteria read via .get() default to absent when unmapped",
    23: "rule-based; boolean criteria read via .get() default to absent when unmapped",
    25: "rule-based; boolean criteria read via .get() default to absent when unmapped",
    27: "rule-based; boolean criteria read via .get() default to absent when unmapped",
    28: "rule-based; boolean criteria read via .get() default to absent when unmapped",
    29: "no implementation file at the version-1.0 tag",
    32: "rule-based; boolean criteria read via .get() default to absent when unmapped",
    33: "rule-based; boolean criteria read via .get() default to absent when unmapped",
    36: "rule-based; boolean criteria read via .get() default to absent when unmapped",
    43: "rule-based; boolean criteria read via .get() default to absent when unmapped",
    45: "rule-based; boolean criteria read via .get() default to absent when unmapped",
    46: "rule-based; boolean criteria read via .get() default to absent when unmapped",
    48: "rule-based; boolean criteria read via .get() default to absent when unmapped",
    49: "dose table keyed by opioid name; not a fixed input set",
    51: "rule-based; boolean criteria read via .get() default to absent when unmapped",
}


def normalise(entities):
    """Rename shipped keys to implementation keys. Unrecognised keys pass through."""
    return {ALIASES.get(k, k): v for k, v in entities.items()}


def is_registered(calc_id):
    return int(calc_id) in REQUIRED


def missing_inputs(calc_id, entities):
    """Required inputs this case does not supply, after renaming."""
    calc_id = int(calc_id)
    if calc_id not in REQUIRED:
        return None
    have = normalise(entities)
    return [k for k in REQUIRED[calc_id] if k not in have]
