#!/usr/bin/env python3
"""Dispatch table from a MedCalc-Bench Calculator ID to its released implementation.


MedCalc-Bench v1.0 ships the calculator implementations but no table saying which
file answers which Calculator ID, so we write one. Every entry names a module in
`data/medcalc/calculators/` and the entry point inside it; nothing here reimplements
a formula. `call(calc_id, entities)` returns the released code's own answer.

The point of routing through the released code rather than our own arithmetic is
that our clean answers are then recomputed, not inherited, and any disagreement
with a shipped label is a fact about MedCalc-Bench rather than about us.
"""
import ast
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import entities as entities_mod  # noqa: E402

CALC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "medcalc", "calculators")

# The implementations import each other by bare name, so their own directory has
# to be on the path exactly as it is in the upstream repo.
if CALC_DIR not in sys.path:
    sys.path.insert(0, CALC_DIR)

# calc_id -> (module, function). Module names with hyphens are why this goes
# through importlib rather than plain imports.
REGISTRY = {
    2:  ("creatinine_clearance", "generate_cockcroft_gault_explanation"),
    3:  ("ckd-epi_2021_creatinine", "ckd_epi_2021_explanation"),
    4:  ("cha2ds2_vasc_score", "generate_cha2ds2_vasc_explanation"),
    5:  ("mean_arterial_pressure", "mean_arterial_pressure_explanation"),
    6:  ("bmi_calculator", "bmi_calculator_explanation"),
    7:  ("calcium_correction", "calculate_corrected_calcium_explanation"),
    8:  ("wells_criteria_pe", "calculate_pe_wells_explanation"),
    9:  ("mdrd_gfr", "mrdr_gfr_explanation"),
    10: ("ideal_body_weight", "ibw_explanation"),
    11: ("qt_calculator_bazett", "bazett_calculator_explanation"),
    13: ("estimated_due_date", "add_40_weeks_explanation"),
    15: ("child_pugh_score", "compute_child_pugh_score_explanation"),
    16: ("wells_criteria_dvt", "compute_wells_criteria_dvt_explanation"),
    17: ("cardiac_risk_index", "compute_cardiac_index_explanation"),
    18: ("heart_score", "compute_heart_score_explanation"),
    19: ("fibrosis_4", "compute_fib4_explanation"),
    20: ("centor_score", "compute_centor_score_explanation"),
    21: ("glasgow_coma_score", "compute_glasgow_coma_score_explanation"),
    22: ("maintenance_fluid_calc", "maintenance_fluid_explanation"),
    23: ("meldna", "compute_meldna_explanation"),
    24: ("steroid_conversion_calculator", "compute_steroid_conversion_explanation"),
    25: ("has_bled_score", "compute_has_bled_score_explanation"),
    26: ("sodium_correction_hyperglycemia",
         "compute_sodium_correction_hyperglycemia_explanation"),
    27: ("glasgow_bleeding_score", "glasgow_bleeding_score_explanation"),
    28: ("apache_ii", "apache_ii_explanation"),
    # 29 (PSI Score) has 20 rows in v1.0's test set but no implementation file in
    # the v1.0 tag. Left unregistered on purpose; the audit reports it as
    # undrivable rather than silently dropping it.
    30: ("sOsm", "compute_serum_osmolality_explanation"),
    31: ("homa_ir", "compute_homa_ir_explanation"),
    32: ("cci", "compute_cci_explanation"),
    33: ("feverpain", "compute_fever_pain_explanation"),
    36: ("caprini_score", "caprini_score_explanation"),
    38: ("free_water_deficit", "free_water_deficit_explanations"),
    39: ("anion_gap", "compute_anion_gap_explanation"),
    40: ("compute_fena", "compute_fena_explanation"),
    43: ("sofa", "compute_sofa_explanation"),
    44: ("ldl_calculated", "compute_ldl_explanation"),
    45: ("curb-65", "curb_65_explanation"),
    46: ("framingham_risk_score", "framingham_risk_score_explanation"),
    48: ("perc_rule", "compute_perc_rule_explanation"),
    49: ("mme", "mme_explanation"),
    51: ("sirs_criteria", "SIRS_criteria_explanation"),
    56: ("qt_calculator_fredericia", "fredericia_calculator_explanation"),
    57: ("qt_calculator_framingham", "framingham_calculator_explanation"),
    58: ("qt_calculator_hodges", "hodges_calculator_explanation"),
    59: ("qt_calculator_rautaharju", "rautaharju_calculator_explanation"),
    60: ("bsa_calculator", "bsa_calculator_explanation"),
    61: ("target_weight", "targetweight_explanation"),
    62: ("adjusted_body_weight", "abw_explanation"),
    63: ("delta_gap", "compute_delta_gap_explanation"),
    64: ("delta_ratio", "compute_delta_ratio_explanation"),
    65: ("albumin_corrected_anion", "compute_albumin_corrected_anion_explanation"),
    66: ("albumin_corrected_delta_gap", "compute_albumin_corrected_delta_gap_explanation"),
    67: ("albumin_delta_ratio", "compute_albumin_delta_ratio_explanation"),
    68: ("estimated_conception_date", "add_2_weeks_explanation"),
    69: ("estimated_gestational_age", "compute_gestational_age_explanation"),
}

_cache = {}


def entry_point(calc_id):
    """The released function for this calculator, or None if we have no driver."""
    calc_id = int(calc_id)
    if calc_id not in REGISTRY:
        return None
    if calc_id not in _cache:
        mod_name, fn_name = REGISTRY[calc_id]
        mod = importlib.import_module(mod_name)
        _cache[calc_id] = getattr(mod, fn_name)
    return _cache[calc_id]


def parse_entities(raw):
    """`Relevant Entities` ships as a stringified Python dict."""
    return raw if isinstance(raw, dict) else ast.literal_eval(raw)


def call(calc_id, entities):
    """Run the released implementation on shipped entities. Returns {'Answer', ...}.

    Entity keys are renamed first; see entities.py for why that layer exists.
    """
    fn = entry_point(calc_id)
    if fn is None:
        raise KeyError(f"no registered implementation for calculator {calc_id}")
    return fn(entities_mod.normalise(parse_entities(entities)))
