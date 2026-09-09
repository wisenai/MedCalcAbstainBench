#!/usr/bin/env python3
"""Build the order-flipped twin of every dissociation value_conflict item.

Task owner: Annotator D. Requested by the mentor in revision 2:
"on dissociation value conflict notes, flip order (40 notes)".

Why this exists. In the shipped corpus the resolvable cue always names the
first-stated of the two conflicting values, so a model that reads only the
first number and ignores the second answers correctly every time. Correct
performance on resolvable is therefore weaker evidence that both values were
read than the paper claims. Flipping which value appears first, while leaving
the cue naming the same value, turns the cued value into the second-stated one.
A model attending only to the first number now gets the wrong answer.

What is held constant. The cue text, the correct answer, the calculator, and
every character of the note outside the injected phrase. Only the order of the
two numbers inside that phrase changes, so any behavioural difference is
attributable to position.

    python3 flip_order.py            # report, writes nothing
    python3 flip_order.py --build    # writes data/items_dissociation_flipped.json

Offline. No API key, no model calls.
"""
import argparse
import hashlib
import json
import os
import re
import sys

SRC = "data/items_dissociation.json"
OUT = "data/items_dissociation_flipped.json"
NUM = re.compile(r"\d+(?:\.\d+)?")


def conditions(item):
    c = item["conditions"]
    return c if isinstance(c, list) else list(c.values())


def injected_region(clean, conflict):
    """Return (start, end_in_conflict, text) for the span that differs.

    The conflict note is the clean note with one located phrase rewritten, so a
    common prefix and suffix scan isolates the rewrite exactly. No assumption is
    made about how the numbers are formatted.
    """
    i = 0
    while i < min(len(clean), len(conflict)) and clean[i] == conflict[i]:
        i += 1
    j = 0
    while (j < min(len(clean), len(conflict)) - i
           and clean[len(clean) - 1 - j] == conflict[len(conflict) - 1 - j]):
        j += 1
    start, end = i, len(conflict) - j
    # The common prefix runs through the first value, because that value is
    # identical in both notes. Extend start back to the beginning of the last
    # number that ends at or before it, so the region holds both values.
    prior = [m for m in NUM.finditer(conflict[:start]) if m.end() >= start - 3]
    if prior:
        start = prior[-1].start()
    return start, end, conflict[start:end]


def flip(region, stated, second):
    """Swap the two numbers inside the injected region, leaving all else alone."""
    hits = [m for m in NUM.finditer(region)]
    want = {f"{stated:g}", f"{second:g}", str(stated), str(second)}
    pair = [m for m in hits if m.group(0) in want or float(m.group(0)) in (stated, second)]
    if len(pair) != 2:
        return None, f"found {len(pair)} of the two values in the injected region"
    a, b = pair
    if float(a.group(0)) != float(stated):
        return None, "first number in the region is not the stated value"
    return region[:a.start()] + b.group(0) + region[a.end():b.start()] + a.group(0) + region[b.end():], None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    args = ap.parse_args()

    src = json.load(open(SRC))
    built, failed = [], []

    for item in src["items"]:
        by = {c["condition"]: c for c in conditions(item)}
        clean, vc, res = by["clean"], by["value_conflict"], by["resolvable"]
        stated = item["creatinine"]["stated"]
        second = item["conflict"]["second_value"]

        if vc["note"] != res["note"]:
            failed.append((item["seed_id"], "value_conflict and resolvable notes already differ"))
            continue

        i, k, region = injected_region(clean["note"], vc["note"])
        flipped_region, err = flip(region, stated, second)
        if err:
            failed.append((item["seed_id"], err))
            continue

        note = vc["note"][:i] + flipped_region + vc["note"][k:]

        # --- assertions: the flip must change order and nothing else -------
        if len(note) != len(vc["note"]):
            failed.append((item["seed_id"], "flipped note changed length")); continue
        if sorted(note) != sorted(vc["note"]):
            failed.append((item["seed_id"], "flipped note changed its characters")); continue
        if note == vc["note"]:
            failed.append((item["seed_id"], "flip was a no-op")); continue
        if note[:i] != vc["note"][:i] or note[k:] != vc["note"][k:]:
            failed.append((item["seed_id"], "text outside the injected phrase moved")); continue
        pos_new = [float(m.group(0)) for m in NUM.finditer(flipped_region)
                   if float(m.group(0)) in (stated, second)]
        if pos_new != [second, stated]:
            failed.append((item["seed_id"], f"order after flip is {pos_new}, expected [{second}, {stated}]")); continue
        if f"{stated:g}" not in res["question"] and str(stated) not in res["question"]:
            failed.append((item["seed_id"], "cue does not name the stated value")); continue

        built.append({
            "seed_id": item["seed_id"],
            "case_id": item["case_id"],
            "calculator": item["calculator"],
            "calculator_short": item["calculator_short"],
            "calculator_id": item["calculator_id"],
            "cued_value": stated,
            "cued_value_position": 2,
            "other_value": second,
            "conditions": [
                {"item_id": f"{item['seed_id']}_value_conflict_flipped",
                 "condition": "value_conflict_flipped", "note": note,
                 "question": vc["question"], "correct_action": vc["correct_action"],
                 "correct_answer": vc.get("correct_answer"), "answer_unit": vc.get("answer_unit"),
                 "rationale": "conflicting pair written in reverse order; no cue"},
                {"item_id": f"{item['seed_id']}_resolvable_flipped",
                 "condition": "resolvable_flipped", "note": note,
                 "question": res["question"], "correct_action": res["correct_action"],
                 "correct_answer": res.get("correct_answer"), "answer_unit": res.get("answer_unit"),
                 "rationale": "same note; cue names the value now written second"},
            ],
        })

    print(f"seeds in source        : {len(src['items'])}")
    print(f"flipped pairs built    : {len(built)}")
    print(f"conditions produced    : {2 * len(built)}")
    print(f"failed                 : {len(failed)}")
    for sid, why in failed:
        print(f"   {sid}: {why}")

    if not args.build:
        print("\nreport only; pass --build to write " + OUT)
        return 0 if not failed else 1

    payload = {
        "built_from": SRC,
        "seeds_digest": src.get("seeds_digest"),
        "n_items": 2 * len(built),
        "n_base_notes": len(built),
        "design": ("Order-flipped twin of the dissociation value_conflict pair. The two "
                   "conflicting values appear in reverse order; the cue names the same "
                   "value as the unflipped item, which now appears second. Correct "
                   "answers are unchanged."),
        "items": built,
    }
    body = json.dumps(payload, sort_keys=True).encode()
    payload["content_digest"] = hashlib.sha256(body).hexdigest()[:16]
    json.dump(payload, open(OUT, "w"), indent=1)
    print(f"\nwrote {OUT}  ({2 * len(built)} conditions, digest {payload['content_digest']})")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
