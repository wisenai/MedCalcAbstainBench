#!/usr/bin/env python3
"""Agreement and category distribution for the mechanism trace coding.

Task owner: Maia -- Week 3, "report that agreement alongside the category
distribution."

Sheets come from make_trace_sheets.py: 30 traces coded by all four people, 35
split one way each, 65 covered in total. Agreement is measured on the 30.
Distribution is reported over all 65.

    python3 analysis/trace_agreement.py
    python3 analysis/trace_agreement.py --allow-partial

Reports
-------
1. progress per coder
2. Fleiss' kappa on the overlap block, plus pairwise Cohen's kappa
3. the same, excluding items one coder had already coded solo in Week 2
4. category distribution by group (A / B / C / value conflict)
5. every overlap disagreement, with the trace, to adjudicate from
6. what the keyword pass in analysis/mechanism.py would have said, and how far
   that is from the humans -- the number that justifies doing this by hand
"""
import argparse
import collections
import csv
import glob
import io
import itertools
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _pilot_dir():
    """Directory holding labels/ and items/. Found, not assumed."""
    for base in (os.path.dirname(HERE), os.getcwd(), HERE):
        for d in (".", "pilot", ".."):
            p = os.path.normpath(os.path.join(base, d))
            if os.path.isdir(os.path.join(p, "labels")) and \
               os.path.isdir(os.path.join(p, "items")):
                return p
    return os.path.dirname(HERE)


PILOT = _pilot_dir()
LABELS = os.path.join(PILOT, "labels")
KEY_PATH = os.path.join(PILOT, "items", "_trace_coding_key.json")

CATEGORIES = ["N", "A", "D"]
CATEGORY_NAME = {
    "N": "never represented",
    "A": "acknowledged, then computed",
    "D": "declined",
}
GROUP_NAME = {"A": "Family A", "B": "Family B", "C": "Family C",
              "VC": "value conflict"}

# The keyword pass this task replaces. Copied verbatim from analysis/mechanism.py.
# If that regex changes, this comparison is stale and must be re-copied.
NAMES = re.compile(
    r"contradict|impossib|inconsist|conflict|cannot both|transpos|revers|"
    r"discrepan|mismatch|does ?n.?t match|disagree|implausib|out of range|"
    r"erroneous|both .{0,60}(deny|denied|no history|not present|absent)",
    re.I,
)


def read_sheet(path):
    """Return (preamble_lines, fieldnames, rows). Preamble is left untouched."""
    with open(path, newline="", encoding="utf-8") as fh:
        raw = fh.read()
    rows = list(csv.reader(io.StringIO(raw)))
    header_at = next(i for i, r in enumerate(rows) if r and r[0] == "row")
    fields = rows[header_at]
    data = [dict(zip(fields, r)) for r in rows[header_at + 1:] if r]
    return rows[:header_at], fields, data


def normalise(code):
    code = str(code or "").strip().upper()
    return code if code in CATEGORIES else None


def load():
    if not os.path.exists(KEY_PATH):
        sys.exit(f"no {KEY_PATH}\nrun: python3 make_trace_sheets.py")
    key = json.load(open(KEY_PATH))

    codes = {}       # who -> item -> code
    traces = {}      # item -> row dict
    assigned = {}    # who -> set of items in their sheet
    for path in sorted(glob.glob(os.path.join(LABELS, "traces_*.csv"))):
        who = os.path.basename(path)[len("traces_"):-len(".csv")]
        _, fields, data = read_sheet(path)
        if "item" not in fields:
            sys.exit(f"{path} has no item column -- it predates the split "
                     "design.\nrun: python3 make_trace_sheets.py")
        codes[who] = {r["item"]: normalise(r.get("code")) for r in data}
        assigned[who] = {r["item"] for r in data}
        for r in data:
            traces.setdefault(r["item"], r)
    return key, codes, traces, assigned


def cohen(pairs):
    if not pairs:
        return None
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    fa = collections.Counter(a for a, _ in pairs)
    fb = collections.Counter(b for _, b in pairs)
    expected = sum((fa[c] / n) * (fb[c] / n) for c in CATEGORIES)
    if expected >= 1.0:
        return 1.0
    return (observed - expected) / (1 - expected)


def fleiss(table):
    """table: per-item category counts, same number of raters on every item."""
    if not table:
        return None
    n_raters = sum(table[0])
    if n_raters < 2 or any(sum(row) != n_raters for row in table):
        return None
    n_items = len(table)
    p_i = [(sum(c * c for c in row) - n_raters) / (n_raters * (n_raters - 1))
           for row in table]
    p_bar = sum(p_i) / n_items
    p_j = [sum(row[j] for row in table) / (n_items * n_raters)
           for j in range(len(CATEGORIES))]
    p_e = sum(p * p for p in p_j)
    return 1.0 if p_e >= 1.0 else (p_bar - p_e) / (1 - p_e)


def majority(votes):
    counts = collections.Counter(v for v in votes if v)
    if not counts:
        return None
    top, n = counts.most_common(1)[0]
    return None if list(counts.values()).count(n) > 1 else top


def _load_rr():
    """rr.parse, if importable. Imported once, not once per trace."""
    if PILOT not in sys.path:
        sys.path.insert(0, PILOT)
    try:
        import rr
        return rr.parse
    except Exception:
        return None


_RR_PARSE = _load_rr()


def keyword_pass(trace):
    """What mechanism.py's regex would call this trace."""
    final = trace.get("final_output", "") or ""
    reasoning = trace.get("reasoning_trace", "") or ""
    if _RR_PARSE is not None:
        try:
            action, _ = _RR_PARSE(final)
            if action == "abstain":
                return "D"
        except Exception:
            pass
    return "A" if NAMES.search(reasoning) else "N"


def agreement_block(items, codes, coders, label):
    """Fleiss + pairwise over items every coder in `coders` has coded."""
    usable = [i for i in items if all(codes[w].get(i) for w in coders)]
    print(f"\n  {label}")
    print(f"    items coded by all {len(coders)}: {len(usable)}/{len(items)}")
    if not usable:
        return
    table = [[[codes[w][i] for w in coders].count(c) for c in CATEGORIES]
             for i in usable]
    k = fleiss(table)
    if k is not None:
        print(f"    Fleiss' kappa (3-way): {k:>6.3f}")
    unanimous = sum(1 for i in usable if len({codes[w][i] for w in coders}) == 1)
    print(f"    unanimous: {unanimous}/{len(usable)} "
          f"({100 * unanimous / len(usable):.0f}%)")
    for a, b in itertools.combinations(sorted(coders), 2):
        pairs = [(codes[a][i], codes[b][i]) for i in usable]
        k = cohen(pairs)
        agree = sum(x == y for x, y in pairs)
        print(f"      {a:>8} vs {b:<8} kappa {k:>6.3f}   "
              f"agree {agree}/{len(pairs)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-partial", action="store_true",
                    help="report before every sheet is finished")
    args = ap.parse_args()

    key, codes, traces, assigned = load()
    overlap = [i for i, v in key.items() if v["in_overlap"]]
    tainted = {i for i in overlap if key[i]["prior_solo_coded"]}

    print("=" * 70)
    print("TRACE CODING -- PROGRESS")
    print("=" * 70)
    for who in sorted(codes):
        done = sum(1 for v in codes[who].values() if v)
        print(f"  {who:>10}  {done:>3}/{len(assigned[who])}")
    print(f"\n  design: {len(overlap)} overlap + "
          f"{len(key) - len(overlap)} split = {len(key)} traces")

    committed = {w: c for w, c in codes.items() if any(c.values())}
    if len(committed) < 2:
        print("\n  agreement needs at least two coders to have committed")
        return

    unfinished = [w for w in committed
                  if sum(1 for v in committed[w].values() if v)
                  < len(assigned[w])]
    if unfinished and not args.allow_partial:
        print(f"\n  still coding: {', '.join(sorted(unfinished))}")
        print("  the sheets say do not compare until every file is pushed.")
        print("  --allow-partial to override.")
        return

    coders = sorted(committed)
    print()
    print("=" * 70)
    print("AGREEMENT -- overlap block only")
    print("=" * 70)
    agreement_block(overlap, committed, coders, "all overlap items")

    if tainted:
        clean = [i for i in overlap if i not in tainted]
        print(f"\n  {len(tainted)} overlap items were hand-coded solo in Week 2")
        print("  (docs/mechanism_traces_value_conflict_labels.csv). That "
              "coder's")
        print("  judgement on them is not independent of the earlier pass.")
        agreement_block(clean, committed, coders,
                        "excluding those items -- report this one")

    # ---- distribution over everything coded ---------------------------
    print()
    print("=" * 70)
    print("CATEGORY DISTRIBUTION -- all coded traces")
    print("=" * 70)
    final, unresolved = {}, []
    for item, meta in key.items():
        votes = [committed[w].get(item) for w in committed
                 if item in assigned.get(w, ())]
        votes = [v for v in votes if v]
        if not votes:
            continue
        label = majority(votes) if meta["in_overlap"] else votes[0]
        if label is None:
            unresolved.append(item)
        else:
            final[item] = label

    by_group = collections.defaultdict(collections.Counter)
    coded_by = collections.defaultdict(collections.Counter)
    for item, label in final.items():
        g = key[item]["group"]
        by_group[g][label] += 1
        coded_by[g]["4" if key[item]["in_overlap"] else "1"] += 1

    print("  " + " " * 22 + "".join(f"{c:>6}" for c in CATEGORIES)
          + "     n   4-coded  1-coded")
    for g in ["A", "B", "C", "VC"]:
        if g not in by_group:
            continue
        row = by_group[g]
        cells = "".join(f"{row[c]:>6}" for c in CATEGORIES)
        print(f"  {GROUP_NAME[g]:<22}{cells}{sum(row.values()):>6}"
              f"{coded_by[g]['4']:>10}{coded_by[g]['1']:>9}")
    total = collections.Counter()
    reliability = collections.Counter()
    for g in by_group:
        total.update(by_group[g])
        reliability.update(coded_by[g])
    n = sum(total.values())
    print("  " + "-" * 63)
    print(f"  {'all':<22}" + "".join(f"{total[c]:>6}" for c in CATEGORIES)
          + f"{n:>6}{reliability['4']:>10}{reliability['1']:>9}")
    if n:
        print("  " + " " * 22
              + "".join(f"{100 * total[c] / n:>5.0f}%" for c in CATEGORIES))
    for c in CATEGORIES:
        print(f"    {c} = {CATEGORY_NAME[c]}")
    print("\n  4-coded rows carry a four-way majority. 1-coded rows are one\n"
          "  person's judgement. Say which is which in the paper.")
    if unresolved:
        print(f"\n  no majority on {len(unresolved)} overlap items -- "
              "adjudicate before reporting")
        for item in unresolved:
            votes = "  ".join(f"{w}={committed[w].get(item) or '-'}"
                              for w in coders)
            print(f"    {item}  {votes}")

    # ---- disagreements -------------------------------------------------
    print()
    print("=" * 70)
    print("DISAGREEMENTS IN THE OVERLAP BLOCK")
    print("=" * 70)
    disagreed = [i for i in overlap
                 if len({committed[w][i] for w in coders
                         if committed[w].get(i)}) > 1]
    if not disagreed:
        print("  none")
    for item in disagreed:
        votes = "  ".join(f"{w}={committed[w].get(item) or '-'}" for w in coders)
        print(f"  {item}  [{GROUP_NAME[key[item]['group']]}]  {votes}")
        print(f"      {(traces[item].get('reasoning_trace') or '')[:120]}...")

    # ---- versus the keyword pass ---------------------------------------
    print()
    print("=" * 70)
    print("HUMAN vs THE KEYWORD PASS")
    print("=" * 70)
    print("  how analysis/mechanism.py's regex would have sorted the same traces")
    pairs, mismatches = [], []
    for item, human in final.items():
        auto = keyword_pass(traces[item])
        pairs.append((human, auto))
        if human != auto:
            mismatches.append((item, human, auto))
    if pairs:
        agree = sum(a == b for a, b in pairs)
        print(f"\n  agree {agree}/{len(pairs)} "
              f"({100 * agree / len(pairs):.0f}%)   "
              f"Cohen's kappa {cohen(pairs):.3f}")
        auto_counts = collections.Counter(a for _, a in pairs)
        human_counts = collections.Counter(h for h, _ in pairs)
        print("\n  " + " " * 20 + "".join(f"{c:>6}" for c in CATEGORIES))
        print("  humans" + " " * 14
              + "".join(f"{human_counts[c]:>6}" for c in CATEGORIES))
        print("  keyword pass" + " " * 8
              + "".join(f"{auto_counts[c]:>6}" for c in CATEGORIES))
        if mismatches:
            print(f"\n  differs on {len(mismatches)}")
            for item, human, auto in mismatches[:20]:
                print(f"    {item}  human={human}  keyword={auto}  "
                      f"[{GROUP_NAME[key[item]['group']]}]")
            if len(mismatches) > 20:
                print(f"    ... and {len(mismatches) - 20} more")


if __name__ == "__main__":
    main()
