#!/usr/bin/env python3
"""Join the full  grid (all 8 item files) to their cached completions.

Covers the three formats Task 1 needs (open_ended, mcq, program_aided) plus
neutral_exit for Task 2's clean-condition validity check -- 676 item_ids x
5 models x 4 (prompt_id, format) pairs.

Identification is purely by recomputing run.py's cache key
(sha256(model_itemid_promptid_format)) for every known combination and
checking file existence -- never by trusting a commit message or manually
tracking which push added what. A "Full grid: chunk N auto-pushed" commit
was found to contain 100% neutral_exit content despite its label, which is
exactly the failure mode this approach avoids.

Standard library only, no API key.

Usage: python3 join_grid.py
"""
import csv
import hashlib
import json
import os
import sys

GRID_FILES = [
    "items_family_a.json",
    "items_family_a_anion_gap.json",
    "items_family_b.json",
    "items_family_c.json",
    "items_breadth_anion_gap.json",
    "items_breadth_ldl.json",
    "items_breadth_osmolality.json",
]
DISSOCIATION_FILE = "items_dissociation.json"

MODELS = [
    "anthropic/claude-opus-4.8",
    "openai/gpt-5",
    "meta-llama/llama-4-maverick",
    "google/gemini-3.6-flash",
    "openai/gpt-5-mini",
]

# (prompt_id, format)
TASK1_COMBOS = [("open_ended", "open_ended"), ("mcq", "mcq"), ("program_aided", "program_aided")]
TASK2_COMBO = ("neutral_exit", "open_ended")
ALL_COMBOS = TASK1_COMBOS + [TASK2_COMBO]

OUT_CSV = "data/grid_rows.csv"
OUT_JSON = "data/grid_rows.json"

CSV_FIELDS = [
    "item_id", "seed_id", "case_id", "condition", "family", "calculator_short",
    "calculator_id", "model", "prompt_id", "format", "correct_action",
    "correct_answer", "answer_unit", "output_tokens", "cost",
    "assigned_label", "extracted_value", "value_correct",
]


def cache_key(model, item_id, prompt_id, fmt):
    return hashlib.sha256(f"{model}_{item_id}_{prompt_id}_{fmt}".encode()).hexdigest()


def load_grid_units():
    """Yields (item_id, seed_id, case_id, family, calculator_short,
    calculator_id, condition_block) for every condition across the 7 grid
    files -- item_id read directly from each condition's own field."""
    for fname in GRID_FILES:
        doc = json.load(open(f"data/{fname}", encoding="utf-8"))
        for item in doc["items"]:
            family = item.get("family") or "dissociation"
            for cond in item["conditions"]:
                yield (
                    cond["item_id"], item["seed_id"], item["case_id"], family,
                    item["calculator_short"], item["calculator_id"], cond,
                )


def load_dissociation_units():
    """Same shape as load_grid_units, but item_id is reconstructed
    (this file predates the item_id field) and family is always
    'dissociation' -- a contributor's checker_boundary.py convention
    (item.get('family') or 'dissociation'), applied identically here."""
    doc = json.load(open(f"data/{DISSOCIATION_FILE}", encoding="utf-8"))
    for item in doc["items"]:
        family = "dissociation"
        for cond in item["conditions"]:
            item_id = f"{item['seed_id']}_{cond['condition']}"
            yield (
                item_id, item["seed_id"], item["case_id"], family,
                item["calculator_short"], item["calculator_id"], cond,
            )


def main():
    units = list(load_grid_units()) + list(load_dissociation_units())
    print(f"total condition units (item_ids): {len(units)}")

    rows = []
    expected = 0
    missing = []
    for item_id, seed_id, case_id, family, calc_short, calc_id, cond in units:
        for prompt_id, fmt in ALL_COMBOS:
            for model in MODELS:
                expected += 1
                key = cache_key(model, item_id, prompt_id, fmt)
                path = f"cache/{key}.json"
                if not os.path.exists(path):
                    missing.append((prompt_id, model, item_id))
                    continue
                rec = json.load(open(path, encoding="utf-8"))
                rows.append({
                    "item_id": item_id,
                    "seed_id": seed_id,
                    "case_id": case_id,
                    "condition": cond["condition"],
                    "family": family,
                    "calculator_short": calc_short,
                    "calculator_id": calc_id,
                    "model": rec["model"],
                    "prompt_id": prompt_id,
                    "format": fmt,
                    "correct_action": cond["correct_action"],
                    "correct_answer": cond["correct_answer"],
                    "answer_unit": cond.get("answer_unit"),
                    "rationale": cond.get("rationale"),
                    "completion_text": rec["response_text"],
                    "prompt_text": rec["prompt"],
                    "input_tokens": rec.get("input_tokens"),
                    "output_tokens": rec.get("output_tokens"),
                    "cost": rec.get("cost"),
                    "assigned_label": None,
                    "extracted_value": None,
                    "value_correct": None,
                })

    print(f"expected cells: {expected}")
    print(f"rows joined: {len(rows)}")
    print(f"missing: {len(missing)}")
    for m in missing[:10]:
        print("  MISSING:", m)

    task1_count = sum(1 for r in rows if r["prompt_id"] in ("open_ended", "mcq", "program_aided"))
    print(f"Task 1 scope (open_ended+mcq+program_aided) rows: {task1_count}")
    if task1_count != 10140:
        print(f"WARNING: expected 10140 Task 1 rows, found {task1_count}", file=sys.stderr)
    if missing:
        print(f"ERROR: {len(missing)} expected cells could not be joined", file=sys.stderr)
        sys.exit(1)

    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump({"n_rows": len(rows), "rows": rows}, fh, indent=2, ensure_ascii=False)

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"wrote {OUT_JSON} and {OUT_CSV}")


if __name__ == "__main__":
    main()
