# MedCalcAbstainBench

When a language model is used as a clinical calculator, it reads a patient note
and returns a number a clinician may act on. Existing benchmarks only ever hand
it a clean note. Real electronic health records are not clean.

This benchmark asks what a model does when the note cannot be trusted. It takes
202 published notes across eleven clinical calculators and rewrites each one in
matched conditions that differ by a single located phrase: the required value
left **intact**, **removed**, **contradicted**, or contradicted alongside a
question naming which of the two values to use. That last pair is byte-identical;
only the question differs. So when a model answers the cued version correctly and
says nothing about the conflict in its twin, silence is a decision rather than a
reading failure.

The headline result is that models decline on 98% of notes with a value deleted
and 64% of the same notes with that value contradicted instead.

## Quickstart

```bash
pip install -r requirements.txt      # analysis deps; verification needs none
python3 fetch_medcalc.py             # pulls MedCalc-Bench v1.0, pinned to a tag
python3 verify_all.py                # expect: 29 of 29 checks pass
python3 reproduce.py analyze         # rebuilds the reported tables
```

`fetch_medcalc.py` is a required setup step, not an optional one. We do not
redistribute MedCalc-Bench; the script downloads it from the official GitHub
release, pinned to `version-1.0` and verified against that tag's commit SHA, and
writes `data/medcalc/`. Standard library only, about 44 MB.

Skip it and `verify_all.py` reports 28 of 29: the anchoring check imports a
calculator module that is not vendored here and cannot run without it.

Nothing above calls a model. Elicitation is a separate step, below.

## What reproduces

**Analysis, offline, about a minute.** Re-scores all 13,520 cached completions
from raw response text and rebuilds every table.

```bash
python3 reproduce.py analyze          # flag rate by condition, family, model
python3 reproduce.py validity         # clean accuracy and the 50% threshold
python3 reproduce.py silent           # silent-commit rate
python3 reproduce.py program-aided    # the low-confidence arm
```

Output lands in `docs/`. Against the paper these come back identical, numerator,
denominator and both interval bounds:

| Table | Values |
|---|---|
| Flag rate by condition | clean 3.8, missing 98.0, value-conflict 64.0, resolvable 2.2, contradiction 22.8 |
| Flag rate by family | A 1.7, B 2.8, C 24.0, breadth 13.9, dissociation 41.1 |
| Flag rate by model | 26.5, 20.4, 17.8, 14.9, 9.6 |
| Clean accuracy | 76.2 through 88.1 |
| Silent commit | missing 1.5, value-conflict 23.5, resolvable 95.4, contradiction 67.6 |

**Construction, offline, no dependencies.** `verify_all.py` re-derives every
edit span, flips every scored criterion, and re-checks the item sets against
their digests. Appendix C.

**Elicitation, network, costs money.** Not part of any check above.

```bash
export OPENROUTER_API_KEY=...
python3 reproduce.py elicit           # 676 conditions x 5 models x 4 prompts
```

Responses cache by content hash, so a rerun resumes rather than repaying.
Re-querying will not return the committed responses byte for byte: decoding uses
provider defaults at one sample per cell, which the paper's Limitations names as
the variance it does not bound.

`judge` also needs the key. Every other stage is deterministic and offline.

## Stages

`python3 reproduce.py --list` prints these with the paper claim each produces.

| Stage | Produces | Paper |
|---|---|---|
| `verify` | The construction check | Appendix C |
| `seeds` | Eight ordered gates; the 40 dissociation seeds and the rejection record | Appendix A |
| `construct` | The four matched conditions, one located edit each | Methods |
| `families` | The three contradiction families and the breadth set | Methods |
| `flip` | The dissociation notes with the two values swapped | Reversed-order control |
| `elicit` | 13,520 responses | Appendix B |
| `join` | Cached responses joined to items | — |
| `analyze` | Flag rate by condition, family, and model | Tables 4-7 |
| `validity` | The pre-registered clean-accuracy threshold | Table 3 |
| `silent` | Silent-commit rate | Tables 8-10 |
| `judge` | Judge agreement, and the open-ended vs MCQ delta | Tables 11-12 |
| `program-aided` | The program-aided arm | — |

## Where things are

```
reproduce.py          one entry point for every stage
verify_all.py         the offline construction check
fetch_medcalc.py      pulls the MedCalc-Bench substrate (required setup)
select_seeds.py       seed selection, eight ordered gates
spans.py              span localization: label, number and unit in one phrase
construct.py          the four conditions, one contiguous edit each
family_a|b|c.py       derived-quantity, impossible-BP, asserted-then-denied
breadth_conflict.py   the breadth set
checker.py            the deterministic contradiction checker
score.py  stats.py    labelling, scoring, Wilson intervals, McNemar
analyze_*.py          one script per reported table group
data/                 seeds, items, digests, cached responses, scored rows
docs/                 generated result tables
tests/                the regression suite
prompts/              all six prompts, frozen and hashed
PREREGISTRATION.md    the analysis plan, with content digests
```

## Known state

`run.py` still imports `google.colab` unguarded, so it runs only in a notebook.
`score.py` and `stats.py` do not, and every analysis stage works anywhere.

## Anonymity

This is a release copy prepared for double-blind review. It carries no
version-control history and none of the project's week-by-week task scaffolding.
The model responses needed to rebuild every table are included, under `data/`.
See [`ANONYMITY.md`](ANONYMITY.md) for exactly what was removed.
