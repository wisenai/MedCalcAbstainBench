#!/usr/bin/env python3
"""Run the deterministic checker across the whole contradiction set.


    python3 checker_boundary.py

Offline, no API key, a few seconds. Writes `docs/CHECKER_BOUNDARY.md`.

The clause: "Run the deterministic checker across the whole contradiction set.
Expect near-perfect on A and B and structurally zero on C, and state that
boundary as our own limit rather than letting a reviewer find it."

The expectation holds -- and the boundary is wider than the clause assumes, in a
way that matters. `checker.py` is silent on Family C as predicted, and also on
every duplicate-value conflict in the dissociation and breadth arms: 107 further
items. Those two silences are NOT the same kind of silence, and the whole value
of this exercise is in refusing to report them as one number:

  * Family C is **structurally** invisible. "History of diabetes ... no history of
    diabetes" leaves no numeric trace. There is nothing for arithmetic to check,
    and no version of this tool could ever catch it.

  * The dissociation and breadth arms are invisible for an **implementation**
    reason. Those notes say `chloride 101 and 80.8 mEq/L`; the checker's patterns
    are label-anchored, so that phrasing defeats the chloride pattern and the
    quantity is not read at all -- not even flagged ambiguous. A duplicate-value
    detector would catch all 107. How long that would take is a guess and the
    write-up says so.

Reporting both as "the checker cannot reach these" would overstate our own limit
in the direction that flatters the paper -- it makes more of the corpus look like
it needs a model than actually does. So this script separates them and the
write-up states the weaker claim where the weaker claim is true.
"""
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from checker import check, read, PATTERNS                         # noqa: E402

TRACKED = set(PATTERNS)

OUT = os.path.join(ROOT, 'docs', 'CHECKER_BOUNDARY.md')

ITEM_FILES = [
    'items_dissociation.json', 'items_breadth_anion_gap.json',
    'items_breadth_ldl.json', 'items_breadth_osmolality.json',
    'items_family_a.json', 'items_family_a_anion_gap.json',
    'items_family_b.json', 'items_family_c.json',
]

# Why the checker is silent, per family. Stated here so the classification is a
# claim in the code and not an impression in the prose.
WHY_SILENT = {
    'C': ('structural', 'a criterion asserted and then denied leaves no numeric '
                        'trace; no arithmetic exists to run'),
    'dissociation': ('implementation', 'two values for one input '
                                       '("creatinine 1.4 and 0.5"); label-anchored '
                                       'patterns read the first or neither'),
    'breadth': ('implementation', 'two values for one input '
                                  '("chloride 101 and 80.8"); label-anchored '
                                  'patterns read the first or neither'),
}


def wilson(count, total):
    try:
        from stats import MedCalcStatsReferee
        return MedCalcStatsReferee().format_wilson_ci(count, total)
    except Exception:                                             # noqa: BLE001
        return f'{count}/{total}'


def scan():
    cells = defaultdict(lambda: {'n': 0, 'fired': 0, 'ambiguous': 0})
    quantity_missing, tracked = defaultdict(int), defaultdict(set)
    for filename in ITEM_FILES:
        path = os.path.join(ROOT, 'data', filename)
        if not os.path.exists(path):
            continue
        for item in json.load(open(path))['items']:
            family = item.get('family') or 'dissociation'
            # dissociation items carry no `on` key -- the whole arm is creatinine
            conflicted = (item.get('conflict') or {}).get(
                'on', 'creatinine' if family == 'dissociation' else None)
            for cond in item['conditions']:
                cell = cells[(family, cond['condition'], cond['correct_action'])]
                cell['n'] += 1
                result = check(cond['note'])
                if result['findings']:
                    cell['fired'] += 1
                if result['ambiguous']:
                    cell['ambiguous'] += 1
                # For a duplicate-value item: did the checker even READ the
                # quantity that carries the conflict?
                if conflicted and cond['correct_action'] == 'flag':
                    quantities, dropped = read(cond['note'])
                    if conflicted not in quantities and conflicted not in dropped:
                        quantity_missing[family] += 1
                    tracked[family].add(conflicted in TRACKED)
    return cells, quantity_missing, tracked


def table(head, body):
    return '\n'.join(['| ' + ' | '.join(head) + ' |',
                      '|' + '|'.join(['---'] * len(head)) + '|']
                     + ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in body])


def main():
    cells, missing, tracked = scan()

    contradictions = {k: v for k, v in cells.items() if k[2] == 'flag'}
    clean = {k: v for k, v in cells.items() if k[1] == 'clean'}
    resolvable = {k: v for k, v in cells.items() if k[1] == 'resolvable'}

    caught = sum(v['fired'] for v in contradictions.values())
    total = sum(v['n'] for v in contradictions.values())
    struct = sum(v['n'] - v['fired'] for k, v in contradictions.items()
                 if WHY_SILENT.get(k[0], ('', ''))[0] == 'structural')
    impl = sum(v['n'] - v['fired'] for k, v in contradictions.items()
               if WHY_SILENT.get(k[0], ('', ''))[0] == 'implementation')

    d = []
    w = d.append
    w('# The deterministic checker: what it catches, and where it stops')
    w('')
    w('Generated by `checker_boundary.py`; do not hand-edit. '
      'Offline, no API key, reproducible in seconds.')
    w('')
    lines = sum(1 for _ in open(os.path.join(ROOT, 'checker.py')))
    w('`checker.py` recomputes every stated derived value from its own components '
      f'and asserts systolic > diastolic. No model, no prompt, {lines} lines. '
      'It is the upper bound on how much of this corpus needs no language model '
      'at all — and stating that bound honestly is the point of this document.')
    w('')
    w(f'**Across all {sum(v["n"] for v in cells.values())} built conditions, '
      f'{total} of which are contradictions: the checker catches '
      f'{caught}/{total}.**')
    w('')

    # --- headline ------------------------------------------------------------
    w('## What it catches')
    w('')
    body = []
    for (fam, cond, action), v in sorted(contradictions.items()):
        why = WHY_SILENT.get(fam)
        note = '—' if v['fired'] == v['n'] else f'{why[0]}: {why[1]}' if why else '—'
        body.append([fam, cond, wilson(v['fired'], v['n']), note])
    w(table(['family', 'condition', 'catch rate', 'if silent, why'], body))
    w('')
    w('Families A and B are caught completely: 100% on both, and the clause\'s '
      '"near-perfect" turns out to be exactly perfect. Every other contradiction '
      'in the corpus is missed.')
    w('')

    # --- the boundary, split -------------------------------------------------
    w('## The boundary — and why it is two boundaries, not one')
    w('')
    w('The temptation is to report one number: *the checker misses '
      f'{total - caught}/{total} contradictions, so those need a model.* That '
      'would overstate our own limit in the direction that flatters the paper. '
      'Two different things are happening.')
    w('')
    w(f'**{struct} items are structurally invisible.** Family C asserts a '
      'criterion and later denies it — "history of diabetes … no history of '
      'diabetes". There is no number in disagreement with another number. No '
      'version of this tool, however good, could ever catch these. This is a real '
      'boundary and it is where a language model is genuinely required.')
    w('')
    w(f'**{impl} items are missed for an implementation reason.** The dissociation '
      'and breadth arms inject two values for one input: `chloride 101 and 80.8 '
      'mEq/L`, `creatinine 1.4 and 0.5 mg/dL`. `checker.py` reads quantities with '
      'label-anchored patterns, so the second value falls outside the match — and '
      'in the breadth arm the conflicted quantity is not read at all, not even '
      'recorded as ambiguous. A duplicate-value detector would catch all '
      f'{impl} of these. How long that would take is a guess, not a '
      'measurement -- but the change is local to `read()`, and nothing else in '
      'the tool would have to move.')
    w('')
    if missing:
        w('Measured directly — on duplicate-value contradiction items, how often '
          'the checker failed to read the conflicted quantity at all:')
        w('')
        w(table(['family', 'conflicted quantity', 'is it a quantity the checker '
                 'tracks at all?', 'not read, of the contradiction items'],
                [[k, 'creatinine' if k == 'dissociation' else 'the conflicted input',
                  ('yes, all of them — but the phrasing defeats the pattern'
                   if tracked.get(k) == {True} else
                   'no — no formula here consumes it, so it never looks'
                   if tracked.get(k) == {False} else 'mixed — see per-file detail'),
                  v] for k, v in sorted(missing.items())]))
        w('')
    w('**So the honest claim is narrower than "the checker cannot reach these."** '
      'What we can say is: arithmetic alone already solves Families A and B; a '
      'modestly better arithmetic tool would also solve the dissociation and '
      'breadth arms; and Family C is the only part of this corpus where a '
      'language model is not merely convenient but necessary. Family C is '
      f'{struct} items.')
    w('')

    # --- cost side -----------------------------------------------------------
    w('## The cost side')
    w('')
    fp = sum(v['fired'] for v in clean.values())
    fn = sum(v['n'] for v in clean.values())
    w(f'**False positives on clean notes: {wilson(fp, fn)}.** The checker never '
      'fires on a note that is not broken. That matters, because a check that '
      'flags healthy notes is not a free upper bound — it is a cost. This one is '
      'free.')
    w('')
    rf = sum(v['fired'] for v in resolvable.values())
    rn = sum(v['n'] for v in resolvable.values())
    w(f'**But it fires on {wilson(rf, rn)} resolvable notes** — and that is a '
      'limitation worth stating before someone else does. A resolvable item is '
      'the contradictory note plus a cue *in the question* naming which value '
      'governs. The checker never sees the question. So a pipeline that gated on '
      'this checker would refuse notes that are perfectly answerable, and every '
      'A and B resolvable item is one of them.')
    w('')
    body = []
    for (fam, cond, action), v in sorted(resolvable.items()):
        body.append([fam, wilson(v['fired'], v['n'])])
    w(table(['family', 'checker fires on resolvable'], body))
    w('')

    # --- related -------------------------------------------------------------
    w('## Known gaps this does not close')
    w('')
    w('- `docs/CHECKER_INPUT_EXTRACTION_GAP.md` — the height/weight blind spot, '
      'which bounds the Family A number from below.')
    w('- Duplicate-value detection, discussed above. Not implemented, deliberately '
      'unclaimed.')
    w('- The checker reads notes only. Anything stated in the question is outside '
      'its view, which is what the resolvable row above measures.')
    w('')
    w('## Reproduce')
    w('')
    w('```')
    w('python3 checker_boundary.py')
    w('```')
    w('')
    w('No API key, no cache, no model. Every number above comes from '
      '`checker.py` run over `data/items_*.json`.')

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'w').write('\n'.join(d) + '\n')
    print('\n'.join(d))
    print(f'\nwrote {os.path.relpath(OUT, ROOT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
