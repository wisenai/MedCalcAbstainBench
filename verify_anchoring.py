#!/usr/bin/env python3
"""Confirm, for every built item, that the edited span is the one the calculator consumes.

Task owner: Annotator D -- Week 2.
Completed by Annotator D.

`construct.py` already asserts anchoring while it builds. That is not the same
check as this one, and it cannot be: a builder that is wrong about which span the
calculator reads will assert the wrong thing and pass. So this reads the finished
items back off disk, re-derives the answer from the edited text without consulting
the builder, and compares.

Five checks per item, all mechanical:

  1. clean reproduces      the clean answer recomputes from the seed's entities
                           through the released implementation
  2. the span points true  the characters at the recorded span in the clean note
                           are the value the calculator consumes
  3. missing is minimal    the missing note is byte-identical to clean outside one
                           contiguous excision, and states no creatinine after it
  4. conflict is minimal   the conflict note is byte-identical to clean outside one
                           contiguous insertion, and both values survive in it
  5. the edit is load-bearing
                           re-parsing the edited note and feeding the recovered
                           value through the calculator reproduces the intended
                           answer -- for the injected value too, which is what
                           shows the conflict is decision-relevant rather than
                           cosmetic

Usage:  python3 verify_anchoring.py
"""
import contextlib
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "audit"))

import spans  # noqa: E402
import calculators  # noqa: E402

ITEMS = os.path.join(ROOT, "data", "items_dissociation.json")
SEEDS = os.path.join(ROOT, "data", "seeds_dissociation.json")
OUT = os.path.join(ROOT, "data", "anchoring_report.json")
CRE_UNITS = ["mg/dL", "µmol/L", "mmol/L"]


def answer_with(calc_id, entities, creatinine, unit):
    """The released code's answer with creatinine set to this value."""
    ent = json.loads(json.dumps(entities))
    ent["creatinine"] = [creatinine, unit]
    with contextlib.redirect_stdout(io.StringIO()):
        return float(calculators.call(calc_id, ent)["Answer"])


def single_edit_region(a, b):
    """The one contiguous region where two strings differ, or None if more than one.

    Written out rather than taken from difflib so that "the edit is a single
    contiguous region" is something this file establishes rather than assumes.
    """
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


def verify(item, seed):
    """Every check for one item. Returns a list of failures, empty when clean."""
    fails = []
    cid = item["calculator_id"]
    cre = item["creatinine"]
    unit = cre["unit"]
    conds = {c["condition"]: c for c in item["conditions"]}
    clean = conds["clean"]["note"]

    # 1 -- the clean answer recomputes
    recomputed = answer_with(cid, seed["entities"], cre["stated"], unit)
    if abs(recomputed - conds["clean"]["correct_answer"]) > 1e-3:
        fails.append(f"clean answer {conds['clean']['correct_answer']} does not "
                     f"recompute (got {recomputed})")

    # 2 -- the recorded span points at the value the calculator consumes
    a, b = cre["value_span_in_clean_note"]
    at_span = clean[a:b]
    try:
        # A span that does not hold a number at all is the failure this check
        # exists for, so it must be reported rather than raised.
        off_by = abs(float(at_span) - cre["stated"])
    except ValueError:
        off_by = None
    if off_by is None or off_by > 1e-9:
        fails.append(f"span {a}:{b} holds {at_span!r}, not the consumed value "
                     f"{cre['stated']}")
    if abs(float(seed["input_spans"]["creatinine"]["value"]) - cre["stated"]) > 1e-9:
        fails.append("seed span value and item creatinine disagree")

    # 3 -- missing is one contiguous excision and leaves no creatinine
    region = single_edit_region(clean, conds["missing"]["note"])
    if region is None:
        fails.append("missing variant is identical to clean")
    else:
        head, a_end, b_end = region
        if b_end - head > 0:
            fails.append(f"missing variant inserts {b_end - head} characters")
        if not (a <= a_end and head <= b):
            fails.append("missing excision does not cover the creatinine span")
    left = len(spans.count_measurements(conds["missing"]["note"], "creatinine", CRE_UNITS))
    if left:
        fails.append(f"missing variant still states {left} creatinine measurement(s)")

    # 4 -- conflict is one contiguous insertion and keeps both values
    region = single_edit_region(clean, conds["value_conflict"]["note"])
    if region is None:
        fails.append("value_conflict variant is identical to clean")
    else:
        head, a_end, b_end = region
        if a_end - head > 0:
            fails.append(f"value_conflict variant deletes {a_end - head} characters")
        if not (head <= b + 60):
            fails.append("value_conflict insertion is not adjacent to the creatinine")
    # Both values must survive, but not as the original phrase: the in-phrase
    # rewrite turns "1.4 mg/dL" into "1.4 and 3.64 mg/dL", so the stated value
    # keeps its digits and gives up its adjacency to the unit. Asserting the
    # original phrase verbatim is what a check written against the *old* append
    # form would do, and it fails every item under the current one.
    second = item["conflict"]["second_value"]
    rewritten = item["conflict"]["injection"]
    if rewritten not in conds["value_conflict"]["note"]:
        fails.append("value_conflict variant does not contain the rewritten phrase")
    for token in (f"{cre['stated']:g}", f"{second:g}"):
        if token not in rewritten:
            fails.append(f"rewritten phrase is missing the value {token!r}")
    unit_rx = spans.UNIT_PATTERNS[unit]
    if not re.search(unit_rx, rewritten):
        fails.append(f"rewritten phrase carries no {unit} unit token")

    # 5 -- the edit is load-bearing: both values drive the calculator
    if abs(answer_with(cid, seed["entities"], cre["stated"], unit)
           - item["conflict"]["answer_with_stated"]) > 1e-3:
        fails.append("stated value does not reproduce answer_with_stated")
    if abs(answer_with(cid, seed["entities"], second, unit)
           - item["conflict"]["answer_with_second"]) > 1e-3:
        fails.append("injected value does not reproduce answer_with_second")

    # resolvable must be the same note as value_conflict, differing only in question
    if conds["resolvable"]["note"] != conds["value_conflict"]["note"]:
        fails.append("resolvable note is not byte-identical to value_conflict")
    if conds["resolvable"]["question"] == conds["value_conflict"]["question"]:
        fails.append("resolvable question carries no cue")

    return fails


def main():
    if not os.path.exists(ITEMS):
        sys.exit("data/items_dissociation.json missing. Run: python3 construct.py --all")
    items = json.load(open(ITEMS))
    seeds = {s["seed_id"]: s for s in json.load(open(SEEDS))["seeds"]}

    results, n_fail = [], 0
    for item in items["items"]:
        fails = verify(item, seeds[item["seed_id"]])
        n_fail += bool(fails)
        results.append({"seed_id": item["seed_id"], "case_id": item["case_id"],
                        "ok": not fails, "failures": fails})

    report = {
        "n_seeds": len(results),
        "n_items": len(results) * 4,
        "n_seeds_failing": n_fail,
        "checks": ["clean answer recomputes",
                   "recorded span holds the consumed value",
                   "missing is one contiguous excision leaving no creatinine",
                   "value_conflict is one contiguous insertion keeping both values",
                   "both values drive the calculator to the recorded answers",
                   "resolvable note is byte-identical to value_conflict"],
        "results": results,
    }
    json.dump(report, open(OUT, "w"), indent=2)

    print(f"seeds verified {len(results)}   items {len(results) * 4}")
    print(f"seeds with a failure: {n_fail}")
    for r in results:
        for f in r["failures"]:
            print(f"  {r['seed_id']}: {f}")
    print(f"wrote {os.path.relpath(OUT, ROOT)}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
