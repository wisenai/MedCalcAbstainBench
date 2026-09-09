#!/usr/bin/env python3
"""A deterministic consistency checker for clinical notes. No model involved.


It does two things. It recomputes every derived value the note states from the
components the note also states, and it asserts that a stated systolic pressure
exceeds its diastolic. Nothing else.

The size is the argument. If a hundred lines of arithmetic catch a contradiction,
then a language model silently computing through that same contradiction is not
failing at something hard. Keeping this deliberately small is what makes that
claim honest -- a checker allowed to grow would eventually catch things by
pattern-matching rather than by arithmetic, and the comparison would stop meaning
anything.

The limit is as important as the catch, and it is structural rather than a matter
of effort. This finds a contradiction only where a number can be derived from
other numbers. A note asserting a patient has no history of stroke and later
scoring them for a prior stroke is flatly self-contradictory and there is no
arithmetic that reaches it. That boundary is our own statement of where a
non-model approach stops, made before a reviewer makes it for us.

Usage:
  python3 checker.py                            # run over the built items
  python3 checker.py --items path/to/items.json
  python3 checker.py --text "...note text..."
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

NUM = r"(\d+(?:\.\d+)?)"


def _f(m, i=1):
    return float(m.group(i))


# --- reading quantities out of a note --------------------------------------
# One pattern per quantity, each requiring the label and the unit, so a number is
# only read as a weight if the note says it is a weight in kilograms.

PATTERNS = {
    # kg/m2 is a BMI, not a weight: "85 kg in weight (body mass index: 27.7 kg/m2)".
    "weight_kg": rf"(?:body )?weigh(?:t|ed|s|ing)\b[^.\n\d]{{0,25}}?{NUM}\s{{0,3}}kg\b(?!\s*/)",
    "height_cm": rf"(?:height|stature)\b[^.\n\d]{{0,25}}?{NUM}\s{{0,3}}cm\b",
    "height_cm_tall": rf"{NUM}\s{{0,3}}cm[^.\n]{{0,20}}?\btall\b",
    "bmi": rf"(?:bmi|body mass index)\b[^.\n\d]{{0,25}}?{NUM}",
    # "Two units of MAP" is mannitol-adenine-phosphate, not a pressure. The bare
    # abbreviation only counts when a pressure unit follows.
    "map": rf"mean arterial pressure\b[^.\n\d]{{0,25}}?{NUM}",
    "map_abbrev": rf"\bmap\b[^.\n\d]{{0,20}}?{NUM}\s*mm\s*hg",
    "sodium": rf"(?:sodium|\bna\+?\b)[^.\n\d]{{0,25}}?{NUM}\s{{0,3}}(?:mmol|mEq)\s*/\s*[lL]",
    "chloride": rf"(?:chloride|\bcl-?\b)[^.\n\d]{{0,25}}?{NUM}\s{{0,3}}(?:mmol|mEq)\s*/\s*[lL]",
    "bicarbonate": rf"(?:bicarbonate|\bhco3-?\b)[^.\n\d]{{0,25}}?{NUM}\s{{0,3}}(?:mmol|mEq)\s*/\s*[lL]",
    # Likewise "high anion gap (pH 6.9, PaO2: 108 mmHg" -- the pH is not the gap.
    "anion_gap": rf"anion gap\b[^.\n\d()]{{0,25}}?{NUM}",
    "total_chol": rf"total cholesterol\b[^.\n\d]{{0,25}}?{NUM}\s{{0,3}}mg\s*/\s*d[lL]",
    "hdl": rf"hdl(?:-cholesterol)?\b[^.\n\d]{{0,25}}?{NUM}\s{{0,3}}mg\s*/\s*d[lL]",
    "ldl": rf"ldl(?:-cholesterol)?\b[^.\n\d]{{0,25}}?{NUM}\s{{0,3}}mg\s*/\s*d[lL]",
    "triglycerides": rf"triglycerides?\b[^.\n\d]{{0,25}}?{NUM}\s{{0,3}}mg\s*/\s*d[lL]",
    # Serum osmolality and the two inputs it needs beyond sodium. Added ;
    # see the note on check_osmolality for what it changed.
    # The `serum |plasma |calculated ` prefix is inside the match on purpose: the
    # qualifier lookback is 12 characters, and `measured serum osmolality` puts
    # `measured` 15 back from the bare label, so without this the osmolal-gap
    # exclusion below never sees it.
    "osmolality": (rf"(?:serum\s+|plasma\s+|calculated\s+)?osmolalit(?:y|ies)\b"
                   rf"[^.\n\d]{{0,25}}?{NUM}\s{{0,3}}mOsm"),
    "bun": (rf"(?:blood urea nitrogen|\bbun\b)[^.\n\d]{{0,25}}?{NUM}"
            rf"\s{{0,3}}mg\s*/\s*d[lL]"),
    "glucose": rf"glucose\b[^.\n\d]{{0,25}}?{NUM}\s{{0,3}}mg\s*/\s*d[lL]",
}

BP_PATTERN = rf"(?:blood pressure|\bbps?\b)[^.\n\d]{{0,25}}?{NUM}\s*/\s*{NUM}"

# A number the note compares against is not a number the note states. "unable to
# maintain a mean arterial pressure above 65 mmHg" reports a target that was
# missed, and reading 65 as the patient's MAP inverts the note's meaning.
COMPARATIVE = re.compile(
    r"\b(?:above|below|over|under|greater|less|lower|higher|exceed\w*|"
    r"at least|at most|up to|target\w*|goal|maintain\w*|keep|kept|"
    r"threshold|normal|reference|range|as low as|as high as|fell to|rose to|"
    r"units of)\b|[<>≥≤]", re.I)

# Some labels name a different quantity once qualified. An anion gap "after
# correcting for albumin" is not the anion gap this checker recomputes, and
# comparing the two produces a contradiction that only exists in our reading.
QUALIFIERS = {
    # The urine anion gap is a different quantity from the serum one, and is not
    # computed from serum sodium, chloride and bicarbonate.
    "anion_gap": re.compile(r"correct|albumin|urin", re.I),
    "bmi": re.compile(r"target|ideal|desired", re.I),
    # A measured osmolality differing from the calculated one is an osmolal gap:
    # a real clinical finding in toxic alcohol ingestion, not an arithmetic error.
    # Urine osmolality is a different quantity again.
    "osmolality": re.compile(r"measured|urin|effective", re.I),
}

# A gap that names another quantity means the number belongs to that one:
# "body mass index (BMI, height 177 cm, weight 87 kg) 27.8" states the BMI after
# the bracket, and a gap-based match reads the height instead.
GAP_NAMES_ANOTHER = {
    "bmi": re.compile(r"height|weight|tall", re.I),
    "weight_kg": re.compile(r"height|body mass|bmi", re.I),
    "height_cm": re.compile(r"weigh|body mass|bmi", re.I),
}
QUALIFIER_WINDOW = 40


LEAD_WINDOW = 40


def _disqualified(note, match, name):
    # Look before the label as well as between label and number: "maintained on a
    # mean arterial pressure of 60-80 mmHg" and "MAP as low as 50" both put the
    # comparative ahead of the quantity.
    lead = note[max(0, match.start() - LEAD_WINDOW):match.start(1)]
    if COMPARATIVE.search(lead):
        return True
    rx = QUALIFIERS.get(name)
    # Look before the label as well as after it: "urinary anion gap of 20" puts the
    # qualifier ahead of the quantity, and a window starting at the match misses it.
    if rx and rx.search(note[max(0, match.start() - 12):match.end() + QUALIFIER_WINDOW]):
        return True
    rx = GAP_NAMES_ANOTHER.get(name)
    if rx and rx.search(note[match.start():match.start(1)]):
        return True
    return False


def read(note):
    """Every quantity the note states, once each. Ambiguity is declined, not guessed.

    A quantity stated twice with different values is dropped rather than resolved.
    That is not this tool's job: it checks arithmetic, and picking which of two
    stated sodiums the note "meant" is exactly the judgement call that would turn
    a deterministic check into an opinion.
    """
    found, dropped = {}, []
    for name, pattern in PATTERNS.items():
        values = {round(_f(m), 4) for m in re.finditer(pattern, note, re.I)
                  if not _disqualified(note, m, name)}
        if len(values) == 1:
            found[name] = values.pop()
        elif len(values) > 1:
            dropped.append(name)
    for primary, fallback in (("height_cm", "height_cm_tall"), ("map", "map_abbrev")):
        if primary not in found and fallback in found:
            found[primary] = found[fallback]
        found.pop(fallback, None)

    pairs = {(round(_f(m, 1), 4), round(_f(m, 2), 4))
             for m in re.finditer(BP_PATTERN, note, re.I)}
    if len(pairs) == 1:
        found["sys_bp"], found["dia_bp"] = pairs.pop()
    elif len(pairs) > 1:
        dropped.append("blood_pressure")
    return found, dropped


# --- the checks ------------------------------------------------------------
# Each returns (stated, recomputed, tolerance) or None when the note does not
# state enough to run it. Tolerances are loose on purpose: the question is whether
# the note contradicts itself, not whether it rounded.

def check_bmi(q):
    if not {"bmi", "weight_kg", "height_cm"} <= q.keys():
        return None
    h = q["height_cm"] / 100.0
    return q["bmi"], q["weight_kg"] / (h * h), 0.05


def check_map(q):
    if not {"map", "sys_bp", "dia_bp"} <= q.keys():
        return None
    return q["map"], (2 * q["dia_bp"] + q["sys_bp"]) / 3.0, 0.05


def check_anion_gap(q):
    if not {"anion_gap", "sodium", "chloride", "bicarbonate"} <= q.keys():
        return None
    return q["anion_gap"], q["sodium"] - (q["chloride"] + q["bicarbonate"]), 0.10


def check_ldl(q):
    """Friedewald. Not valid above 400 mg/dL of triglycerides, so it is not run there."""
    if not {"ldl", "total_chol", "hdl", "triglycerides"} <= q.keys():
        return None
    if q["triglycerides"] > 400:
        return None
    return q["ldl"], q["total_chol"] - q["hdl"] - q["triglycerides"] / 5.0, 0.10


def check_osmolality(q):
    """Calculated serum osmolality: 2*Na + BUN/2.8 + glucose/18.

    Added in , and not silently. This checker is the instrument a contributor's
    catch-rate figures are measured with, so adding a quantity to it was tested
    against the corpus those figures came from before being committed: of 454
    distinct notes, **three** change, each from no finding to one. All three are
    the same item, `Osmolality-421` (`family: A`, `probe: contradiction`,
    `gold_answer: ABSTAIN`) -- an injected contradiction reading `The calculated
    serum osmolality is reported as 233 mOsm/kg` against a recomputation of
    424.28.

    So this is not a new false-positive surface. It is three real defects the
    checker was blind to, and the Family A catch rate goes up rather than down.
    It still moves a reported number, which is why it is written down here and in
    docs/CHECKER_INPUT_EXTRACTION_GAP.md rather than left for someone to notice.

    The measured-versus-calculated distinction is real -- an osmolal gap is a
    genuine clinical finding, not an error -- so notes reporting a *measured*
    osmolality alongside a calculated one are excluded by the qualifier below.
    """
    if not {"osmolality", "sodium", "bun", "glucose"} <= q.keys():
        return None
    return (q["osmolality"],
            2 * q["sodium"] + q["bun"] / 2.8 + q["glucose"] / 18.0,
            0.05)


DERIVED = {
    "BMI": (check_bmi, "weight / height^2"),
    "mean arterial pressure": (check_map, "(2*diastolic + systolic) / 3"),
    "anion gap": (check_anion_gap, "sodium - (chloride + bicarbonate)"),
    "LDL": (check_ldl, "total cholesterol - HDL - triglycerides/5"),
    "serum osmolality": (check_osmolality, "2*sodium + BUN/2.8 + glucose/18"),
}


def check(note):
    """Every contradiction arithmetic can reach in this note."""
    q, dropped = read(note)
    findings = []

    for name, (fn, formula) in DERIVED.items():
        result = fn(q)
        if result is None:
            continue
        stated, recomputed, tol = result
        if name == "BMI" and not (5 <= recomputed <= 100):
            # "height 1.65 cm" is a unit typo in the note. Real, but a different
            # kind of defect from a derived value disagreeing with its components,
            # and reporting a BMI of 374655 as a contradiction helps nobody.
            findings.append({
                "check": "implausible_component", "quantity": name,
                "stated": round(stated, 3), "recomputed": None, "formula": formula,
                "detail": f"components give an impossible {name} ({recomputed:.0f}); "
                          "the note's height or weight unit is wrong"})
            continue
        if abs(stated - recomputed) > tol * max(abs(recomputed), 1e-9):
            findings.append({
                "check": "derived_value",
                "quantity": name,
                "stated": round(stated, 3),
                "recomputed": round(recomputed, 3),
                "formula": formula,
                "detail": f"the note states {name} = {stated:g}, but its own "
                          f"components give {recomputed:.1f}",
            })

    if {"sys_bp", "dia_bp"} <= q.keys() and q["sys_bp"] <= q["dia_bp"]:
        findings.append({
            "check": "impossible_value",
            "quantity": "blood pressure",
            "stated": f"{q['sys_bp']:g}/{q['dia_bp']:g}",
            "recomputed": None,
            "formula": "systolic > diastolic",
            "detail": f"systolic {q['sys_bp']:g} is not above diastolic "
                      f"{q['dia_bp']:g}",
        })

    return {"findings": findings, "quantities": q, "ambiguous": dropped}


# --- reporting -------------------------------------------------------------

def run_over_items(path):
    with open(path) as f:
        data = json.load(f)

    by_condition = defaultdict(lambda: {"n": 0, "caught": 0})
    detail = []
    for item in data["items"]:
        for cond in item["conditions"]:
            result = check(cond["note"])
            bucket = by_condition[cond["condition"]]
            bucket["n"] += 1
            if result["findings"]:
                bucket["caught"] += 1
                detail.append((item["seed_id"], cond["condition"], result["findings"]))

    print(f"{os.path.basename(path)}: {data['n_items']} items, "
          f"{data['n_seeds_built']} seeds\n")
    print(f"{'condition':<16}{'items':>7}{'caught':>8}{'rate':>8}")
    for name in data["conditions"]:
        b = by_condition[name]
        rate = b["caught"] / b["n"] if b["n"] else 0
        print(f"{name:<16}{b['n']:>7}{b['caught']:>8}{rate:>7.0%}")

    if detail:
        print("\nfindings:")
        for seed_id, cond, findings in detail:
            for f in findings:
                print(f"  {seed_id} [{cond}] {f['detail']}")

    print("\nA zero on value_conflict is the expected result, not a bug. Those items")
    print("state two values for one quantity; neither is derived from anything, so")
    print("there is no arithmetic that contradicts either. Catching them needs a")
    print("reader, which is the whole question the benchmark asks.")


def run_over_corpus(path):
    """Run over the published notes, which are presumed internally consistent.

    Two reasons this matters. A checker that never fires proves nothing, so it has
    to be shown firing somewhere. And every hit here is either a real contradiction
    in a published case report or a false positive in this file; both are things we
    need to know before any catch rate is quoted, and neither is discoverable from
    our own constructed items, where we already know the answer.
    """
    import csv
    csv.field_size_limit(10 ** 9)
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    hits, runnable = [], 0
    for row in rows:
        result = check(row["Patient Note"])
        q = result["quantities"]
        if any(fn(q) is not None for fn, _ in DERIVED.values()) or \
                {"sys_bp", "dia_bp"} <= q.keys():
            runnable += 1
        if result["findings"]:
            hits.append((row["Note ID"], row["Calculator Name"], result["findings"]))

    print(f"{os.path.basename(path)}: {len(rows)} published notes")
    print(f"  at least one check runnable: {runnable} "
          f"({runnable / len(rows):.0%})")
    print(f"  notes with a finding:        {len(hits)} "
          f"({len(hits) / len(rows):.1%})\n")
    for note_id, calc, findings in hits:
        for f in findings:
            print(f"  {note_id:<18} {calc[:34]:<36} {f['detail']}")
    print("\nEach line above is a published note whose own numbers disagree. They are")
    print("not ours and we did not inject them; they are what a checker finds when")
    print("pointed at real case reports. Whether each is a genuine contradiction or")
    print("an extraction artifact of this file is a reading task, not an arithmetic")
    print("one -- and that reading is 's naturally-occurring-conflict search.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--items", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "items_dissociation.json"))
    ap.add_argument("--text", help="check one note given on the command line")
    ap.add_argument("--corpus", nargs="?", const=os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data", "medcalc", "test_data.csv"),
        help="run over the published MedCalc-Bench notes instead")
    args = ap.parse_args()

    if args.corpus:
        if not os.path.exists(args.corpus):
            sys.exit(f"{args.corpus} not found. Run: python3 fetch_medcalc.py")
        run_over_corpus(args.corpus)
        return 0

    if args.text:
        result = check(args.text)
        print(json.dumps(result, indent=2))
        return 1 if result["findings"] else 0

    if not os.path.exists(args.items):
        sys.exit(f"{args.items} not found. Run: python3 construct.py")
    run_over_items(args.items)
    return 0


if __name__ == "__main__":
    sys.exit(main())
