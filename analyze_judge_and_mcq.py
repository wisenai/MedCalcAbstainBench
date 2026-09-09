#!/usr/bin/env python3
""", Task 4: judge agreement on a stratified sample from each family,
plus the open-ended vs. multiple-choice flag-rate delta -- "was offering
an exit enough."

Needs OPENROUTER_API_KEY (Colab, via score.py's existing google.colab.
userdata lookup) for the judge sample -- the only network-bound piece.
Judge responses are cached in data/judge_cache/, keyed on
(item_id, model), so a re-run is free and reproduces exactly.

The delta and its paired McNemar test are computed per family from the
same (item_id, model) pair: the same note, same model, scored once as
open_ended and once as mcq -- structurally identical to 's
missing-vs-value_conflict pairing, which is why it gets McNemar too, not
just Wilson CIs, even though the task text only says "report the delta."

Reads data/scored.json (written by analyze_flag_rates.py). Writes
docs/JUDGE_AGREEMENT_AND_MCQ.md directly, with a reserved validity placeholder
on the delta table.

Usage: python3 analyze_judge_and_mcq.py
"""
import csv
import hashlib
import json
import os
import random

from score import get_judge_label
from stats import MedCalcStatsReferee

IN_JSON = "data/scored.json"
OUT_CSV = "data/judge_sample.csv"
OUT_MD = "docs/JUDGE_AGREEMENT_AND_MCQ.md"
CACHE_DIR = "data/judge_cache"

SEED = 42
SAMPLE_FRACTION = 0.20
FAMILIES = ("A", "B", "C", "breadth", "dissociation")
CONDITIONS = ("clean", "missing", "value_conflict", "resolvable", "contradiction")
MODELS = [
    "anthropic/claude-opus-4.8", "openai/gpt-5", "meta-llama/llama-4-maverick",
    "google/gemini-3.6-flash", "openai/gpt-5-mini",
]

ref = MedCalcStatsReferee()


def stratified_sample_open_ended(rows):
    """20% per (family, condition, model) cell, at least 1 where the cell
    is non-empty, fixed seed for reproducibility."""
    by_cell = {}
    for r in rows:
        by_cell.setdefault((r["family"], r["condition"], r["model"]), []).append(r)
    rng = random.Random(SEED)
    sample = []
    for cell, cell_rows in sorted(by_cell.items()):
        cell_rows_sorted = sorted(cell_rows, key=lambda r: r["item_id"])
        n = max(1, round(len(cell_rows_sorted) * SAMPLE_FRACTION))
        sample.extend(rng.sample(cell_rows_sorted, min(n, len(cell_rows_sorted))))
    return sample


def cache_path(row):
    key = hashlib.sha256(f"{row['item_id']}_{row['model']}".encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{key}.json")


def judge_row(row):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = cache_path(row)
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    decision = get_judge_label(row["completion_text"], row["prompt_text"])
    result = {"judge_label": decision.label, "justification_span": decision.justification_span}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False)
    return result


def cohens_kappa(a, b, categories):
    n = len(a)
    if n == 0:
        return 0.0
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa = {c: sum(1 for x in a if x == c) / n for c in categories}
    pb = {c: sum(1 for x in b if x == c) / n for c in categories}
    pe = sum(pa[c] * pb[c] for c in categories)
    if pe == 1:
        return 1.0
    return (po - pe) / (1 - pe)


def flagged_rate(rows):
    total = len(rows)
    flagged = sum(1 for r in rows if r["assigned_label"] == "flagged")
    return flagged, total


def main():
    doc = json.load(open(IN_JSON, encoding="utf-8"))
    all_rows = doc["rows"]

    open_ended_rows = [r for r in all_rows if r["prompt_id"] == "open_ended"]
    mcq_rows = [r for r in all_rows if r["prompt_id"] == "mcq"]

    # ---- Judge sample, per family ----
    sample = stratified_sample_open_ended(open_ended_rows)
    for row in sample:
        result = judge_row(row)
        row["judge_label"] = result["judge_label"]
        row["justification_span"] = result["justification_span"]

    LABELS = ("flagged", "committed_with_acknowledgment", "committed_silent")
    ACK_SILENT = {"committed_with_acknowledgment", "committed_silent"}

    lines = [
        "#  -- Task 4: judge agreement per family, and the open-ended vs. MCQ delta",
        "",
        "**What this measures.** Two checks. First, an independent LLM judge",
        "re-labels a stratified 20% sample of open_ended completions from",
        "each family, to confirm classify_response's labels are trustworthy",
        "at this larger scale (not just the  dissociation pilot).",
        "Second, the flag-rate delta between open_ended and mcq on the same",
        "notes and models -- \"was offering an exit enough\": a large delta",
        "means simply listing an abstain option changes behavior; a small",
        "one means it doesn't.",
        "",
        "*Validity markers (`<!--VALIDITY:...-->`) are placeholders, filled in*",
        "*by Task 2 (`analyze_validity.py`) after this file is written.*",
        "",
        "## Judge agreement, per family",
        "",
        "| family | n | coarse agreement | coarse kappa | three-way agreement | three-way kappa |",
        "|---|---|---|---|---|---|",
    ]

    for fam in FAMILIES:
        fam_sample = [r for r in sample if r["family"] == fam]
        n = len(fam_sample)
        if n == 0:
            lines.append(f"| `{fam}` | 0 | -- | -- | -- | -- |")
            continue
        classify_labels = [r["assigned_label"] for r in fam_sample]
        judge_labels = [r["judge_label"] for r in fam_sample]
        coarse_c = ["flagged" if l == "flagged" else "commit" for l in classify_labels]
        coarse_j = ["flagged" if l == "flagged" else "commit" for l in judge_labels]
        coarse_agree = sum(1 for x, y in zip(coarse_c, coarse_j) if x == y)
        coarse_kappa = cohens_kappa(coarse_c, coarse_j, ("flagged", "commit"))
        three_agree = sum(1 for x, y in zip(classify_labels, judge_labels) if x == y)
        three_kappa = cohens_kappa(classify_labels, judge_labels, LABELS)
        lines.append(
            f"| `{fam}` | {n} | {ref.format_wilson_ci(coarse_agree, n)} | {coarse_kappa:.3f} "
            f"| {ref.format_wilson_ci(three_agree, n)} | {three_kappa:.3f} |"
        )

    all_disagreements = [r for r in sample if r["assigned_label"] != r["judge_label"]]
    boundary = [r for r in all_disagreements
                if {r["assigned_label"], r["judge_label"]} <= ACK_SILENT]
    lines.append("")
    lines.append(
        f"Disagreements: {len(all_disagreements)} of {len(sample)}. "
        f"{len(boundary)} at the acknowledged/silent boundary (never crosses "
        f"the flag/commit line), {len(all_disagreements) - len(boundary)} "
        f"cross the flag/commit line."
    )
    lines.append("")

    # ---- Open-ended vs. MCQ delta, per family ----
    lines.append("## Open-ended vs. MCQ flag-rate delta, per family")
    lines.append("")
    lines.append(
        "| family | flagged/total (open_ended) | flagged/total (mcq) | delta (mcq - open_ended), pp | paired McNemar p | n pairs |"
    )
    lines.append("|---|---|---|---|---|---|")

    for fam in FAMILIES:
        oe_fam = [r for r in open_ended_rows if r["family"] == fam]
        mcq_fam = [r for r in mcq_rows if r["family"] == fam]

        oe_flagged, oe_total = flagged_rate(oe_fam)
        mcq_flagged, mcq_total = flagged_rate(mcq_fam)

        oe_by_key = {(r["item_id"], r["model"]): r["assigned_label"] for r in oe_fam}
        mcq_by_key = {(r["item_id"], r["model"]): r["assigned_label"] for r in mcq_fam}
        common_keys = sorted(set(oe_by_key) & set(mcq_by_key))
        a = [oe_by_key[k] for k in common_keys]
        b = [mcq_by_key[k] for k in common_keys]

        if common_keys:
            p_value, significant = ref.mcnemar_exact_test(a, b, target_category="flagged")
            p_str = f"{p_value:.4g}" + (" *" if significant else "")
        else:
            p_str = "n/a"

        oe_rate = oe_flagged / oe_total if oe_total else 0.0
        mcq_rate = mcq_flagged / mcq_total if mcq_total else 0.0
        delta = (mcq_rate - oe_rate) * 100

        lines.append(
            f"| `{fam}` | {ref.format_wilson_ci(oe_flagged, oe_total)} "
            f"| {ref.format_wilson_ci(mcq_flagged, mcq_total)} "
            f"| {delta:+.1f} | {p_str} | {len(common_keys)} |"
        )

    lines.append("")
    lines.append("<!--VALIDITY:delta-->")
    lines.append("")
    lines.append(
        "**Interpretation.** [Fill in once real numbers are available: "
        "whether the delta is large (offering an exit changes behavior) or "
        "small (it doesn't) per family, and whether that pattern differs "
        "for Family C -- the family with no arithmetic escape -- versus the "
        "others.]"
    )
    lines.append("")

    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    fields = ["item_id", "seed_id", "condition", "family", "model",
              "assigned_label", "judge_label", "justification_span"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(sample)

    print(f"judged {len(sample)} rows ({len(all_disagreements)} disagreements)")
    print(f"wrote {OUT_CSV}, {OUT_MD}")


if __name__ == "__main__":
    main()
