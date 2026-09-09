#!/usr/bin/env python3
"""Build Family B: a physically impossible blood pressure on the note's only reading.

Task owner: Annotator D -- Week 3.
Completed by Annotator D.

Two injection shapes on the same base notes, so the comparison is within-note:

  transposed   the note's own pair, swapped. 80/45 -> 45/80. This is the shape a
               model can recognise as a data-entry pattern rather than reason
               about, which is exactly why it needs a control.
  lowered      the systolic replaced by a value below the note's own diastolic,
               which the diastolic keeps. 161/78 -> 63/78. Impossible, but not a
               swap of anything, so recognising transposition does not help.

If flag rates differ sharply between the two, the model is pattern-matching on
transposition rather than reasoning about the values, and that is a result rather
than a nuisance.

WHAT BUILDING THIS CHANGED IN THE SPEC. Two things did not survive contact with
the arithmetic, and both are recorded in docs/ITEM_FAMILY_SPEC.md:

1. The spec's own injection-2 example raised the diastolic (161/78 -> 161/171).
   MAP is (2*dia + sys)/3, so swapping a pair moves the answer by (dia-sys)/3 --
   the closer the two numbers, the smaller the move. 161/171 puts the two
   readings 2.0% apart, inside MedCalc's own 5% tolerance band, so a resolvable
   arm built on it could not be scored at all. Lowering the systolic instead
   keeps the pair wide.

2. The dissociation arm's >25% divergence rule is unreachable here: 9 of 826
   eligible notes clear it, against 350 at >15%. That is a property of the MAP
   formula, not of the sample. Family B uses >15% -- three times the scoring
   tolerance -- and only the transposed shape carries a resolvable arm, because
   only it is guaranteed separable.

Usage:  python3 family_b.py --select        freeze the seed list
        python3 family_b.py --build         build items from the frozen seeds
"""
import argparse
import ast
import csv
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "audit"))

import spans          # noqa: E402  the anchoring guarantee, shared with every family
import construct      # noqa: E402  the build gate and the cue blocklist, not copied
import checker        # noqa: E402

csv.field_size_limit(10 ** 7)

MAP_CALC_ID = "5"
SEEDS = os.path.join(ROOT, "data", "seeds_family_b.json")
OUT = os.path.join(ROOT, "data", "items_family_b.json")
MEDCALC = os.path.join(ROOT, "data", "medcalc")

TARGET_SEEDS = 30           # the plan's "rate rather than an anecdote"
MIN_SEPARATION = 0.15       # 3x MedCalc's 5% tolerance; see the note above
SYS_BELOW_DIA = 15          # how far under the diastolic the lowered systolic sits
MIN_PLAUSIBLE_SYS = 40      # a systolic below this is a typo, not a contradiction

# Words that, sitting in the same sentence as the pressure, assert it is fine.
FRAMING = (r"\b(?:normal|unremarkable|within\s+normal\s+limits|stable|"
           r"normotensive|reassuring)\b")


def mean_arterial_pressure(systolic, diastolic):
    """The released implementation's formula, written out for the gates.

    Item answers are recomputed through the released code itself; this is used
    only to decide separability before an item is built.
    """
    return (2.0 * diastolic + systolic) / 3.0


def separation(systolic, diastolic):
    """How far apart the two readings of one pair are, relative to the larger."""
    a = mean_arterial_pressure(systolic, diastolic)
    b = mean_arterial_pressure(diastolic, systolic)
    return abs(a - b) / max(a, b)


def load_map_rows():
    if not os.path.isdir(MEDCALC):
        sys.exit("data/medcalc missing. Run: python3 fetch_medcalc.py")
    rows = []
    for split in ("test", "train"):
        with open(os.path.join(MEDCALC, f"{split}_data.csv")) as fh:
            for r in csv.DictReader(fh):
                if r.get("Calculator ID") == MAP_CALC_ID:
                    r["_split"] = split
                    rows.append(r)
    return rows


def entities_of(row):
    d = ast.literal_eval(row["Relevant Entities"])
    s, dia = d.get("Systolic Blood Pressure"), d.get("Diastolic Blood Pressure")
    if not (s and dia):
        return None
    return float(s[0]), float(dia[0])


def screen(row):
    """Every gate a base note must pass, or the reason it failed.

    Returns (record, None) or (None, reason). The reasons are kept and reported
    rather than discarded: a gate that silently drops notes is a gate nobody can
    argue with later.
    """
    note = row["Patient Note"]
    ent = entities_of(row)
    if ent is None:
        return None, "no blood pressure entities"
    systolic, diastolic = ent

    try:
        rec = spans.find_blood_pressure(note, systolic, diastolic)
    except spans.NotFound:
        return None, "entities disagree with the note's own text"
    except spans.Ambiguous:
        return None, "more than one span matches the consumed pair"

    if len(spans.count_blood_pressures(note)) != 1:
        return None, "note states more than one blood pressure"
    if rec["impossible"]:
        return None, "published note is already impossible"
    if not rec["has_unit"]:
        return None, "pressure carries no unit"
    if separation(systolic, diastolic) <= MIN_SEPARATION:
        # One gate, one reason. Putting the measured value in the string would
        # split this into one bucket per percentage and bury the shape of it.
        return None, f"transposition separable by <= {MIN_SEPARATION:.0%}"
    if diastolic - SYS_BELOW_DIA < MIN_PLAUSIBLE_SYS:
        return None, "lowered systolic would be implausible on its own"

    # Framing in the same sentence as the pressure. `Physical examination was
    # normal (... blood pressure 125/70 ...)` and `vital signs were reported as a
    # blood pressure of ...` after `clinically stable` both end up asserting that
    # an impossible pressure is normal, which is a second contradiction we did
    # not build and a model may flag instead of ours. Found by reading the first
    # ten, not by any check.
    #
    # This gate is deliberately over-strict. `normal` can attach to a different
    # noun in the same sentence -- in one note it modifies `sinus rhythm`, not
    # the pressure -- and deciding which noun a modifier governs is not something
    # this can do reliably. Over-rejecting costs supply we have (278 eligible for
    # 30 items); under-rejecting ships a broken item.
    c0, c1 = spans._clause_bounds(note, rec["sys_span"][0])
    m = re.search(FRAMING, note[c0:c1], re.I)
    if m:
        return None, f"clinical framing {m.group(0)!r} sits in the same sentence"
    return {"note_id": row["Note ID"], "split": row["_split"],
            "systolic": systolic, "diastolic": diastolic,
            "question": row["Question"], "published_answer": row["Ground Truth Answer"],
            "separation": round(separation(systolic, diastolic), 4),
            "span": rec}, None


def choose(candidates, target):
    """Test split before train, in corpus order. No scoring, no cherry-picking."""
    ordered = ([c for c in candidates if c["split"] == "test"]
               + [c for c in candidates if c["split"] == "train"])
    return ordered[:target]


def rewrite_pair(note, span_record, systolic, diastolic):
    """Replace the located pair, touching nothing else in the note.

    The two numbers are written back into their own spans, so everything between
    and around them -- the separator, the unit, the spacing -- is the note's own.
    Done right-to-left so the first replacement cannot move the second's offsets.
    """
    s0, s1 = span_record["sys_span"]
    d0, d1 = span_record["dia_span"]
    if not (s1 <= d0):
        raise construct.BuildError("systolic span does not precede diastolic span")
    out = note[:s0] + construct.fmt(systolic) + note[s1:d0] + construct.fmt(diastolic) + note[d1:]
    return out


def cue_for(systolic, diastolic):
    """The resolvable cue, appended to the question and never to the note.

    Returns (text, cue_systolic, cue_diastolic) so the caller can recompute the
    answer from the values the cue actually names, rather than from what the cue
    was meant to name. Those came apart in the first version of this function --
    the sentence said "treat 80 as the systolic" on a note reading 80/140 while
    the recorded answer was MAP(140, 80) -- and no assertion caught it because
    every check was about the note, not about the sentence. The build now
    recomputes from these two values and refuses if they disagree.

    The cue names which number governs rather than supplying a repaired value, so
    both numbers still have to be read out of the note for the answer to be
    right: the same property the dissociation arm's cue has.
    """
    text = (f" The pair is recorded diastolic first: treat {construct.fmt(systolic)}"
            f" as the systolic and {construct.fmt(diastolic)} as the diastolic.")
    return text, systolic, diastolic


def build_one(seed, note, answer_of):
    """The conditions for one base note. Raises BuildError rather than degrading."""
    systolic, diastolic = seed["systolic"], seed["diastolic"]
    rec = seed["span"]

    clean_answer = answer_of(systolic, diastolic)

    # -- transposed: the note's own pair, swapped
    transposed = rewrite_pair(note, rec, diastolic, systolic)
    trans_written = answer_of(diastolic, systolic)     # what computing on it gives
    cue_text, cue_sys, cue_dia = cue_for(systolic, diastolic)
    trans_cued = answer_of(cue_sys, cue_dia)           # from the values the cue names
    if abs(trans_cued - clean_answer) > 1e-9:
        raise construct.BuildError(
            f"cue names {cue_sys:g}/{cue_dia:g} giving {trans_cued}, but recovering the "
            f"published reading should give {clean_answer}")

    # -- lowered: systolic put below the note's own diastolic, diastolic untouched
    lowered_sys = diastolic - SYS_BELOW_DIA
    lowered = rewrite_pair(note, rec, lowered_sys, diastolic)
    lowered_written = answer_of(lowered_sys, diastolic)

    for name, text in (("transposed", transposed), ("lowered", lowered)):
        if text == note:
            raise construct.BuildError(f"{name} variant is identical to the published note")

    question = seed["question"]
    seed_id = f"map-{seed['note_id']}"

    def item_id(condition, shape=None):
        """Explicit, unique, and not left for a consumer to reconstruct.

        `run.py` keys the cache on hash(model, item_id, prompt_id, format) with
        item_id built as seed_id + "_" + condition. Family B has two conditions
        called `contradiction` on the same seed -- transposed and lowered -- so
        that convention collides and one silently overwrites the other in the
        cache. The shape goes in the id, and every condition carries the id it
        should be run under rather than a rule someone has to know.
        """
        return f"{seed_id}_{condition}" + (f"_{shape}" if shape else "")

    conditions = [
        {"item_id": item_id("clean"), "condition": "clean", "shape": None,
         "note": note, "question": question,
         "correct_action": "compute", "correct_answer": clean_answer,
         "rationale": "the note as published; the control that shows the model can "
                      "compute this at all on this note"},
        {"item_id": item_id("contradiction", "transposed"),
         "condition": "contradiction", "shape": "transposed", "note": transposed,
         "question": question, "correct_action": "flag", "correct_answer": None,
         "rationale": f"the note's only pressure reads {construct.fmt(diastolic)}/"
                      f"{construct.fmt(systolic)}; a systolic below its diastolic is "
                      f"not a rare value, it is not a value"},
        {"item_id": item_id("resolvable", "transposed"),
         "condition": "resolvable", "shape": "transposed", "note": transposed,
         "question": question + cue_text,
         "cue_names": {"systolic": cue_sys, "diastolic": cue_dia},
         "correct_action": "compute", "correct_answer": trans_cued,
         "rationale": "byte-identical note to the transposed contradiction, plus a cue "
                      "naming which number governs; a correct answer proves both were read"},
        {"item_id": item_id("contradiction", "lowered"),
         "condition": "contradiction", "shape": "lowered", "note": lowered,
         "question": question, "correct_action": "flag", "correct_answer": None,
         "rationale": f"systolic lowered to {construct.fmt(lowered_sys)} against the "
                      f"note's own diastolic {construct.fmt(diastolic)}; impossible, but "
                      f"not a transposition of anything"},
    ]
    return {
        "seed_id": f"map-{seed['note_id']}",
        "case_id": seed["note_id"],
        "split": seed["split"],
        "calculator": "Mean Arterial Pressure (MAP)",
        "calculator_short": "map",
        "calculator_id": MAP_CALC_ID,
        "family": "B",
        "blood_pressure": {
            "systolic": systolic, "diastolic": diastolic,
            "as_written": rec["pair_text"], "has_unit": rec["has_unit"],
            "sys_span_in_clean_note": rec["sys_span"],
            "dia_span_in_clean_note": rec["dia_span"],
            "phrase": rec["text"],
        },
        "injections": {
            "transposed": {"pair": f"{construct.fmt(diastolic)}/{construct.fmt(systolic)}",
                           "answer_if_computed": trans_written,
                           "answer_if_cued": trans_cued,
                           "separation": seed["separation"]},
            "lowered": {"pair": f"{construct.fmt(lowered_sys)}/{construct.fmt(diastolic)}",
                        "answer_if_computed": lowered_written,
                        "resolvable_arm": False,
                        "why_no_resolvable_arm":
                            "MAP moves by (dia-sys)/3, so a cued reading of this pair "
                            "would sit inside the 5% tolerance band and could not be scored"},
        },
        "conditions": conditions,
    }


def verify(item, note):
    """Assertions, not intentions. Every one of these can fail a build."""
    fails = []
    conds = item["conditions"]
    clean = next(c for c in conds if c["condition"] == "clean")["note"]
    if clean != note:
        fails.append("clean note is not the published note")

    for c in conds:
        if c["condition"] == "clean":
            continue
        region = single_edit_region(clean, c["note"])
        if region is None:
            fails.append(f"{c['shape']} note is identical to clean")
            continue
        head, a_end, b_end = region
        s0, d1 = item["blood_pressure"]["sys_span_in_clean_note"][0], \
            item["blood_pressure"]["dia_span_in_clean_note"][1]
        if head < s0 or a_end > d1:
            fails.append(f"{c['shape']} edit reaches outside the located pair")
        for word in construct.CUE_BLOCKLIST:
            if word in c["note"].lower() and word not in clean.lower():
                fails.append(f"{c['shape']} note introduces the cue word {word!r}")

    trans = [c for c in conds if c["shape"] == "transposed"]
    if len({c["note"] for c in trans}) != 1:
        fails.append("transposed contradiction and resolvable notes differ")
    if len({c["question"] for c in trans}) != len(trans):
        fails.append("resolvable question carries no cue")

    # Read the cue back out of the question and recompute from what it says, not
    # from what the builder intended it to say. The two came apart once.
    res = next((c for c in conds if c["condition"] == "resolvable"), None)
    if res is not None:
        m = re.search(r"treat\s+([\d.]+)\s+as the systolic and\s+([\d.]+)\s+as the diastolic",
                      res["question"])
        if not m:
            fails.append("resolvable cue does not parse")
        else:
            said_sys, said_dia = float(m.group(1)), float(m.group(2))
            if abs(mean_arterial_pressure(said_sys, said_dia) - res["correct_answer"]) > 1e-3:
                fails.append(
                    f"cue text names {said_sys:g}/{said_dia:g} -> "
                    f"{mean_arterial_pressure(said_sys, said_dia):.3f}, but the item records "
                    f"{res['correct_answer']}")
            if {said_sys, said_dia} != {item["blood_pressure"]["systolic"],
                                        item["blood_pressure"]["diastolic"]}:
                fails.append("cue names values that are not the note's own pair")

    for c in conds:
        if c["correct_action"] != "flag":
            continue
        found = checker.check(c["note"])["findings"]
        if not any(f.get("check") == "impossible_value"
                   and f.get("quantity") == "blood pressure" for f in found):
            fails.append(f"{c['shape']} note does not trip the deterministic checker")

    # The clean note must NOT trip it, or the family's claim is about our edit
    # rather than about the model.
    if any(f.get("check") == "impossible_value" and f.get("quantity") == "blood pressure"
           for f in checker.check(clean)["findings"]):
        fails.append("published note already trips the checker on blood pressure")
    return fails


def single_edit_region(a, b):
    if a == b:
        return None
    head = 0
    while head < min(len(a), len(b)) and a[head] == b[head]:
        head += 1
    tail = 0
    while (tail < min(len(a), len(b)) - head
           and a[len(a) - 1 - tail] == b[len(b) - 1 - tail]):
        tail += 1
    return head, len(a) - tail, len(b) - tail


def digest(seeds):
    payload = json.dumps([[s["note_id"], s["systolic"], s["diastolic"]] for s in seeds],
                         sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def do_select(target):
    rows = load_map_rows()
    kept, reasons = [], {}
    for r in rows:
        rec, why = screen(r)
        if rec:
            kept.append(rec)
        else:
            reasons[why] = reasons.get(why, 0) + 1
    chosen = choose(kept, target)
    for c in chosen:
        c.pop("span", None)
    out = {"calculator": "Mean Arterial Pressure (MAP)", "calculator_id": MAP_CALC_ID,
           "family": "B", "n_screened": len(rows), "n_eligible": len(kept),
           "n_selected": len(chosen), "rejections": reasons,
           "gates": {"one pressure in the note": True,
                     "entities agree with the note's text": True,
                     "published pair is possible": True,
                     "pressure carries a unit": True,
                     "transposition separable by more than": MIN_SEPARATION,
                     "lowered systolic at least": MIN_PLAUSIBLE_SYS},
           "seeds_digest": digest(chosen), "seeds": chosen}
    json.dump(out, open(SEEDS, "w"), indent=2)
    print(f"screened {len(rows)}   eligible {len(kept)}   selected {len(chosen)}")
    for k, v in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"   rejected {v:4}  {k}")
    print(f"digest {out['seeds_digest'][:16]}")
    print(f"wrote {os.path.relpath(SEEDS, ROOT)}")


def do_build():
    if not os.path.exists(SEEDS):
        sys.exit("no frozen seeds. Run: python3 family_b.py --select")
    suite = construct.run_regression_suite()
    if not suite["passed"]:
        print(suite.get("output", ""))
        sys.exit("Refusing to build. Known extraction failures must pass first.")
    print(f"regression suite: {suite['n_tests']} tests pass")

    frozen = json.load(open(SEEDS))
    notes = {}
    for r in load_map_rows():
        notes[r["Note ID"]] = r["Patient Note"]

    items, failures = [], []
    for seed in frozen["seeds"]:
        note = notes[seed["note_id"]]
        try:
            span = spans.find_blood_pressure(note, seed["systolic"], seed["diastolic"])
            seed = dict(seed, span=span)
            item = build_one(seed, note, lambda s, d: round(mean_arterial_pressure(s, d), 3))
            bad = verify(item, note)
            if bad:
                failures.append({"seed": seed["note_id"], "failures": bad})
                continue
            items.append(item)
        except (construct.BuildError, spans.NotFound, spans.Ambiguous) as exc:
            failures.append({"seed": seed["note_id"], "failures": [str(exc)]})

    doc = {"family": "B", "calculator": "Mean Arterial Pressure (MAP)",
           "seeds_digest": frozen["seeds_digest"],
           "regression_suite": {k: suite[k] for k in ("passed", "n_tests", "detail")},
           "n_seeds_attempted": len(frozen["seeds"]), "n_seeds_built": len(items),
           "n_items": sum(len(i["conditions"]) for i in items),
           "shapes": ["transposed", "lowered"],
           "conditions": ["clean", "contradiction", "resolvable"],
           "construction_rules": {
               "minimal_edit": "only the located systolic and diastolic digits are rewritten",
               "resolvable_note": "byte-identical to the transposed contradiction; the cue "
                                  "is appended to the question so the note is held fixed",
               "separability": f"transposition must move MAP by more than {MIN_SEPARATION:.0%}",
           },
           "failures": failures, "items": items}
    json.dump(doc, open(OUT, "w"), indent=2)
    print(f"seeds {len(frozen['seeds'])}   built {len(items)}   items {doc['n_items']}")
    for f in failures:
        print(f"   FAILED {f['seed']}: {f['failures']}")
    print(f"wrote {os.path.relpath(OUT, ROOT)}")
    return 1 if failures else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--select", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--target", type=int, default=TARGET_SEEDS)
    args = ap.parse_args()
    if args.select:
        do_select(args.target)
        return 0
    if args.build:
        return do_build()
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
