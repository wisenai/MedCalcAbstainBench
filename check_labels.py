#!/usr/bin/env python3
"""Fail if mitigation numbers appear anywhere without the non-comparability label.


    python3 check_labels.py            # check
    python3 check_labels.py --list     # show what it considers a mitigation doc

The clause says "everywhere they appear", and everywhere is not something a
person remembers under deadline. This makes it mechanical: any tracked markdown
or CSV that reports mitigation-arm results must carry the label, and CI fails if
one does not.

**This is a heuristic and says so.** It detects a mitigation document by the names
that only the mitigation arm uses -- `inline_consistency`, `detector_only`, the
arm labels, `mitigation_`. It cannot detect a number retyped into prose with no
surrounding vocabulary, and nothing can. What it does catch is the common case: a
table copied into another document, or a new report generated without the caption.
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# Vocabulary that only mitigation-arm output uses.
MARKERS = [
    r'\binline_consistency\b', r'\bdetector_only\b', r'\bdetector_scoped\b',
    r'\bmitigation[_ ]arm\b', r'\bmitigation_scores\b',
    r'verifier pass', r'verifier, advisory', r'verifier, GATING',
]

# Any one of these counts as labelled.
LABELS = [
    'NOT COMPARABLE TO THE UNPROMPTED HEADLINE',
    'Cued by design',
    'cued by design',
    'not comparable to the unprompted',
]

# Files that discuss the label rather than report numbers under it.
EXEMPT = {'the non-comparability note (not released)', 'check_labels.py', 'the mitigation arm (not released)'}

# A table row with a rate in it -- the thing that must not travel unlabelled.
RATE = re.compile(r'\d+/\d+ \(\d+\.\d%')


def scan(path):
    rel = os.path.relpath(path, ROOT)
    if rel.replace(os.sep, '/') in EXEMPT:
        return None
    try:
        text = open(path, encoding='utf-8', errors='replace').read()
    except OSError:
        return None
    if not any(re.search(m, text) for m in MARKERS):
        return None                       # not a mitigation document
    if not RATE.search(text) and not path.endswith('.csv'):
        return None                       # mentions the arm but reports no rates
    if path.endswith('.csv'):
        first = text.split('\n', 1)[0]
        return None if 'comparability' in first else (rel, 'no `comparability` column')
    if any(l in text for l in LABELS):
        # markdown: also require the label near each table, not only once
        missing = [h for h in re.findall(r'^## .+$', text, re.M)
                   if 'deterministic checker' not in h
                   and not _labelled_under(text, h)]
        if missing:
            return (rel, 'unlabelled section(s): ' + '; '.join(m[3:40] for m in missing))
        return None
    return (rel, 'no non-comparability label at all')


def _labelled_under(text, heading):
    """Is there a label within the few lines after this heading?"""
    i = text.index(heading) + len(heading)
    window = text[i:i + 400]
    return any(l in window for l in LABELS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--list', action='store_true')
    args = ap.parse_args()

    problems, checked = [], []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs
                   if d not in {'.git', 'cache', '__pycache__', 'node_modules'}]
        for f in files:
            if not f.endswith(('.md', '.csv')):
                continue
            p = os.path.join(base, f)
            r = scan(p)
            if r is None:
                if args.list:
                    text = open(p, encoding='utf-8', errors='replace').read()
                    if any(re.search(m, text) for m in MARKERS):
                        checked.append(os.path.relpath(p, ROOT))
            else:
                problems.append(r)

    if args.list:
        print('mitigation documents that pass:')
        for c in sorted(checked):
            print('   ', c)
        print()

    if problems:
        print('UNLABELLED MITIGATION RESULTS:\n')
        for rel, why in sorted(problems):
            print(f'  {rel}\n      {why}')
        print('\nWording to use: the non-comparability note (not released) §2')
        return 1
    print(f'ok — every mitigation document carries the label '
          f'({len(checked) if args.list else "checked"} files)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
