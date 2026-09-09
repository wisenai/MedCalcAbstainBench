#!/usr/bin/env python3
""", Task 2: apply the validity threshold mechanically -- mark
low-validity open-ended cells in every table where they appear, including
models that pass in one arm and fail in the other.

Per PREREGISTRATION.md sect4, "study" here is read as prompt arm
(open_ended vs. neutral_exit) -- that document's entire validity/
reliability machinery (sect1) was built around exactly those two prompts,
never mcq/program_aided, and the task's own wording of needing clean items
under both prompts only makes sense under that reading.

Computes clean-condition accuracy per (model, arm), scoring neutral_exit
itself here (Task 1 only scored open_ended/mcq/program_aided). Writes its
own docs/VALIDITY_THRESHOLD.md with the accuracy numbers behind every
determination, then makes ONE targeted string-replacement edit per file to
TASK1_RESULT.md, TASK3_RESULT.md, and TASK4_RESULT.md --
filling in the `<!--VALIDITY:...-->` placeholders those scripts reserved.
Never touches any other part of those files.

Must run after analyze_flag_rates.py, analyze_silent_commit.py, and
analyze_judge_and_mcq.py, since it edits their output.

Usage: python3 analyze_validity.py
"""
import json

from score import classify_response, extract_and_verify_score
from stats import MedCalcStatsReferee

GRID_JSON = "data/grid_rows.json"
SCORED_JSON = "data/scored.json"
OUT_MD = "docs/VALIDITY_THRESHOLD.md"

TARGET_FILES = [
    "docs/FLAG_RATES.md",
    "docs/SILENT_COMMIT.md",
    "docs/JUDGE_AGREEMENT_AND_MCQ.md",
]

MODELS = [
    "anthropic/claude-opus-4.8", "openai/gpt-5", "meta-llama/llama-4-maverick",
    "google/gemini-3.6-flash", "openai/gpt-5-mini",
]
ARMS = ("open_ended", "neutral_exit")
THRESHOLD = 0.50

ref = MedCalcStatsReferee()


def clean_accuracy(rows, model, arm_prompt_id):
    sub = [r for r in rows
           if r["model"] == model and r["prompt_id"] == arm_prompt_id
           and r["condition"] == "clean"]
    correct = sum(1 for r in sub if r["value_correct"])
    total = len(sub)
    return correct, total


def main():
    scored = json.load(open(SCORED_JSON, encoding="utf-8"))["rows"]
    grid = json.load(open(GRID_JSON, encoding="utf-8"))["rows"]

    # Task 1 already scored open_ended; score neutral_exit's clean items here.
    neutral_exit_clean = [r for r in grid
                           if r["prompt_id"] == "neutral_exit" and r["condition"] == "clean"]
    for row in neutral_exit_clean:
        extracted, correct = extract_and_verify_score(row["completion_text"], row["correct_answer"])
        row["extracted_value"] = extracted
        row["value_correct"] = correct
        row["assigned_label"] = classify_response(row["completion_text"])

    open_ended_clean = [r for r in scored
                         if r["prompt_id"] == "open_ended" and r["condition"] == "clean"]

    # (model, arm) -> (correct, total, accuracy, low_validity)
    determinations = {}
    for model in MODELS:
        for arm, rows in (("open_ended", open_ended_clean), ("neutral_exit", neutral_exit_clean)):
            correct, total = clean_accuracy(rows, model, arm)
            accuracy = correct / total if total else 0.0
            determinations[(model, arm)] = {
                "correct": correct, "total": total, "accuracy": accuracy,
                "low_validity": accuracy < THRESHOLD,
            }

    # ---- Write the standalone validity report ----
    lines = [
        "#  -- Task 2: validity threshold",
        "",
        "**What this measures.** Per PREREGISTRATION.md sect4, a model whose",
        "clean-condition accuracy falls below 50% cannot have its flag rate",
        "trusted as evidence about conflict detection -- it may not have",
        "engaged with the note's numbers at all. \"Study\" here means prompt",
        "arm (open_ended vs. neutral_exit), matching sect1's own scope: that's",
        "the pair of prompts this project's whole validity machinery was",
        "built around, not mcq/program_aided.",
        "",
        "| model | arm | clean accuracy | status |",
        "|---|---|---|---|",
    ]
    for model in MODELS:
        for arm in ARMS:
            d = determinations[(model, arm)]
            status = "**LOW-VALIDITY**" if d["low_validity"] else "OK"
            lines.append(
                f"| `{model}` | `{arm}` | {ref.format_wilson_ci(d['correct'], d['total'])} | {status} |"
            )
    lines.append("")

    split_models = [m for m in MODELS
                     if determinations[(m, "open_ended")]["low_validity"]
                     != determinations[(m, "neutral_exit")]["low_validity"]]
    if split_models:
        lines.append(
            f"**{len(split_models)} model(s) pass in one arm and fail in the "
            f"other:** {', '.join(f'`{m}`' for m in split_models)}. Per the "
            "task's own wording, this is exactly the case the mechanical "
            "marking exists to catch."
        )
    else:
        lines.append("No model passes in one arm and fails in the other.")
    lines.append("")
    lines.append(
        "**Interpretation.** [Fill in once real numbers are available: "
        "which models, if any, are low-validity, and what that means for "
        "how much weight their flag rates in Tasks 1/3/4 can carry.]"
    )
    lines.append("")

    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"wrote {OUT_MD}")

    # ---- Fill in the placeholders in the other three files ----
    low_validity_by_arm = {
        arm: [m for m in MODELS if determinations[(m, arm)]["low_validity"]]
        for arm in ARMS
    }

    def footnote_text():
        any_low = any(low_validity_by_arm[arm] for arm in ARMS)
        if not any_low:
            return ("*Validity: all 5 models clear the 50% clean-accuracy "
                     "threshold in both the open_ended and neutral_exit arms "
                     "(PREREGISTRATION.md sect4). See docs/VALIDITY_THRESHOLD.md.*")
        parts = []
        for arm in ARMS:
            if low_validity_by_arm[arm]:
                names = ", ".join(f"`{m}`" for m in low_validity_by_arm[arm])
                parts.append(f"{names} low-validity in `{arm}`")
        return ("*Validity: " + "; ".join(parts) +
                " -- their data is pooled into the numbers above. "
                "See docs/VALIDITY_THRESHOLD.md.*")

    def model_cell_text(model):
        d = determinations[(model, "open_ended")]
        return "**LOW-VALIDITY**" if d["low_validity"] else "OK"

    replacements = {}
    for model in MODELS:
        replacements[f"<!--VALIDITY:model:{model}-->"] = model_cell_text(model)
    for prefix in ("by_condition", "by_family"):
        replacements[f"<!--VALIDITY:{prefix}-->"] = footnote_text()
    replacements["<!--VALIDITY:delta-->"] = footnote_text()

    for path in TARGET_FILES:
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        original = content
        for token, value in replacements.items():
            content = content.replace(token, value)
        if content != original:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
            print(f"updated {path}")
        else:
            print(f"WARNING: no placeholders found/replaced in {path}")


if __name__ == "__main__":
    main()
