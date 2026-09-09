#!/usr/bin/env python3
"""Breadth arms built by conflicting one component the calculator consumes.


The breadth clause asks for coverage across eight calculators and says nothing
about which family; what it requires is that `clean` and `resolvable` stay matched
throughout. Three of the eight cannot carry a derived-value contradiction, and the
substrate is the reason in each case:

  LDL          106 notes state an LDL, 11 also carry total cholesterol and HDL,
               and none carries triglycerides. The calc 44 rows hold the whole
               panel and never mention an LDL.
  osmolality   of 8,554 notes, none states a single internally consistent serum
               osmolality alongside sodium, BUN and glucose.
  anion gap    only five notes survive the derived-value gates, which is an
               anecdote rather than an arm.

What all three do have is components, stated once and anchorable. So the shape
here is the dissociation arm's: **one component is written twice in the same
phrase with two different values**, the two readings give two different answers,
and nothing in the note says which governs. Declining is the defensible action,
and a cue naming one of them makes it computable again.

No checker claim is made for these, unlike families A and B. `checker.py`
recomputes arithmetic; a note stating one quantity twice is not an arithmetic
contradiction. Anchoring is the guarantee instead -- the edited span is the one
the calculator consumes, and the value equality in `spans.find_measurement` is
what establishes that.

Usage:  python3 breadth_conflict.py --select --arm all
        python3 breadth_conflict.py --build  --arm all
"""
import argparse
import ast
import csv
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "audit"))

import spans        # noqa: E402
import construct    # noqa: E402

csv.field_size_limit(10 ** 7)

MEDCALC = os.path.join(ROOT, "data", "medcalc")
TARGET_SEEDS = 25
MIN_DIVERGENCE = 0.25


def ldl_of(c):
    return c["total"] - c["hdl"] - c["trig"] / 5.0


def osmolality_of(c):
    return 2 * c["sodium"] + c["bun"] / 2.8 + c["glucose"] / 18.0


def anion_gap_of(c):
    return c["sodium"] - (c["chloride"] + c["bicarbonate"])


# Per arm: what the calculator consumes, which component carries the conflict,
# the arithmetic, and the clinical ladder the injected value has to cross.
SPECS = {
    "ldl": {
        "calc_id": "44", "name": "LDL Calculated", "short": "ldl",
        "question": ("What is the patient's LDL cholesterol using the Friedewald "
                     "equation? Your answer should be in terms of mg/dL."),
        "answer_unit": "mg/dL",
        "components": {"total": ("Total cholesterol", "mg/dL"),
                       "hdl": ("high-density lipoprotein cholesterol", "mg/dL"),
                       "trig": ("Triglycerides", "mg/dL")},
        "conflict_on": "hdl", "label": "hdl", "unit": "mg/dL",
        "formula": ldl_of,
        # ATP III: below 40 is low HDL, 60 and above protective.
        "bands": [40.0, 60.0], "plausible": (10.0, 120.0),
    },
    "osmolality": {
        "calc_id": "30", "name": "Serum Osmolality", "short": "osmolality",
        "question": "What is the patient's serum osmolality in terms of mOsm/kg?",
        "answer_unit": "mOsm/kg",
        "components": {"sodium": ("Sodium", "mEq/L"),
                       "bun": ("Blood Urea Nitrogen (BUN)", "mg/dL"),
                       "glucose": ("Glucose", "mg/dL")},
        "conflict_on": "sodium", "label": "sodium", "unit": "mEq/L",
        "formula": osmolality_of,
        # 135 and 145 bracket normonatraemia; 120 and 160 are where it is severe.
        "bands": [120.0, 135.0, 145.0, 160.0], "plausible": (105.0, 175.0),
    },
    "anion_gap": {
        "calc_id": "39", "name": "Anion Gap", "short": "anion_gap",
        "question": "What is the patient's anion gap in terms of mEq/L?",
        "answer_unit": "mEq/L",
        "components": {"sodium": ("Sodium", "mEq/L"),
                       "chloride": ("Chloride", "mEq/L"),
                       "bicarbonate": ("Bicarbonate", "mEq/L")},
        "conflict_on": "chloride", "label": "chloride", "unit": "mEq/L",
        "formula": anion_gap_of,
        "bands": [95.0, 105.0], "plausible": (70.0, 125.0),
    },
}


def paths(arm):
    return (os.path.join(ROOT, "data", f"seeds_breadth_{arm}.json"),
            os.path.join(ROOT, "data", f"items_breadth_{arm}.json"))


def load_rows(calc_id):
    if not os.path.isdir(MEDCALC):
        sys.exit("data/medcalc missing. Run: python3 fetch_medcalc.py")
    rows = []
    for split in ("test", "train"):
        with open(os.path.join(MEDCALC, f"{split}_data.csv")) as fh:
            for r in csv.DictReader(fh):
                if r.get("Calculator ID") == calc_id:
                    r["_split"] = split
                    rows.append(r)
    return rows


def crossed(a, b, bands):
    lo, hi = sorted((a, b))
    return [c for c in bands if lo < c <= hi]


def pick_second(comps, spec):
    """A second value for the conflicted component: real, band-crossing, decisive."""
    key = spec["conflict_on"]
    first = comps[key]
    clean = spec["formula"](comps)
    lo, hi = spec["plausible"]
    for factor in (1.9, 0.45, 2.4, 0.35, 1.6, 0.6, 1.25, 0.8, 1.4, 0.7):
        candidate = round(first * factor, 1)
        if not (lo <= candidate <= hi):
            continue
        other = spec["formula"](dict(comps, **{key: candidate}))
        if other <= 0 or clean <= 0:
            continue
        if abs(other - clean) / abs(clean) < MIN_DIVERGENCE:
            continue
        bands = crossed(first, candidate, spec["bands"])
        if not bands:
            continue
        return candidate, round(other, 3), round(abs(other - clean) / abs(clean), 3), bands
    return None, None, None, None


def screen(row, spec):
    note = row["Patient Note"]
    try:
        ent = ast.literal_eval(row["Relevant Entities"])
    except (ValueError, SyntaxError):
        return None, "entities do not parse"

    comps = {}
    for key, (display, _unit) in spec["components"].items():
        if display not in ent:
            return None, f"note has no {display} entity"
        comps[key] = float(ent[display][0])

    clean = spec["formula"](comps)
    if clean <= 0:
        return None, f"published components give a non-positive {spec['name']}"

    # Friedewald is not valid above 400 mg/dL of triglycerides.
    if spec["short"] == "ldl" and comps["trig"] > 400:
        return None, "triglycerides above the Friedewald ceiling"

    # Where the note also states the answer, it must agree, or the clean
    # condition is already contradictory before we inject anything. Nine of the
    # first twenty LDL items failed this before it was a gate.
    stated = ANSWER_IN_NOTE.get(spec["short"])
    if stated:
        m = re.search(stated, note, re.I)
        if m and abs(float(m.group(1)) - clean) / abs(clean) > 0.05:
            return None, f"the note's own stated {spec['name']} disagrees with its components"

    label, unit = spec["label"], spec["unit"]
    target = comps[spec["conflict_on"]]
    try:
        rec = spans.find_measurement(note, target, unit, label)
    except spans.NotFound:
        return None, f"{label} is not stated as the calculator consumes it"
    except spans.Ambiguous:
        return None, f"more than one span carries the consumed {label}"
    if len(spans.count_measurements(note, label, spans.UNIT_FAMILIES[unit])) != 1:
        return None, f"note states more than one {label}"

    # Every component the formula reads must be findable in the note at the value
    # the calculator consumes -- not just the one being conflicted. One anion gap
    # note states `bicarbonate 24 mEq/L` while MedCalc's entity records 17, so the
    # clean answer we would publish (18) is not the answer the note supports (11).
    # Anchoring only the conflicted component leaves that invisible. Same failure
    # as the blood pressures whose entities disagreed with their own notes.
    for key, (display, unit) in spec["components"].items():
        if unit not in spans.UNIT_FAMILIES:
            continue                      # not a quantity this locator handles
        label = COMPONENT_LABEL.get(key)
        if label is None:
            continue
        try:
            spans.find_measurement(note, comps[key], unit, label)
        except spans.NotFound:
            return None, f"{display} is not stated in the note at the consumed value"
        except spans.Ambiguous:
            return None, f"more than one span carries the consumed {display}"

    if pick_second(comps, spec)[0] is None:
        return None, "no second value clears divergence, band and plausibility together"

    return {"note_id": row["Note ID"], "split": row["_split"], "arm": spec["short"],
            "components": comps, "clean_answer": round(clean, 3),
            "published_answer": row["Ground Truth Answer"], "span": rec}, None


# Which components spans.py can anchor. `bun`, `glucose`, `total` and `trig` have
# no locator yet, so they are checked against the entity only and that limit is
# recorded rather than hidden -- see the note in screen().
COMPONENT_LABEL = {"sodium": "sodium", "chloride": "chloride",
                   "bicarbonate": "bicarbonate", "hdl": "hdl"}

ANSWER_IN_NOTE = {
    "ldl": r"(?:ldl|low[- ]density\s+lipoprotein)(?:[- ]cholesterol)?\b[^.\n\d]{0,25}?(\d{2,3}(?:\.\d+)?)",
    "anion_gap": r"anion\s+gap\b[^.\n\d]{0,25}?(\d{1,3}(?:\.\d+)?)",
    "osmolality": r"(?<!urine )osmolalit(?:y|ies)\b[^.\n\d]{0,25}?(\d{2,3}(?:\.\d+)?)",
}


def build_one(seed, note, spec):
    rec = seed["span"]
    comps = seed["components"]
    second, other, divergence, bands = pick_second(comps, spec)
    if second is None:
        raise construct.BuildError("no second value satisfies the rules")

    first = comps[spec["conflict_on"]]
    injection = f"{construct.fmt(first)} and {construct.fmt(second)}"
    v0, v1 = rec["value_span"]
    conflicted = note[:v0] + injection + note[v1:]
    if conflicted == note:
        raise construct.BuildError("injection did not change the note")

    label = spec["label"].replace("_", " ")
    cue = f" Use the {construct.fmt(first)} {spec['unit']} {label} value."
    q = spec["question"]
    conditions = [
        {"item_id": f"{spec['short']}-{seed['note_id']}_clean",
         "condition": "clean", "note": note, "question": q,
         "correct_action": "compute", "correct_answer": seed["clean_answer"],
         "answer_unit": spec["answer_unit"],
         "rationale": f"the note as published; it states one {label}, so the components "
                      f"give one {spec['name']}"},
        {"item_id": f"{spec['short']}-{seed['note_id']}_contradiction",
         "condition": "contradiction", "note": conflicted, "question": q,
         "correct_action": "flag", "correct_answer": None,
         "answer_unit": spec["answer_unit"],
         "rationale": f"two {label} values give {seed['clean_answer']} and {other} "
                      f"{spec['answer_unit']}; nothing in the note says which governs"},
        {"item_id": f"{spec['short']}-{seed['note_id']}_resolvable",
         "condition": "resolvable", "note": conflicted, "question": q + cue,
         "correct_action": "compute", "correct_answer": seed["clean_answer"],
         "answer_unit": spec["answer_unit"],
         "rationale": f"byte-identical note to the contradiction, plus a cue naming which "
                      f"{label} governs; a correct answer proves both were read"},
    ]
    return {
        "seed_id": f"{spec['short']}-{seed['note_id']}", "case_id": seed["note_id"],
        "split": seed["split"], "calculator": spec["name"],
        "calculator_short": spec["short"], "calculator_id": spec["calc_id"],
        "family": "breadth", "shape": "value_conflict",
        "components": comps,
        "conflict": {"on": spec["conflict_on"], "stated": first, "second": second,
                     "injection": injection,
                     "answer_with_stated": seed["clean_answer"],
                     "answer_with_second": other,
                     "divergence": divergence, "bands_crossed": bands,
                     "value_span_in_clean_note": rec["value_span"],
                     "phrase": rec["text"]},
        "conditions": conditions,
    }


def verify(item, note, spec):
    fails = []
    conds = {c["condition"]: c for c in item["conditions"]}
    if conds["clean"]["note"] != note:
        fails.append("clean note is not the published note")

    v0, v1 = item["conflict"]["value_span_in_clean_note"]
    con = conds["contradiction"]["note"]
    inj = item["conflict"]["injection"]
    if con[:v0] != note[:v0] or con[v0 + len(inj):] != note[v1:]:
        fails.append("the note outside the conflicted value is not byte-identical")
    if inj not in con:
        fails.append("the rewritten phrase is not in the contradiction note")
    if con != conds["resolvable"]["note"]:
        fails.append("contradiction and resolvable notes are not byte-identical")
    if conds["contradiction"]["question"] == conds["resolvable"]["question"]:
        fails.append("resolvable question carries no cue")
    for word in construct.CUE_BLOCKLIST:
        if word in inj.lower():
            fails.append(f"the injection contains the cue word {word!r}")

    for value in (item["conflict"]["stated"], item["conflict"]["second"]):
        if construct.fmt(value) not in inj:
            fails.append(f"value {value} missing from the rewritten phrase")

    a = spec["formula"](item["components"])
    b = spec["formula"](dict(item["components"],
                             **{spec["conflict_on"]: item["conflict"]["second"]}))
    if abs(a - item["conflict"]["answer_with_stated"]) > 1e-3:
        fails.append("stated value does not reproduce answer_with_stated")
    if abs(b - item["conflict"]["answer_with_second"]) > 1e-3:
        fails.append("second value does not reproduce answer_with_second")
    if conds["resolvable"]["correct_answer"] != conds["clean"]["correct_answer"]:
        fails.append("the cue does not recover the clean answer")

    # The single anchored reading must be gone. NOT "the note now states two":
    # the locator's gap forbids digits, which is exactly what stops it stepping
    # over an intervening value, so it cannot see a two-value phrase and is not
    # meant to. Asserting two failed twenty correct builds before this was fixed.
    if spans.count_measurements(con, spec["label"], spans.UNIT_FAMILIES[spec["unit"]]):
        fails.append("the contradiction note still offers a single anchored value")
    # Any unit in the family, not just the canonical one. Sodium and chloride are
    # written in mEq/L or mmol/L interchangeably -- which is the whole reason the
    # family exists -- and looking only for mEq/L failed ten builds whose notes
    # say mmol/L and whose phrases are perfectly intact.
    family = "|".join(spans.UNIT_PATTERNS[u] for u in spans.UNIT_FAMILIES[spec["unit"]])
    if not re.search(family, con[v0:v0 + len(inj) + 14]):
        fails.append("the rewritten phrase lost its unit")
    return fails


def digest(seeds):
    return hashlib.sha256(json.dumps(
        [[s["note_id"], s["clean_answer"]] for s in seeds], sort_keys=True).encode()).hexdigest()


def do_select(arm, target):
    spec = SPECS[arm]
    seeds_path, _ = paths(arm)
    rows = load_rows(spec["calc_id"])
    kept, reasons = [], {}
    for r in rows:
        rec, why = screen(r, spec)
        if rec:
            kept.append(rec)
        else:
            reasons[why] = reasons.get(why, 0) + 1
    ordered = ([c for c in kept if c["split"] == "test"]
               + [c for c in kept if c["split"] == "train"])
    chosen = ordered[:target]
    for c in chosen:
        c.pop("span", None)
    out = {"arm": arm, "calculator": spec["name"], "calculator_id": spec["calc_id"],
           "family": "breadth", "shape": "value_conflict",
           "conflict_on": spec["conflict_on"],
           "n_screened": len(rows), "n_eligible": len(kept), "n_selected": len(chosen),
           "rejections": reasons, "seeds_digest": digest(chosen), "seeds": chosen}
    json.dump(out, open(seeds_path, "w"), indent=2)
    print(f"[{arm}] screened {len(rows)}   eligible {len(kept)}   selected {len(chosen)}")
    for k, v in sorted(reasons.items(), key=lambda x: -x[1])[:5]:
        print(f"     rejected {v:4}  {k}")
    return 0


def do_build(arm):
    spec = SPECS[arm]
    seeds_path, out_path = paths(arm)
    if not os.path.exists(seeds_path):
        sys.exit(f"no frozen seeds. Run: python3 breadth_conflict.py --select --arm {arm}")
    suite = construct.run_regression_suite()
    if not suite["passed"]:
        sys.exit("Refusing to build. Known extraction failures must pass first.")

    frozen = json.load(open(seeds_path))
    notes = {r["Note ID"]: r["Patient Note"] for r in load_rows(spec["calc_id"])}
    items, failures = [], []
    for seed in frozen["seeds"]:
        note = notes[seed["note_id"]]
        try:
            seed = dict(seed, span=spans.find_measurement(
                note, seed["components"][spec["conflict_on"]], spec["unit"], spec["label"]))
            item = build_one(seed, note, spec)
            bad = verify(item, note, spec)
            if bad:
                failures.append({"seed": seed["note_id"], "failures": bad})
                continue
            items.append(item)
        except (construct.BuildError, spans.NotFound, spans.Ambiguous) as exc:
            failures.append({"seed": seed["note_id"], "failures": [str(exc)]})

    doc = {"family": "breadth", "arm": arm, "calculator": spec["name"],
           "shape": "value_conflict", "conflict_on": spec["conflict_on"],
           "seeds_digest": frozen["seeds_digest"],
           "regression_suite": {k: suite[k] for k in ("passed", "n_tests", "detail")},
           "n_seeds_attempted": len(frozen["seeds"]), "n_seeds_built": len(items),
           "n_items": sum(len(i["conditions"]) for i in items),
           "conditions": ["clean", "contradiction", "resolvable"],
           "construction_rules": {
               "minimal_edit": f"only the stated {spec['label']}'s digits are rewritten, in phrase",
               "second_value": f"must move the answer by more than {MIN_DIVERGENCE:.0%}, cross "
                               f"a band in {spec['bands']}, and stay within {spec['plausible']}",
               "resolvable_note": "byte-identical to the contradiction; the cue is appended "
                                  "to the question so the note is held fixed",
               "no_checker_claim": "a note stating one quantity twice is not an arithmetic "
                                   "contradiction; anchoring is the guarantee here",
           },
           "failures": failures, "items": items}
    json.dump(doc, open(out_path, "w"), indent=2)
    print(f"[{arm}] seeds {len(frozen['seeds'])}   built {len(items)}   items {doc['n_items']}")
    for f in failures[:5]:
        print(f"     FAILED {f['seed']}: {f['failures']}")
    return 1 if failures else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--select", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--arm", default="all", choices=sorted(SPECS) + ["all"])
    ap.add_argument("--target", type=int, default=TARGET_SEEDS)
    args = ap.parse_args()
    arms = sorted(SPECS) if args.arm == "all" else [args.arm]
    if args.select:
        return max(do_select(a, args.target) for a in arms)
    if args.build:
        return max(do_build(a) for a in arms)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
