#!/usr/bin/env python3
"""Locate the exact character span in a note that carries a given formula input.

Task owner: Annotator D -- Week 1 task S2.
Completed by Annotator D.

This is the anchoring layer both the seed freeze and the injection engine depend
on. The rule it implements: a span counts only when a label word for the quantity,
the number, and the expected unit occur together in one uninterrupted phrase — and
the number equals the value the calculator actually consumes.

Anchoring is done with explicit phrase patterns rather than "a number near the word
creatinine", because proximity is not the same as reference. A line reading
`blood urea nitrogen (BUN), 34.4 mg/dL; and creatinine, 1.4 mg/dL` puts the BUN
value well within any reasonable window of the word "creatinine". The gap between
label and number is therefore constrained to contain no digits and no sentence
punctuation, which is what stops a match from stepping over an intervening value.

Uniqueness does the rest of the work. A note saying the patient weighed 67.2 kg
and had previously weighed 71.2 kg has two weights; editing the wrong one produces
an item where the contradiction we think we injected is not the one the calculator
sees. An ambiguous locate is reported as ambiguous, and the caller drops the seed.

Everything here is read-only on the note. Nothing edits text; construct.py does
that, using the spans this returns.
"""
import re

NUM = r"(?P<value>\d+(?:[.,]\d+)?)"

# Gap between a label and its value: no digits (cannot step over another value)
# and no sentence-ending punctuation (cannot leave the clause).
GAP = r"[^.\n\d]{0,%d}?"

# Unit as MedCalc's entities spell it -> how a note may write it.
UNIT_PATTERNS = {
    "mg/dL": r"mg\s*/\s*d[lL]\b",
    "µmol/L": r"[µμu]mol\s*/\s*[lL]\b",
    "mmol/L": r"mmol\s*/\s*[lL]\b",
    "mEq/L": r"m(?:Eq|eq|EQ)\s*/\s*[lL]\b",
    "kg": r"kg\b",
    "lbs": r"(?:lbs?|pounds)\b",
    "cm": r"cm\b",
    "m": r"m\b",
    "years": r"years?\b",
}

# Units that may substitute for each other when matching a stated value: a note
# writing "0.86 mg/dL" satisfies an entity recorded in mg/dL and nothing else.
UNIT_FAMILIES = {
    "mg/dL": ["mg/dL"],
    "µmol/L": ["µmol/L"],
    "mmol/L": ["mmol/L"],
    # For sodium, chloride and bicarbonate these are numerically the same, since
    # all three are monovalent. Notes use them interchangeably, and refusing one
    # would drop half the substrate for no gain in correctness. This equivalence
    # does NOT hold in general, which is why it lives here per unit rather than
    # being applied to every analyte.
    "mEq/L": ["mEq/L", "mmol/L"],
    "kg": ["kg"],
    "cm": ["cm"],
    "years": ["years"],
}


def _u(units):
    return r"(?P<unit>" + "|".join(UNIT_PATTERNS[u] for u in units) + r")"


def _patterns(units):
    """Phrase patterns per label, given the units we will accept."""
    u = _u(units)
    return {
        "creatinine": [
            r"(?P<label>(?:serum |plasma |blood )?creatinine)\b" + GAP % 25 + NUM + r"\s{0,3}" + u,
            r"(?P<label>\bs?cr)\b" + GAP % 15 + NUM + r"\s{0,3}" + u,
        ],
        "weight": [
            r"(?P<label>(?:body )?weigh(?:t|ed|s|ing))\b" + GAP % 25 + NUM + r"\s{0,3}" + u,
            NUM + r"\s{0,3}" + u + GAP % 15 + r"(?:in )?(?P<label>(?:body )?weight)\b",
        ],
        "height": [
            r"(?P<label>height|stature)\b" + GAP % 25 + NUM + r"\s{0,3}" + u,
            # "160 cm (5 ft 3 in) tall" — the parenthetical carries digits, so this
            # one pattern deliberately allows them; the value check still applies.
            NUM + r"\s{0,3}" + u + r"[^.\n]{0,20}?\b(?P<label>tall)\b",
        ],
        "age": [
            NUM + r"[-\s]?(?P<unit>years?)[-\s]?(?P<label>old)\b",
            r"(?P<label>aged?)\b" + GAP % 12 + NUM + r"\s{0,3}" + u,
        ],
        # Week 3 breadth: LDL is computed from the lipid panel, and HDL is the
        # component a conflict is injected into. `LDL` and `HDL` differ by one
        # letter, so the label is anchored rather than matched loosely.
        "hdl": [
            r"(?P<label>HDL(?:[- ]cholesterol)?|high[- ]density\s+lipoprotein"
            r"(?:\s+cholesterol)?)\b" + GAP % 25 + NUM + r"\s{0,3}" + u,
        ],
        # Electrolytes, for the breadth arms whose calculators consume them.
        # The abbreviations are anchored tightly: a bare `na` matches inside
        # ordinary words, and `cl` is a unit prefix as often as it is chloride.
        "sodium": [
            r"(?P<label>serum\s+sodium|sodium|\bNa\+?\b)" + GAP % 25 + NUM
            + r"\s{0,3}" + u,
        ],
        "chloride": [
            r"(?P<label>serum\s+chloride|chloride|\bCl-?\b)" + GAP % 25 + NUM
            + r"\s{0,3}" + u,
        ],
        "bicarbonate": [
            r"(?P<label>bicarbonate|\bHCO3-?\b)" + GAP % 25 + NUM
            + r"\s{0,3}" + u,
        ],
    }


# Categorical inputs are located by the words that carry them, not by a number.
SEX_PATTERNS = {
    "Male": r"\b(?:man|male|gentleman|boy|he|his|him)\b",
    "Female": r"\b(?:woman|female|lady|girl|she|her|hers)\b",
}

# Race has to be anchored to a person, or it matches the laboratory section. A
# bare \bwhite\b hits "white blood cell count" and "white matter hypodensity",
# which is how a first version of this located race in seven notes that never
# mention it. Two admissible shapes: the term qualifies a person noun ("a
# 45-year-old white man"), or it follows an explicit race/ethnicity label.
_PERSON = (r"(?:m[ae]n|wom[ae]n|male|female|patient|boy|girl|gentleman|lady|"
           r"adult|individual|child)")
_RACE_TERMS = {"Black": r"black|african[- ]american",
               "White": r"white|caucasian"}
RACE_PATTERNS = {
    key: (rf"\b(?:race|ethnicity)\b[^.\n]{{0,15}}?\b(?:{terms})\b"
          rf"|\b(?:{terms})\b(?=[^.\n]{{0,25}}?\b{_PERSON}\b)")
    for key, terms in _RACE_TERMS.items()
}


# Blood pressure is a pair sharing one label and one unit, which makes it a
# different object from the single measurements above: an edit targets one of the
# two numbers, or swaps them, so both spans have to come back separately.
#
# Anchoring is on the label and the unit for the same reason as everywhere else.
# A bare \d{2,3}/\d{2,3} matches "Glasgow Coma Score was 15/15", and it matches
# the date and dose forms too. The unit is what makes a slash-pair a pressure.
BP_LABEL = (r"(?P<label>(?:arterial\s+)?blood\s+pressure(?:\s*\(\s*BP\s*\))?"
            r"|\bBP\b)")
BP_PAIR = r"(?P<sys>\d{2,3})\s*/\s*(?P<dia>\d{2,3})"
BP_UNIT = r"(?P<unit>mm\s*(?:of\s*)?\s*Hg)"

# The unit is spelled three ways in this corpus (mmHg, mm Hg, mm of Hg) and is
# occasionally absent. Absent-unit matches are returned, but flagged, because a
# pair with no unit is one register short of certain and the caller may want to
# refuse it. The trailing (?!\s*/) stops "15/15/15"-style runs being read as a
# pressure whose second number happens to fit.
BP_WITH_UNIT = BP_LABEL + GAP % 25 + BP_PAIR + r"\s{0,3}" + BP_UNIT
BP_NO_UNIT = BP_LABEL + GAP % 25 + BP_PAIR + r"(?!\s*/)"


# BMI is a derived value: the note states it and also states the height and weight
# it is derived from. Locating it is what lets Family A rewrite the claim without
# touching either component.
#
# The unit is optional here, unlike blood pressure. Notes write "BMI is 42 kg/m2",
# "body mass index, 18.3" and "a body mass index of 22.1 kilograms per meter
# squared" in roughly equal measure, and requiring the unit would throw away most
# of the substrate. The label carries enough on its own -- "BMI" and "body mass
# index" are not ambiguous the way a bare slash-pair is.
BMI_LABEL = (r"(?P<label>body\s+mass\s+index(?:\s*\(\s*BMI\s*\))?"
             r"|BMI(?:\s*\(\s*body\s+mass\s+index\s*\))?)")
BMI_UNIT = r"(?P<unit>kg\s*/\s*m\s*(?:\^\s*2|²|2)?|kilograms?\s+per\s+met(?:er|re)\w*\s*(?:squared)?)"
BMI_PATTERN = BMI_LABEL + r"[:,]?" + GAP % 30 + NUM + r"(?:\s{0,3}" + BMI_UNIT + r")?"


# --- Week 3, Family C: scored yes/no criteria -------------------------------
#
# A criterion is a claim, not a number, so locating one is a different problem
# from every locator above. Three things go wrong, and all three were found by
# reading CHA2DS2-VASc notes rather than predicted:
#
#   the word names a different condition   `pulmonary hypertension` and `portal
#       hypertension` are not the systemic hypertension the score means, and the
#       corpus is full of both.
#   the sentence denies it                 `no history of hypertension,
#       dyslipidaemia, diabetes` -- one negator governing a whole list, so
#       scanning a fixed window backwards from the match is not enough.
#   it belongs to someone else             `Her family history is positive for
#       hypertension` is the patient's mother, and MedCalc records the criterion
#       as present. Same failure as the seed whose creatinine was the patient's
#       grandmother's.
#
# The vocabulary is therefore a term list plus a disqualifying-qualifier list per
# criterion, and assertion is decided by negation scope rather than proximity.
CRITERION_TERMS = {
    # CHA2DS2-VASc
    "hypertension": {
        "terms": r"hypertensi(?:on|ve)",
        "not_when_preceded_by": r"pulmonary(?:\s+arter\w+)?|portal|intracranial|ocular|"
                                r"venous|renovascular|gestational|white[- ]coat|"
                                r"pulmonary\s+artery",
    },
    "diabetes": {"terms": r"diabet(?:es|ic)", "not_when_preceded_by": r"insipidus"},
    "chf": {"terms": r"congestive\s+heart\s+failure|CHF|heart\s+failure", "not_when_preceded_by": r""},
    "stroke": {"terms": r"strokes?|cerebrovascular\s+accident|CVA", "not_when_preceded_by": r"heat|sun"},
    "tia": {"terms": r"transient\s+ischemic\s+attacks?|TIA", "not_when_preceded_by": r""},
    "thromboembolism": {"terms": r"thromboembolism|thromboembolic", "not_when_preceded_by": r""},
    "vascular_disease": {"terms": r"peripheral\s+arter\w+\s+disease|vascular\s+disease|"
                                  r"myocardial\s+infarction|aortic\s+plaque",
                         "not_when_preceded_by": r"cerebro"},
    # CURB-65
    "confusion": {"terms": r"confus(?:ion|ed)|disorient(?:ed|ation)", "not_when_preceded_by": r""},
    # Wells' PE
    "clinical_dvt": {"terms": r"deep\s+vein\s+thrombosis|DVT", "not_when_preceded_by": r""},
    "hemoptysis": {"terms": r"h(?:a)?emoptysis", "not_when_preceded_by": r""},
    "previous_pe": {"terms": r"pulmonary\s+embolism|PE\b", "not_when_preceded_by": r""},
    "malignancy_with_treatment": {"terms": r"malignancy|carcinoma|cancer",
                                  "not_when_preceded_by": r""},
    "immobilization_for_3days": {"terms": r"immobili[sz]ation|immobili[sz]ed|bed[- ]rest",
                                 "not_when_preceded_by": r""},
    "surgery_in_past4weeks": {"terms": r"surger(?:y|ies)|operation", "not_when_preceded_by": r""},
}

# Which criteria a keyword locator can actually carry, measured against all 1,087
# rows rather than guessed. The test is the false-positive column: how often the
# locator calls a criterion asserted where the score does not have it, because
# that is the direction that builds a broken item.
#
# EXCLUDED, and why -- each of these was read, not inferred from a number:
#
#   surgery_in_past4weeks       26 false positives. The word does not name the
#       event: `Surgery was consulted` is a department, `During the operation`
#       and `Surgical intervention was performed` are this admission's procedure,
#       none of them a surgery in the previous four weeks. The criterion carries
#       a time window that keyword matching cannot see.
#   immobilization_for_3days    same shape, and only 1 usable case anyway.
#   malignancy_with_treatment   13 false positives; `within 6 months or
#       palliative` is again a window the vocabulary cannot check.
#   previous_pe                 15 false positives. `pulmonary embolism` is the
#       thing being diagnosed on this admission far more often than a previous
#       one, and `previous` is not reliably adjacent.
#   pe_number_one               no vocabulary. "PE is the #1 diagnosis or equally
#       likely" is a clinician's judgement, not a claim notes make in words.
#   previous_dvt                not separable from clinical_dvt by vocabulary.
#
# A separate finding, and the reason locator and score must AGREE rather than the
# score being trusted: of the notes where MedCalc records hypertension present but
# the locator finds no assertion, most have **no mention of hypertension anywhere
# in the note text**. The annotation supplies criteria the note never states.
# Requiring both to agree filters our errors and theirs at once.
USABLE_CRITERIA = {
    "hypertension", "diabetes", "chf", "stroke", "tia", "thromboembolism",
    "vascular_disease", "confusion", "hemoptysis", "clinical_dvt",
}

# Criterion vocabulary inside the name of a measuring instrument. `The National
# Institutes of Health Stroke Scale (NIHSS) score was 12` contains the word
# stroke and asserts nothing about a stroke history; `Thrombolysis In Myocardial
# Infarction (TIMI) flow 3` is an angiographic grade, not an infarction. Three of
# the first thirty Family C items were anchored on one of these, and only reading
# them found it -- every automated check passed, because the word really is there
# and really is undenied and really is about the patient's admission.
INSTRUMENT_AFTER = r"\s*(?:scale|score|index|criteria|classification|grade|stag(?:e|ing))\b"
INSTRUMENT_BEFORE = (r"(?:thrombolysis\s+in|national\s+institutes?\s+of\s+health|"
                     r"\bNIH|modified\s+rankin)\s*$")

# A negator anywhere earlier in the same clause turns an assertion into a denial.
# `no history of hypertension, dyslipidaemia, diabetes` denies all three, so scope
# runs from the negator forward until the clause ends rather than a fixed window.
NEGATORS = (r"\b(?:no|not|non|without|denies|denied|negative\s+for|free\s+of|"
            r"ruled\s+out|absence\s+of|absent|never|unremarkable\s+for)\b")

# What ends a negation's reach. A list keeps it alive across commas and `or`;
# a full stop, a semicolon or a contrastive conjunction ends it.
NEGATION_ENDS = r"[.;:\n]|\b(?:but|however|although|though|except|positive\s+for)\b"

# Family history and relatives. A criterion inside one of these belongs to
# somebody who is not the patient.
THIRD_PARTY = (r"\b(?:family\s+histor\w+|father|mother|grandmother|grandfather|"
               r"parents?|sister|brother|sibling|son|daughter|aunt|uncle|cousin|"
               r"maternal|paternal)\b")


class Ambiguous(Exception):
    """More than one span in the note satisfies the anchoring rule."""

    def __init__(self, matches):
        self.matches = matches
        super().__init__(f"{len(matches)} candidate spans")


class NotFound(Exception):
    """No span satisfies the anchoring rule."""


def _numeric_equal(text, value):
    try:
        return abs(float(text.replace(",", ".")) - float(value)) < 1e-9
    except ValueError:
        return False


def _hits(note, label, units):
    """Every anchored measurement of `label` in `note`, deduplicated by span."""
    out = {}
    for pattern in _patterns(units)[label]:
        for m in re.finditer(pattern, note, re.I):
            key = (m.start("value"), m.end("value"))
            if key in out:
                continue
            out[key] = m
    return [out[k] for k in sorted(out)]


def _record(note, m, label, unit, context):
    v0, v1 = m.span("value")
    u0, u1 = m.span("unit")
    l0, l1 = m.span("label")
    return {
        "label": label,
        "value": float(m.group("value").replace(",", ".")),
        "unit": unit,
        "value_span": [v0, v1],
        "value_text": m.group("value"),
        "unit_span": [u0, u1],
        "unit_text": m.group("unit"),
        "span": [min(v0, l0), max(u1, l1)],
        "text": note[min(v0, l0):max(u1, l1)],
        "anchor_text": m.group("label"),
        "anchor_span": [l0, l1],
        "context": note[max(0, min(v0, l0) - context):max(u1, l1) + context],
    }


def find_measurement(note, value, unit, label, context=45):
    """The span carrying `value` `unit` for `label`. Raises NotFound / Ambiguous.

    The returned record distinguishes three nested spans:
      value_span   the digits alone — what a minimal edit rewrites
      unit_span    the unit token — what an edit must leave intact
      span         label through unit — the whole phrase, for human review
    """
    units = UNIT_FAMILIES.get(unit)
    if units is None:
        raise NotFound(f"{label}: unit {unit!r} not recognised")
    matching = [m for m in _hits(note, label, units)
                if _numeric_equal(m.group("value"), value)]
    if not matching:
        raise NotFound(f"{label} {value} {unit}")
    records = [_record(note, m, label, unit, context) for m in matching]
    if len(records) > 1:
        raise Ambiguous(records)
    return records[0]


def find_age(note, value, context=45):
    """Age, written as a unit-bearing number: "an 87-year-old man"."""
    return find_measurement(note, value, "years", "age", context=context)


def find_word(note, patterns, key, label, context=45):
    """The span of the first word carrying a categorical input (sex, race).

    Repeated mentions are expected and harmless here — a note says "he" many times
    — so the first occurrence is taken rather than demanding uniqueness. What is
    checked instead is whether the note also asserts the opposite category, which
    would make the input contradictory before we touched it.
    """
    if key not in patterns:
        raise NotFound(f"{label}={key!r} is not a category we can locate")
    rx = re.compile(patterns[key], re.I)
    m = rx.search(note)
    if m is None:
        raise NotFound(f"{label}={key}")
    return {
        "label": label,
        "value": key,
        "unit": None,
        "value_span": [m.start(), m.end()],
        "value_text": m.group(0),
        "span": [m.start(), m.end()],
        "text": m.group(0),
        "anchor_text": m.group(0),
        "anchor_span": [m.start(), m.end()],
        "context": note[max(0, m.start() - context):m.end() + context],
        "other_categories_present": [k for k in patterns if k != key
                                     and re.search(patterns[k], note, re.I)],
        "n_mentions": len(rx.findall(note)),
    }


def _bp_hits(note):
    """Every anchored blood pressure in `note`, unit-bearing ones preferred.

    Unit-bearing and unitless matches are not pooled. A note that states one
    pressure with a unit and mentions another without is not a note with two
    equally good candidates, and pooling them would make it ambiguous and drop a
    usable seed. Unitless matches are consulted only when nothing carries a unit.
    """
    out = {}
    for m in re.finditer(BP_WITH_UNIT, note, re.I):
        out[m.span("sys")] = (m, True)
    if not out:
        for m in re.finditer(BP_NO_UNIT, note, re.I):
            out[m.span("sys")] = (m, False)
    return [out[k] for k in sorted(out)]


def _bp_record(note, m, has_unit, context):
    s0, s1 = m.span("sys")
    d0, d1 = m.span("dia")
    l0, l1 = m.span("label")
    end = m.end("unit") if has_unit else d1
    return {
        "label": "blood_pressure",
        "systolic": float(m.group("sys")),
        "diastolic": float(m.group("dia")),
        "sys_span": [s0, s1],
        "sys_text": m.group("sys"),
        "dia_span": [d0, d1],
        "dia_text": m.group("dia"),
        "pair_span": [s0, d1],
        "pair_text": note[s0:d1],
        "unit_span": [m.start("unit"), m.end("unit")] if has_unit else None,
        "unit_text": m.group("unit") if has_unit else None,
        "has_unit": has_unit,
        "span": [min(s0, l0), max(end, l1)],
        "text": note[min(s0, l0):max(end, l1)],
        "anchor_text": m.group("label"),
        "anchor_span": [l0, l1],
        "impossible": float(m.group("sys")) < float(m.group("dia")),
        "context": note[max(0, min(s0, l0) - context):max(end, l1) + context],
    }


def find_blood_pressure(note, systolic, diastolic, context=45):
    """The span carrying this systolic/diastolic pair. Raises NotFound / Ambiguous.

    `systolic` and `diastolic` are the values the calculator consumes, and the
    match must equal them. That equality is doing real work here rather than
    being a formality: MedCalc's shipped entities disagree with the note's own
    text on twenty of the 948 MAP rows, and in one of those (`pmc-6637642-1`) the
    note reads `blood pressure 85/140 mmHg` while the entities record 140/85 --
    the extraction silently put an impossible pair back into plausible order.
    Seeding from a note whose stated pair is not the pair being consumed would
    mean editing a number the calculator never reads.
    """
    matching = [(m, u) for m, u in _bp_hits(note)
                if _numeric_equal(m.group("sys"), systolic)
                and _numeric_equal(m.group("dia"), diastolic)]
    if not matching:
        raise NotFound(f"blood pressure {systolic:g}/{diastolic:g}")
    records = [_bp_record(note, m, u, context) for m, u in matching]
    if len(records) > 1:
        raise Ambiguous(records)
    return records[0]


def count_blood_pressures(note):
    """Spans of every blood pressure the note states, at any value.

    The eligibility gate for Family B: transposing the one pressure a note states
    is a controlled edit, and doing it to one of several is not -- the others
    remain plausible and the note no longer contains a single impossible claim.
    """
    return [list(m.span("sys")) for m, _ in _bp_hits(note)]


# Every derived value a note can state alongside its own components, in the same
# shape: a label, an optional unit, and a number. BMI was the first; anion gap and
# serum osmolality behave identically, so they get a table entry rather than a
# second locator. The unit stays optional throughout -- notes write "anion gap of
# 18" as readily as "anion gap 18 mEq/L", and requiring it throws away substrate
# for no gain, because these labels are unambiguous in a way a bare number is not.
DERIVED_TERMS = {
    "bmi": {
        "label": (r"body\s+mass\s+index(?:\s*\(\s*BMI\s*\))?"
                  r"|BMI(?:\s*\(\s*body\s+mass\s+index\s*\))?"),
        "unit": (r"kg\s*/\s*m\s*(?:\^\s*2|²|2)?"
                 r"|kilograms?\s+per\s+met(?:er|re)\w*\s*(?:squared)?"),
    },
    "anion_gap": {
        "label": r"anion\s+gap(?:\s*\(\s*AG\s*\))?",
        "unit": r"m(?:Eq|mol)\s*/\s*[lL]",
    },
    "osmolality": {
        "label": r"(?:serum|plasma|calculated)?\s*osmolalit(?:y|ies)",
        "unit": r"mOsm\s*/\s*(?:kg|[lL])(?:\s*H2O)?",
        # Urine osmolality is a different quantity; a *measured* osmolality
        # differing from the calculated one is an osmolal gap, a real clinical
        # finding rather than a contradiction. Without these the locator reads
        # `urine specific gravity, serum and urine osmolality were found as
        # 1,007, 323 mOsm/kg` and returns the specific gravity.
        "not_when_preceded_by": r"urin\w*|measured|effective|paired",
    },
}


def _derived_pattern(key):
    spec = DERIVED_TERMS[key]
    return (rf"(?P<label>{spec['label']})[:,]?" + GAP % 30 + NUM
            + rf"(?:\s{{0,3}}(?P<unit>{spec['unit']}))?")


def _derived_hits(note, key):
    qual = DERIVED_TERMS[key].get("not_when_preceded_by")
    out = {}
    for m in re.finditer(_derived_pattern(key), note, re.I):
        if qual:
            before = note[max(0, m.start() - 32):m.start()]
            if re.search(rf"(?:{qual})\W*$", before, re.I):
                continue
        out[m.span("value")] = m
    return [out[k] for k in sorted(out)]


def find_derived(note, key, value=None, context=45):
    """The span carrying a documented derived value. Raises NotFound / Ambiguous.

    `value` is optional for the same reason it is on BMI: the number is not one
    the calculator consumes, it is a claim the note makes about its own
    components, so the caller recomputes and compares rather than matching.
    """
    if key not in DERIVED_TERMS:
        raise NotFound(f"{key!r} is not a derived value we locate")
    hits = _derived_hits(note, key)
    if value is not None:
        hits = [m for m in hits if _numeric_equal(m.group("value"), value)]
    if not hits:
        raise NotFound(key + (f" {value}" if value is not None else ""))
    if len(hits) > 1:
        raise Ambiguous([_bmi_record(note, m, context) for m in hits])
    return _bmi_record(note, hits[0], context)


def count_derived(note, key):
    """Spans of every documented mention. The eligibility gate for Family A."""
    return [list(m.span("value")) for m in _derived_hits(note, key)]


def _bmi_hits(note):
    return _derived_hits(note, "bmi")


def find_bmi(note, value=None, context=45):
    """The span carrying a documented BMI. Raises NotFound / Ambiguous.

    `value` is optional because, unlike every other locator here, the number is
    not one the calculator consumes -- it is a claim the note makes about its own
    height and weight. When given, it is checked; when not, the note's single
    stated BMI is returned and the caller compares it against the recomputation.
    """
    hits = _bmi_hits(note)
    if value is not None:
        hits = [m for m in hits if _numeric_equal(m.group("value"), value)]
    if not hits:
        raise NotFound("body mass index" + (f" {value}" if value is not None else ""))
    if len(hits) > 1:
        raise Ambiguous([_bmi_record(note, m, context) for m in hits])
    return _bmi_record(note, hits[0], context)


def _bmi_record(note, m, context):
    v0, v1 = m.span("value")
    l0, l1 = m.span("label")
    has_unit = m.group("unit") is not None
    end = m.end("unit") if has_unit else v1
    return {
        "label": "body_mass_index",
        "value": float(m.group("value").replace(",", ".")),
        "value_span": [v0, v1],
        "value_text": m.group("value"),
        "unit_span": [m.start("unit"), m.end("unit")] if has_unit else None,
        "unit_text": m.group("unit") if has_unit else None,
        "has_unit": has_unit,
        "span": [min(v0, l0), max(end, l1)],
        "text": note[min(v0, l0):max(end, l1)],
        "anchor_text": m.group("label"),
        "anchor_span": [l0, l1],
        "context": note[max(0, min(v0, l0) - context):max(end, l1) + context],
    }


def count_bmis(note):
    """Spans of every documented BMI. The eligibility gate for Family A."""
    return [list(m.span("value")) for m in _bmi_hits(note)]


def _clause_bounds(note, pos):
    """The sentence containing `pos`, as (start, end)."""
    start = max((note.rfind(ch, 0, pos) for ch in ".;\n"), default=-1) + 1
    ends = [note.find(ch, pos) for ch in ".;\n"]
    ends = [e for e in ends if e != -1]
    return start, (min(ends) if ends else len(note))


def _is_negated(note, start, end):
    """Does a negator earlier in this clause govern the term at [start:end]?

    Scope runs forward from the negator and dies at a clause end or a contrastive
    conjunction, so one `no history of` covers a comma-separated list but does not
    survive `... but has hypertension`.
    """
    c0, _ = _clause_bounds(note, start)
    lead = note[c0:start]
    last = None
    for m in re.finditer(NEGATORS, lead, re.I):
        last = m
    if last is None:
        return False
    between = lead[last.end():]
    return re.search(NEGATION_ENDS, between, re.I) is None


def _is_third_party(note, start):
    """Is the criterion attributed to a relative rather than to the patient?"""
    c0, _ = _clause_bounds(note, start)
    return re.search(THIRD_PARTY, note[c0:start], re.I) is not None


def _criterion_hits(note, key):
    """Every mention of the criterion's vocabulary, with why each was kept or not."""
    spec = CRITERION_TERMS.get(key)
    if spec is None:
        raise NotFound(f"{key!r} has no criterion vocabulary")
    out = []
    for m in re.finditer(rf"\b(?:{spec['terms']})\b", note, re.I):
        qual = spec.get("not_when_preceded_by") or ""
        before = note[max(0, m.start() - 30):m.start()]
        after = note[m.end():m.end() + 30]
        if qual and re.search(rf"(?:{qual})\s*$", before, re.I):
            out.append((m, "names a different condition"))
        elif (re.match(INSTRUMENT_AFTER, after, re.I)
              or re.search(INSTRUMENT_BEFORE, before, re.I)):
            out.append((m, "part of an instrument name"))
        elif _is_negated(note, m.start(), m.end()):
            out.append((m, "denied"))
        elif _is_third_party(note, m.start()):
            out.append((m, "attributed to a relative"))
        else:
            out.append((m, None))
    return out


def find_criterion(note, key, context=60):
    """Where the note asserts this scored criterion. Raises NotFound / Ambiguous.

    Only unqualified, undenied, patient-attributed mentions count as assertions.
    The rejected mentions come back on the record so a caller can report why a
    note was dropped rather than only that it was.
    """
    hits = _criterion_hits(note, key)
    kept = [m for m, why in hits if why is None]
    if not kept:
        raise NotFound(f"{key}: no asserted mention"
                       + (f" ({len(hits)} rejected)" if hits else ""))
    if len(kept) > 1:
        raise Ambiguous([_criterion_record(note, m, key, context) for m in kept])
    rec = _criterion_record(note, kept[0], key, context)
    rec["rejected_mentions"] = [{"text": m.group(0), "span": list(m.span()), "why": why}
                                for m, why in hits if why is not None]
    return rec


def _criterion_record(note, m, key, context):
    c0, c1 = _clause_bounds(note, m.start())
    return {
        "label": "criterion",
        "criterion": key,
        "value": True,
        "value_span": list(m.span()),
        "value_text": m.group(0),
        "span": list(m.span()),
        "text": m.group(0),
        "anchor_text": m.group(0),
        "anchor_span": list(m.span()),
        "clause_span": [c0, c1],
        "clause_text": note[c0:c1].strip(),
        "context": note[max(0, m.start() - context):m.end() + context],
    }


def count_criterion_mentions(note, key):
    """Asserted mentions only. The eligibility gate for Family C."""
    return [list(m.span()) for m, why in _criterion_hits(note, key) if why is None]


def count_measurements(note, label, units):
    """Spans of every measurement of `label` the note states, at any value.

    An eligibility gate: injecting a second creatinine is only a controlled edit
    if the note stated exactly one to begin with. A note reporting a trend has
    already made the point we are trying to introduce.
    """
    return [list(m.span("value")) for m in _hits(note, label, units)]
