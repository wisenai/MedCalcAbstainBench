# MedCalcAbstain-Bench

## Reproducing the paper

```
python3 reproduce.py --list     # every stage, and the paper claim it produces
python3 reproduce.py verify     # offline construction check
python3 reproduce.py analyze    # rebuild the reported tables
```

Stage names replace the week-numbered scripts the working repository used. Only
`elicit` touches the network; it needs `OPENROUTER_API_KEY`. Everything else
reads what is committed under `data/` and is deterministic.

This is a release copy prepared for double-blind review. It is not the working
repository, and it carries no version-control history. See `ANONYMITY.md` for
exactly what was removed and replaced.

## Before running the verifier

`verify_all.py` needs the MedCalc-Bench substrate on disk. Fetch it first:

```
python3 fetch_medcalc.py
python3 verify_all.py
```

Run cold, without the substrate, two of the 28 checks cannot execute and are
reported as failures rather than skips:

- `every edit lands on the consumed span` raises `ModuleNotFoundError` on the
  calculator module it imports.
- `criteria + substrate checks` correctly reports itself skipped.

A third check, `week2_scored.csv has no retired seeds`, fails on a single
retired seed (`mdrd-tr3279`) left in the week-2 pilot file. Week 2 is pilot
data and is not the grid the paper reports; `week3_scored.csv`, which is,
passes the same check.

This is the state of the source repository as well, not something introduced
by the anonymized copy.


## Checking that the construction still holds

```
python3 verify_all.py
```

Offline, no API key, no network. Runs the regression and join suites, re-derives
every edit span, flips every rule-based criterion, re-checks the eight item sets
and their digests, and confirms the files bound in `PREREGISTRATION.md` §2 are the
files on disk. Exits non-zero if anything fails.

It verifies what is committed; it does not rebuild it. For a rebuild from an empty
`data/`, and for what each file in `data/` is, see [`data/README.md`](data/README.md).

This section covers construction only. It is not a description of the project.
