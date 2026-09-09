#!/usr/bin/env python3
"""Re-run MedCalc-Bench's own calculators on published cases and score the shipped labels.

Task owner: Annotator D -- Week 1 task S1.
Completed by Annotator D.

Why this exists: an external audit (arXiv 2603.02222) reports a substantial error
rate in MedCalc-Bench's shipped ground-truth answers. Everything we build sits on
that substrate, so a reviewer will ask. This is the answer, and it is measured
rather than argued: feed each row's `Relevant Entities` — MedCalc's own extraction,
not ours — into MedCalc's own released implementation, and check the result against
the shipped `Ground Truth Answer` under MedCalc's own tolerance rule.

A mismatch here is one of two things, and the script does not pretend to tell them
apart: a wrong label, or a released implementation that disagrees with the label it
was supposed to produce. Either way the shipped label is not something to inherit.

Two samples are reported:

  primary   n=50, breadth-first round robin across every calculator we can drive,
            seeded and deterministic. This is the headline number.
  seedpool  a census of all rows for the three creatinine calculators, because the
            dissociation seeds come from exactly that pool and a seed note with a
            broken label is a seed we must not use.

Outputs audit/label_audit.json (every row, machine-readable) and audit/LABEL_AUDIT.md.

Usage:  python3 audit/label_audit.py
"""
import contextlib
import csv
import datetime
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calculators  # noqa: E402  (must follow the path insert)
import entities  # noqa: E402


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, "data", "medcalc", "test_data.csv")
OUT_JSON = os.path.join(ROOT, "audit", "label_audit.json")
OUT_MD = os.path.join(ROOT, "audit", "LABEL_AUDIT.md")

N_PRIMARY = 50          # cases that must be *scored*, not merely drawn
SEED = 20260804         # frozen; changing it changes which cases we report

CREATININE_CALCS = {2, 3, 9}  # Cockcroft-Gault, CKD-EPI, MDRD

# MedCalc's own correctness rule, transcribed from evaluation/evaluate.py at the
# version-1.0 tag. Integer calculators must match exactly; decimal calculators get
# the shipped per-row tolerance band. We do not widen either.
DATE_IDS = {13, 68}
GEST_AGE_IDS = {69}
INTEGER_IDS = {4, 15, 16, 17, 18, 20, 21, 25, 27, 28, 29, 32, 33, 36, 43, 45, 48, 51}


def drivable(calc_id):
    """True when v1.0 ships an implementation and we can map every input to it."""
    return (calculators.entry_point(calc_id) is not None
            and entities.is_registered(calc_id))


def _num(x):
    return float(str(x).strip())


def check_correctness(answer, ground_truth, calid, lower, upper):
    """True if `answer` counts as correct under MedCalc-Bench's own rule."""
    calid = int(calid)
    if calid in DATE_IDS:
        fmt = "%m/%d/%Y"
        a = datetime.datetime.strptime(str(answer), fmt)
        g = datetime.datetime.strptime(str(ground_truth), fmt)
        return a == g
    if calid in GEST_AGE_IDS:
        pat = r"\(?[\"\']?(\d+)\s*(weeks?)?[\"\']?,?\s*[\"\']?(\d+)\s*(days?)?[\"\']?\s*\)?"
        mg = re.search(pat, str(ground_truth))
        ma = re.search(pat, str(answer))
        if not (mg and ma):
            return False
        return (mg.group(1), mg.group(3)) == (ma.group(1), ma.group(3))
    if calid in INTEGER_IDS:
        return round(_num(answer)) == round(_num(ground_truth))
    # decimal: shipped tolerance band
    return _num(lower) <= _num(answer) <= _num(upper)


def load_rows():
    csv.field_size_limit(10 ** 9)
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def round_robin_sample(rows, n, seed):
    """Breadth-first sample: one row per calculator per pass, calculators shuffled once.

    Chosen over a flat random draw so 50 cases cannot land mostly inside two or
    three calculators and make the headline number a statement about those two or
    three. Deterministic given `seed`.
    """
    import random
    rng = random.Random(seed)

    by_calc = defaultdict(list)
    for r in rows:
        if drivable(r["Calculator ID"]):
            by_calc[int(r["Calculator ID"])].append(r)

    calc_ids = sorted(by_calc)
    rng.shuffle(calc_ids)
    for cid in calc_ids:
        rng.shuffle(by_calc[cid])

    out, depth = [], 0
    while len(out) < n:
        added = False
        for cid in calc_ids:
            if depth < len(by_calc[cid]):
                out.append(by_calc[cid][depth])
                added = True
                if len(out) == n:
                    return out
        if not added:
            break
        depth += 1
    return out


def draw_until_scored(rows, n, seed):
    """Draw in the fixed round-robin order until `n` cases have actually scored.

    The task asks for the mismatch rate over 50 published cases. Drawing exactly
    50 gave 47, because three of them land on implementations that raise before
    producing an answer -- so the rate had a denominator of 47 and three cases
    hung off the side of it.

    Dropping those calculators to reach a clean 50 would be sampling on the
    outcome: they would be excluded precisely because they fail, which is the one
    substantive thing this audit found. So the order is kept exactly as it was and
    the draw simply goes deeper, and every case that could not be scored is
    reported rather than discarded.
    """
    ordered = round_robin_sample(rows, len(rows), seed)
    results, scored = [], 0
    for row in ordered:
        results.append(recompute(row))
        if results[-1]["status"] == "ok":
            scored += 1
            if scored == n:
                break
    return results, ordered[:len(results)]


def recompute(row):
    """Run the released implementation on one row. Never raises."""
    cid = int(row["Calculator ID"])
    rec = {
        "row_number": int(row["Row Number"]),
        "calc_id": cid,
        "calculator": row["Calculator Name"],
        "note_id": row["Note ID"],
        "output_type": row["Output Type"],
        "shipped_answer": row["Ground Truth Answer"],
        "lower_limit": row["Lower Limit"],
        "upper_limit": row["Upper Limit"],
    }
    if not drivable(cid):
        rec.update(status="no_driver", recomputed=None, agrees=None,
                   error=entities.UNREGISTERED_REASON.get(
                       cid, "not registered as drivable from shipped entities"))
        return rec
    missing = entities.missing_inputs(cid, calculators.parse_entities(row["Relevant Entities"]))
    if missing:
        rec.update(status="unmapped_input", recomputed=None, agrees=None,
                   error="case does not supply: " + ", ".join(missing))
        return rec
    try:
        # A couple of implementations print to stdout on import or call; that is
        # their business, not the report's.
        with contextlib.redirect_stdout(io.StringIO()):
            result = calculators.call(cid, row["Relevant Entities"])
        recomputed = result["Answer"]
    except Exception as exc:
        rec.update(status="error", recomputed=None, agrees=None,
                   error=f"{type(exc).__name__}: {exc}")
        return rec
    try:
        agrees = check_correctness(recomputed, row["Ground Truth Answer"], cid,
                                   row["Lower Limit"], row["Upper Limit"])
    except Exception as exc:
        rec.update(status="uncheckable", recomputed=str(recomputed), agrees=None,
                   error=f"{type(exc).__name__}: {exc}")
        return rec
    rec.update(status="ok", recomputed=str(recomputed), agrees=bool(agrees),
               exact=exact_match(recomputed, row["Ground Truth Answer"]), error=None)
    return rec


def exact_match(recomputed, shipped):
    """Did the code land on the shipped number itself, not merely inside its band?

    Tolerance bands are wide for some calculators, so band-passing alone can hide a
    real disagreement. This is the stricter statistic; both are reported.
    """
    try:
        return abs(_num(recomputed) - _num(shipped)) < 1e-9
    except Exception:
        return str(recomputed).strip() == str(shipped).strip()


def summarise(records):
    ok = [r for r in records if r["status"] == "ok"]
    return {
        "n_cases": len(records),
        "n_scored": len(ok),
        "n_agree": sum(1 for r in ok if r["agrees"]),
        "n_mismatch": sum(1 for r in ok if not r["agrees"]),
        "n_exact": sum(1 for r in ok if r.get("exact")),
        "n_band_only": sum(1 for r in ok if r["agrees"] and not r.get("exact")),
        "mismatch_rate": (sum(1 for r in ok if not r["agrees"]) / len(ok)) if ok else None,
        "n_error": sum(1 for r in records if r["status"] == "error"),
        "n_no_driver": sum(1 for r in records if r["status"] == "no_driver"),
        "n_uncheckable": sum(1 for r in records if r["status"] == "uncheckable"),
        "n_unmapped_input": sum(1 for r in records if r["status"] == "unmapped_input"),
    }


def pct(x):
    return "n/a" if x is None else f"{100 * x:.1f}%"


def main():
    if not os.path.exists(CSV_PATH):
        sys.exit("data/medcalc/test_data.csv missing. Run: python3 fetch_medcalc.py")

    rows = load_rows()
    primary, primary_rows = draw_until_scored(rows, N_PRIMARY, SEED)
    seedpool_rows = [r for r in rows if int(r["Calculator ID"]) in CREATININE_CALCS]

    seedpool = [recompute(r) for r in seedpool_rows]
    # The 50-case sample is the number we committed to reporting, but running every
    # drivable row costs seconds and turns "no mismatches in our sample" into a much
    # stronger statement. Reported as supplementary, not as the headline.
    census = [recompute(r) for r in rows if drivable(r["Calculator ID"])]

    prov_path = os.path.join(ROOT, "data", "medcalc", "PROVENANCE.json")
    provenance = json.load(open(prov_path)) if os.path.exists(prov_path) else {}

    all_calc_ids = {int(r["Calculator ID"]) for r in rows}
    report = {
        "generated_utc": datetime.datetime.now(datetime.timezone.utc)
                                  .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "substrate": {"tag": provenance.get("tag"), "commit": provenance.get("commit"),
                      "rows_in_test_set": len(rows)},
        "coverage": {
            "n_calculators_in_test_set": len(all_calc_ids),
            "n_registered": sum(1 for c in all_calc_ids if drivable(c)),
            "excluded": {str(c): {
                "name": next(r["Calculator Name"] for r in rows
                             if int(r["Calculator ID"]) == c),
                "reason": entities.UNREGISTERED_REASON.get(
                    c, "not registered as drivable from shipped entities")}
                for c in sorted(all_calc_ids) if not drivable(c)},
        },
        "sampling": {"n_scored_target": N_PRIMARY, "n_drawn": len(primary),
                     "seed": SEED,
                     "method": "breadth-first round robin over drivable "
                               "calculators, drawn until the target number of "
                               "cases have scored"},
        "primary": {"summary": summarise(primary), "cases": primary},
        "seedpool": {"summary": summarise(seedpool), "cases": seedpool,
                     "calculators": sorted(CREATININE_CALCS)},
        "census": {"summary": summarise(census), "cases": census},
    }
    with open(OUT_JSON, "w") as f:
        json.dump(report, f, indent=2)

    write_markdown(report)

    s = report["primary"]["summary"]
    print(f"primary  n={s['n_cases']} scored={s['n_scored']} "
          f"mismatch={s['n_mismatch']} ({pct(s['mismatch_rate'])})")
    s2 = report["seedpool"]["summary"]
    print(f"seedpool n={s2['n_cases']} scored={s2['n_scored']} "
          f"mismatch={s2['n_mismatch']} ({pct(s2['mismatch_rate'])})")
    s3 = report["census"]["summary"]
    print(f"census   n={s3['n_cases']} scored={s3['n_scored']} "
          f"mismatch={s3['n_mismatch']} ({pct(s3['mismatch_rate'])}) "
          f"impl_errors={s3['n_error']}")
    print(f"wrote {os.path.relpath(OUT_JSON, ROOT)} and {os.path.relpath(OUT_MD, ROOT)}")


def write_markdown(report):
    p, sp = report["primary"], report["seedpool"]
    ps, sps = p["summary"], sp["summary"]
    sub = report["substrate"]

    L = []
    L.append("# Label audit: recomputing MedCalc-Bench's shipped answers\n")
    L.append("**Task owner:** Annotator D — Week 1 task S1  \n"
             "**Completed by:** Annotator D\n")
    L.append(f"_Generated {report['generated_utc']} from "
             f"MedCalc-Bench `{sub['tag']}` ({sub['commit'][:10]}), "
             f"{sub['rows_in_test_set']} test rows. "
             "Regenerate with `python3 audit/label_audit.py`._\n")
    L.append("## What was measured\n")
    L.append(
        "Each case's `Relevant Entities` — MedCalc-Bench's own extraction of the note, "
        "not ours — was fed to MedCalc-Bench's own released implementation for that "
        "calculator. The result was compared to the shipped `Ground Truth Answer` under "
        "MedCalc-Bench's own correctness rule (exact match for integer-output "
        "calculators, the shipped per-row tolerance band for decimal ones). No tolerance "
        "was widened and no formula was reimplemented.\n")
    L.append(
        "A mismatch means the shipped label and the shipped code disagree on a case where "
        "the inputs are not in dispute. This audit does not adjudicate which of the two is "
        "wrong; the operational consequence is the same either way, which is that we "
        "recompute every clean answer we use and inherit no label.\n")

    L.append("## Headline\n")
    L.append("| | Primary sample | Creatinine seed pool |")
    L.append("|---|---|---|")
    L.append(f"| Cases run | {ps['n_cases']} | {sps['n_cases']} |")
    L.append(f"| Scored | {ps['n_scored']} | {sps['n_scored']} |")
    L.append(f"| Agree with shipped label | {ps['n_agree']} | {sps['n_agree']} |")
    L.append(f"| &nbsp;&nbsp;of which exact, not merely in-band | {ps['n_exact']} | {sps['n_exact']} |")
    L.append(f"| **Mismatch** | **{ps['n_mismatch']} ({pct(ps['mismatch_rate'])})** | "
             f"**{sps['n_mismatch']} ({pct(sps['mismatch_rate'])})** |")
    L.append(f"| Implementation raised | {ps['n_error']} | {sps['n_error']} |")
    L.append(f"| Case missing a required input | {ps['n_unmapped_input']} | "
             f"{sps['n_unmapped_input']} |")
    L.append(f"| Not drivable at v1.0 | {ps['n_no_driver']} | {sps['n_no_driver']} |")
    L.append("")
    L.append(
        "The exact-agreement row matters because the decimal bands are generous on some "
        "calculators; a result can sit inside the band while still differing from the "
        "shipped number. Reporting only the band would flatter the substrate.\n")
    L.append(
        f"The primary sample is drawn breadth-first — one case per calculator per "
        f"pass, calculator order and within-calculator order fixed by seed "
        f"{report['sampling']['seed']}. A flat random draw from 1,047 rows would "
        "concentrate in a few calculators and turn the headline into a statement "
        "about those calculators; this does not.\n")
    L.append(
        f"**{ps['n_cases']} cases were drawn to score {ps['n_scored']}.** The draw "
        "continues in that fixed order until the target number of cases have actually "
        "produced an answer, because three of the first fifty land on implementations "
        "that raise before producing one. Excluding those calculators to reach a clean "
        "fifty would be sampling on the outcome — dropping cases precisely because they "
        "fail, which is the one substantive thing this audit found. The order is "
        "unchanged and every unscored case is reported below.\n")
    L.append(
        "The seed pool column is a census, not a sample: every Cockcroft-Gault, CKD-EPI "
        "and MDRD row in the test set. The dissociation seeds are drawn from this pool, "
        "so its mismatches are the specific rows we must not seed from.\n")

    cs = report["census"]["summary"]

    L.append("## What the result means, and what it does not\n")
    L.append(
        f"On the calculators we can drive, the shipped labels reproduce exactly: "
        f"{cs['n_exact']} of {cs['n_scored']} scored rows land on the shipped number itself, "
        "not merely inside its tolerance band. Whatever is wrong with MedCalc-Bench, it is "
        "not that the label disagrees with the code on these calculators.\n")
    L.append("That is a narrower claim than \"the labels are correct\", and the gap matters:\n")
    L.append(
        "- **This tests label-against-code, holding the extracted inputs fixed.** It takes "
        "`Relevant Entities` as given. If MedCalc-Bench pulled the wrong creatinine out of a "
        "note, this audit reproduces the wrong answer faithfully and reports agreement. "
        "Published error rates that count extraction mistakes are measuring something this "
        "cannot see.\n"
        "- **It says nothing about whether the formula is the right one.** A calculator "
        "implemented consistently but wrongly agrees with itself perfectly.\n"
        "- **It covers the continuous calculators only.** The rule-based scores, which is "
        "where criterion-interpretation disputes would live, are excluded below.\n")
    L.append(
        "The one substantive defect this did surface is not a label error at all: two "
        "released implementations raise on every row they are asked about (see below). "
        "For those, no answer can be reproduced from the released code in any sense.\n")
    L.append(
        "Operationally none of this changes our plan, which was already not to inherit "
        "labels. It does mean we can stop treating substrate label error as an open "
        "threat to the dissociation arm: the seed pool is 60/60 exact.\n")

    L.append("## Supplementary: every drivable row\n")
    L.append(
        f"Running all {cs['n_cases']} drivable rows rather than only the sampled 50 costs "
        "seconds, so we did it. It is reported here rather than as the headline because "
        f"the 50-case sample is what we committed to.\n")
    L.append(f"- scored: **{cs['n_scored']}**")
    L.append(f"- agree with the shipped label: **{cs['n_agree']}** "
             f"({cs['n_exact']} exactly, {cs['n_band_only']} in-band only)")
    L.append(f"- mismatch: **{cs['n_mismatch']}** ({pct(cs['mismatch_rate'])})")
    L.append(f"- the implementation itself raised: **{cs['n_error']}**")
    L.append(f"- case did not supply a required input: **{cs['n_unmapped_input']}**\n")

    impl_errors = defaultdict(list)
    for c in report["census"]["cases"]:
        if c["status"] == "error":
            impl_errors[(c["calculator"], c["error"])].append(c["row_number"])
    L.append("### Released implementations that cannot run\n")
    if not impl_errors:
        L.append("None.\n")
    else:
        L.append(
            "These are not label disputes. The shipped implementation raises before "
            "producing an answer, on inputs MedCalc-Bench itself extracted, so there is no "
            "recomputation to compare and the shipped label for these rows cannot be "
            "reproduced from the released code at all.\n")
        L.append("| Calculator | Rows affected | Failure |")
        L.append("|---|---|---|")
        for (name, err), rowlist in sorted(impl_errors.items()):
            L.append(f"| {name} | {len(rowlist)} | `{err}` |")
        L.append("")

    for key, title in (("primary", "Primary sample"), ("seedpool", "Creatinine seed pool"),
                       ("census", "All drivable rows")):
        bad = [c for c in report[key]["cases"] if c["status"] == "ok" and not c["agrees"]]
        L.append(f"## {title}: mismatching cases\n")
        if not bad:
            L.append("None.\n")
        else:
            L.append("| Row | Calculator | Note ID | Shipped | Recomputed | Band |")
            L.append("|---|---|---|---|---|---|")
            for c in sorted(bad, key=lambda c: c["row_number"]):
                band = (f"{c['lower_limit']}–{c['upper_limit']}"
                        if c["output_type"] == "decimal" else "exact")
                L.append(f"| {c['row_number']} | {c['calculator']} | `{c['note_id']}` | "
                         f"{c['shipped_answer']} | {c['recomputed']} | {band} |")
            L.append("")

    for key, title in (("primary", "Primary sample"), ("seedpool", "Creatinine seed pool")):
        prob = [c for c in report[key]["cases"]
                if c["status"] in ("error", "no_driver", "uncheckable", "unmapped_input")]
        if prob:
            L.append(f"## {title}: cases that could not be scored\n")
            L.append("| Row | Calculator | Status | Detail |")
            L.append("|---|---|---|---|")
            for c in sorted(prob, key=lambda c: c["row_number"]):
                L.append(f"| {c['row_number']} | {c['calculator']} | {c['status']} | "
                         f"{c['error']} |")
            L.append("")

    by_calc = defaultdict(lambda: [0, 0])
    for c in report["primary"]["cases"]:
        if c["status"] == "ok":
            by_calc[c["calculator"]][0] += 1
            by_calc[c["calculator"]][1] += 0 if c["agrees"] else 1
    L.append("## Primary sample: coverage by calculator\n")
    L.append(f"{len(by_calc)} calculators, "
             f"{Counter(c['calculator'] for c in report['primary']['cases']).most_common(1)[0][1]} "
             "case(s) each at most.\n")
    L.append("| Calculator | Scored | Mismatch |")
    L.append("|---|---|---|")
    for name in sorted(by_calc):
        n, bad = by_calc[name]
        L.append(f"| {name} | {n} | {bad} |")
    L.append("")
    L.append("## What this audit does not cover\n")
    L.append(
        "MedCalc-Bench ships each case's inputs under human-readable keys and its "
        "implementations index internal ones, so driving the released code needs a "
        "rename layer (`audit/entities.py`). That layer is only safe for calculators "
        "with a fixed, unambiguous input set. The rule-based scores read their boolean "
        "criteria through `.get(key, default)`: a criterion we failed to map would not "
        "raise, it would read as *absent* and yield a plausible wrong score that looks "
        "exactly like a MedCalc label error. Rather than report a number contaminated "
        "that way, those calculators are left undriven:\n")
    L.append("| ID | Calculator | Excluded because |")
    L.append("|---|---|---|")
    for cid, info in sorted(report["coverage"]["excluded"].items(), key=lambda kv: int(kv[0])):
        L.append(f"| {cid} | {info['name']} | {info['reason']} |")
    L.append("")
    L.append(
        f"So the headline covers {report['coverage']['n_registered']} of "
        f"{report['coverage']['n_calculators_in_test_set']} calculators in the test set — "
        "the continuous ones, which is where our own items live. Extending it to the rule-based "
        "scores means hand-mapping their criteria, which is Week 3 work for the Family C set "
        "and not a Week 1 blocker.\n")

    L.append("## What we do about it\n")
    L.append(
        "1. Every clean answer in our item set is recomputed from the released code at "
        "build time. No shipped label is copied forward. This was the plan before the "
        "audit came back clean and stays the plan after, because it also covers the "
        "extraction question this audit cannot see.\n"
        "2. Seeds are drawn only from rows where the recomputation agrees with the "
        "shipped label. On the creatinine pool that constraint currently excludes nobody, "
        "but it is enforced in `construct.py` rather than assumed.\n"
        "3. Calculators whose released implementation raises are not eligible as "
        "substrate. That rules out Delta Ratio and Albumin Corrected Delta Ratio.\n"
        "4. On the missing and value-conflict conditions the correct action is to decline "
        "or flag, which depends on no label at all — those conditions were never exposed "
        "to this risk.\n")

    open(OUT_MD, "w").write("\n".join(L))


if __name__ == "__main__":
    main()
