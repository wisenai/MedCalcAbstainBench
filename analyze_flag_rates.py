#!/usr/bin/env python3
""", Task 1: score the full grid (10,140 completions across
open_ended/mcq/program_aided) and build the three core tables -- flag rate
by condition, by family, and by model -- reported on the open_ended
scoring specifically (see docs/FLAG_RATES.md's own framing text
for why: PREREGISTRATION.md's validity/reliability machinery was only ever
built for open_ended/neutral_exit, so keeping these three tables
open_ended-only is what makes Task 2's "mark the low-validity open-ended
cells" meaningful at all).

Reads data/grid_rows.json (written by join_grid.py). Scores
open_ended with score.py's existing functions (unchanged), mcq with
scoring_mcq.py, program_aided with scoring_program_aided.py --
all 10,140 rows, satisfying "score the full grid" even though only the
open_ended subset feeds these three tables.

Writes docs/FLAG_RATES.md directly, with a reserved validity
placeholder in each table for analyze_validity.py to fill in later --
this script never edits it again after writing it once.

Usage: python3 analyze_flag_rates.py
"""
import csv
import json

from score import classify_response, extract_and_verify_score
from stats import MedCalcStatsReferee

from scoring_mcq import classify_mcq
from scoring_program_aided import classify_program_aided

IN_JSON = "data/grid_rows.json"
OUT_JSON = "data/scored.json"
OUT_CSV = "data/scored.csv"
OUT_MD = "docs/FLAG_RATES.md"

MODELS = [
    "anthropic/claude-opus-4.8", "openai/gpt-5", "meta-llama/llama-4-maverick",
    "google/gemini-3.6-flash", "openai/gpt-5-mini",
]
CONDITIONS = ("clean", "missing", "value_conflict", "resolvable", "contradiction")
FAMILIES = ("A", "B", "C", "breadth", "dissociation")

CSV_FIELDS = [
    "item_id", "seed_id", "condition", "family", "calculator_short", "model",
    "prompt_id", "correct_action", "correct_answer",
    "assigned_label", "extracted_value", "value_correct", "low_confidence",
    "output_tokens", "cost",
]

ref = MedCalcStatsReferee()


def score_rows(rows):
    for row in rows:
        row["low_confidence"] = False
        pid = row["prompt_id"]
        if pid == "open_ended":
            extracted, correct = extract_and_verify_score(row["completion_text"], row["correct_answer"])
            row["extracted_value"] = extracted
            row["value_correct"] = correct
            row["assigned_label"] = classify_response(row["completion_text"])
        elif pid == "mcq":
            label, extracted, correct = classify_mcq(
                row["prompt_text"], row["completion_text"], row["correct_answer"])
            row["assigned_label"] = label
            row["extracted_value"] = extracted
            row["value_correct"] = correct
        elif pid == "program_aided":
            # classify_program_aided returns the label only, by design: this
            # format gives no output-format instruction, so the extracted value
            # is not recoverable reliably. See its module docstring.
            row["assigned_label"] = classify_program_aided(row["completion_text"])
            row["extracted_value"] = None
            row["value_correct"] = None
            row["low_confidence"] = True
        # neutral_exit rows pass through unscored here -- Task 2 owns them.
    return rows


def flagged_count(rows, key, value):
    sub = [r for r in rows if r.get(key) == value]
    flagged = sum(1 for r in sub if r["assigned_label"] == "flagged")
    return flagged, len(sub)


def build_table(rows, key, row_values, placeholder_prefix, with_model_column=False):
    lines = []
    if with_model_column:
        lines.append(f"| {key} | flagged/total (Wilson 95% CI) | validity |")
        lines.append("|---|---|---|")
        for v in row_values:
            flagged, total = flagged_count(rows, key, v)
            placeholder = f"<!--VALIDITY:{placeholder_prefix}:{v}-->"
            lines.append(f"| `{v}` | {ref.format_wilson_ci(flagged, total)} | {placeholder} |")
    else:
        lines.append(f"| {key} | flagged/total (Wilson 95% CI) |")
        lines.append("|---|---|")
        for v in row_values:
            flagged, total = flagged_count(rows, key, v)
            lines.append(f"| `{v}` | {ref.format_wilson_ci(flagged, total)} |")
        lines.append("")
        lines.append(f"<!--VALIDITY:{placeholder_prefix}-->")
    return lines


def main():
    doc = json.load(open(IN_JSON, encoding="utf-8"))
    rows = score_rows(doc["rows"])

    open_ended_rows = [r for r in rows if r["prompt_id"] == "open_ended"]

    lines = [
        "#  -- Task 1: flag rate by condition, by family, and by model",
        "",
        "**What this measures.** Every open_ended completion in the full grid",
        "(Family A, B, C, the breadth calculators, and the dissociation arm --",
        "676 base items x 5 models) scored under the same three-way rubric",
        "used throughout this project: `flagged` (declined), `committed_with_",
        "acknowledgment` (noticed, computed anyway), `committed_silent`",
        "(computed with no mention of the problem). These three tables are",
        "the headline view of that scoring -- how often each model flags,",
        "broken down three ways. `mcq` and `program_aided` completions are",
        "also scored (10,140 rows total, satisfying \"score the full grid\"),",
        "but feed Task 4's delta rather than these tables -- see",
        "PREREGISTRATION.md sect1/sect4 for why open_ended is the reporting format",
        "here: it's the format the project's whole validity/reliability",
        "machinery was built around.",
        "",
        "Condition labels are kept exactly as constructed, not merged --",
        "`missing`/`value_conflict` (dissociation arm) and `contradiction`",
        "(grid) are related but not identical defects, so collapsing them",
        "into one label would hide that distinction.",
        "",
        "*Validity markers (`<!--VALIDITY:...-->`) are placeholders, filled in*",
        "*by Task 2 (`analyze_validity.py`) after this file is written.*",
        "",
        "## By condition",
        "",
    ]
    lines += build_table(open_ended_rows, "condition", CONDITIONS, "by_condition")
    lines.append("")
    lines.append("## By family")
    lines.append("")
    lines += build_table(open_ended_rows, "family", FAMILIES, "by_family")
    lines.append("")
    lines.append("## By model")
    lines.append("")
    lines += build_table(open_ended_rows, "model", MODELS, "model", with_model_column=True)
    lines.append("")
    lines.append(
        "**Interpretation.** [Fill in once real numbers are available: which "
        "condition(s) show the highest flag rate, whether that's concentrated "
        "in a particular family or model, and how it compares to the  "
        "dissociation-only headline.]"
    )
    lines.append("")

    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump({"n_rows": len(rows), "rows": rows}, fh, indent=2, ensure_ascii=False)

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"scored {len(rows)} rows ({len(open_ended_rows)} open_ended)")
    print(f"wrote {OUT_JSON}, {OUT_CSV}, {OUT_MD}")


if __name__ == "__main__":
    main()
