# MedCalcAbstainBench

Do language models flag a clinical note they cannot trust, or compute from it
anyway? 676 conditions built from 202 MedCalc-Bench notes across eleven
calculators, each note rewritten with its required value left intact, removed,
contradicted, or contradicted alongside a question naming which value to use.

## Run it

```bash
pip install -r requirements.txt
python3 fetch_medcalc.py     # downloads MedCalc-Bench v1.0, pinned to a tag
python3 verify_all.py        # expect: 29 of 29 checks pass
python3 reproduce.py analyze # expect: the tables below
```

Offline and deterministic. No API key, no model calls. `fetch_medcalc.py` is
required: we do not redistribute MedCalc-Bench, and without it one check cannot
import the calculator module it needs.

## What you should see

`reproduce.py analyze` writes `docs/FLAG_RATES.md`. It should match the paper:

| Condition | Flagged |
|---|---|
| clean | 38/1010 (3.8%) |
| missing | 196/200 (98.0%) |
| value-conflict | 128/200 (64.0%) |
| resolvable | 22/1010 (2.2%) |
| contradiction | 219/960 (22.8%) |

The other reported tables:

```bash
python3 reproduce.py validity       # clean accuracy, 76.2-88.1%
python3 reproduce.py silent         # silent commit: 1.5, 23.5, 95.4, 67.6%
python3 reproduce.py program-aided  # the low-confidence arm
python3 reproduce.py --list         # every stage, and the table it produces
```

## What is where

```
reproduce.py        one entry point for every stage
verify_all.py       re-derives every edit span, re-checks digests
select_seeds.py     seed selection, eight ordered gates
spans.py            span localization
construct.py        the four conditions, one contiguous edit each
family_a|b|c.py     the three contradiction families
checker.py          the deterministic contradiction checker
score.py stats.py   labelling, Wilson intervals, McNemar
analyze_*.py        one script per reported table
data/               seeds, items, digests, model responses
docs/               generated result tables
PREREGISTRATION.md  the analysis plan, with content digests
```

## Regenerating the responses

Not needed for anything above; the responses are in `data/`.

```bash
export OPENROUTER_API_KEY=...
python3 reproduce.py elicit    # 676 x 5 models x 4 prompts
```

`run.py` imports `google.colab`, so the harness runs only in a notebook.
Decoding uses provider defaults at one sample per cell, so a rerun will not
return the committed responses byte for byte.
