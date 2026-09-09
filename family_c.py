#!/usr/bin/env python3
"""Build Family C: a scored criterion asserted and later explicitly denied.


The note states a criterion the score reads -- `a past medical history of
hypertension` -- and a later sentence denies it. Nothing in the note says which
is right, and the two give different scores, so declining is the defensible move.

WHAT THIS FAMILY DOES DIFFERENTLY, AND WHY IT MATTERS.

Families A and B rewrite a value that is already there. C **appends a sentence**,
which is a different edit shape, and it is the case the item spec flagged as the
one that might not fit the minimal-edit rule. It does fit, but only once the rule
is read properly: minimal edit has never meant "few characters", it means "the
note outside the edit is untouched and the edit is one contiguous region". An
insertion satisfies that as cleanly as a rewrite. What changes is the check --
there is no value span to compare against, so the assertion is that the insertion
sits at a sentence boundary and that every character of the original survives.

The `resolvable` cue also points the other way here than in the other families.
Elsewhere it names the originally stated value and so recovers the clean answer.
Here it names the **denial**, because "asserted and later denied" makes the later
statement the one a reader would take as superseding, and because that makes the
cued answer differ from the clean answer -- so a model that ignores the injected
sentence gets it wrong, which is what makes the arm a parsing probe rather than a
formality.

Only criteria a keyword locator can carry are used; `spans.USABLE_CRITERIA`
records which, and the six exclusions are argued there rather than here.

Usage:  python3 family_c.py --select
        python3 family_c.py --build
"""
import argparse
import ast
import contextlib
import csv
import hashlib
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "audit"))

import spans        # noqa: E402
import construct    # noqa: E402
import entities     # noqa: E402
import calculators  # noqa: E402

csv.field_size_limit(10 ** 7)

SEEDS = os.path.join(ROOT, "data", "seeds_family_c.json")
OUT = os.path.join(ROOT, "data", "items_family_c.json")
MEDCALC = os.path.join(ROOT, "data", "medcalc")

CALCULATORS = {4: "CHA2DS2-VASc", 45: "CURB-65", 8: "Wells' PE"}
SHORT = {4: "cha2ds2_vasc", 45: "curb_65", 8: "wells_pe"}

# Per calculator, so the thin ones are not crowded out by CHA2DS2-VASc's supply.
TARGET_PER_CALCULATOR = {4: 20, 8: 6, 45: 4}

# How the denial is worded per criterion. Plain clinical register, no cue words,
# and phrased so our own locator reads it as a denial rather than a second
# assertion -- which is also what makes the note contain exactly one of each.
DENIALS = {
    "hypertension": "The patient has no history of hypertension.",
    "diabetes": "The patient has no history of diabetes.",
    "chf": "The patient has no history of congestive heart failure.",
    "stroke": "The patient has no history of stroke.",
    "tia": "The patient has no history of transient ischemic attacks.",
    "thromboembolism": "The patient has no history of thromboembolism.",
    "vascular_disease": "The patient has no history of vascular disease.",
    "confusion": "The patient is not confused.",
    "hemoptysis": "The patient has no hemoptysis.",
    "clinical_dvt": "There are no clinical signs or symptoms of deep vein thrombosis.",
}


def load_rows(calc_id):
    if not os.path.isdir(MEDCALC):
        sys.exit("data/medcalc missing. Run: python3 fetch_medcalc.py")
    rows = []
    for split in ("test", "train"):
        with open(os.path.join(MEDCALC, f"{split}_data.csv")) as fh:
            for r in csv.DictReader(fh):
                if r.get("Calculator ID") == str(calc_id):
                    r["_split"] = split
                    rows.append(r)
    return rows


def to_params(row, calc_id):
    try:
        shipped = ast.literal_eval(row["Relevant Entities"])
    except (ValueError, SyntaxError):
        return None
    params = {}
    for display, value in shipped.items():
        internal = (entities.CRITERIA.get(calc_id, {}).get(display)
                    or entities.ALIASES.get(display))
        if internal:
            params[internal] = value
    return params


def score(calc_id, params):
    with contextlib.redirect_stdout(io.StringIO()):
        return float(calculators.call(calc_id, params)["Answer"])


def screen(row, calc_id):
    note = row["Patient Note"]
    params = to_params(row, calc_id)
    if params is None:
        return None, "entities do not parse"
    needed = set(entities.RULE_BASED_REQUIRED.get(calc_id, []))
    if not needed <= set(params):
        return None, "a continuous input the score needs is missing"

    display_of = {v: k for k, v in entities.CRITERIA[calc_id].items()}
    candidates = []
    for internal in entities.CRITERIA[calc_id].values():
        if internal not in spans.USABLE_CRITERIA or internal not in DENIALS:
            continue
        if not params.get(internal):
            continue                       # the score does not have it
        try:
            rec = spans.find_criterion(note, internal)
        except (spans.NotFound, spans.Ambiguous):
            continue                       # the note does not assert it exactly once
        with_it = score(calc_id, params)
        without = score(calc_id, {k: v for k, v in params.items() if k != internal})
        if abs(with_it - without) < 1e-9:
            continue                       # denying it would change nothing
        candidates.append({"criterion": internal, "display": display_of[internal],
                           "span": rec, "score_with": with_it, "score_without": without})

    if not candidates:
        return None, "no criterion is asserted once, scored, and decision-relevant"

    # One criterion per note, chosen by the largest score movement so the item is
    # as decision-relevant as the note allows. Ties break on name, for determinism.
    best = max(candidates, key=lambda c: (abs(c["score_with"] - c["score_without"]),
                                          c["criterion"]))
    return {"note_id": row["Note ID"], "split": row["_split"], "calculator_id": calc_id,
            "question": row["Question"], "published_answer": row["Ground Truth Answer"],
            "criterion": best["criterion"], "display": best["display"],
            "score_with": best["score_with"], "score_without": best["score_without"],
            "n_candidates": len(candidates), "span": best["span"]}, None


def insert_denial(note, span_record, sentence):
    """Put the denial immediately after the sentence that made the assertion.

    Appending at the very end of the note would work too, but it puts an unknown
    amount of text between the two statements and makes distance a hidden
    variable across items. Directly after the asserting sentence keeps that
    constant, and keeps the insertion one contiguous region at a boundary.
    """
    _, clause_end = span_record["clause_span"]
    end = clause_end
    while end < len(note) and note[end] in ".;":
        end += 1
    if end >= len(note):
        return note.rstrip() + " " + sentence, len(note.rstrip()) + 1
    return note[:end] + " " + sentence + note[end:], end + 1


def cue_for(criterion):
    return (" The later entry supersedes the earlier one: treat the patient as "
            f"not having {criterion.replace('_', ' ')} for this calculation.")


def build_one(seed, note):
    rec = seed["span"]
    denial = DENIALS[seed["criterion"]]
    contradicted, insert_at = insert_denial(note, rec, denial)
    if contradicted == note:
        raise construct.BuildError("denial did not change the note")

    calc_id = seed["calculator_id"]
    question = seed["question"]
    conditions = [
        {"item_id": f"{SHORT[calc_id]}-{seed['note_id']}_clean",
         "condition": "clean", "note": note, "question": question,
         "correct_action": "compute", "correct_answer": seed["score_with"],
         "rationale": "the note as published; it asserts the criterion once and never "
                      "denies it, so nothing is in dispute"},
        {"item_id": f"{SHORT[calc_id]}-{seed['note_id']}_contradiction",
         "condition": "contradiction", "note": contradicted, "question": question,
         "correct_action": "flag", "correct_answer": None,
         "rationale": f"the note asserts {seed['criterion']} and then denies it; the two "
                      f"give {seed['score_with']} and {seed['score_without']}, and nothing "
                      f"in the note says which holds"},
        {"item_id": f"{SHORT[calc_id]}-{seed['note_id']}_resolvable",
         "condition": "resolvable", "note": contradicted,
         "question": question + cue_for(seed["criterion"]),
         "correct_action": "compute", "correct_answer": seed["score_without"],
         "rationale": "byte-identical note to the contradiction, plus a cue naming the "
                      "later entry as governing; the cued answer differs from the clean "
                      "answer, so answering it correctly requires having read the denial"},
    ]
    return {
        "seed_id": f"{SHORT[calc_id]}-{seed['note_id']}",
        "case_id": seed["note_id"], "split": seed["split"],
        "calculator": CALCULATORS[calc_id], "calculator_short": SHORT[calc_id],
        "calculator_id": str(calc_id), "family": "C",
        "criterion": {
            "internal": seed["criterion"], "shipped_as": seed["display"],
            "asserted_text": rec["value_text"],
            "asserted_span_in_clean_note": rec["value_span"],
            "asserting_sentence": rec["clause_text"],
            "other_eligible_criteria_in_note": seed["n_candidates"] - 1,
        },
        "injection": {
            "denial": denial, "inserted_at": insert_at,
            "score_with_criterion": seed["score_with"],
            "score_without_criterion": seed["score_without"],
            "points_at_stake": abs(seed["score_with"] - seed["score_without"]),
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


def verify(item, note):
    """The minimal-edit rule, restated for an insertion."""
    fails = []
    conds = {c["condition"]: c for c in item["conditions"]}
    if conds["clean"]["note"] != note:
        fails.append("clean note is not the published note")

    region = single_edit_region(note, conds["contradiction"]["note"])
    if region is None:
        fails.append("contradiction note is identical to clean")
    else:
        head, a_end, b_end = region
        if a_end - head > 0:
            fails.append(f"the edit deletes {a_end - head} characters; it must only insert")

        # Everything outside one contiguous insertion must survive verbatim. This
        # is the real check, and it is alignment-independent.
        rebuilt = (conds["contradiction"]["note"][:head]
                   + conds["contradiction"]["note"][b_end:])
        if rebuilt != note:
            fails.append("the note outside the insertion is not byte-identical")

        # The inserted region is NOT compared to the denial character for
        # character, because which characters count as inserted is not unique.
        # Inserting " The patient is not confused." before a sentence that also
        # begins " The" lets the common-prefix scan slide the boundary, and the
        # region comes back as " patient is not confused. The" -- the same
        # insertion under a different, equally correct alignment. Asserting the
        # exact region failed 9 of 30 builds that were in fact perfectly formed.
        # What is actually required is that the note grew by exactly the denial
        # and a separator, and that the denial is present.
        grew = len(conds["contradiction"]["note"]) - len(note)
        if grew != len(item["injection"]["denial"]) + 1:
            fails.append(f"note grew by {grew} characters, not by the denial plus one space")
        if item["injection"]["denial"] not in conds["contradiction"]["note"]:
            fails.append("the denial does not appear in the contradiction note")

    if conds["contradiction"]["note"] != conds["resolvable"]["note"]:
        fails.append("contradiction and resolvable notes are not byte-identical")
    if conds["contradiction"]["question"] == conds["resolvable"]["question"]:
        fails.append("resolvable question carries no cue")
    for word in construct.CUE_BLOCKLIST:
        if word in item["injection"]["denial"].lower():
            fails.append(f"the denial contains the cue word {word!r}")

    # After the injection the note must still assert the criterion exactly once,
    # and the denial must read as a denial rather than as a second assertion.
    key = item["criterion"]["internal"]
    asserted = spans.count_criterion_mentions(conds["contradiction"]["note"], key)
    if len(asserted) != 1:
        fails.append(f"after injection the note asserts {key} {len(asserted)} times, not once")

    # The two readings must give different scores, or there is nothing at stake.
    if item["injection"]["points_at_stake"] <= 0:
        fails.append("denying the criterion does not change the score")
    if conds["resolvable"]["correct_answer"] == conds["clean"]["correct_answer"]:
        fails.append("the cued answer equals the clean answer, so the cue proves nothing")
    return fails


def round_robin(candidates, target):
    """Take in rotation across criteria, test split first, rather than in corpus order.

    Straight corpus order gave 15 hypertension items out of 30, because
    hypertension is simply the commonest criterion in the substrate. A family
    half made of one criterion measures that criterion, not the family. This is
    the same mistake as the  worked ten, which came out all Cockcroft-Gault
    until they were drawn in rotation, and it gets the same fix.

    Within each criterion the order is untouched -- test split first, then corpus
    order -- so nothing is chosen for how it behaves.
    """
    buckets = {}
    for c in candidates:
        buckets.setdefault(c["criterion"], {"test": [], "train": []})[c["split"]].append(c)
    queues = {k: v["test"] + v["train"] for k, v in buckets.items()}

    out = []
    while len(out) < target and any(queues.values()):
        for key in sorted(queues):
            if len(out) >= target:
                break
            if queues[key]:
                out.append(queues[key].pop(0))
    return out


def digest(seeds):
    payload = json.dumps([[s["note_id"], s["calculator_id"], s["criterion"]]
                          for s in seeds], sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def do_select():
    chosen, reasons, per_calc = [], {}, {}
    for calc_id, target in TARGET_PER_CALCULATOR.items():
        rows = load_rows(calc_id)
        kept = []
        for r in rows:
            rec, why = screen(r, calc_id)
            if rec:
                kept.append(rec)
            else:
                reasons[f"calc {calc_id}: {why}"] = reasons.get(f"calc {calc_id}: {why}", 0) + 1
        take = round_robin(kept, target)
        per_calc[calc_id] = {"eligible": len(kept), "selected": len(take), "target": target}
        chosen.extend(take)
    for c in chosen:
        c.pop("span", None)
    out = {"family": "C", "calculators": CALCULATORS,
           "per_calculator": per_calc, "rejections": reasons,
           "n_selected": len(chosen), "seeds_digest": digest(chosen), "seeds": chosen}
    json.dump(out, open(SEEDS, "w"), indent=2)
    for cid, p in per_calc.items():
        short = "  SHORT" if p["selected"] < p["target"] else ""
        print(f"  calc {cid:3} {CALCULATORS[cid]:14} eligible {p['eligible']:4}  "
              f"selected {p['selected']:3}/{p['target']}{short}")
    print(f"  total {len(chosen)}   digest {out['seeds_digest'][:16]}")
    for k, v in sorted(reasons.items(), key=lambda x: -x[1])[:6]:
        print(f"     rejected {v:4}  {k}")
    print(f"wrote {os.path.relpath(SEEDS, ROOT)}")


def do_build():
    if not os.path.exists(SEEDS):
        sys.exit("no frozen seeds. Run: python3 family_c.py --select")
    suite = construct.run_regression_suite()
    if not suite["passed"]:
        print(suite.get("output", ""))
        sys.exit("Refusing to build. Known extraction failures must pass first.")
    print(f"regression suite: {suite['n_tests']} tests pass")

    frozen = json.load(open(SEEDS))
    notes = {}
    for calc_id in CALCULATORS:
        for r in load_rows(calc_id):
            notes[(str(calc_id), r["Note ID"])] = r["Patient Note"]

    items, failures = [], []
    for seed in frozen["seeds"]:
        note = notes[(str(seed["calculator_id"]), seed["note_id"])]
        try:
            seed = dict(seed, span=spans.find_criterion(note, seed["criterion"]))
            item = build_one(seed, note)
            bad = verify(item, note)
            if bad:
                failures.append({"seed": seed["note_id"], "failures": bad})
                continue
            items.append(item)
        except (construct.BuildError, spans.NotFound, spans.Ambiguous) as exc:
            failures.append({"seed": seed["note_id"], "failures": [str(exc)]})

    by_calc = {}
    for i in items:
        by_calc[i["calculator"]] = by_calc.get(i["calculator"], 0) + 1
    doc = {"family": "C", "calculators": CALCULATORS,
           "seeds_digest": frozen["seeds_digest"],
           "regression_suite": {k: suite[k] for k in ("passed", "n_tests", "detail")},
           "n_seeds_attempted": len(frozen["seeds"]), "n_seeds_built": len(items),
           "n_items": sum(len(i["conditions"]) for i in items),
           "items_per_calculator": by_calc,
           "conditions": ["clean", "contradiction", "resolvable"],
           "construction_rules": {
               "minimal_edit": "one contiguous insertion at a sentence boundary; every "
                               "character of the published note survives",
               "denial": "explicit, plain register, carries no cue word, and reads as a "
                         "denial rather than a second assertion",
               "resolvable_note": "byte-identical to the contradiction; the cue names the "
                                  "later entry as governing, so the cued answer differs "
                                  "from the clean answer",
           },
           "failures": failures, "items": items}
    json.dump(doc, open(OUT, "w"), indent=2)
    print(f"seeds {len(frozen['seeds'])}   built {len(items)}   items {doc['n_items']}")
    print(f"   per calculator: {by_calc}")
    for f in failures[:8]:
        print(f"   FAILED {f['seed']}: {f['failures']}")
    print(f"wrote {os.path.relpath(OUT, ROOT)}")
    return 1 if failures else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--select", action="store_true")
    ap.add_argument("--build", action="store_true")
    args = ap.parse_args()
    if args.select:
        do_select()
        return 0
    if args.build:
        return do_build()
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
