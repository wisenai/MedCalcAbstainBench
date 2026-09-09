"""
Builds a standalone results doc for the program_aided format: flag rate
by condition, by family, and by model -- same shape as TASK1_RESULT.md's
open_ended tables, but for program_aided specifically.

Deliberately a separate script, not a change to analyze_flag_rates.py:
that pipeline's already-generated outputs (data/scored.csv,
docs/FLAG_RATES.md) stay untouched. This reads the same already-
joined data/grid_rows.json (written by join_grid.py -- no
rejoining, no API calls) and only writes its own new doc.

Reports flagged/committed_with_acknowledgment/committed_silent rates only
-- no extracted numeric value or accuracy check. See
scoring_program_aided.py's module docstring for why: exact-value
extraction turned out unreliable (a markdown-bold-number pattern kept
colliding with Python's ** exponent operator across several different
code-formatting variants) and isn't needed for this project's question,
which only asks whether a model committed to an answer or declined, not
what the answer was. The flagged/ack/silent classification itself WAS
hand-validated against real cached completions -- see the interpretation
note at the bottom of the doc this script writes.

Usage: python3 analyze_program_aided.py
"""
import json

from statsmodels.stats.proportion import proportion_confint

from scoring_program_aided import classify_program_aided

ALPHA = 0.05
IN_JSON = "data/grid_rows.json"
OUT_MD = "docs/PROGRAM_AIDED.md"

MODELS = [
    "anthropic/claude-opus-4.8", "openai/gpt-5", "meta-llama/llama-4-maverick",
    "google/gemini-3.6-flash", "openai/gpt-5-mini",
]
CONDITIONS = ("clean", "missing", "value_conflict", "resolvable", "contradiction")
FAMILIES = ("A", "B", "C", "breadth", "dissociation")


def wilson_fmt(count, total):
    if total == 0:
        return "0/0"
    p = count / total
    lo, hi = proportion_confint(count, total, alpha=ALPHA, method="wilson")
    lo, hi = max(0.0, lo), min(1.0, hi)
    return f"{count}/{total} ({p*100:.1f}% [{lo*100:.1f}% - {hi*100:.1f}%])"


def main():
    with open(IN_JSON, encoding="utf-8") as f:
        data = json.load(f)
    rows = [r for r in data["rows"] if r["prompt_id"] == "program_aided"]
    print(f"program_aided rows: {len(rows)}")

    for r in rows:
        r["assigned_label"] = classify_program_aided(r["completion_text"])

    from collections import Counter
    dist = Counter(r["assigned_label"] for r in rows)
    print("label distribution:", dict(dist))

    def flagged_count(key, value):
        sub = [r for r in rows if r.get(key) == value]
        flagged = sum(1 for r in sub if r["assigned_label"] == "flagged")
        return flagged, len(sub)

    def silent_count(key, value):
        sub = [r for r in rows if r.get(key) == value]
        silent = sum(1 for r in sub if r["assigned_label"] == "committed_silent")
        return silent, len(sub)

    def unparseable_count(key, value):
        sub = [r for r in rows if r.get(key) == value]
        up = sum(1 for r in sub if r["assigned_label"] == "unparseable")
        return up, len(sub)

    lines = []
    lines.append("#  -- program_aided format: flag rate by condition, by family, and by model")
    lines.append("")
    lines.append(
        "**What this measures.** Every `program_aided` completion in the "
        "full grid (676 base items x 5 models = 3,380 rows), scored under "
        "the same three-way rubric used everywhere else in this project: "
        "`flagged` (declined), `committed_with_acknowledgment` (noticed, "
        "computed anyway), `committed_silent` (computed with no mention "
        "of the problem). This is a standalone companion to "
        "TASK1_RESULT.md's open_ended tables -- program_aided was "
        "scored as part of that task's \"score the full grid\" scope but "
        "never got its own reported table; this fills that gap."
    )
    lines.append("")
    lines.append(
        "**No extracted value or accuracy check is reported here.** "
        "Unlike `open_ended`/`mcq`, the `program_aided` prompt gives no "
        "output-format instruction, so \"what number did the model land "
        "on\" has to be guessed from free-form code and prose rather than "
        "parsed from a fixed convention. Every extraction pattern precise "
        "enough to pick out *the* answer turned out to have a real "
        "false-positive mode on real data (worst: a markdown-bold-number "
        "pattern colliding with Python's `**` exponent operator, e.g. "
        "`height ** 2` misread as bold text starting with \"2\"). That "
        "problem doesn't need solving here: nothing downstream runs this "
        "code or acts on its output, so the only thing this project's "
        "question needs is whether the model committed to an answer at "
        "all versus declined -- which only requires detecting *presence* "
        "of an attempted computation (print() output, an explicit Output:/"
        "Result: section, a boxed expression), not picking out its exact value. "
        "See `scoring_program_aided.py`'s module docstring for the "
        "full investigation."
    )
    lines.append("")
    lines.append(
        "*A response with neither an attempted computation nor an "
        "abstention phrase is labeled `unparseable` and excluded from the "
        "flagged/total denominators below, so it doesn't silently count "
        "as either behavior.*"
    )
    lines.append("")

    lines.append("## By condition")
    lines.append("")
    lines.append("| condition | flagged/total (Wilson 95% CI) | unparseable/total |")
    lines.append("|---|---|---|")
    for cond in CONDITIONS:
        f, t = flagged_count("condition", cond)
        up, t_all = unparseable_count("condition", cond)
        t_denom = t_all - up
        lines.append(f"| `{cond}` | {wilson_fmt(f, t_denom)} | {up}/{t_all} |")
    lines.append("")

    lines.append("## By family")
    lines.append("")
    lines.append("| family | flagged/total (Wilson 95% CI) | unparseable/total |")
    lines.append("|---|---|---|")
    for fam in FAMILIES:
        f, t = flagged_count("family", fam)
        up, t_all = unparseable_count("family", fam)
        t_denom = t_all - up
        lines.append(f"| `{fam}` | {wilson_fmt(f, t_denom)} | {up}/{t_all} |")
    lines.append("")

    lines.append("## By model")
    lines.append("")
    lines.append("| model | flagged/total (Wilson 95% CI) | unparseable/total |")
    lines.append("|---|---|---|")
    for model in MODELS:
        f, t = flagged_count("model", model)
        up, t_all = unparseable_count("model", model)
        t_denom = t_all - up
        lines.append(f"| `{model}` | {wilson_fmt(f, t_denom)} | {up}/{t_all} |")
    lines.append("")

    lines.append("## Committed-silent rate, non-clean conditions")
    lines.append("")
    lines.append(
        "Same framing as TASK3_RESULT.md: `clean` excluded, since "
        "silent computation there is correct behavior, not danger."
    )
    lines.append("")
    lines.append("| condition | committed_silent/total (Wilson 95% CI) |")
    lines.append("|---|---|")
    for cond in ("missing", "value_conflict", "resolvable", "contradiction"):
        s, t = silent_count("condition", cond)
        up, t_all = unparseable_count("condition", cond)
        t_denom = t_all - up
        lines.append(f"| `{cond}` | {wilson_fmt(s, t_denom)} |")
    lines.append("")

    total_unparseable = sum(1 for r in rows if r["assigned_label"] == "unparseable")
    lines.append(
        f"**Interpretation.** {total_unparseable}/{len(rows)} "
        f"({100*total_unparseable/len(rows):.1f}%) of program_aided "
        "responses are `unparseable` -- no attempted computation and no "
        "abstention phrase detected -- and are excluded from every "
        "denominator above. This is expected to be higher than "
        "open_ended's near-zero unparseable rate: program_aided has no "
        "output-format instruction, so a real fraction of responses "
        "compute a value only inside unexecuted code with no restatement "
        "in text, which is honestly unrecoverable rather than a bug. The "
        "flagged/acknowledged/silent classification itself was hand-"
        "validated against real cached completions across multiple "
        "rounds (samples read directly, false positives found and fixed "
        "in `scoring_program_aided.py`), so the *labels* here carry "
        "similar confidence to `open_ended`/`mcq`'s, even though no "
        "extracted-value accuracy check accompanies them."
    )
    lines.append("")

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
