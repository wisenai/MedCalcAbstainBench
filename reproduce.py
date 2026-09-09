#!/usr/bin/env python3
"""One entry point for MedCalcAbstain-Bench.

Every stage the paper reports, in the order it runs, with the paper claim each
stage produces. Run a single stage by name or the whole chain.

    python3 reproduce.py verify        # offline, no API key, no network
    python3 reproduce.py analyze       # rebuild every reported table
    python3 reproduce.py --list
    python3 reproduce.py all

Stages that call a provider need OPENROUTER_API_KEY and are marked NETWORK.
Nothing else touches the network. The construction and analysis stages read
what is committed under data/ and are deterministic.
"""
import argparse
import subprocess
import sys

STAGES = [
    ("verify", "verify_all.py", False,
     "Re-derives every edit span, flips every rule-based criterion, re-checks "
     "the item sets and their digests. Appendix C."),
    ("seeds", "select_seeds.py", False,
     "Eight ordered gates over the creatinine candidates; writes the 40 "
     "dissociation seeds and the rejection record. Appendix A."),
    ("construct", "construct.py", False,
     "Builds clean, missing, conflicting and resolvable from each seed by one "
     "located edit. Methods, Condition Construction."),
    ("families", None, False,
     "family_a.py, family_b.py, family_c.py, breadth_conflict.py: the three "
     "contradiction families and the breadth set. Methods."),
    ("flip", "flip_order.py", False,
     "Rebuilds the dissociation notes with the two conflicting values swapped. "
     "Reversed-order control."),
    ("elicit", "full_grid.py", True,
     "NETWORK. 676 conditions x 5 models x 4 prompts = 13,520 responses, "
     "cached by content hash. Appendix B."),
    ("join", "join_grid.py", False,
     "Joins cached completions to items across the four formats."),
    ("analyze", "analyze_flag_rates.py", False,
     "Flag rate by condition, by family, and by model. Tables 4-7."),
    ("validity", "analyze_validity.py", False,
     "Applies the pre-registered 50 percent clean-accuracy threshold. Table 3."),
    ("silent", "analyze_silent_commit.py", False,
     "Silent-commit rate as its own table. Tables 8-10."),
    ("judge", "analyze_judge_and_mcq.py", False,
     "Judge agreement per family and the open-ended vs MCQ delta. Tables 11-12."),
    ("program-aided", "analyze_program_aided.py", False,
     "The program-aided arm, reported separately and marked low-confidence."),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", nargs="?", default="--list")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list or a.stage == "--list":
        w = max(len(s[0]) for s in STAGES)
        for name, script, net, desc in STAGES:
            tag = "NETWORK" if net else "offline"
            print(f"  {name:<{w}}  [{tag}]  {desc}")
            if script:
                print(f"  {'':<{w}}            {script}")
        return 0

    todo = STAGES if a.stage == "all" else [s for s in STAGES if s[0] == a.stage]
    if not todo:
        print(f"unknown stage {a.stage!r}; use --list", file=sys.stderr)
        return 2

    for name, script, net, _ in todo:
        if script is None:
            print(f"[{name}] run the family scripts individually; see --list")
            continue
        print(f"\n=== {name} ({script}) ===", flush=True)
        r = subprocess.run([sys.executable, script])
        if r.returncode != 0:
            print(f"stage {name} failed with exit {r.returncode}", file=sys.stderr)
            return r.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
