#!/usr/bin/env python3
"""Week 3, Task 3: report the committed-silent rate as its own table --
"the most dangerous mode," per the task's own wording, and deliberately
not folded into Task 1's table (opposite treatment from Week 2's Task 3,
which WAS folded in for prominence -- here the task explicitly asks for
separation instead).

Re-slices Task 1's already-scored open_ended data (data/week3_scored.json)
for assigned_label == committed_silent, excluding `clean` -- a model
silently computing on a clean note is just behaving correctly, not
"dangerous" the way silently computing on a defect condition is.

Same by-condition/by-family/by-model shape as Task 1, same reserved
validity placeholder, filled in later by analyze_validity.py.

Usage: python3 analyze_silent_commit.py
"""
import json

from stats import MedCalcStatsReferee

IN_JSON = "data/week3_scored.json"
OUT_MD = "docs/WEEK3_TASK3_RESULT.md"

MODELS = [
    "anthropic/claude-opus-4.8", "openai/gpt-5", "meta-llama/llama-4-maverick",
    "google/gemini-3.6-flash", "openai/gpt-5-mini",
]
NON_CLEAN_CONDITIONS = ("missing", "value_conflict", "resolvable", "contradiction")
FAMILIES = ("A", "B", "C", "breadth", "dissociation")

ref = MedCalcStatsReferee()


def silent_count(rows, key, value):
    sub = [r for r in rows if r.get(key) == value]
    silent = sum(1 for r in sub if r["assigned_label"] == "committed_silent")
    return silent, len(sub)


def build_table(rows, key, row_values, placeholder_prefix, with_model_column=False):
    lines = []
    if with_model_column:
        lines.append(f"| {key} | committed_silent/total (Wilson 95% CI) | validity |")
        lines.append("|---|---|---|")
        for v in row_values:
            silent, total = silent_count(rows, key, v)
            placeholder = f"<!--VALIDITY:{placeholder_prefix}:{v}-->"
            lines.append(f"| `{v}` | {ref.format_wilson_ci(silent, total)} | {placeholder} |")
    else:
        lines.append(f"| {key} | committed_silent/total (Wilson 95% CI) |")
        lines.append("|---|---|")
        for v in row_values:
            silent, total = silent_count(rows, key, v)
            lines.append(f"| `{v}` | {ref.format_wilson_ci(silent, total)} |")
        lines.append("")
        lines.append(f"<!--VALIDITY:{placeholder_prefix}-->")
    return lines


def main():
    doc = json.load(open(IN_JSON, encoding="utf-8"))
    rows = [r for r in doc["rows"]
            if r["prompt_id"] == "open_ended" and r["condition"] != "clean"]

    lines = [
        "# Week 3 -- Task 3: committed-silent rate",
        "",
        "**What this measures.** Of the non-clean open_ended completions",
        "(missing, value_conflict, resolvable, and contradiction conditions",
        "-- clean excluded, since silent computation there is correct",
        "behavior, not danger), how often a model computes a number with",
        "*zero* mention of the problem -- not even an acknowledgment. This",
        "is the most dangerous failure mode in the whole taxonomy: nobody",
        "downstream gets a warning. Reported as its own table, deliberately",
        "not buried inside Task 1's flag-rate numbers.",
        "",
        "*Validity markers (`<!--VALIDITY:...-->`) are placeholders, filled in*",
        "*by Task 2 (`analyze_validity.py`) after this file is written.*",
        "",
        "## By condition",
        "",
    ]
    lines += build_table(rows, "condition", NON_CLEAN_CONDITIONS, "by_condition")
    lines.append("")
    lines.append("## By family")
    lines.append("")
    lines += build_table(rows, "family", FAMILIES, "by_family")
    lines.append("")
    lines.append("## By model")
    lines.append("")
    lines += build_table(rows, "model", MODELS, "model", with_model_column=True)
    lines.append("")
    lines.append(
        "**Interpretation.** [Fill in once real numbers are available: "
        "which condition/family shows the highest committed-silent rate, "
        "and whether it concentrates in models/families where the checker "
        "(docs/CHECKER_BOUNDARY.md) can't reach -- i.e. whether the "
        "dangerous mode is worst exactly where a language model is "
        "genuinely required.]"
    )
    lines.append("")

    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    print(f"scored rows in scope: {len(rows)}")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
