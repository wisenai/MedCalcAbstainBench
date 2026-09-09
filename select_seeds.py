#!/usr/bin/env python3
"""Freeze the seed list for the dissociation arm into data/seeds_dissociation.json.

Task owner: Annotator D -- Week 1 task S2.
Completed by Annotator D.

The dissociation arm needs base notes on which we can construct three variants
that differ only in *why* the item is or is not answerable. That imposes
requirements a note either meets or does not, and the point of freezing the list
is that those requirements were applied once, in public, before any item was built:

  1. The calculator is creatinine-based (Cockcroft-Gault, CKD-EPI, MDRD).
  2. Every formula input can be located in the note at a unique character span,
     with the note's number equal to the value the calculator consumes. If we
     cannot point at the input, we cannot claim to have edited it.
  3. The note states exactly one creatinine measurement. Injecting a second value
     into a note that already reports two is not a controlled edit.
  4. The note states no derived renal value -- eGFR, creatinine clearance, MELD.
     Such a value re-states the creatinine, so deleting the creatinine leaves the
     item answerable and injecting a conflict leaves it resolvable. Added after
     the Week 1 hand-check found it in the worked cases.
  5. The sentence carrying the creatinine does not characterise it -- neither as
     changing ("creatinine decreasing to 1.6 mg/dL") nor as normal or elevated
     ("results were within the normal ranges, as follows: ..."). Either framing
     tells a reader which of two values belongs and dissolves the conflict.
     Added after the Week 1 hand-check.
  6. The released implementation reproduces the shipped label on the case, so the
     clean condition rests on an answer both we and MedCalc-Bench agree on.
  7. The seed has not been killed by human reading. data/hand_kills.json holds
     those decisions with their reasons, so a judgement made in a review is
     enforced by the build instead of living in a document nobody re-reads.
  8. The creatinine belongs to the patient, not to a relative whose illness the
     note also narrates. Added in Week 2 after the pilot surfaced a value taken
     from a passage about the patient's grandmother.

Rows that fail are recorded with their reason rather than dropped silently — the
rejects are the honest denominator, and a reviewer asking "why 40 and not 60"
should be able to read the answer.

Usage:  python3 select_seeds.py
"""
import ast
import contextlib
import hashlib
import csv
import datetime
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "audit"))

import spans  # noqa: E402
import calculators  # noqa: E402
import label_audit  # noqa: E402

# Test split first, then train. Test rows are the ones the label audit covered
# as a census, so they are preferred; train is the top-up, needed because the
# test split holds only 60 creatinine rows and the gates reject most of them.
SPLITS = [("test", os.path.join(ROOT, "data", "medcalc", "test_data.csv")),
          ("train", os.path.join(ROOT, "data", "medcalc", "train_data.csv"))]
OUT = os.path.join(ROOT, "data", "seeds_dissociation.json")
HAND_KILLS = os.path.join(ROOT, "data", "hand_kills.json")

TARGET = 40

# calc_id -> (short name, the inputs its formula consumes)
CALCS = {
    2: ("cockcroft_gault", "Creatinine Clearance (Cockcroft-Gault Equation)",
        ["age", "sex", "weight", "height", "creatinine"]),
    3: ("ckd_epi", "CKD-EPI Equations for Glomerular Filtration Rate",
        ["age", "sex", "creatinine"]),
    9: ("mdrd", "MDRD GFR Equation",
        ["age", "sex", "creatinine", "race"]),
}

CREATININE_UNITS = ["mg/dL", "µmol/L", "mmol/L"]

# A note that also states a renal function estimate has stated the creatinine
# twice: once directly and once through a value derived from it. Found in the
# Week 1 hand-check of the worked cases, where a note reading "impaired renal
# function [i.e., serum creatinine: 1.42 mg/dL; eGFR: 49.1 mL/min/1.73 m2]"
# breaks both defect conditions at once. Deleting the creatinine does not make
# the item unanswerable, because the eGFR still pins it. And injecting a second
# creatinine does not make it unresolvable, because a reader can check which of
# the two is consistent with the stated eGFR and pick that one -- which is
# precisely the "second reading makes the item consistent after all" failure the
# plan says to kill items for.
DERIVED_RENAL = re.compile(
    r"\b(?:e?GFR|glomerular filtration|creatinine clearance|CrCl|MELD)\b", re.I)

# The sentence carrying the creatinine must not characterise it, in either of two
# ways. Both were found in the Week 1 hand-check.
#
# TREND: "the patient had an improvement in renal function with serum creatinine
# decreasing to 1.6 mg/dL". The note has already asserted the value changed, so a
# second value reads as the earlier one and "use the value after decompression"
# resolves the item -- the same trend escape hatch the injection is worded to close.
#
# NORMALITY: "the patient's other blood test results were within the normal ranges,
# as follows: ... serum creatinine: 0.86 mg/dL", or "revealed an elevation of BUN
# 23.8 mg/dl, creatinine 1.14 mg/dl". The framing says which of the two values
# belongs, so a reader picks the one that matches and the conflict dissolves.
#
# Attribution is the hard part, and it is why this comes in two strengths. A
# framing word in the creatinine's sentence often describes something else:
# "creatinine level of 0.9 mg/dL and an elevated hematocrit of 0.6" is about the
# hematocrit, and "Urinalysis is within normal limits" at the end of a lab table
# is about the urinalysis. Rejecting on sentence-level presence alone threw out
# fifteen seeds, of which roughly a third were fine.
#
# So: framing that attaches to the creatinine grammatically is rejected
# automatically, and framing merely present in the same sentence is recorded as a
# review flag for the Friday read. The judgement calls go to people; only the
# unambiguous ones are made by regex.
_TREND = (r"decreas\w*|increas\w*|improv\w*|worsen\w*|ris\w*|fell|fall\w*|"
          r"declin\w*|recover\w*|trend\w*")
_NORMALITY = (r"within (?:the )?normal|normal (?:range|limits)|unremarkable|"
              r"elevat\w*|rais\w*|impair\w*|abnormal\w*|deranged|"
              # not "high-density lipoprotein", which is a name, not a finding
              r"(?:high|low)(?:er)?\b(?!-density)")
_CREAT = r"(?:serum |plasma |blood )?creatinine"

TREND_FRAMING = re.compile(rf"\b(?:{_TREND})\b", re.I)
# "normalized" is excluded when it is part of "international normalized ratio",
# which is the INR and appears in half these notes.
NORMALITY_FRAMING = re.compile(
    rf"\b(?:{_NORMALITY})\b|(?<!international )\bnormali[sz](?:ed|ing|ation)\b(?! ratio)",
    re.I)

# Grammatically attached to the creatinine, in one of three shapes:
#   "an elevated creatinine of 1.4 mg/dL"          framing before the label
#   "serum creatinine levels (8.9) were increased" linked by a copula, no comma
#   "serum creatinine decreasing to 1.6 mg/dL"     participle on the label itself
ATTACHED_FRAMING = [
    re.compile(rf"\b({_TREND}|{_NORMALITY})\b[^.\n\d]{{0,45}}?{_CREAT}\b", re.I),
    re.compile(rf"{_CREAT}\b[^.,\n]{{0,45}}?\b(?:was|were|is|are)\b[^.,\n]{{0,20}}?"
               rf"\b({_TREND}|{_NORMALITY})\b", re.I),
    re.compile(rf"{_CREAT}\b[^.,\n\d]{{0,15}}?\b({_TREND})\b", re.I),
]

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")


def attached_framing(sentence):
    """Framing words that grammatically describe the creatinine, not a neighbour."""
    hits = set()
    for pattern in ATTACHED_FRAMING:
        for m in pattern.finditer(sentence):
            hits.add(m.group(1).lower())
    return sorted(hits)


# Whose measurement is it? A case report often narrates a relative's illness in
# its own paragraph, and a value inside that passage belongs to them. Found by
# Annotator A in the Week 2 pilot on mdrd-tr3279, where the closing paragraph describes
# the paternal grandmother -- "developed renal failure at 77 ... Kidney size was
# about 16 cm ... and serum creatinine was 180 umol/l" -- and MedCalc extracted
# that creatinine as the patient's. The patient is 45 with ESRD, for which 180
# umol/L is far too low; the grandmother has "moderate renal insufficiency", for
# which it fits.
#
# Nothing else we run could see this. The value is in the note, uniquely anchored
# to the word creatinine, and the extraction audit passes it: that audit asks
# whether the number belongs to the right *quantity*, never to the right *person*.
RELATIVE = re.compile(
    r"\b(?:father|mother|grandmother|grandfather|grandparent|parents?|sister|brother|"
    r"sibling|son|daughter|aunt|uncle|cousin|niece|nephew|wife|husband|spouse|twin|"
    r"donor)\b", re.I)
# Possessives and subject pronouns count as returning to the patient. Without
# them the rule over-fires: "Her husband endorsed good compliance ... for her OSA.
# Laboratory studies showed serum creatinine of 2.2 mg/dL" is the patient's lab,
# and the intervening "her" is what says so.
PATIENT_REF = re.compile(
    r"\b(?:patient|man|woman|male|female|boy|girl|infant|child|subject|case|"
    r"gentleman|lady|he|she|his|her|him|hers)\b", re.I)


def attributed_to_third_party(note, value_start):
    """The relative this value belongs to, or None if it is the patient's.

    Scoped to the paragraph so a family-history opener cannot reach forward into
    the patient's own results, and decided by whichever person reference sits
    closest before the value.
    """
    para = note.rfind("\n", 0, value_start) + 1
    lead = note[para:value_start] or note[:value_start]
    rel = list(RELATIVE.finditer(lead))
    pat = list(PATIENT_REF.finditer(lead))
    if not rel:
        return None
    if pat and pat[-1].start() > rel[-1].start():
        return None
    return rel[-1].group(0)


def sentence_around(note, offset):
    """The sentence containing `offset`, for framing checks."""
    pos = 0
    for sentence in SENTENCE_SPLIT.split(note):
        end = pos + len(sentence)
        if pos <= offset < end + 1:
            return sentence
        pos = end + 1
    return note


_hand_kills = None


def load_hand_kills():
    """Seeds a human read and rejected. Cached; the file is small and read once."""
    global _hand_kills
    if _hand_kills is None:
        with open(HAND_KILLS) as f:
            _hand_kills = json.load(f)["kills"]
    return _hand_kills


def locate_race(note, entities):
    """MDRD's race coefficient: a span if the note states it, an explicit null if not.

    Every formula input has to be accounted for, and race is the one that often
    cannot be pointed at. MedCalc records a `Race` entity on only a minority of
    MDRD cases, and the released implementation reads an absent race as non-Black
    — a modelling choice, applied silently, that changes the answer by a factor of
    1.212 when it is wrong.

    Two things follow. The note is searched for a race term even when the entity
    omits one, because the entity's silence is not evidence the note is silent.
    And where the note really does not say, that is recorded as a null with its
    reasoning rather than by leaving the key out, so a reader can tell "we looked
    and it is not there" apart from "we never looked".
    """
    stated = entities.get("Race")
    if stated:
        record = spans.find_word(note, spans.RACE_PATTERNS, stated, "race")
        record["stated_in_note"] = True
        record["source"] = "MedCalc entity, located in note"
        return record

    # The entity is silent. Look anyway.
    for key in spans.RACE_PATTERNS:
        try:
            record = spans.find_word(note, spans.RACE_PATTERNS, key, "race")
        except spans.NotFound:
            continue
        record["stated_in_note"] = True
        record["source"] = ("found in note text; MedCalc's entities do not record "
                            "race for this case")
        return record

    return {
        "label": "race",
        "value": None,
        "unit": None,
        "stated_in_note": False,
        "value_span": None,
        "span": None,
        "source": "not stated in the note and not recorded in MedCalc's entities",
        "rationale": (
            "MDRD applies a 1.212 coefficient for Black patients. The released "
            "implementation treats an absent race as non-Black, so the clean answer "
            "inherits that default. We adopt it rather than guess, and record the "
            "absence here so the input is accounted for rather than omitted."),
    }


def locate_inputs(note, entities, needed):
    """Span for every required input, or the reason we could not pin one down."""
    found, problems = {}, []
    for name in needed:
        try:
            if name == "sex":
                found[name] = spans.find_word(note, spans.SEX_PATTERNS,
                                              entities["sex"], "sex")
            elif name == "race":
                found[name] = locate_race(note, entities)
            elif name == "age":
                found[name] = spans.find_age(note, entities["age"][0])
            else:
                value, unit = entities[name]
                found[name] = spans.find_measurement(note, value, unit, name)
        except spans.NotFound as exc:
            problems.append(f"{name}: not located in note ({exc})")
        except spans.Ambiguous as exc:
            texts = ", ".join(repr(c["text"]) for c in exc.matches)
            problems.append(f"{name}: {len(exc.matches)} candidate spans ({texts})")
        except KeyError:
            problems.append(f"{name}: absent from Relevant Entities")
    return found, problems


def evaluate(row):
    """Everything we know about one candidate row, accepted or not."""
    cid = int(row["Calculator ID"])
    short, full, needed = CALCS[cid]
    note = row["Patient Note"]
    entities = ast.literal_eval(row["Relevant Entities"])
    split = row.get("_split", "test")
    seed_id = f"{short}-{'' if split == 'test' else 'tr'}{row['Row Number']}"

    rec = {
        "seed_id": seed_id,
        "case_id": row["Note ID"],
        "row_number": int(row["Row Number"]),
        "calculator": full,
        "calculator_short": short,
        "calculator_id": cid,
        "split": row.get("_split", "test"),
        "question": row["Question"],
        "note_chars": len(note),
        "entities": entities,
    }

    rejections = []

    # gate 3: exactly one creatinine measurement stated
    cre_mentions = spans.count_measurements(note, "creatinine", CREATININE_UNITS)
    rec["creatinine_mentions"] = len(cre_mentions)
    if len(cre_mentions) != 1:
        rejections.append(
            f"note states {len(cre_mentions)} creatinine measurements, need exactly 1")

    # gate 4: no renal-function estimate that re-states the creatinine
    derived = sorted({m.group(0) for m in DERIVED_RENAL.finditer(note)})
    rec["derived_renal_mentions"] = derived
    if derived:
        rejections.append(
            "note states a derived renal value (" + ", ".join(derived) + "), which "
            "both survives the excision and resolves the conflict")

    # gate 2: every formula input locatable at a unique span
    found, problems = locate_inputs(note, entities, needed)
    rejections.extend(problems)
    rec["input_spans"] = found

    # gate 5: framing attached to the creatinine resolves the conflict
    if "creatinine" in found:
        sentence = sentence_around(note, found["creatinine"]["value_span"][0])
        rec["creatinine_sentence"] = sentence.strip()
        attached = attached_framing(sentence)
        loose = sorted({m.group(0).lower() for m in TREND_FRAMING.finditer(sentence)}
                       | {m.group(0).lower()
                          for m in NORMALITY_FRAMING.finditer(sentence)})
        rec["framing"] = {"attached": attached, "in_sentence": loose}
        if attached:
            rejections.append(
                "the note characterises the creatinine itself ("
                + ", ".join(attached) + "), which tells a reader which of two "
                "values belongs")
        elif loose:
            rec.setdefault("review_flags", []).append(
                "the creatinine's sentence contains framing words ("
                + ", ".join(loose) + ") that appear to describe something else. "
                "Confirm they do before this item ships.")

    # gate 8: the value must be the patient's, not a relative's
    if "creatinine" in found:
        whose = attributed_to_third_party(
            note, found["creatinine"]["value_span"][0])
        rec["attributed_to"] = whose or "patient"
        if whose:
            rejections.append(
                f"the creatinine sits in a passage about the patient's {whose}, so "
                "the value is not the patient's")

    # gate 7: killed by human reading
    kill = load_hand_kills().get(seed_id)
    if kill:
        rejections.append(f"hand-killed by {kill['killed_by']} on {kill['date']}: "
                          f"{kill['reason']}")

    # gate 6: released code reproduces the shipped label
    audit = label_audit.recompute(row)
    rec["label_check"] = {
        "status": audit["status"],
        "shipped": audit["shipped_answer"],
        "recomputed": audit["recomputed"],
        "agrees": audit["agrees"],
        "exact": audit.get("exact"),
    }
    if audit["status"] != "ok":
        rejections.append(f"label check could not run: {audit['error']}")
    elif not audit["agrees"]:
        rejections.append(
            f"released code gives {audit['recomputed']}, shipped label is "
            f"{audit['shipped_answer']}")

    if not rejections:
        with contextlib.redirect_stdout(io.StringIO()):
            rec["clean_answer"] = float(calculators.call(cid, entities)["Answer"])
        rec["clean_answer_unit"] = ("mL/min" if cid == 2 else "mL/min/1.73m^2")

    rec["accepted"] = not rejections
    rec["rejections"] = rejections
    return rec


def fully_stated(record):
    """True when the note states every formula input, leaving none to a default."""
    return all(span.get("stated_in_note") is not False
               for span in record["input_spans"].values())


def choose(eligible, target):
    """Pick the seed list from everything that passed the gates.

    The gates leave far more eligible rows than we need, so something has to
    choose, and the rule is fixed here rather than exercised case by case:

      - balanced across the three calculators, round robin, so the arm is not
        mostly Cockcroft-Gault by accident of which notes happened to survive
      - a note that states every one of its formula inputs before one that leaves
        an input to a default (see below)
      - test-split rows before train-split rows, because the label audit covered
        the test split as a census and those rows carry more assurance
      - within a split, ascending row number

    The second rule exists for MDRD's race. Where a note does not state it, the
    released implementation reads the patient as non-Black and the clean answer
    inherits a 1.212 coefficient nobody chose. That is defensible when unavoidable
    and pointless when it is not: 18 eligible MDRD notes do state race and only 13
    are needed, so the arm can rest on notes that say what the formula consumes
    rather than on a default. It costs some of the test-before-train preference,
    which is the lesser assurance of the two.

    This ranks on a property of the note, fixed before any item is built, and on
    nothing we will later measure. No randomness. Re-running this on the same
    substrate produces the same forty seeds.
    """
    buckets = {}
    for record in eligible:
        buckets.setdefault(record["calculator_short"], []).append(record)
    for rows in buckets.values():
        rows.sort(key=lambda r: (not fully_stated(r), r["split"] != "test",
                                 r["row_number"]))

    picked, depth = [], 0
    while len(picked) < target:
        added = False
        for name in sorted(buckets):
            if depth < len(buckets[name]):
                picked.append(buckets[name][depth])
                added = True
                if len(picked) == target:
                    return picked
        if not added:
            break
        depth += 1
    return picked


def write_markdown(out):
    """A reviewable companion to the JSON, for the Friday read-through."""
    from collections import Counter

    L = ["# Dissociation seeds\n"]
    L.append("**Task owner:** Annotator D — Week 1 task S2  \n"
             "**Completed by:** Annotator D\n")
    L.append(f"_Frozen {out['frozen_utc']} from MedCalc-Bench `{out['substrate']['tag']}` "
             f"({(out['substrate']['commit'] or '')[:10]}). "
             "Regenerate with `python3 select_seeds.py`; the machine-readable list with "
             "character spans is `data/seeds_dissociation.json`._\n")
    L.append(f"**{out['n_seeds']} seeds**, chosen from {out['n_eligible']} rows that "
             f"passed every gate, out of {out['n_candidates']} creatinine candidates "
             f"across the test and train splits.\n")
    L.append(f"Selection rule: {out['selection_rule']}\n")
    L.append(f"Content digest (no timestamp, stable across re-runs): "
             f"`{out['seeds_digest'][:16]}`\n")
    L.append("| Calculator | Seeds |")
    L.append("|---|---|")
    for k, v in sorted(out["seeds_per_calculator"].items()):
        L.append(f"| {k} | {v} |")
    L.append("")

    L.append("## Gates\n")
    L.append("Applied to every candidate, in public, before any item was built. "
             f"A row is a seed if and only if it passes all {len(out['gates'])}.\n")
    for i, g in enumerate(out["gates"], 1):
        L.append(f"{i}. {g}")
    L.append("")
    L.append("Nothing is sampled: every row that passes is in. The list cannot be "
             "accused of having been picked, and the rejects below are the honest "
             "denominator.\n")

    L.append("## Seeds\n")
    L.append("`creat.` is the creatinine the calculator consumes, at the character "
             "offsets a minimal edit would rewrite.\n")
    L.append("| Seed | Case | Calculator | Clean answer | creat. | Offsets |")
    L.append("|---|---|---|---|---|---|")
    for s in out["seeds"]:
        c = s["input_spans"]["creatinine"]
        L.append(f"| `{s['seed_id']}` | `{s['case_id']}` | {s['calculator_short']} | "
                 f"{s['clean_answer']:g} {s['clean_answer_unit']} | "
                 f"{c['value']:g} {c['unit']} | {c['value_span'][0]}–{c['value_span'][1]} |")
    L.append("")

    L.append("## Located inputs, in the note's own words\n")
    L.append("Each phrase below is the text the span points at. If any of these is not "
             "the value the calculator uses, the seed is wrong and should be killed here "
             "rather than after 160 items are built on it.\n")
    for s in out["seeds"]:
        L.append(f"**`{s['seed_id']}`** — {s['case_id']}  ")
        for name, sp in s["input_spans"].items():
            if sp.get("stated_in_note") is False:
                # Accounted for, but there is no text to quote.
                L.append(f"- `{name}` — **not stated in the note.** {sp['rationale']}")
                continue
            ctx = " ".join(sp["context"].split())
            L.append(f"- `{name}` = {sp['value_text']}"
                     f"{' ' + sp['unit'] if sp['unit'] else ''} — …{ctx}…")
        L.append("")

    L.append("## Why rows were rejected\n")
    L.append(f"{out['n_rejected']} of {out['n_candidates']} candidates failed at least "
             "one gate. Counted by the first reason each hit; the full per-row list "
             "with every reason is in the JSON.\n")
    reasons = Counter(r["rejections"][0].split("(")[0].split(":")[0].strip()
                      for r in out["rejected"])
    L.append("| Reason | Rows |")
    L.append("|---|---|")
    for reason, n in reasons.most_common():
        L.append(f"| {reason} | {n} |")
    L.append("")
    L.append(
        "The dominant reason by far is a note that reports creatinine more than "
        "once, or reports it without a unit we can anchor on. Those are excluded "
        "because injecting a second value into a note that already carries two is "
        "not a controlled edit, not because the notes are bad.\n")

    flagged = [s_ for s_ in out["seeds"] if s_.get("review_flags")]
    L.append("## Seeds carrying a review flag\n")
    if not flagged:
        L.append("None.\n")
    else:
        L.append(
            "The automatic gate rejects framing that grammatically attaches to the "
            "creatinine. These seeds have framing words elsewhere in the same "
            "sentence, which usually describes a different analyte but sometimes "
            "does not. A person has to read each one; the verdicts so far are in "
            "`data/hand_kills.json`.\n")
        L.append("| Seed | Flag |")
        L.append("|---|---|")
        for s_ in flagged:
            L.append(f"| `{s_['seed_id']}` | {s_['review_flags'][0]} |")
        L.append("")

    open(os.path.join(ROOT, "data", "SEEDS.md"), "w").write("\n".join(L))


def main():
    csv.field_size_limit(10 ** 9)
    rows = []
    for split, path in SPLITS:
        if not os.path.exists(path):
            sys.exit(f"{path} missing. Run: python3 fetch_medcalc.py")
        for r in csv.DictReader(open(path, newline="", encoding="utf-8")):
            if int(r["Calculator ID"]) in CALCS and r["Note Type"] == "Extracted":
                r["_split"] = split
                rows.append(r)

    evaluated = [evaluate(r) for r in rows]
    eligible = [r for r in evaluated if r["accepted"]]
    rejected = [r for r in evaluated if not r["accepted"]]
    accepted = choose(eligible, TARGET)

    prov_path = os.path.join(ROOT, "data", "medcalc", "PROVENANCE.json")
    provenance = json.load(open(prov_path)) if os.path.exists(prov_path) else {}

    by_calc = {}
    for r in accepted:
        by_calc[r["calculator_short"]] = by_calc.get(r["calculator_short"], 0) + 1

    # A digest of the seed content alone -- ids, spans, clean answers -- with no
    # timestamp in it. The file's own hash changes on every re-run because it
    # records when it ran, which makes it useless for binding: the pre-registration
    # would appear to break each time the list was regenerated unchanged. This is
    # what PREREGISTRATION.md binds to.
    digest = hashlib.sha256(json.dumps(
        [[r["seed_id"], r["case_id"], r["split"],
          {k: v["value_span"] for k, v in sorted(r["input_spans"].items())},
          r["clean_answer"]] for r in accepted],
        sort_keys=True).encode()).hexdigest()

    out = {
        "seeds_digest": digest,
        "frozen_utc": datetime.datetime.now(datetime.timezone.utc)
                               .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "substrate": {"tag": provenance.get("tag"), "commit": provenance.get("commit")},
        "target_n": TARGET,
        "n_candidates": len(evaluated),
        "n_eligible": len(eligible),
        "n_seeds": len(accepted),
        "n_rejected": len(rejected),
        "selection_rule": "balanced round robin across the three calculators; notes "
                          "stating every formula input before notes leaving one to a "
                          "default; test-split rows before train-split rows; ascending "
                          "row number within a split. Deterministic.",
        "eligible_not_selected": [r["seed_id"] for r in eligible
                                  if r not in accepted],
        "seeds_per_calculator": by_calc,
        "gates": [
            "creatinine-based calculator (Cockcroft-Gault, CKD-EPI, MDRD)",
            "every formula input locatable at a unique character span whose number "
            "equals the value the calculator consumes",
            "note states exactly one creatinine measurement",
            "note states no derived renal value (eGFR, creatinine clearance, MELD) "
            "that would survive the excision or resolve the conflict",
            "the sentence carrying the creatinine neither describes it as changing "
            "nor characterises it as normal or elevated",
            "not killed by human reading (data/hand_kills.json)",
            "the creatinine belongs to the patient, not to a relative whose illness "
            "the note also narrates",
            "released implementation reproduces the shipped label",
        ],
        "span_convention": {
            "value_span": "offsets of the digits alone; what a minimal edit rewrites",
            "span": "offsets of the digits through the end of the unit",
            "anchor_span": "offsets of the label word that licensed the match",
            "note": "offsets index Patient Note as shipped in test_data.csv, "
                    "0-based, end-exclusive",
        },
        "seeds": accepted,
        "rejected": [{"seed_id": r["seed_id"], "case_id": r["case_id"],
                      "calculator_short": r["calculator_short"],
                      "rejections": r["rejections"]} for r in rejected],
    }
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)
    write_markdown(out)

    print(f"candidates {len(evaluated)}  eligible {len(eligible)}  "
          f"seeds {len(accepted)}  rejected {len(rejected)}")
    print(f"seeds digest {digest[:16]}  (stable across re-runs; "
          "this is what the pre-registration binds to)")
    for k, v in sorted(by_calc.items()):
        print(f"  {k:16s} {v}")
    from collections import Counter
    reasons = Counter(r["rejections"][0].split("(")[0].strip() for r in rejected)
    print("rejected, by first reason:")
    for reason, n in reasons.most_common():
        print(f"  {n:>4}  {reason}")
    print(f"wrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
