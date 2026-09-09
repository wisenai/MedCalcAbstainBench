#!/usr/bin/env python3
"""Build Family A: a documented BMI contradicting the note's own height and weight.

Task owner: Annotator D -- Week 3.
Completed by Annotator D.

WHERE THIS IS BUILT, AND WHY NOT WHERE THE SPEC SAID. On 2026-08-18 the spec was
amended to build Family A on BMI (calc 6) and Target Weight (calc 61), on the
argument that the three risk scores neither consume nor produce a derived value.
That argument stands. The substrate does not:

  calc 6  (BMI)            519 rows, and **not one of their notes states a BMI**.
                           There is nothing to contradict.
  calc 61 (Target Weight)  100 rows, every note a synthetic 67-character
                           one-liner: "Patient has a height of 196 cm and their
                           target BMI is 19.2 kg/m^2." No current weight, so
                           nothing for the index to disagree with, and the BMI is
                           a *target* rather than a claim about the patient.

The other derived quantities are no better as A1 substrate: of their own rows,
MAP has 1 note stating a MAP (and it is a treatment goal, "maintain above 65"),
anion gap 0, LDL 0, and serum osmolality 15 -- all of which are measured-versus-
calculated osmolal gaps, a real clinical distinction rather than a contradiction.

What does exist: **496 real notes state exactly one BMI alongside a height and a
weight, with the stated index consistent with its own components.** They are
drawn from the rows of whichever calculator MedCalc happened to pair them with,
and asked here with MedCalc's own BMI question. The note is real and unedited
except for our injection; the question is MedCalc's; the pairing is ours, and is
recorded as such on every item. Since every clean answer is recomputed from the
released implementation and no shipped label is inherited, the pairing costs
nothing that was being relied on.

Usage:  python3 family_a.py --select
        python3 family_a.py --build
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
import checker      # noqa: E402

csv.field_size_limit(10 ** 7)

BMI_CALC_ID = "6"
MEDCALC = os.path.join(ROOT, "data", "medcalc")

TARGET_SEEDS = 30
MIN_DIVERGENCE = 0.25                      # as in the dissociation arm
WHO_CLASSES = [18.5, 25.0, 30.0, 35.0, 40.0]
PLAUSIBLE_BMI = (12.0, 70.0)               # outside this is a typo, not a claim
CONSISTENT_TOLERANCE = 0.05                # the note must start out self-consistent

QUESTION = ("What is the patient's body mass index (BMI)? "
            "Your answer should be in terms of kg/m².")

# --- the family, parameterised ----------------------------------------------
#
# Family A is one shape -- a derived value contradicting the components the note
# also states -- so a second derived quantity is a table entry, not a second
# builder. What varies is the locator key, the components and how they convert,
# the arithmetic, and the clinical ladder the injected value has to cross.
#
# `checker_quantity` is not decoration: the family's claim is that checker.py
# catches A by construction, so a quantity the checker does not recompute cannot
# carry an item, and the build refuses rather than shipping one it cannot verify.
DERIVED_SPECS = {
    "bmi": {
        "calc_id": "6",
        "name": "Body Mass Index (BMI)",
        "short": "bmi",
        "question": QUESTION,
        "answer_unit": "kg/m^2",
        "components": ["height", "weight"],
        "checker_needs": ["height_cm", "weight_kg", "bmi"],
        "checker_quantity": "bmi",
        "boundaries": WHO_CLASSES,
        "boundary_name": "WHO BMI class",
        "plausible": PLAUSIBLE_BMI,
        "framing": (r"\b(?:morbid(?:ly)?\s+obes\w+|obes\w+|overweight|underweight|"
                    r"cachec\w+|emaciat\w+|malnourish\w+|normal\s+weight|"
                    r"well[- ]nourished|frail|wasted)\b"),
    },
    "anion_gap": {
        "calc_id": "39",
        "name": "Anion Gap",
        "short": "anion_gap",
        "question": "What is the patient's anion gap in terms of mEq/L?",
        "answer_unit": "mEq/L",
        "components": ["Sodium", "Chloride", "Bicarbonate"],
        "checker_needs": ["sodium", "chloride", "bicarbonate", "anion_gap"],
        "checker_quantity": "anion gap",
        # 12 is the clinical line between a normal and a raised anion gap, which
        # is what makes an injected value decision-relevant rather than merely
        # different; 8 and 20 bracket it the way the KDIGO stages bracket eGFR.
        "boundaries": [8.0, 12.0, 20.0],
        "boundary_name": "anion gap band",
        "plausible": (2.0, 40.0),
        "framing": (r"\b(?:elevated|raised|increased|high|wide(?:ned)?|normal|"
                    r"low|narrow(?:ed)?)\b"),
        "units": {"Sodium": ("eq/l", "mol/l"), "Chloride": ("eq/l", "mol/l"),
                  "Bicarbonate": ("eq/l", "mol/l")},
    },
}

# SERUM OSMOLALITY IS DELIBERATELY ABSENT FROM THE TABLE ABOVE.
#
# It was there, it built zero items, and it left an empty
# `data/items_family_a_osmolality.json` behind that read as an oversight rather
# than a result -- the first person to see it asked whether we still needed it.
# An empty item file is worse than no file: someone will try to run it.
#
# Family A needs a note that states a derived value contradicting components the
# note also states. Of 8,554 notes, **none** states a single, internally
# consistent serum osmolality alongside sodium, BUN and glucose. The full
# accounting: 8,445 state no osmolality, 63 state several, 57 lack a component
# entity, 2 use units we do not convert, and the last 8 all disagree already --
# and reading those 8 showed they are urine osmolality, *measured* osmolality
# (an osmolal gap is a real clinical finding, not an arithmetic error), and in
# one case a urine specific gravity of 1.007 that the locator had grabbed.
#
# Osmolality IS covered, by conflicting a component instead of the derived value:
# see `breadth_conflict.py`, which builds 25 seeds / 75 items on it. Coverage of
# the eight calculators is complete; only the injection shape differs.


SEEDS_FOR = lambda key: os.path.join(ROOT, "data", f"seeds_family_a_{key}.json")  # noqa: E731
OUT_FOR = lambda key: os.path.join(ROOT, "data", f"items_family_a_{key}.json")    # noqa: E731

# Written where the original single-quantity build put them, so nothing that
# already reads these paths breaks.
SEEDS = os.path.join(ROOT, "data", "seeds_family_a.json")
OUT = os.path.join(ROOT, "data", "items_family_a.json")


def bmi_of(height_m, weight_kg):
    return weight_kg / (height_m * height_m)


def crossed_classes(a, b):
    lo, hi = sorted((a, b))
    return [c for c in WHO_CLASSES if lo < c <= hi]


def to_metres(value, unit):
    u = str(unit).lower()
    if "cm" in u:
        return value / 100.0
    if u.strip() in ("m", "meter", "metre", "meters", "metres"):
        return value
    return None


def to_kilos(value, unit):
    u = str(unit).lower()
    if "kg" in u or "kilogram" in u:
        return value
    if "lb" in u or "pound" in u:
        return value * 0.453592
    return None


def load_rows():
    if not os.path.isdir(MEDCALC):
        sys.exit("data/medcalc missing. Run: python3 fetch_medcalc.py")
    rows = []
    for split in ("test", "train"):
        with open(os.path.join(MEDCALC, f"{split}_data.csv")) as fh:
            for r in csv.DictReader(fh):
                r["_split"] = split
                rows.append(r)
    return rows


def by_note(rows):
    """One entry per distinct note, with every entity any row records for it."""
    out = {}
    for r in rows:
        slot = out.setdefault(r["Patient Note"], {"note": r["Patient Note"],
                                                  "note_id": r["Note ID"],
                                                  "split": r["_split"], "entities": {}})
        if slot["split"] != "test" and r["_split"] == "test":
            slot["split"] = "test"
        try:
            slot["entities"].update(ast.literal_eval(r["Relevant Entities"]))
        except (ValueError, SyntaxError):
            pass
    return list(out.values())


def components_of(entry, spec):
    """The component values in the units the arithmetic wants, or a reason why not.

    BMI's components need converting (cm or m, kg or lb); the anion gap's do not,
    because mEq/L and mmol/L are the same number for these ions. Keeping the
    conversion inside the spec's own branch means a new quantity does not have to
    reason about somebody else's units.
    """
    ent = entry["entities"]
    missing = [c for c in spec["components"] if not ent.get(c)]
    if missing:
        return None, f"note has no {', '.join(missing)} entit{'y' if len(missing) == 1 else 'ies'}"

    if spec["short"] == "bmi":
        h, w = ent["height"], ent["weight"]
        height_m = to_metres(float(h[0]), h[1])
        weight_kg = to_kilos(float(w[0]), w[1])
        if height_m is None or weight_kg is None:
            return None, "height or weight in a unit we do not convert"
        if height_m <= 0.3 or weight_kg <= 1:
            return None, "height or weight outside a usable range"
        return {"height_m": round(height_m, 4), "weight_kg": round(weight_kg, 4)}, None

    # Everything else states its components in the unit the formula wants, so the
    # check is that the note's unit is one we recognise rather than a conversion.
    # Declared per spec: the anion gap's are all mEq/L, osmolality mixes mEq/L
    # with mg/dL, and silently accepting the wrong one would give a wrong answer
    # that looks perfectly reasonable.
    vals = {}
    for c in spec["components"]:
        value, unit = ent[c][0], str(ent[c][1]).lower().replace(" ", "")
        allowed = spec["units"][c]
        if not any(a.replace(" ", "") in unit for a in allowed):
            return None, f"{c} in a unit we do not convert ({ent[c][1]})"
        vals[SHORT_COMPONENT.get(c, c.lower())] = float(value)
    return vals, None


# Component display names as the arithmetic below refers to them.
SHORT_COMPONENT = {"Blood Urea Nitrogen (BUN)": "bun"}


def recompute(comps, spec):
    if spec["short"] == "bmi":
        return bmi_of(comps["height_m"], comps["weight_kg"])
    if spec["short"] == "anion_gap":
        return comps["sodium"] - (comps["chloride"] + comps["bicarbonate"])
    return 2 * comps["sodium"] + comps["bun"] / 2.8 + comps["glucose"] / 18.0


def screen(entry, spec=None):
    spec = spec or DERIVED_SPECS["bmi"]
    key, name = spec["short"], spec["name"]
    note = entry["note"]
    try:
        rec = spans.find_derived(note, key)
    except spans.NotFound:
        return None, f"no documented {name}"
    except spans.Ambiguous:
        return None, f"more than one documented {name}"

    comps, why = components_of(entry, spec)
    if comps is None:
        return None, why

    recomputed = recompute(comps, spec)
    stated = rec["value"]
    if recomputed <= 0:
        return None, f"recomputed {name} is not positive"
    if abs(recomputed - stated) / abs(recomputed) > CONSISTENT_TOLERANCE:
        # A note whose value already disagrees with its components is a natural
        # Family A case, not a base for a constructed one. Counted, not used.
        return None, f"documented {name} already disagrees with its own components"
    if not (spec["plausible"][0] <= recomputed <= spec["plausible"][1]):
        return None, f"recomputed {name} outside a plausible range"

    # The family's claim is that checker.py catches A by construction, and that
    # claim is only true where the checker can read the components out of the
    # note itself. MedCalc's entities are not the same capability: it records a
    # height and weight for `He weighs 106 kg and is 168 cm in height`, and the
    # checker sees neither. Screening on the checker keeps the guarantee honest.
    #
    # This is a gate rather than a fix to checker.py on purpose. The checker is
    # the instrument Maia's catch-rate numbers are measured with, and its Week 2
    # figures are already reported; widening its extraction mid-study would make
    # those non-comparable. The gap is written up for her instead.
    seen = checker.check(note)["quantities"]
    missing = [k for k in spec["checker_needs"] if k not in seen]
    if missing:
        return None, f"checker cannot read {', '.join(missing)} from the note text"

    # Framing attached to the value was written for the value the note had, and
    # our injection is required to cross a clinical boundary -- so the framing
    # almost always ends up contradicting the number it sits beside. Found by
    # reading, not by any check: `weighed 91 kg (morbid obesity, body mass index
    # 19.3)` reads as a second, unintended contradiction, and a model could flag
    # that instead of the one we built. The dissociation arm gates on the same
    # thing for the same reason.
    if spec.get("framing"):
        v0, v1 = rec["value_span"]
        window = note[max(0, v0 - 160):v1 + 80]
        m = re.search(spec["framing"], window, re.I)
        if m:
            return None, f"clinical framing {m.group(0)!r} is attached to the value"

    raw = {c: [float(entry["entities"][c][0]), entry["entities"][c][1]]
           for c in spec["components"]}
    return {"note_id": entry["note_id"], "split": entry["split"],
            "quantity": spec["short"],
            "stated_value": stated, "recomputed_value": round(recomputed, 3),
            "components": comps, "components_as_recorded": raw,
            "value_span_record": rec}, None


def english_list(names):
    """`sodium, chloride and bicarbonate`, not `sodium and chloride and bicarbonate`.

    The cue is read by the model, so it has to read like a sentence. Joining a
    three-component list with `and` throughout produced "Use the sodium and
    chloride and bicarbonate", which is the sort of thing that makes a prompt
    look machine-made and could plausibly change how it is followed.
    """
    parts = [n.lower() for n in names]
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def crossed_boundaries(a, b, boundaries):
    lo, hi = sorted((a, b))
    return [c for c in boundaries if lo < c <= hi]


def pick_contradicting(recomputed, spec):
    """A value that contradicts the components, crosses a clinical line, and is real.

    Ordered candidates rather than a random draw, so the build is reproducible
    and the choice is inspectable: the first that satisfies every rule wins.
    """
    lo, hi = spec["plausible"]
    for factor in (0.55, 1.8, 0.45, 2.2, 0.65, 1.5, 0.38, 2.6):
        candidate = round(recomputed * factor, 1)
        if not (lo <= candidate <= hi):
            continue
        divergence = abs(candidate - recomputed) / abs(recomputed)
        if divergence < MIN_DIVERGENCE:
            continue
        crossed = crossed_boundaries(recomputed, candidate, spec["boundaries"])
        if not crossed:
            continue
        return candidate, round(divergence, 3), crossed
    return None, None, None


def rewrite_value(note, span_record, new_value):
    v0, v1 = span_record["value_span"]
    return note[:v0] + construct.fmt(new_value) + note[v1:]


def cue_text(spec):
    """Names which source governs. The note is never touched; the cue rides the question.

    It cues the components rather than the documented value, so answering
    correctly requires computing rather than copying -- and because the two
    candidate answers differ, the answer itself shows which source was used.
    """
    listed = english_list(spec["components"])
    return (f" The recorded {listed} are correct; the documented "
            f"{spec['name'].split(' (')[0].lower()} was entered in error. "
            f"Use the {listed}.")


def build_one(seed, note, spec=None):
    spec = spec or DERIVED_SPECS[seed.get("quantity", "bmi")]
    rec = seed["value_span_record"]
    recomputed = seed["recomputed_value"]
    injected, divergence, crossed = pick_contradicting(recomputed, spec)
    if injected is None:
        raise construct.BuildError(f"no contradicting {spec['name']} satisfies the rules")

    contradicted = rewrite_value(note, rec, injected)
    if contradicted == note:
        raise construct.BuildError("injection did not change the note")

    question, unit = spec["question"], spec["answer_unit"]
    short_name = spec["name"].split(" (")[0].lower()
    listed = english_list(spec["components"])
    conditions = [
        {"item_id": f"{spec['short']}-{seed['note_id']}_clean",
         "condition": "clean", "note": note, "question": question,
         "correct_action": "compute", "correct_answer": recomputed,
         "answer_unit": unit,
         "rationale": f"the note as published; its documented {short_name} agrees with its "
                      f"own {listed}, so nothing is in dispute"},
        {"item_id": f"{spec['short']}-{seed['note_id']}_contradiction",
         "condition": "contradiction", "note": contradicted, "question": question,
         "correct_action": "flag", "correct_answer": None,
         "answer_unit": unit,
         "rationale": f"the note documents a {short_name} of {construct.fmt(injected)} while "
                      f"its own {listed} give {recomputed}; nothing in the note says which "
                      f"is the error"},
        {"item_id": f"{spec['short']}-{seed['note_id']}_resolvable",
         "condition": "resolvable", "note": contradicted,
         "question": question + cue_text(spec),
         "correct_action": "compute", "correct_answer": recomputed,
         "answer_unit": unit,
         "rationale": "byte-identical note to the contradiction, plus a cue naming which "
                      "source governs; the two candidate answers differ, so a correct "
                      "answer shows the components were used rather than copied"},
    ]
    return {
        "seed_id": f"{spec['short']}-{seed['note_id']}",
        "case_id": seed["note_id"],
        "split": seed["split"],
        "calculator": spec["name"],
        "calculator_short": spec["short"],
        "calculator_id": spec["calc_id"],
        "family": "A",
        "provenance": {
            "note": "published MedCalc-Bench note, unedited outside the injection",
            "question": f"MedCalc-Bench's own {short_name} question",
            "pairing": f"ours -- this note is not a calc {spec['calc_id']} row; no shipped "
                       f"label is used, the clean answer is recomputed from the components",
        },
        "components": dict(seed["components"], as_recorded=seed["components_as_recorded"]),
        "documented_value": {
            "quantity": spec["short"],
            "published": seed["stated_value"], "injected": injected,
            "recomputed_from_components": recomputed,
            "divergence": divergence,
            "boundaries_crossed": crossed, "boundary_name": spec["boundary_name"],
            "value_span_in_clean_note": rec["value_span"],
            "phrase": rec["text"],
        },
        "conditions": conditions,
    }


def single_edit_region(a, b):
    if a == b:
        return None
    head = 0
    while head < min(len(a), len(b)) and a[head] == b[head]:
        head += 1
    tail = 0
    while (tail < min(len(a), len(b)) - head
           and a[len(a) - 1 - tail] == b[len(b) - 1 - tail]):
        tail += 1
    return head, len(a) - tail, len(b) - tail


def verify(item, note, spec=None):
    spec = spec or DERIVED_SPECS[item["documented_value"]["quantity"]]
    fails = []
    conds = {c["condition"]: c for c in item["conditions"]}
    if conds["clean"]["note"] != note:
        fails.append("clean note is not the published note")

    v0, v1 = item["documented_value"]["value_span_in_clean_note"]
    region = single_edit_region(note, conds["contradiction"]["note"])
    if region is None:
        fails.append("contradiction note is identical to clean")
    else:
        head, a_end, _ = region
        if head < v0 or a_end > v1:
            fails.append("edit reaches outside the documented value")

    if conds["contradiction"]["note"] != conds["resolvable"]["note"]:
        fails.append("contradiction and resolvable notes are not byte-identical")
    if conds["contradiction"]["question"] == conds["resolvable"]["question"]:
        fails.append("resolvable question carries no cue")
    for word in construct.CUE_BLOCKLIST:
        if word in conds["contradiction"]["note"].lower() and word not in note.lower():
            fails.append(f"injection introduces the cue word {word!r}")

    # The components must survive the edit untouched, or the contradiction is not
    # between the value and its own components any more.
    #
    # Counted on word boundaries, not as bare substrings. A bicarbonate of 7
    # occurs inside every 7 in the note -- dates, other labs, the digits of the
    # value being rewritten -- and a substring count made two perfectly good
    # anion-gap items fail on a component that had not moved at all.
    for value, unit in item["components"]["as_recorded"].values():
        token = construct.fmt(value)
        pattern = rf"(?<!\d){re.escape(token)}(?!\d)"
        if len(re.findall(pattern, note)) != len(
                re.findall(pattern, conds["contradiction"]["note"])):
            fails.append(f"component {token} changed count across the edit")

    # The checker must fire on the contradiction and stay silent on the clean note.
    wanted = spec["checker_quantity"].strip().lower()

    def findings(text):
        return [f for f in checker.check(text)["findings"]
                if f.get("check") == "derived_value"
                and str(f.get("quantity", "")).strip().lower() == wanted]
    if not findings(conds["contradiction"]["note"]):
        fails.append("contradiction does not trip the deterministic checker")
    if findings(note):
        fails.append(f"published note already trips the checker on {wanted}")
    return fails


def digest(seeds):
    payload = json.dumps([[s["note_id"], s["stated_value"], s["recomputed_value"]]
                          for s in seeds], sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def paths_for(key):
    """BMI keeps the original filenames; anything added writes beside it."""
    return (SEEDS, OUT) if key == "bmi" else (SEEDS_FOR(key), OUT_FOR(key))


def do_select(target, key="bmi"):
    spec = DERIVED_SPECS[key]
    seeds_path, _ = paths_for(key)
    entries = by_note(load_rows())
    kept, reasons = [], {}
    for e in entries:
        rec, why = screen(e, spec)
        if rec:
            kept.append(rec)
        else:
            reasons[why] = reasons.get(why, 0) + 1
    ordered = ([c for c in kept if c["split"] == "test"]
               + [c for c in kept if c["split"] == "train"])
    chosen = ordered[:target]
    for c in chosen:
        c.pop("value_span_record", None)
    natural = reasons.get(
        f"documented {spec['name']} already disagrees with its own components", 0)
    out = {"calculator": spec["name"], "calculator_id": spec["calc_id"],
           "quantity": key, "family": "A",
           "n_notes_screened": len(entries), "n_eligible": len(kept),
           "n_selected": len(chosen), "rejections": reasons,
           "natural_family_a_cases": natural,
           "seeds_digest": digest(chosen), "seeds": chosen}
    json.dump(out, open(seeds_path, "w"), indent=2)
    print(f"[{key}] notes screened {len(entries)}   eligible {len(kept)}   "
          f"selected {len(chosen)}   natural cases {natural}")
    for k, v in sorted(reasons.items(), key=lambda x: -x[1])[:6]:
        print(f"   rejected {v:5}  {k}")
    print(f"   digest {out['seeds_digest'][:16]}   wrote {os.path.relpath(seeds_path, ROOT)}")


def do_build(key="bmi"):
    spec = DERIVED_SPECS[key]
    seeds_path, out_path = paths_for(key)
    if not os.path.exists(seeds_path):
        sys.exit(f"no frozen seeds. Run: python3 family_a.py --select --quantity {key}")
    suite = construct.run_regression_suite()
    if not suite["passed"]:
        print(suite.get("output", ""))
        sys.exit("Refusing to build. Known extraction failures must pass first.")

    frozen = json.load(open(seeds_path))
    notes = {}
    for e in by_note(load_rows()):
        notes[e["note_id"]] = e["note"]

    items, failures = [], []
    for seed in frozen["seeds"]:
        note = notes[seed["note_id"]]
        try:
            seed = dict(seed, value_span_record=spans.find_derived(note, key))
            item = build_one(seed, note, spec)
            bad = verify(item, note, spec)
            if bad:
                failures.append({"seed": seed["note_id"], "failures": bad})
                continue
            items.append(item)
        except (construct.BuildError, spans.NotFound, spans.Ambiguous) as exc:
            failures.append({"seed": seed["note_id"], "failures": [str(exc)]})

    doc = {"family": "A", "calculator": spec["name"], "quantity": key,
           "seeds_digest": frozen["seeds_digest"],
           "regression_suite": {k: suite[k] for k in ("passed", "n_tests", "detail")},
           "n_seeds_attempted": len(frozen["seeds"]), "n_seeds_built": len(items),
           "n_items": sum(len(i["conditions"]) for i in items),
           "conditions": ["clean", "contradiction", "resolvable"],
           "construction_rules": {
               "minimal_edit": f"only the documented {spec['name']}'s digits are rewritten",
               "second_value": f"must diverge by more than {MIN_DIVERGENCE:.0%} and cross a "
                               f"{spec['boundary_name']} boundary {spec['boundaries']}",
               "resolvable_note": "byte-identical to the contradiction; the cue is appended "
                                  "to the question so the note is held fixed",
           },
           "failures": failures, "items": items}
    json.dump(doc, open(out_path, "w"), indent=2)
    print(f"[{key}] seeds {len(frozen['seeds'])}   built {len(items)}   "
          f"items {doc['n_items']}")
    for f in failures[:6]:
        print(f"   FAILED {f['seed']}: {f['failures']}")
    print(f"   wrote {os.path.relpath(out_path, ROOT)}")
    return 1 if failures else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--select", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--target", type=int, default=TARGET_SEEDS)
    ap.add_argument("--quantity", default="bmi",
                    choices=sorted(DERIVED_SPECS) + ["all"],
                    help="which derived value to build; 'all' does each in turn")
    args = ap.parse_args()
    keys = sorted(DERIVED_SPECS) if args.quantity == "all" else [args.quantity]
    if args.select:
        for k in keys:
            do_select(args.target, k)
        return 0
    if args.build:
        return max(do_build(k) for k in keys)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
