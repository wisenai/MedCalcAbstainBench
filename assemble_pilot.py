#!/usr/bin/env python3
"""Join the cached completions to the items they were generated from.

what nothing owned. `run.py` and the cache are a contributor's; `score.py` and `stats.py`
are a contributor's. Neither clause covers the step in between -- walking the cache,
working out which item and condition each completion belongs to, and handing the
result over as one table -- so scoring could not start even though both halves
had been built. This file is only that step.

What it deliberately does NOT do, because those are a contributor's  clauses:
assign the three-way label, call the judge, decide whether a numeric answer is
correct, or compute any statistic. The two columns those produce are emitted
empty, with the ground truth alongside them so `score.py` can be pointed at this
file and fill them in.

The join is exact, not heuristic. `run.py` keys the cache as

    sha256(f"{model}_{item_id}_{prompt_id}_{format}")

and item_id is f"{seed_id}_{condition}", so every cell's filename can be computed
from the frozen item set rather than recovered by matching note text back out of
the prompt. That matters: the notes in `value_conflict` and `resolvable` are
byte-identical by construction, so text matching cannot tell those two conditions
apart, and a join that silently confuses them would corrupt the one comparison
the study exists to make.

Standard library only, and no API key: assembling the table must not require
credentials, or it cannot run in CI.

Usage:  python3 assemble_pilot.py
        python3 assemble_pilot.py --arm open_ended --arm neutral_exit
"""
import argparse
import csv
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, "cache")
ITEMS = os.path.join(ROOT, "data", "items_dissociation.json")
OUT_JSON = os.path.join(ROOT, "data", "pilot_completions.json")
OUT_CSV = os.path.join(ROOT, "data", "pilot_completions.csv")

CONDITIONS = ("clean", "missing", "value_conflict", "resolvable")

# (arm name, model, prompt_id, format, conditions the arm was meant to cover) as
# the pilot was actually run.
#
# The expected-conditions field is what stops "this arm has one clean cell and
# forty value_conflict cells" from reading as damage. The reasoning capture was
# only ever asked for on the value-conflict cells, so partial coverage there is
# the design; partial coverage on a pilot arm is a fault. An arm that does not
# say which cells it owns cannot tell those two apart.
#
# `format` reads "open_ended" for both open-ended arms rather than "open". That
# is how a contributor ran it, and the key is only a cache address -- the string is never
# sent to the model -- so the two arms remain comparable. It is recorded here as
# observed rather than as it perhaps should have been, because the cache is the
# artefact and guessing a tidier value would simply miss every file.
ARMS = [
    ("open_ended",   "anthropic/claude-opus-4.8", "open_ended",           "open_ended",    CONDITIONS),
    ("neutral_exit", "anthropic/claude-opus-4.8", "neutral_exit",         "open_ended",    CONDITIONS),
    ("reasoning",    "anthropic/claude-opus-4.8", "open_ended_reasoning", "open_ended",    ("value_conflict",)),
    ("smoke_open",   "openai/gpt-5-mini",         "open_ended",           "open_ended",    CONDITIONS),
    ("smoke_mcq",    "openai/gpt-5-mini",         "mcq",                  "mcq",           CONDITIONS),
    ("smoke_pal",    "openai/gpt-5-mini",         "program_aided",        "program_aided", CONDITIONS),
]

# Arms whose coverage is measured against all 40 seeds. The smoke test ran on 5.
FULL_SCALE = ("open_ended", "neutral_exit", "reasoning")

# The arms that carry the primary comparison. The smoke-test arms are a contributor's
#  harness check on 5 seeds, not pilot data, and must not be pooled with it.
PILOT_ARMS = ("open_ended", "neutral_exit")


def cache_key(model, item_id, prompt_id, fmt):
    """Reproduce run.py's addressing scheme exactly."""
    return hashlib.sha256(f"{model}_{item_id}_{prompt_id}_{fmt}".encode()).hexdigest()


def ground_truth(item, cond):
    """What a correct answer would be, and what the correct action is.

    `missing` and `value_conflict` have no correct number by construction -- the
    right move is to decline or to flag -- so the truth is None and any number is
    wrong. Recording None rather than omitting the field keeps that an assertion
    rather than an accident of a missing key.
    """
    block = next(c for c in item["conditions"] if c["condition"] == cond)
    return {
        "correct_action": block["correct_action"],
        "ground_truth": block["correct_answer"],
        "answer_unit": block["answer_unit"],
        "rationale": block["rationale"],
    }


def load_items():
    if not os.path.exists(ITEMS):
        sys.exit("data/items_dissociation.json missing. Run: python3 construct.py --all")
    doc = json.load(open(ITEMS))
    return doc, {i["seed_id"]: i for i in doc["items"]}


def assemble(arms):
    doc, items = load_items()
    seeds = list(items)
    rows, used = [], set()

    for arm, model, prompt_id, fmt, _expected in arms:
        for seed_id in seeds:
            item = items[seed_id]
            for cond in CONDITIONS:
                item_id = f"{seed_id}_{cond}"
                path = os.path.join(CACHE, cache_key(model, item_id, prompt_id, fmt) + ".json")
                if not os.path.exists(path):
                    continue
                used.add(os.path.basename(path))
                rec = json.load(open(path))
                gt = ground_truth(item, cond)
                rows.append({
                    # identity
                    "item_id": item_id,
                    "seed_id": seed_id,
                    "case_id": item["case_id"],
                    "condition": cond,
                    "variant": cond,          # the name stats.py uses
                    "arm": arm,
                    "model": rec["model"],
                    "prompt_id": prompt_id,
                    "format": fmt,
                    "calculator": item["calculator_short"],
                    "calculator_id": item["calculator_id"],
                    # truth
                    "correct_action": gt["correct_action"],
                    "ground_truth": gt["ground_truth"],
                    "answer_unit": gt["answer_unit"],
                    "answer_with_second": (item["conflict"]["answer_with_second"]
                                           if cond in ("value_conflict", "resolvable") else None),
                    # what the model said
                    "completion_text": rec["response_text"],
                    "reasoning": rec.get("reasoning"),
                    "prompt_text": rec["prompt"],
                    "input_tokens": rec.get("input_tokens"),
                    "output_tokens": rec.get("output_tokens"),
                    "cost": rec.get("cost"),
                    # left for score.py -- deliberately not filled here
                    "assigned_label": None,
                    "justification_span": None,
                    "extracted_value": None,
                    "value_correct": None,
                })
    return doc, rows, used


def orphans(used):
    """Cache files no arm addressed.

    These are completions for seeds that have since been retired -- a real one,
    `mdrd-tr3279`, was removed after its creatinine turned out to belong to the
    patient's grandmother. They must not be scored, and counting cache files
    rather than joined rows is exactly how they would sneak back in.
    """
    if not os.path.isdir(CACHE):
        return []
    every = {f for f in os.listdir(CACHE) if f.endswith(".json")}
    return sorted(every - used)


def coverage(rows, arms, n_seeds):
    """Per arm: cells found, against the cells that arm was meant to produce.

    "Complete" means every condition the arm owns is present for the same set of
    seeds, and -- for the full-scale arms -- that the set is all of them. An arm
    covering 39 of 40 seeds evenly is balanced and still short, so both halves
    have to be checked or a missing seed passes as symmetry.
    """
    out = {}
    for arm, _, _, _, expected in arms:
        sub = [r for r in rows if r["arm"] == arm]
        per = {c: len({r["seed_id"] for r in sub if r["condition"] == c}) for c in CONDITIONS}
        owned = {c: per[c] for c in expected}
        unowned = {c: per[c] for c in CONDITIONS if c not in expected and per[c]}
        balanced = len(set(owned.values())) == 1
        target = n_seeds if arm in FULL_SCALE else max(owned.values() or [0])
        out[arm] = {
            "n_rows": len(sub),
            "conditions_owned": list(expected),
            "seeds_per_condition": per,
            "seeds_outside_scope": unowned,
            "target_seeds": target,
            "complete": balanced and bool(owned) and min(owned.values()) == target,
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", action="append", dest="only",
                    help="restrict to named arm(s); default is all")
    args = ap.parse_args()

    arms = [a for a in ARMS if not args.only or a[0] in args.only]
    if not arms:
        sys.exit(f"no such arm. known: {', '.join(a[0] for a in ARMS)}")

    doc, rows, used = assemble(arms)
    n_seeds = len(doc["items"])
    cov = coverage(rows, arms, n_seeds)
    orph = orphans(used)

    report = {
        "built_utc": doc["built_utc"],
        "items_file": os.path.relpath(ITEMS, ROOT),
        "n_seeds": n_seeds,
        "substrate": doc["substrate"],
        "join": "exact, on sha256(model_itemid_promptid_format) as run.py computes it",
        "labels": "assigned_label / value_correct are intentionally empty -- score.py fills them",
        "arms": {a[0]: {"model": a[1], "prompt_id": a[2], "format": a[3],
                        "conditions_owned": list(a[4])} for a in arms},
        "pilot_arms": list(PILOT_ARMS),
        "coverage": cov,
        "n_rows": len(rows),
        "orphan_cache_files": orph,
        "rows": rows,
    }
    json.dump(report, open(OUT_JSON, "w"), indent=2)

    flat = ["item_id", "seed_id", "condition", "variant", "arm", "model", "prompt_id",
            "calculator", "correct_action", "ground_truth", "assigned_label",
            "value_correct", "output_tokens", "cost"]
    with open(OUT_CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=flat, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"items {n_seeds} seeds x {len(CONDITIONS)} conditions")
    for arm, c in cov.items():
        owned = c["conditions_owned"]
        per = c["seeds_per_condition"]
        mark = "ok " if c["complete"] else "GAP"
        shown = "  ".join(f"{k} {per[k]}/{c['target_seeds']}" for k in owned)
        extra = (f"   (+{sum(c['seeds_outside_scope'].values())} outside scope)"
                 if c["seeds_outside_scope"] else "")
        print(f"  {mark} {arm:14} {c['n_rows']:4} rows   {shown}{extra}")
    print(f"rows {len(rows)}   orphan cache files {len(orph)}")
    for o in orph[:12]:
        print(f"  orphan {o[:12]}... not addressed by any arm; retired seed")
    print(f"wrote {os.path.relpath(OUT_JSON, ROOT)} and {os.path.relpath(OUT_CSV, ROOT)}")

    # A partial pilot arm is the failure worth stopping on: it would be scored
    # and reported as though it were the whole thing.
    bad = [a for a in PILOT_ARMS if a in cov and not cov[a]["complete"]]
    if bad:
        print(f"\nincomplete pilot arm(s): {', '.join(bad)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
