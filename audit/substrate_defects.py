#!/usr/bin/env python3
"""Defects in the released substrate that our own machinery surfaced.


The  label audit asks whether the shipped labels agree with the shipped
code, and finds 0% mismatch on 586 scorable rows. That agreement is close to
guaranteed, because the labels were produced by that code, and it is silent about
two failures it structurally cannot see:

  a constant inside an implementation being wrong, since the label inherits the
  same wrong constant and the two agree perfectly;

  an extracted entity disagreeing with the note it was drawn from, since the
  audit compares code against label and never against the prose.

Both were found later, by different routes: the first by a model disagreeing with
our ground truth on a clean item, the second by building a blood-pressure locator
that required the note's own text to match the value the calculator consumes.

Nothing here is repaired. The pre-registration pins the substrate to version-1.0
at commit 353ded7c61 and recomputes every clean answer from that released code;
patching a constant would mean evaluating against a private fork rather than
against MedCalc-Bench, and would move the seed digest that the frozen item sets
and every scored row depend on. The defects are recorded, their blast radius is
measured, and the affected items are named so they can be footnoted rather than
counted as model errors.

Usage:  python3 audit/substrate_defects.py
Offline, no API key, no writes outside audit/.
"""
import ast
import csv
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDCALC = os.path.join(ROOT, "data", "medcalc")
OUT_JSON = os.path.join(ROOT, "audit", "substrate_defects.json")

csv.field_size_limit(10 ** 7)


def rows(calc_id):
    out = []
    for split in ("test", "train"):
        path = os.path.join(MEDCALC, f"{split}_data.csv")
        if not os.path.exists(path):
            continue
        with open(path) as fh:
            for r in csv.DictReader(fh):
                if r.get("Calculator ID") == str(calc_id):
                    r["_split"] = split
                    out.append(r)
    return out


def entities(row):
    try:
        return ast.literal_eval(row["Relevant Entities"])
    except (ValueError, SyntaxError):
        return {}


# --- defect 1: the CKD-EPI 2021 male coefficient -----------------------------
#
# The published 2021 CKD-EPI creatinine equation uses kappa = 0.7 for females and
# kappa = 0.9 for males. The released implementation hard-codes a = 0.7 in the
# male branch for creatinine at or below 0.9 mg/dL. The other three branches are
# right, including a = 0.9 for males above 0.9, so only the male low-creatinine
# branch is affected. The wrong constant also appears in the explanation string
# the benchmark ships as its rationale, so it is a deliberate value rather than a
# typo in one place.

def ckd_epi_male_coefficient():
    impl = os.path.join(MEDCALC, "calculators", "ckd-epi_2021_creatinine.py")
    if not os.path.exists(impl):
        return None
    src = open(impl).read()
    m = re.search(r"creatinine_val <= 0\.9 and gender == \"Male\":\s*\n\s*a = ([\d.]+)", src)
    coded = float(m.group(1)) if m else None

    def gfr(scr, age, a, b, coef=1.0):
        return 142 * (scr / a) ** b * 0.9938 ** age * coef

    affected, examples = 0, []
    for r in rows(3):
        e = entities(r)
        cre, sex = e.get("creatinine"), e.get("sex")
        if not cre or sex != "Male":
            continue
        if not str(cre[1]).lower().startswith("mg"):
            continue
        scr = float(cre[0])
        if scr > 0.9:
            continue
        affected += 1
        if len(examples) < 5:
            age = float(e["age"][0]) if isinstance(e.get("age"), list) else float(e.get("age", 0))
            examples.append({
                "note_id": r["Note ID"], "split": r["_split"],
                "creatinine": scr, "age": age,
                "shipped_answer": r["Ground Truth Answer"],
                "as_implemented_a_0_7": round(gfr(scr, age, 0.7, -0.302), 3),
                "as_published_a_0_9": round(gfr(scr, age, 0.9, -0.302), 3),
            })
    return {
        "defect": "CKD-EPI 2021 uses kappa = 0.7 in the male branch; the published equation uses 0.9",
        "file": "calculators/ckd-epi_2021_creatinine.py",
        "coded_value": coded, "published_value": 0.9,
        "branch": "male, creatinine <= 0.9 mg/dL",
        "rows_in_corpus": len(rows(3)),
        "rows_affected": affected,
        "examples": examples,
    }


# --- defect 2: entities that disagree with their own note --------------------
#
# Found while building the Family B locator, which requires the pair in the note
# to equal the pair the calculator consumes. Twenty of the 948 MAP rows fail that
# equality. Two are worth naming: in one the extraction silently reordered an
# impossible reading into a plausible one, which is the behaviour this project
# exists to measure, performed by the annotation pipeline rather than by a model.

BP = re.compile(r"(?:blood pressure|\bBP\b)[^.\n\d]{0,25}?(\d{2,3})\s*/\s*(\d{2,3})", re.I)


def bp_entity_mismatches():
    mism, named = 0, []
    interesting = {"pmc-6637642-1", "pmc-5676363-1"}
    for r in rows(5):
        e = entities(r)
        s, d = e.get("Systolic Blood Pressure"), e.get("Diastolic Blood Pressure")
        if not (s and d):
            continue
        hits = BP.findall(r["Patient Note"])
        if not hits:
            continue
        if any((float(a), float(b)) == (float(s[0]), float(d[0])) for a, b in hits):
            continue
        mism += 1
        if r["Note ID"] in interesting:
            a, b = hits[0]
            named.append({
                "note_id": r["Note ID"],
                "note_states": f"{a}/{b}",
                "entities_record": f"{float(s[0]):.0f}/{float(d[0]):.0f}",
                "shipped_answer": r["Ground Truth Answer"],
                "why_it_matters": (
                    "the note's only pressure is physiologically impossible and the "
                    "extraction put it back into plausible order"
                    if float(a) < float(b) else
                    "the shipped pair is itself impossible, so the shipped answer "
                    "is computed from a systolic below its diastolic"),
            })
    return {
        "defect": "extracted blood pressure disagrees with the pair stated in the note",
        "rows_in_corpus": len(rows(5)),
        "rows_affected": mism,
        "named": named,
    }


def main():
    if not os.path.isdir(MEDCALC):
        sys.exit("data/medcalc missing. Run: python3 fetch_medcalc.py")

    report = {
        "_what_this_is": "Defects in the released MedCalc-Bench substrate, recorded "
                         "rather than repaired. See the module docstring for why.",
        "substrate": {"tag": "version-1.0", "commit": "353ded7c61"},
        "ckd_epi_male_coefficient": ckd_epi_male_coefficient(),
        "bp_entity_mismatch": bp_entity_mismatches(),
    }
    json.dump(report, open(OUT_JSON, "w"), indent=2)

    c = report["ckd_epi_male_coefficient"]
    if c:
        print(f"CKD-EPI 2021 male branch: coded a={c['coded_value']}, "
              f"published a={c['published_value']}")
        print(f"  affected {c['rows_affected']} of {c['rows_in_corpus']} CKD-EPI rows")
        for ex in c["examples"][:3]:
            print(f"    {ex['note_id']:16} shipped {ex['shipped_answer']:>9} | "
                  f"published {ex['as_published_a_0_9']}")
    b = report["bp_entity_mismatch"]
    print(f"\nblood pressure entity mismatch: {b['rows_affected']} of "
          f"{b['rows_in_corpus']} MAP rows")
    for n in b["named"]:
        print(f"    {n['note_id']:16} note says {n['note_states']:>8} | "
              f"entities {n['entities_record']}")
    print(f"\nwrote {os.path.relpath(OUT_JSON, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
