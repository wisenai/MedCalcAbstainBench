#!/usr/bin/env python3
"""Prove that every mapped criterion of the rule-based scores is actually read.


The rule-based scores read their criteria as `params.get(key)` or `'key' in
params`, so a key we map wrongly does not raise. It reads as "criterion absent",
the score comes out plausible and wrong, and nothing anywhere says so. That is
the exact failure that produced a 41.2% apparent label-mismatch rate in ,
which turned out to be our own unmapped keys rather than anything wrong with
MedCalc.

Family C's whole premise is that denying a criterion changes the score. So the
mapping has to be established rather than asserted, and the test is behavioural:

  for each criterion, on each real case that states it
      compute the score with the criterion present
      compute it again with the criterion absent
      the two must differ

A criterion that can be flipped without moving the total is either mapped to a
name the implementation never reads, or is not scored at all. Either way it
cannot carry a Family C item, and this refuses to let it.

The converse matters too and is checked: the score computed from the shipped
entities must reproduce MedCalc's own shipped answer. A mapping can be
self-consistent and still be wrong about which criterion is which; agreeing with
the published label on hundreds of cases is what rules that out.

Usage:  python3 verify_criteria.py
"""
import ast
import contextlib
import csv
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "audit"))

import entities      # noqa: E402
import calculators   # noqa: E402

csv.field_size_limit(10 ** 7)

MEDCALC = os.path.join(ROOT, "data", "medcalc")
OUT = os.path.join(ROOT, "data", "criteria_verification.json")

NAMES = {4: "CHA2DS2-VASc", 45: "CURB-65", 8: "Wells' PE"}


def load(calc_id):
    rows = []
    for split in ("test", "train"):
        path = os.path.join(MEDCALC, f"{split}_data.csv")
        with open(path) as fh:
            for r in csv.DictReader(fh):
                if r.get("Calculator ID") == str(calc_id):
                    r["_split"] = split
                    rows.append(r)
    return rows


def build_params(row, calc_id):
    """Translate one shipped row into the parameter dict the implementation reads."""
    try:
        shipped = ast.literal_eval(row["Relevant Entities"])
    except (ValueError, SyntaxError):
        return None
    params = {}
    for display, value in shipped.items():
        internal = entities.CRITERIA.get(calc_id, {}).get(display)
        if internal is None:
            internal = entities.ALIASES.get(display)
        if internal is None:
            continue
        params[internal] = value
    return params


def score(calc_id, params):
    with contextlib.redirect_stdout(io.StringIO()):
        return float(calculators.call(calc_id, params)["Answer"])


def check_reproduces(calc_id, rows):
    """Does the mapping reproduce MedCalc's own shipped answers?"""
    agree = disagree = skipped = 0
    examples = []
    needed = set(entities.RULE_BASED_REQUIRED.get(calc_id, []))
    for row in rows:
        params = build_params(row, calc_id)
        if params is None or not needed <= set(params):
            skipped += 1
            continue
        try:
            got = score(calc_id, params)
            want = float(row["Ground Truth Answer"])
        except Exception:
            skipped += 1
            continue
        if abs(got - want) < 1e-6:
            agree += 1
        else:
            disagree += 1
            if len(examples) < 5:
                examples.append({"note_id": row["Note ID"], "got": got, "shipped": want})
    return {"agree": agree, "disagree": disagree, "skipped": skipped,
            "examples": examples}


def check_load_bearing(calc_id, rows):
    """Flip each criterion where a case states it; the score must move."""
    out = {}
    needed = set(entities.RULE_BASED_REQUIRED.get(calc_id, []))
    for display, internal in entities.CRITERIA.get(calc_id, {}).items():
        moved = unmoved = tested = 0
        example = None
        for row in rows:
            params = build_params(row, calc_id)
            if params is None or internal not in params or not needed <= set(params):
                continue
            present = dict(params)
            absent = {k: v for k, v in params.items() if k != internal}
            try:
                a, b = score(calc_id, present), score(calc_id, absent)
            except Exception:
                continue
            tested += 1
            if abs(a - b) > 1e-9:
                moved += 1
                if example is None:
                    example = {"note_id": row["Note ID"], "with": a, "without": b}
            else:
                unmoved += 1
            if tested >= 40:
                break
        out[display] = {"internal": internal, "cases_tested": tested,
                        "score_moved": moved, "score_unmoved": unmoved,
                        "load_bearing": tested > 0 and moved > 0,
                        "example": example}
    return out


def main():
    if not os.path.isdir(MEDCALC):
        sys.exit("data/medcalc missing. Run: python3 fetch_medcalc.py")

    report, failures = {}, []
    for calc_id in sorted(entities.CRITERIA):
        rows = load(calc_id)
        repro = check_reproduces(calc_id, rows)
        crit = check_load_bearing(calc_id, rows)
        report[calc_id] = {"name": NAMES.get(calc_id, str(calc_id)),
                           "rows": len(rows), "reproduces_shipped": repro,
                           "criteria": crit}

        print(f"\n=== calc {calc_id}  {NAMES.get(calc_id)}  ({len(rows)} rows) ===")
        total = repro["agree"] + repro["disagree"]
        pct = (100.0 * repro["agree"] / total) if total else 0.0
        print(f"  reproduces shipped answer: {repro['agree']}/{total} ({pct:.1f}%)"
              f"   skipped {repro['skipped']}")
        for ex in repro["examples"]:
            print(f"     disagree {ex['note_id']}: ours {ex['got']} vs shipped {ex['shipped']}")
        if repro["disagree"]:
            failures.append(f"calc {calc_id}: {repro['disagree']} answers disagree with the "
                            f"shipped label")
        for display, c in crit.items():
            mark = "ok " if c["load_bearing"] else "DEAD"
            print(f"  {mark} {c['internal']:26} moved {c['score_moved']:3}/"
                  f"{c['cases_tested']:<3} <- {display[:44]}")
            if not c["load_bearing"]:
                failures.append(f"calc {calc_id}: criterion {display!r} -> "
                                f"{c['internal']!r} never moves the score")

    json.dump(report, open(OUT, "w"), indent=2)
    print(f"\nwrote {os.path.relpath(OUT, ROOT)}")
    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f"  {f}")
        return 1
    print("\nEvery mapped criterion is load-bearing and every score reproduces.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
