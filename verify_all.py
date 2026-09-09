#!/usr/bin/env python3
"""One command that checks whether the construction still holds.

Task owner: Annotator D.
Completed by Annotator D.

The construction side of this project makes a handful of claims: that the item
sets on disk were built from the seed lists that sit beside them, that every edit
lands on the span the calculator reads, that the pre-registration's bound
artifacts are the files actually present, that the criteria the rule-based scores
depend on are really read, and that the known extraction failures still fail. Each
of those has a checker, and until now you had to know all six and the order to run
them in. That makes reproducibility a thing you assert rather than a thing anyone
can confirm in one step.

    python3 verify_all.py

Offline, no API key, no network. Exits non-zero if any check fails, so it works
as a pre-commit or CI gate.

Two checks write a file, and both are idempotent: `verify_anchoring.py` rewrites
`data/anchoring_report.json` and `audit/substrate_defects.py` rewrites
`audit/substrate_defects.json`, each with the same content it had before. Nothing
else is touched, and no item set or digest is regenerated. This verifies what is
on disk; it does not rebuild it.
"""
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

EXPECTED_ITEMS = {
    "items_dissociation": 160, "items_family_a": 90,
    "items_family_a_anion_gap": 15, "items_family_b": 120,
    "items_family_c": 90, "items_breadth_anion_gap": 75,
    "items_breadth_osmolality": 75, "items_breadth_ldl": 51,
}
PAIRED = ["family_a", "family_a_anion_gap", "family_b", "family_c",
          "breadth_anion_gap", "breadth_osmolality", "breadth_ldl"]

results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""))
    return ok


def run(name, argv, needle=None):
    """Run a script and pass on a zero exit, optionally requiring a phrase."""
    try:
        p = subprocess.run([PY] + argv, capture_output=True, text=True, cwd=ROOT)
    except Exception as exc:
        return record(name, False, str(exc))
    out = p.stdout + p.stderr
    ok = p.returncode == 0 and (needle is None or needle in out)
    tail = next((l for l in reversed(out.strip().splitlines()) if l.strip()), "")
    return record(name, ok, tail[:70])


def check_items():
    total, ok = 0, True
    for stem, want in EXPECTED_ITEMS.items():
        p = os.path.join(ROOT, "data", f"{stem}.json")
        if not os.path.exists(p):
            ok = record(f"item set {stem}", False, "missing") and ok
            continue
        got = json.load(open(p))["n_items"]
        total += got
        ok = record(f"item set {stem} = {want}", got == want, f"got {got}") and ok
    return record("676 conditions in total", total == 676, f"got {total}") and ok


def check_digests():
    ok = True
    for stem in PAIRED:
        s = json.load(open(os.path.join(ROOT, "data", f"seeds_{stem}.json")))["seeds_digest"]
        i = json.load(open(os.path.join(ROOT, "data", f"items_{stem}.json")))["seeds_digest"]
        ok = record(f"seed/item digest {stem}", s == i) and ok
    d = json.load(open(os.path.join(ROOT, "data", "seeds_dissociation.json")))["seeds_digest"][:16]
    return record("dissociation digest pinned", d == "16d121a94b66b7cd", d) and ok


def check_prereg():
    """Every hash PREREGISTRATION.md §2 binds must be the file on disk.

    §2 says a changed hash means the registration no longer applies until it is
    re-registered, so this is the check that makes that sentence enforceable
    rather than decorative.
    """
    pre = open(os.path.join(ROOT, "PREREGISTRATION.md")).read()
    try:
        sec = pre[pre.index("## 2. Bound artifacts"):pre.index("## 3.")]
    except ValueError:
        return record("prereg section 2 present", False)
    ok = True
    for path, expected in re.findall(r"\|\s*`([a-z_/.]+\.(?:py|json))`\s*\|\s*`([0-9a-f]{16})`\s*\|", sec):
        if "seeds_dissociation" in path:
            continue
        full = os.path.join(ROOT, path)
        if not os.path.exists(full):
            ok = record(f"bound {path}", False, "missing") and ok
            continue
        got = hashlib.sha256(open(full, "rb").read()).hexdigest()[:16]
        ok = record(f"bound {path}", got == expected, f"{expected} vs {got}") and ok
    return ok


def check_no_retired_seeds():
    """Scored rows must reference seeds that are still in the item sets.

    Amendment 8 retired `mdrd-tr3279`. A scored file still carrying it is
    reporting numbers from a seed that no longer exists, which is exactly the
    failure this catches.
    """
    current = set()
    for p in [os.path.join(ROOT, "data", "items_dissociation.json")] + \
             glob.glob(os.path.join(ROOT, "data", "items_family_*.json")) + \
             glob.glob(os.path.join(ROOT, "data", "items_breadth_*.json")):
        for it in json.load(open(p))["items"]:
            current.add(it["seed_id"])
    ok = True
    import csv
    csv.field_size_limit(10 ** 7)
    for f in ("week2_scored.csv", "week3_scored.csv"):
        p = os.path.join(ROOT, "data", f)
        if not os.path.exists(p):
            continue
        scored = {r["seed_id"] for r in csv.DictReader(open(p))}
        stale = sorted(scored - current)
        ok = record(f"{f} has no retired seeds", not stale,
                    ", ".join(stale[:3]) if stale else "") and ok
    return ok


def main():
    print("Construction checks. Offline, no API key.\n")

    print("Suites")
    run("regression suite", ["tests/test_regression.py"], "OK")
    run("cache-to-item join tests", ["tests/test_assemble.py"], "OK")

    print("\nAnchoring and criteria")
    run("every edit lands on the consumed span", ["verify_anchoring.py"],
        "seeds with a failure: 0")
    if os.path.isdir(os.path.join(ROOT, "data", "medcalc")):
        run("rule-based criteria are load-bearing", ["verify_criteria.py"],
            "Every mapped criterion is load-bearing")
        run("substrate defects still reproduce", ["audit/substrate_defects.py"])
    else:
        record("criteria + substrate checks", True,
               "skipped, data/medcalc absent (run fetch_medcalc.py)")

    print("\nItem sets")
    check_items()

    print("\nDigests")
    check_digests()

    print("\nPre-registration section 2")
    check_prereg()

    print("\nScored data")
    check_no_retired_seeds()

    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)} of {len(results)} checks pass")
    if failed:
        print("\nfailing:")
        for n in failed:
            print(f"  {n}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
