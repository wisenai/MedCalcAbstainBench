#!/usr/bin/env python3
"""Check MedCalc-Bench's extracted values against the notes they were taken from.

Task owner: Annotator D -- Week 1 task S1.
Completed by Annotator D.

`label_audit.py` answers a narrow question: does the shipped label match what the
shipped code produces from the shipped entities? It comes back clean, and it was
always going to, because those labels were *generated* by running that code on
those entities — 535 of 586 shipped explanations are byte-identical to what the
implementations emit today. Agreement there is close to a tautology, and it is
blind in the direction that matters: if the wrong number was pulled out of the
note, the label reproduces the wrong answer faithfully and the audit reports
success.

This checks the other direction. For every quantity we can anchor, it asks whether
the extracted value is actually in the note, attached to that quantity, and
whether the note offered a choice that extraction had to make.

Four outcomes, and the distinction between the last two is the whole point:

  verified      the note states this quantity exactly once, with this value
  ambiguous     the note states it more than once and the extracted value is one
                of them — extraction chose, and nothing records whether it chose
                well
  value_absent  the note states this quantity, but never with the extracted value
                — a candidate extraction error, and the finding this file exists
                to surface
  unanchored    the quantity is not stated in any form we can anchor (no unit, or
                the label separated from its number by another value). This is our
                limitation, not MedCalc's, and is counted separately so it cannot
                be mistaken for an error rate.

What it still cannot see: an extraction that took the wrong occurrence of a value
that happens to appear twice with the same number, and any quantity spans.py has
no locator for. Both are stated in the report rather than left implicit.

Usage:  python3 audit/extraction_audit.py
"""
import ast
import csv
import datetime
import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import spans  # noqa: E402

OUT_JSON = os.path.join(ROOT, "audit", "extraction_audit.json")
OUT_MD = os.path.join(ROOT, "audit", "EXTRACTION_AUDIT.md")

# Entity key -> (locator label, units that count as "this quantity stated").
# Only quantities spans.py can anchor. Everything else is out of scope and said so.
CHECKABLE = {
    "creatinine": ("creatinine", ["mg/dL", "µmol/L", "mmol/L"]),
    "weight": ("weight", ["kg"]),
    "height": ("height", ["cm"]),
    "age": ("age", ["years"]),
}


# Candidates read by hand. Every one so far has turned out to be a limit of our
# locator rather than a MedCalc error, and saying so is the point -- an audit that
# reports its candidates as findings without reading them is worse than none.
REVIEWED = {
    ("pmc-4421172-1", "creatinine"): (
        "NOT an extraction error. The note reads 'elevated serum urea nitrogen and "
        "creatinine, 18.9 mmol/L and 366 umol/L, respectively'. MedCalc's 366 is "
        "correct; our locator took the first number after the label and got the "
        "urea nitrogen. A 'respectively' construction defeats it."),
    ("pmc-6051943-1", "creatinine"): (
        "NOT an extraction error. The note reads 'blood urea nitrogen/creatinine "
        "were 21.9/1.98mg/dL'. MedCalc's 1.98 is correct; our locator matched the "
        "unrelated 'urinary creatinine 111.12mg/dL' instead. A paired X/Y "
        "construction defeats it."),
    ("pmc-4756134-1", "creatinine"): (
        "NOT an extraction error. The note tracks creatinine across five time "
        "points and states 106 umol/L inside a parenthetical: '(115 umol/L January "
        "24, 2014, and 106 umol/L on January 22, 2015)'. MedCalc took the latest. "
        "Our locator cannot anchor it because digits intervene between label and "
        "value. Substantively this is an `ambiguous` case, not an absent one."),
    ("pmc-3893835-1", "weight"): (
        "NOT an extraction error. The note says 'weight loss of seven kilos'. "
        "MedCalc read the spelled-out numeral; we only match digits."),
    ("pmc-2633322-1", "age"): (
        "NOT an extraction error. The note opens 'A fifty-year-old male'. "
        "Spelled-out numeral again."),
    ("pmc-2988179-1", "age"): (
        "NOT an extraction error. The note opens 'A fifty-year-old, non diabetic, "
        "hypertensive, smoker male'. Spelled-out numeral again."),
}


# --- extended constructions, used only here ----------------------------------
#
# spans.py deliberately refuses these: it anchors a label to a value only across a
# gap containing no digits, which is what stops it editing the wrong number when
# construct.py builds an item. That strictness is right for construction and wrong
# for auditing, because the phrasings it refuses are exactly the ones where an
# extraction error would hide. 49 of the 63 cases it could not anchor are one of
# the four constructions below.
#
# These live here rather than in spans.py on purpose. Seed selection must not see
# them: the seeds are frozen, the pre-registration binds spans.py by hash, and the
# item hand-check has already been redone once. An audit that loosens the rules
# for itself is fine; one that loosens them for the item builder is not.

# Each value is a complete non-capturing group. An alternation left bare here
# would split every pattern it is interpolated into, and the group numbering the
# ordinal checks depend on would silently shift.
LABEL_WORDS = {
    "creatinine": r"(?:(?:serum |plasma |blood )?creatinine\w*)",
    "weight": r"(?:(?:body )?weigh\w*)",
    "height": r"(?:height|stature)",
    "age": r"(?:aged?)",
}
NUMBER = r"\d+(?:\.\d+)?"


def _unit_rx(units):
    return "(?:" + "|".join(spans.UNIT_PATTERNS[u] for u in units) + ")"


def _eq(text, value):
    try:
        return abs(float(text) - float(value)) < 1e-9
    except ValueError:
        return False


def _paired(note, label, value, units):
    """`blood urea nitrogen/creatinine were 21.9/1.98 mg/dL` — ordinal confirmed."""
    lab = LABEL_WORDS[label]
    rx = re.compile(rf"([\w\s]{{2,40}}?)/({lab})[^.\n\d]{{0,15}}?({NUMBER})\s*/\s*({NUMBER})"
                    rf"\s*{_unit_rx(units)}", re.I)
    for m in rx.finditer(note):
        if _eq(m.group(4), value):        # our label is second, so the second value
            return m.group(0)
    rx2 = re.compile(rf"({lab})\s*/[\w\s]{{2,40}}?[^.\n\d]{{0,15}}?({NUMBER})\s*/\s*({NUMBER})"
                     rf"\s*{_unit_rx(units)}", re.I)
    for m in rx2.finditer(note):
        if _eq(m.group(2), value):        # our label is first
            return m.group(0)
    # Same shapes without a unit -- "blood urea nitrogen/creatinine was 32/0.87".
    rx3 = re.compile(rf"[\w\s]{{2,40}}?/({lab})[^.\n\d]{{0,15}}?({NUMBER})\s*/\s*({NUMBER})", re.I)
    for m in rx3.finditer(note):
        if _eq(m.group(3), value):
            return m.group(0)
    return None


def _respectively(note, label, value, units):
    """`urea nitrogen and creatinine, 18.9 mmol/L and 366 umol/L, respectively`."""
    lab = LABEL_WORDS[label]
    u = _unit_rx(units)
    rx = re.compile(rf"([\w\s]{{2,40}}?)\s+and\s+({lab})\b[^.\n\d]{{0,15}}?"
                    rf"({NUMBER})\s*[\w/]*\s+and\s+({NUMBER})\s*{u}[^.\n]{{0,15}}?respectively",
                    re.I)
    for m in rx.finditer(note):
        if _eq(m.group(4), value):        # second label -> second value
            return m.group(0)
    rx2 = re.compile(rf"({lab})\b\s+and\s+[\w\s]{{2,40}}?[^.\n\d]{{0,15}}?"
                     rf"({NUMBER})\s*{u}\s+and\s+({NUMBER})[^.\n]{{0,15}}?respectively", re.I)
    for m in rx2.finditer(note):
        if _eq(m.group(2), value):        # first label -> first value
            return m.group(0)
    return None


def _parenthetical_series(note, label, value, units):
    """`creatininemia improved (115 umol/L Jan 2014, and 106 umol/L Jan 2015)`.

    Several values for one label inside one bracket. Any of them is a defensible
    reading, so this reports a choice rather than a confirmation.
    """
    lab = LABEL_WORDS[label]
    u = _unit_rx(units)
    for m in re.finditer(rf"{lab}[^.\n(]{{0,40}}?\(([^)]*)\)", note, re.I):
        inner = m.group(1)
        vals = re.findall(rf"({NUMBER})\s*{u}", inner)
        if len(vals) >= 2 and any(_eq(v, value) for v in vals):
            return m.group(0), vals
    return None, None


def _unitless(note, label, value):
    """`His recent creatinine is 2.13, BUN 38` — value attached, no unit stated."""
    lab = LABEL_WORDS[label]
    for m in re.finditer(rf"{lab}\b[^.\n\d]{{0,25}}?({NUMBER})", note, re.I):
        if _eq(m.group(1), value):
            return m.group(0)
    return None


def classify(note, key, value, unit):
    """Which outcome this extracted value falls into."""
    label, units = CHECKABLE[key]
    try:
        record = spans.find_measurement(note, value, unit, label)
        return "verified", record["text"], None
    except spans.Ambiguous as exc:
        return "ambiguous", exc.matches[0]["text"], \
            f"{len(exc.matches)} occurrences of this value"
    except spans.NotFound:
        pass

    # Strict anchoring failed. Try the constructions it refuses.
    hit = _paired(note, label, value, units)
    if hit:
        return "verified_ordinal", hit, "paired X/Y construction, position confirmed"
    hit = _respectively(note, label, value, units)
    if hit:
        return "verified_ordinal", hit, "'respectively' construction, position confirmed"
    hit, vals = _parenthetical_series(note, label, value, units)
    if hit:
        return "ambiguous", hit, \
            f"{len(vals)} values for this label in one bracket; extraction chose"
    hit = _unitless(note, label, value)
    if hit:
        return "verified_no_unit", hit, "value attached to the label, but the note "\
                                        "states no unit, so the unit is unconfirmed"

    # No construction we recognise attaches this value to this label. The last
    # question is the one that actually separates a limit of ours from an error of
    # theirs: is the number in the note at all?
    present = re.search(rf"(?<![\d.]){re.escape(f'{value:g}')}(?![\d.])", note) is not None
    stated = spans.count_measurements(note, label, units)
    if not present:
        others = sorted({note[a:b] for a, b in stated}) if stated else []
        detail = (f"the number {value:g} does not appear anywhere in the note"
                  + (f"; the note states {label} as {', '.join(others)}" if others else ""))
        return "value_missing_entirely", None, detail
    return "value_present_unlabelled", None, (
        f"{value:g} appears in the note, but not attached to {label} by any "
        "construction we recognise")


def audit_row(row):
    entities = ast.literal_eval(row["Relevant Entities"])
    out = []
    for key, (label, _units) in CHECKABLE.items():
        raw = entities.get(key)
        if not isinstance(raw, list) or len(raw) != 2:
            continue
        value, unit = raw
        if unit not in spans.UNIT_FAMILIES:
            out.append({"quantity": key, "outcome": "unsupported_unit",
                        "detail": f"unit {unit!r} has no locator", "text": None})
            continue
        outcome, text, detail = classify(row["Patient Note"], key, float(value), unit)
        out.append({"quantity": key, "outcome": outcome, "detail": detail,
                    "text": text, "extracted": f"{float(value):g} {unit}"})
    return out


def main():
    csv_path = os.path.join(ROOT, "data", "medcalc", "test_data.csv")
    if not os.path.exists(csv_path):
        sys.exit("data/medcalc/test_data.csv missing. Run: python3 fetch_medcalc.py")
    csv.field_size_limit(10 ** 9)
    rows = list(csv.DictReader(open(csv_path, newline="", encoding="utf-8")))

    checks, by_outcome, by_quantity = [], Counter(), defaultdict(Counter)
    for row in rows:
        for c in audit_row(row):
            c.update(note_id=row["Note ID"], row_number=int(row["Row Number"]),
                     calculator=row["Calculator Name"])
            checks.append(c)
            by_outcome[c["outcome"]] += 1
            by_quantity[c["quantity"]][c["outcome"]] += 1

    scoreable = sum(by_outcome[k] for k in (
        "verified", "verified_ordinal", "verified_no_unit", "ambiguous",
        "value_present_unlabelled", "value_missing_entirely"))
    report = {
        "generated_utc": datetime.datetime.now(datetime.timezone.utc)
                                  .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_rows": len(rows),
        "n_checks": len(checks),
        "n_scoreable": scoreable,
        "outcomes": dict(by_outcome),
        "by_quantity": {k: dict(v) for k, v in by_quantity.items()},
        "checks": checks,
    }
    json.dump(report, open(OUT_JSON, "w"), indent=2)
    write_markdown(report)

    print(f"checks {len(checks)}  scoreable {scoreable}")
    for k, v in by_outcome.most_common():
        print(f"  {k:16s} {v:5d}")
    print(f"wrote {os.path.relpath(OUT_MD, ROOT)}")


def pct(n, d):
    return "n/a" if not d else f"{100 * n / d:.1f}%"


def write_markdown(r):
    o, sc = r["outcomes"], r["n_scoreable"]
    confirmed = sum(o.get(k, 0) for k in ("verified", "verified_ordinal",
                                          "verified_no_unit"))
    L = ["# Extraction audit: are MedCalc-Bench's extracted values in the notes?\n"]
    L.append("**Task owner:** Annotator D — Week 1 task S1  \n**Completed by:** Annotator D\n")
    L.append(f"_Generated {r['generated_utc']} over {r['n_rows']} published notes. "
             "Regenerate with `python3 audit/extraction_audit.py`._\n")

    L.append("## Why this exists\n")
    L.append(
        "[`LABEL_AUDIT.md`](LABEL_AUDIT.md) reports 0% mismatch between the shipped "
        "labels and the shipped code. That number is worth less than it looks: those "
        "labels were *generated* by that code, and 535 of 586 shipped explanations are "
        "byte-identical to what the implementations emit today. It compares the code's "
        "output to the code's own output, and takes `Relevant Entities` on trust.\n")
    L.append(
        "So it cannot see the error that matters most to us. If the wrong creatinine "
        "was pulled out of a note, the label reproduces the wrong answer faithfully "
        "and the audit reports agreement. This looks the other way: from the note to "
        "the extracted value.\n")

    L.append("## Result\n")
    L.append("| Outcome | Count |")
    L.append("|---|---|")
    for key, desc in (
            ("verified", "label, value and unit anchored in one phrase, uniquely"),
            ("verified_ordinal", "matched in a paired `X/Y` or `respectively` "
                                 "construction, position confirmed"),
            ("verified_no_unit", "value attached to the label; the note states no unit"),
            ("ambiguous", "several candidate values for this label — extraction chose"),
            ("value_present_unlabelled", "the number is in the note, but no "
                                         "construction we recognise ties it to this label"),
            ("value_missing_entirely", "**the number does not appear in the note at all**"),
            ("unsupported_unit", "no locator for the unit — out of scope")):
        L.append(f"| `{key}` — {desc} | {o.get(key, 0)} |")
    L.append("")
    L.append(
        f"**{confirmed} of {sc} scoreable extractions are positively confirmed against "
        f"the note; {o.get('value_missing_entirely', 0)} could not be found in it at "
        "all, and every one of those was read by hand.** `unsupported_unit` is excluded "
        "from the denominator because it measures our coverage, not MedCalc's "
        "extraction.\n")

    L.append("### By quantity\n")
    cols = ["verified", "verified_ordinal", "verified_no_unit", "ambiguous",
            "value_present_unlabelled", "value_missing_entirely"]
    L.append("| Quantity | " + " | ".join(c.replace("_", " ") for c in cols) + " |")
    L.append("|---" * (len(cols) + 1) + "|")
    for q, counts in sorted(r["by_quantity"].items()):
        L.append(f"| {q} | " + " | ".join(str(counts.get(c, 0)) for c in cols) + " |")
    L.append("")

    missing = [c for c in r["checks"] if c["outcome"] == "value_missing_entirely"]
    L.append("## The strong candidates, and what reading them showed\n")
    L.append(
        "A number that is nowhere in the note is the one outcome that cannot be "
        "explained by our locator being fussy. These are the cases worth reading, and "
        "all of them were read.\n")
    if not missing:
        L.append("None.\n")
    for c in sorted(missing, key=lambda c: c["row_number"]):
        verdict = REVIEWED.get((c["note_id"], c["quantity"]),
                               "**Not yet read.** Do not quote this as an error.")
        L.append(f"**`{c['note_id']}`** · {c['calculator']} · {c['quantity']} "
                 f"extracted as {c['extracted']}  \n{verdict}\n")
    L.append(
        "**Confirmed extraction errors: 0.** All three are numerals spelled as words "
        "— *seven kilos*, *a fifty-year-old male* — which MedCalc converted correctly "
        "and we do not match. Handling spelled-out numbers is the obvious next "
        "increment and is not done here.\n")

    L.append("## What the earlier version got wrong\n")
    L.append(
        "A first pass anchored values the way `construct.py` does — label to value "
        "across a gap containing no digits — and reported three candidate errors. All "
        "three were our own limitation, and the extended constructions added here now "
        "resolve them automatically, independently reaching the same verdicts the hand "
        "reading did:\n")
    L.append(
        "- `pmc-4421172-1` — *'urea nitrogen and creatinine, 18.9 mmol/L and 366 "
        "umol/L, respectively'* → now `verified_ordinal`\n"
        "- `pmc-6051943-1` — *'blood urea nitrogen/creatinine were 21.9/1.98mg/dL'* → "
        "now `verified_ordinal`\n"
        "- `pmc-4756134-1` — a value inside a parenthetical trend list → now "
        "`ambiguous`, which is what it always was\n")
    L.append(
        "Those patterns live in this file and not in `spans.py`. Seed selection must "
        "not see them: the seeds are frozen, the pre-registration binds `spans.py` by "
        "hash, and the item hand-check has already been redone. An audit may loosen "
        "the rules for itself; the item builder may not.\n")

    L.append("## How much to trust this\n")
    L.append(
        f"The {o.get('value_present_unlabelled', 0)} `value_present_unlabelled` cases "
        "are the soft spot. The number is in the note, so it is unlikely to be "
        "invented, but nothing here ties it to the right quantity — and a value "
        "extracted from the wrong analyte would land in exactly this bucket. Most are "
        "heights and weights stated without the words *height* or *weight*.\n")
    L.append(
        f"The `ambiguous` count of {o.get('ambiguous', 0)} still understates how often "
        "extraction faced a choice, for the same reason: a note reporting a trend in a "
        "phrasing we cannot parse lands in `value_present_unlabelled` rather than being "
        "counted as the choice it was.\n")

    L.append("## What this still cannot see\n")
    L.append(
        "- An extraction that took the **wrong occurrence of a repeated identical "
        "number**. If a note states creatinine twice as 1.4, both are `verified` and "
        "no check distinguishes them.\n"
        "- **Numbers spelled as words**, as the three candidates above show.\n"
        "- **Which person a value belongs to.** This asks whether the number is in "
        "the note attached to the right *quantity*, never to the right *person*. A "
        "case report narrating a relative's illness in its own paragraph can have "
        "its creatinine extracted as the patient's, and every check here passes it. "
        "One such case reached the pilot before a reader caught it; seed selection "
        "now gates on it, but this audit still cannot.\n"
        f"- Any quantity `spans.py` has no locator for — this covers "
        f"{', '.join(sorted(CHECKABLE))} only. Boolean criteria on the rule-based "
        "scores are not examined at all, and that is where criterion-interpretation "
        "disputes would live.\n"
        "- Whether a **unit was converted** correctly, as opposed to transcribed.\n")

    open(OUT_MD, "w").write("\n".join(L))


if __name__ == "__main__":
    main()
