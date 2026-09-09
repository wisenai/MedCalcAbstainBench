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
pip install -r requirements.txt
python3 reproduce.py --list      # every stage, and the paper claim it produces
python3 reproduce.py verify      # offline: does the construction still hold?
python3 reproduce.py analyze     # rebuild the reported tables from cached responses
```

`verify` needs no dependencies, no API key and no network. `analyze` needs the
packages above but still no network: it reads the responses committed under
`data/`.

## What reproduces what

| Stage | Produces | Paper |
|---|---|---|
| `verify` | Re-derives every edit span, flips every scored criterion, re-checks item sets and digests | Appendix C |
| `seeds` | Eight ordered gates over the creatinine candidates; the 40 dissociation seeds and the rejection record | Appendix A |
| `construct` | The four matched conditions, one located edit each | Methods |
| `families` | The three contradiction families and the breadth set | Methods |
| `flip` | The dissociation notes with the two conflicting values swapped | Reversed-order control |
| `elicit` | 676 conditions x 5 models x 4 prompts = 13,520 responses | Appendix B |
| `join` | Cached responses joined to items across the four formats | — |
| `analyze` | Flag rate by condition, by family, and by model | Tables 4-7 |
| `validity` | The pre-registered 50% clean-accuracy threshold | Table 3 |
| `silent` | Silent-commit rate as its own table | Tables 8-10 |
| `judge` | Judge agreement per family, and the open-ended vs MCQ delta | Tables 11-12 |
| `program-aided` | The program-aided arm, reported separately and marked low-confidence | — |

Only `elicit` and `judge` call a provider. Both need `OPENROUTER_API_KEY`, from
the environment or from Colab Secrets. Every other stage is deterministic and
offline.

## Where things are

```
reproduce.py         one entry point for every stage
verify_all.py        the offline construction check
select_seeds.py      seed selection, eight gates
spans.py             span localization: label, number and unit in one phrase
construct.py         the four conditions, one contiguous edit each
family_a|b|c.py      derived-quantity, impossible-BP, and asserted-then-denied
breadth_conflict.py  the breadth set
checker.py           the deterministic contradiction checker
score.py stats.py    labelling, scoring, Wilson intervals, McNemar
analyze_*.py         one script per reported table group
data/                seeds, items, digests, cached responses, scored rows
docs/                generated result tables
tests/               the regression suite
prompts/             all six prompts, frozen and hashed
PREREGISTRATION.md   the analysis plan, with content digests
```

## Known state

`verify_all.py` reports **26 of 27**. The one failure, `every edit lands on the
consumed span`, raises `ModuleNotFoundError` because it imports a MedCalc-Bench
calculator module that is not vendored here. Fetch the substrate first and it
passes:

```bash
python3 fetch_medcalc.py
python3 verify_all.py
```

`run.py` still imports `google.colab` unguarded, so it runs only in a notebook.
`score.py` and `stats.py` do not, and the analysis stages work anywhere.

## Anonymity

This is a release copy prepared for double-blind review. It carries no
version-control history, no response cache, and no pilot data. See
[`ANONYMITY.md`](ANONYMITY.md) for exactly what was removed and replaced.
