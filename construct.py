#!/usr/bin/env python3
"""Build the dissociation variants from the frozen seeds.


Four conditions per seed, differing only in why the item is or is not answerable:

  clean           the note as published                      -> compute
  missing         the creatinine measurement is deleted      -> decline
  value_conflict  two divergent creatinines, no cue which    -> flag
  resolvable      the same two values, plus a cue naming one -> compute the cued one

`value_conflict` and `resolvable` share byte-identical notes. The only thing that
differs between them is one sentence appended to the question. That is deliberate:
if the cue lived in the note, a difference between the two conditions could be a
difference in the text, and the parsing-vs-flagging split we want to measure would
be confounded by it. With the note held fixed, a model that computes correctly
under `resolvable` has demonstrably parsed both values, so failing to flag under
`value_conflict` is not a parsing failure.

**The minimal-edit rule.** Only the words carrying the target value are touched,
and which words those are comes from spans.py's anchoring, not from a search for
the number. The unit is what makes the value the one the calculator consumes, so
every edit is expressed relative to the located label-value-unit phrase.

**Why the second value is what it is.** A second creatinine that changes the
answer by 3% is not a conflict anyone needs to resolve. Candidates are scored on
producing a decision-relevant divergence, preferring a pair that crosses a KDIGO
chronic-kidney-disease stage boundary where the two answers imply different
staging, and rejected outright if either value leaves physiological range.

By default this builds only the first ten seeds, because the plan gates scaling on
all four of us having read those ten. Pass --all to build the rest afterwards.

Usage:
  python3 construct.py            # the ten worked cases
  python3 construct.py --all      # all 40 seeds, after the Friday read
"""
import argparse
import contextlib
import subprocess
import copy
import datetime
import io
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "audit"))

import spans  # noqa: E402
import calculators  # noqa: E402

SEEDS = os.path.join(ROOT, "data", "seeds_dissociation.json")
OUT = os.path.join(ROOT, "data", "items_dissociation.json")

WORKED_CASES = 10

CREATININE_UNITS = ["mg/dL", "µmol/L", "mmol/L"]

# Physiological bounds on a serum creatinine. A second value outside these is not
# an ambiguity, it is a typo the model should reject for a different reason.
VALUE_RANGE = {
    "mg/dL": (0.3, 15.0),
    "µmol/L": (27.0, 1300.0),
    "mmol/L": (0.027, 1.3),
}

# The answer must move by at least this fraction, or the two values do not
# describe a decision anyone has to make.
MIN_DIVERGENCE = 0.25

# KDIGO chronic-kidney-disease stage boundaries, in the units all three of these
# calculators report. A pair that crosses one of these implies different staging
# and different management, not merely different numbers.
#
# Using the whole ladder rather than 60 alone matters for the sick end of the
# corpus. On a note whose stated creatinine is 12.9 mg/dL there is no plausible
# second value that produces a GFR above 60, so a single 60 cut-off scores every
# advanced-CKD item as decision-irrelevant when in fact moving a patient between
# stage 4 and stage 5 is exactly the decision that changes management.
CKD_STAGE_BOUNDARIES = [15.0, 30.0, 45.0, 60.0, 90.0]


def crossed_boundaries(a, b):
    """Stage boundaries lying between two answers."""
    lo, hi = (a, b) if a <= b else (b, a)
    return [t for t in CKD_STAGE_BOUNDARIES if lo < t <= hi]

CANDIDATE_MULTIPLIERS = [1.8, 0.55, 2.2, 0.45, 1.5, 0.65, 3.0, 0.35, 2.6, 0.5, 1.35, 0.75]

# Words that would let a model resolve the conflict by recency or salience rather
# than by noticing it. None may appear in the value_conflict injection.
CUE_BLOCKLIST = [
    "current", "recent", "latest", "most recent", "baseline", "admission",
    "presentation", "arrival", "follow-up", "follow up", "repeat", "initial",
    "previous", "prior", "earlier", "later", "subsequent", "trend", "rose",
    "fell", "increased", "decreased", "improved", "worsened",
]

# Two forms of the conflict, both built, one primary.
#
# `in_phrase` rewrites the located value-through-unit run and nothing else:
#
#     creatinine, 1.4 mg/dL   ->   creatinine, 1.4 mg/dL and 2.5 mg/dL
#
# This is the minimal-edit rule taken literally -- only the words carrying the
# target value change, the label and everything around it are untouched. It also
# closes the temporal reading better than prose does: one laboratory entry listing
# two values for one analyte offers no "use the later one" escape, because there is
# no earlier and later. And it drops the register mismatch of a narrative clause
# inserted into a lab table.
#
# `prose` is the earlier form, kept because  has to test whether flagging
# tracks our phrasing rather than the conflict. Same two values, different
# sentence; if the flag rates diverge, the effect is partly ours.
CONFLICT_FORMS = {
    "in_phrase": "{v1} and {v2} {unit}",
    "prose": "{v1}, with the same specimen also reported as creatinine {v2} {unit}",
}
PRIMARY_FORM = "in_phrase"


TESTS = os.path.join(ROOT, "tests", "test_regression.py")


def run_regression_suite():
    """Every known extraction failure must still be caught before a build is made.

    The plan says these must pass *before any build is accepted*, and a check that
    only runs in CI accepts the build first and complains afterwards. Running it
    here means a bad build is never produced, which is the difference the wording
    is asking for.

    Run in a subprocess so a test that mutates module state cannot leak into the
    build it is gating.
    """
    if not os.path.exists(TESTS):
        return {"passed": False, "n_tests": 0, "detail": "suite not found"}
    proc = subprocess.run([sys.executable, TESTS], capture_output=True, text=True)
    tail = proc.stderr.strip().splitlines()
    ran = next((l for l in reversed(tail) if l.startswith("Ran ")), "")
    n = int(ran.split()[1]) if ran.startswith("Ran ") else 0
    return {"passed": proc.returncode == 0, "n_tests": n,
            "detail": tail[-1] if tail else "", "output": proc.stderr[-2000:]}


class BuildError(Exception):
    """A variant could not be constructed to specification."""


def load_seeds():
    with open(SEEDS) as f:
        return json.load(f)


def answer_for(calc_id, entities, creatinine_value):
    """The released code's answer with creatinine set to `creatinine_value`."""
    ent = copy.deepcopy(entities)
    ent["creatinine"] = [creatinine_value, ent["creatinine"][1]]
    with contextlib.redirect_stdout(io.StringIO()):
        return float(calculators.call(calc_id, ent)["Answer"])


def fmt(value):
    """Render a creatinine the way a note would: no trailing zeros."""
    return f"{value:g}"


def pick_second_value(calc_id, entities, v1, unit, answer1):
    """Choose the conflicting creatinine, and say why it was chosen."""
    lo, hi = VALUE_RANGE[unit]
    best = None
    for mult in CANDIDATE_MULTIPLIERS:
        v2 = round(v1 * mult, 2 if unit == "mg/dL" else 0)
        if not (lo <= v2 <= hi) or abs(v2 - v1) < 1e-9:
            continue
        answer2 = answer_for(calc_id, entities, v2)
        divergence = abs(answer2 - answer1) / answer1
        if divergence <= MIN_DIVERGENCE:
            continue
        crossed = crossed_boundaries(answer1, answer2)
        straddles = bool(crossed)
        # Prefer crossing a stage boundary; among those, prefer a divergence near
        # 0.6 -- large enough to matter, not so large it reads as a typo.
        score = (straddles, -abs(divergence - 0.6))
        if best is None or score > best[0]:
            best = (score, {
                "value": v2,
                "answer": answer2,
                "divergence": divergence,
                "straddles_threshold": straddles,
                "boundaries_crossed": crossed,
                "multiplier": mult,
            })
    if best is None:
        raise BuildError(
            f"no second creatinine in {lo}-{hi} {unit} moves the answer by more "
            f"than {MIN_DIVERGENCE:.0%}")
    return best[1]


# --- the three edits -------------------------------------------------------

# A measurement is often followed by its reference range. Three ways notes write
# one, all of which must come out with the value: a labelled parenthetical, a bare
# numeric parenthetical, and a bracketed range. Leaving one behind orphans it
# against the previous analyte -- "urea 44 mg/dL [17-43] [0.51-0.95]".
TRAILING_PARENTHETICAL = re.compile(
    r"\s*(?:"
    r"\((?:normal|reference|ref)[^)]{0,60}\)"          # (normal 0.6-1.3 mg/dL)
    r"|\([^)]{0,30}?[\d.]+\s*[-–—]\s*[\d.]+[^)]{0,20}\)"  # (0.50-1.05 mg/dL)
    r"|\[[^\]\n]{0,40}\]"                              # [0.51-0.95]
    r")", re.I)

# A conjunction joining this measurement to the next, with no punctuation between.
# "hematocrit: 30% and creatinine 4.7 mg/dL." leaves a dangling "and." otherwise.
LEADING_CONJUNCTION = re.compile(r"[ \t]+(?:and|or)[ \t]+(?:an?|the)?[ \t]*$", re.I)
TRAILING_CONJUNCTION = re.compile(r"[ \t]+(?:and|or)[ \t]+")
TRAILING_SEPARATOR = re.compile(r"[ \t]*[;,][ \t]*(?:and[ \t]+)?")
LEADING_SEPARATOR = re.compile(r"[ \t]*[;,][ \t]*(?:and[ \t]+)?$")


TIDY_MARGIN = 40

# What a botched excision looks like: a separator with nothing before it, two
# separators in a row, an empty bracket pair, or a clause ending on the
# preposition that introduced the value we removed.
DEFECT = re.compile(
    r"[ \t][.,;:]"                                    # stranded separator
    r"|[;,][ \t]*[;,]"                                # doubled separator
    r"|\([ \t]*\)|\[[ \t]*\]|\)\)"                  # empty or doubled bracket
    r"|\][ \t]*\["                                    # orphaned reference range
    r"|\b(?:with|of|to|at|was|were|is|are|and|or|a|an|the)[ \t]*[.;,]"  # dangling
    r"|\b(?:revealed|showed|shows|reveal|demonstrated|noted)[ \t]+"
    r"(?:from|and|of|in|with)\b"                      # verb stripped of its object
    r"|[a-z]{2}(?:she|he|and|the|was|were|with)\b")   # words fused by the excision


def delete_measurement(note, span_record):
    """Remove the measurement phrase, taking exactly one separator with it.

    Which separator matters. Deleting `serum creatinine level was 1.1 mg/dL, `
    from `revealed that his serum creatinine level was 1.1 mg/dL, urea nitrogen
    level was 19 mg/dL` leaves `his` attached to the next measurement and the
    sentence intact. Taking the leading separator instead would strand it. So the
    trailing separator goes first, and the leading one is only consumed when the
    phrase ends its clause and there is no trailing separator to take.

    Returns the edited note and the window that was touched. Repair of the seam is
    confined to that window: these are real case reports and they contain their own
    typography (one of our notes says `polycystic liver .`), which a whole-note
    clean-up would silently rewrite. Then the difference between clean and missing
    would no longer be only the deleted value, and the condition would not be the
    controlled comparison we are claiming it is.
    """
    start = span_record["span"][0]
    end = span_record["span"][1]

    while True:
        m = TRAILING_PARENTHETICAL.match(note, end)
        if not m:
            break
        end = m.end()

    # The measurement may sit inside a parenthesis it does not own -- "serum
    # creatinine (0.57 mg/dL)" inside a list. The span stops at the unit, so the
    # closing bracket would be orphaned. Balance whatever the deletion opens.
    for opener, closer in (("(", ")"), ("[", "]")):
        excess = note[start:end].count(opener) - note[start:end].count(closer)
        while excess > 0 and closer in note[end:end + 4]:
            end = note.index(closer, end) + 1
            excess -= 1

    # A measurement can be the entire content of a parenthetical -- "renal function
    # was severely disturbed (creatinine = 5.4 mg/dL), and ...". Removing only the
    # inside leaves an empty pair and a stranded space before the comma, so the
    # brackets and the space that introduced them go too.
    absorbed_leading_space = False
    if note[start - 1:start] == "(" and note[end:end + 1] == ")":
        start -= 1
        end += 1
        while start > 0 and note[start - 1] in " \t":
            start -= 1
            absorbed_leading_space = True

    # Exactly one separator comes out with the measurement, never two. Absorbing a
    # leading space along with an enclosing bracket already counts as that one:
    # taking a trailing separator as well fuses the neighbouring words together
    # ("severely disturbed" + "she had also" -> "disturbedshe").
    #
    # Which separator matters. Deleting `serum creatinine level was 1.1 mg/dL, `
    # from `revealed that his serum creatinine level was 1.1 mg/dL, urea nitrogen
    # level was 19 mg/dL` leaves `his` attached to the next measurement and the
    # sentence intact. Taking the leading one instead would strand it. So trailing
    # goes first, and leading is used only when the phrase ends its clause.
    if not absorbed_leading_space:
        for pattern, leading in ((TRAILING_SEPARATOR, False),
                                 (TRAILING_CONJUNCTION, False),
                                 (LEADING_SEPARATOR, True),
                                 (LEADING_CONJUNCTION, True)):
            if leading:
                m = pattern.search(note[:start])
                if m:
                    start = m.start()
                    break
            else:
                m = pattern.match(note, end)
                if m and note[m.end():m.end() + 1] not in ("", "\n"):
                    end = m.end()
                    break

    joined = note[:start] + note[end:]
    lo = max(0, start - TIDY_MARGIN)
    hi = min(len(joined), start + TIDY_MARGIN)
    repaired = tidy(joined[lo:hi])
    out = joined[:lo] + repaired + joined[hi:]
    return out, (lo, lo + len(repaired))


def tidy(text):
    """Repair the punctuation and spacing an excision leaves behind at the seam."""
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"[ \t]+([.,;:])", r"\1", text)
    text = re.sub(r"([;,])[ \t]*\1", r"\1", text)
    text = re.sub(r"[;,][ \t]*\.", ".", text)
    text = re.sub(r":[ \t]*;", ":", text)
    text = re.sub(r"\([ \t]*\)", "", text)
    return text


def inject_conflict(note, span_record, v2, unit_text, form=PRIMARY_FORM):
    """Rewrite the located measurement so it carries both values.

    The span replaced runs from the first digit of the stated value to the end of
    its unit -- exactly the words carrying the target value, and nothing else. The
    label, the punctuation before it and the text after are byte-identical to the
    published note.

    A reference range following the measurement is stepped over rather than
    written through. Landing inside it would attach `(normal: 0.65-1.09 mg/dL)` to
    the injected value and quietly tell the reader the second number is out of
    range, which is a hint that something is wrong.
    """
    v_start = span_record["value_span"][0]
    end = span_record["unit_span"][1]
    m = TRAILING_PARENTHETICAL.match(note, end)
    trailing = note[end:m.end()] if m else ""
    if m:
        end = m.end()

    v1_text = note[v_start:span_record["unit_span"][1]] if form == "prose" \
        else span_record["value_text"]
    replacement = CONFLICT_FORMS[form].format(
        v1=v1_text, v2=fmt(v2), unit=unit_text)
    if form == "prose":
        replacement = replacement.replace(v1_text, v1_text + trailing, 1)
        trailing = ""

    return note[:v_start] + replacement + trailing + note[end:], replacement


def selector_sentence(stated_as_written):
    """The cue that makes the conflict resolvable, appended to the question.

    Quotes the value exactly as the note writes it -- one note says "8mg/dL" with
    no space -- so the cue names a string the model can find rather than a
    normalised version of it.
    """
    return (f" Two serum creatinine values are recorded; use the "
            f"{stated_as_written} value for this calculation.")


# --- guardrails ------------------------------------------------------------

def check_missing(note, new_note, seed, window):
    n = len(spans.count_measurements(new_note, "creatinine", CREATININE_UNITS))
    if n != 0:
        raise BuildError(f"missing variant still states {n} creatinine measurement(s)")
    if len(new_note) >= len(note):
        raise BuildError("missing variant is not shorter than the original")
    lo, hi = window
    seam = new_note[lo:hi]
    # Judged against the original, not in isolation: these are real case reports
    # and some ship with a space before a full stop. What must not happen is the
    # excision *adding* a defect -- a dangling separator, or a sentence left
    # hanging on the preposition that introduced the value we removed.
    #
    # Compared as a multiset of the actual defect strings rather than as a count.
    # A count is fooled by a trade: deleting "serum creatinine decreasing to 1.6
    # mg/dL" from "improvement in renal function with serum creatinine decreasing
    # to 1.6 mg/dL ()." removes the stray "()" and leaves "renal function with.",
    # which is one defect before and one after and badly broken in between.
    original = Counter(DEFECT.findall(note[lo:hi + (len(note) - len(new_note))]))
    introduced = Counter(DEFECT.findall(seam)) - original
    if introduced:
        raise BuildError(
            f"excision introduced {list(introduced)} at the seam: {seam!r}")
    # Outside the seam the note must be untouched, byte for byte. This is the
    # minimal-edit rule stated as a test rather than as an intention.
    if new_note[:lo] != note[:lo]:
        raise BuildError("excision changed text before the edit window")
    if not note.endswith(new_note[hi:]):
        raise BuildError("excision changed text after the edit window")
    check_other_inputs_survive(new_note, seed)


def check_conflict(new_note, seed, stated_as_written, v2, unit_text, replacement):
    """Both values present, the label intact, no cue added, no range misattributed.

    Deliberately not asserting "two anchored creatinine measurements" any more.
    Under the in-phrase form the second value sits behind the first, so the gap
    between the label and it contains digits and the locator cannot anchor it --
    correctly, since it is one measurement phrase reporting two values, not two
    phrases. The assertion is on the rewritten phrase instead.
    """
    if replacement not in new_note:
        raise BuildError("value_conflict variant does not contain the rewritten phrase")
    for token in (fmt(seed["input_spans"]["creatinine"]["value"]), fmt(v2)):
        if token not in replacement:
            raise BuildError(f"rewritten phrase is missing the value {token!r}")
    if unit_text not in replacement:
        raise BuildError("rewritten phrase lost its unit")
    # The label must survive untouched, immediately before the rewritten run.
    anchor = seed["input_spans"]["creatinine"]["anchor_text"]
    if anchor not in new_note:
        raise BuildError(f"value_conflict variant lost the label {anchor!r}")
    # Only the words we wrote are ours to police. The published note may well say
    # "on admission" somewhere; that is the note's own text, not a cue we added.
    for cue in CUE_BLOCKLIST:
        if cue in replacement.lower():
            raise BuildError(f"value_conflict injection carries the cue {cue!r}")
    # A reference range after the phrase is fine when it covers both values --
    # "creatinine of 1.7 and 3.74 mg/dL (normal range 0.6-1.2 mg/dL)" says the same
    # thing about each. What is not fine is a range that covers the injected value
    # alone, which silently marks it as the abnormal one and tells the reader which
    # to discard.
    after = new_note[new_note.find(replacement) + len(replacement):]
    if TRAILING_PARENTHETICAL.match(after):
        stated = fmt(seed["input_spans"]["creatinine"]["value"])
        if not (stated in replacement and fmt(v2) in replacement):
            raise BuildError("a reference range follows the injected value alone, "
                             "which would mark it as the abnormal one")
    check_other_inputs_survive(new_note, seed)


def check_other_inputs_survive(new_note, seed):
    """Every non-creatinine formula input must still be locatable, and unchanged.

    An edit that silently broke the weight is an edit whose effect we cannot
    attribute, so this re-locates from scratch in the edited note rather than
    trusting arithmetic on the original offsets.
    """
    for name, record in seed["input_spans"].items():
        if name == "creatinine":
            continue
        # An input the note never stated has no span to disturb. It is recorded
        # with stated_in_note False so that it is accounted for, not so that it
        # can be re-located here.
        if record.get("stated_in_note") is False:
            continue
        try:
            if name in ("sex", "race"):
                patterns = spans.SEX_PATTERNS if name == "sex" else spans.RACE_PATTERNS
                spans.find_word(new_note, patterns, record["value"], name)
            elif name == "age":
                spans.find_age(new_note, record["value"])
            else:
                spans.find_measurement(new_note, record["value"], record["unit"], name)
        except (spans.NotFound, spans.Ambiguous) as exc:
            raise BuildError(f"edit disturbed {name}: {exc}") from exc


# --- assembly --------------------------------------------------------------

def build_seed(seed, note):
    cid = seed["calculator_id"]
    entities = seed["entities"]
    cre = seed["input_spans"]["creatinine"]
    v1, unit = cre["value"], cre["unit"]
    v1_text, unit_text = cre["value_text"], cre["unit_text"]

    answer1 = answer_for(cid, entities, v1)
    if abs(answer1 - seed["clean_answer"]) > 1e-6:
        raise BuildError("clean answer does not reproduce from the seed record")

    second = pick_second_value(cid, entities, v1, unit, answer1)

    missing_note, seam = delete_measurement(note, cre)
    check_missing(note, missing_note, seed, seam)

    stated_as_written = note[cre["value_span"][0]:cre["unit_span"][1]]
    conflict_note, injection = inject_conflict(note, cre, second["value"], unit_text)
    check_conflict(conflict_note, seed, stated_as_written, second["value"],
                   unit_text, injection)

    # The alternative phrasing, built and checked but not shipped as a condition.
    #  compares flag rates across the two to test whether the model responds
    # to the conflict or to how we wrote it.
    variant_note, variant_injection = inject_conflict(
        note, cre, second["value"], unit_text, form="prose")
    check_conflict(variant_note, seed, stated_as_written, second["value"],
                   unit_text, variant_injection)

    question = seed["question"]
    unit_label = seed["clean_answer_unit"]

    conditions = [
        {
            "condition": "clean",
            "note": note,
            "question": question,
            "correct_action": "compute",
            "correct_answer": round(answer1, 3),
            "answer_unit": unit_label,
            "rationale": "the note as published; the control that shows the model "
                         "can do this calculation on this note at all",
        },
        {
            "condition": "missing",
            "note": missing_note,
            "question": question,
            "correct_action": "decline",
            "correct_answer": None,
            "answer_unit": unit_label,
            "rationale": "the creatinine the formula consumes is not in the note, so "
                         "no answer is derivable and declining is the only correct move",
        },
        {
            "condition": "value_conflict",
            "note": conflict_note,
            "question": question,
            "correct_action": "flag",
            "correct_answer": None,
            "answer_unit": unit_label,
            "rationale": f"two creatinines from the same draw give "
                         f"{answer1:.1f} and {second['answer']:.1f} {unit_label}; "
                         "nothing in the note says which is the input, so committing "
                         "to either is committing to an untrustworthy value",
        },
        {
            "condition": "resolvable",
            "note": conflict_note,
            "question": question + selector_sentence(stated_as_written),
            "correct_action": "compute",
            "correct_answer": round(answer1, 3),
            "answer_unit": unit_label,
            "rationale": "byte-identical note to value_conflict, plus a cue naming "
                         "the input; a correct answer here proves both values were "
                         "parsed, so silence under value_conflict is not a parsing "
                         "failure",
        },
    ]

    return {
        "seed_id": seed["seed_id"],
        "case_id": seed["case_id"],
        "calculator": seed["calculator"],
        "calculator_short": seed["calculator_short"],
        "calculator_id": cid,
        "creatinine": {
            "stated": v1, "unit": unit, "as_written": stated_as_written,
            "value_span_in_clean_note": cre["value_span"],
            "phrase": cre["text"],
        },
        "conflict": {
            "second_value": second["value"],
            "answer_with_stated": round(answer1, 3),
            "answer_with_second": round(second["answer"], 3),
            "divergence": round(second["divergence"], 3),
            "straddles_threshold": second["straddles_threshold"],
            "boundaries_crossed": second["boundaries_crossed"],
            "injection": injection,
            "form": PRIMARY_FORM,
            "phrasing_variant": {
                "form": "prose",
                "injection": variant_injection,
                "note": variant_note,
                "purpose": " phrasing check: same two values, different "
                           "sentence. A flag-rate difference between this and the "
                           "primary form is a difference our wording made.",
            },
        },
        "conditions": conditions,
    }


def worked_ten(seeds):
    """The ten cases for the four-way read, spread across all three calculators.

    Taking the first ten in frozen order gives ten Cockcroft-Gault items, because
    the freeze is ordered by calculator. The read would then approve a construction
    that had never been looked at on CKD-EPI or MDRD, and those differ in which
    inputs the formula consumes -- MDRD reads race, CKD-EPI does not read weight.
    Round-robin instead, so every calculator gets read before anything scales.
    """
    by_calc = {}
    for seed in seeds:
        by_calc.setdefault(seed["calculator_short"], []).append(seed)
    picked, depth = [], 0
    while len(picked) < WORKED_CASES:
        added = False
        for name in sorted(by_calc):
            if depth < len(by_calc[name]):
                picked.append(by_calc[name][depth])
                added = True
                if len(picked) == WORKED_CASES:
                    return picked
        if not added:
            break
        depth += 1
    return picked


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--all", action="store_true",
                    help="build every seed, not just the ten worked cases")
    ap.add_argument("--no-verify", action="store_true",
                    help="build even if the regression suite fails; the override is "
                         "recorded in the output so the artifact says so")
    args = ap.parse_args()

    suite = run_regression_suite()
    suite["overridden"] = bool(args.no_verify and not suite["passed"])
    if suite["passed"]:
        print(f"regression suite: {suite['n_tests']} tests pass")
    elif args.no_verify:
        print(f"regression suite FAILED ({suite['detail']}) -- building anyway "
              "because --no-verify was given. The item file records this.")
    else:
        print(f"regression suite FAILED: {suite['detail']}")
        print(suite.get("output", ""))
        sys.exit("Refusing to build. Known extraction failures must pass first; "
                 "pass --no-verify to override, which is recorded in the output.")

    frozen = load_seeds()
    seeds = frozen["seeds"] if args.all else worked_ten(frozen["seeds"])

    # Seeds come from both splits, and row numbers are only unique within one.
    import csv
    csv.field_size_limit(10 ** 9)
    notes = {}
    for split in ("test", "train"):
        path = os.path.join(ROOT, "data", "medcalc", f"{split}_data.csv")
        if not os.path.exists(path):
            sys.exit(f"{path} missing. Run: python3 fetch_medcalc.py")
        for r in csv.DictReader(open(path, newline="", encoding="utf-8")):
            notes[(split, int(r["Row Number"]))] = r["Patient Note"]

    built, failed = [], []
    for seed in seeds:
        try:
            note = notes[(seed.get("split", "test"), seed["row_number"])]
            built.append(build_seed(seed, note))
        except BuildError as exc:
            failed.append({"seed_id": seed["seed_id"], "error": str(exc)})

    out = {
        "built_utc": datetime.datetime.now(datetime.timezone.utc)
                              .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scope": "all seeds" if args.all else f"first {WORKED_CASES} seeds (worked cases)",
        "substrate": frozen["substrate"],
        "seeds_frozen_utc": frozen["frozen_utc"],
        "regression_suite": {k: suite[k] for k in
                             ("passed", "n_tests", "detail", "overridden")},
        "n_seeds_attempted": len(seeds),
        "n_seeds_built": len(built),
        "n_items": len(built) * 4,
        "conditions": ["clean", "missing", "value_conflict", "resolvable"],
        "construction_rules": {
            "minimal_edit": "only the located label-value-unit phrase is rewritten",
            "second_value": f"answer must move by more than {MIN_DIVERGENCE:.0%}; "
                            "a pair crossing a KDIGO CKD stage boundary is preferred",
            "no_cue": "the value_conflict injection may not contain any of "
                      + ", ".join(CUE_BLOCKLIST),
            "resolvable_note": "byte-identical to value_conflict; the cue is appended "
                               "to the question so the note is held fixed",
        },
        "failures": failed,
        "items": built,
    }
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)

    print(f"seeds {len(built)}/{len(seeds)} built -> {len(built) * 4} items")
    straddle = sum(1 for b in built if b["conflict"]["straddles_threshold"])
    print(f"conflicts crossing a CKD stage boundary: {straddle}/{len(built)}")
    for f_ in failed:
        print(f"  FAILED {f_['seed_id']}: {f_['error']}")
    if not args.all:
        print(f"\nBuilt the first {WORKED_CASES} seeds only. Scaling to all 40 is "
              "gated on the four-way read of these ten (--all afterwards).")
    print(f"wrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
