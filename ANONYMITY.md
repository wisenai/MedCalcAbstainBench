# What was anonymized in this release copy

This repository is a double-blind release copy. It is derived from a working
repository that is not linked here. The following changes were made, and
nothing else.

## Removed

- **All version-control history.** The copy carries no `.git` directory, so no
 commit author names, emails, or timestamps travel with it.
- **The response cache** (`cache/`), which held raw provider completions keyed
 by hash and is not needed to verify the construction.
- **Two large derived files**, `data/grid_rows.json` and
 `data/scored.json`, at 65 MB and 66 MB. Their CSV equivalents,
 `grid_rows.csv` and `scored.csv`, are included and carry the same
 rows.
- ** pilot data and scripts, the `pilot/` tree, per-annotator trace
 files, and working memos.** None of it backs a number in the paper; the
 reported grid is . Removing it also removes the retired-seed failure
 that the source repository still carries in `scored.csv`.

## Replaced

- **Contributor names**, in filenames and in file contents, with
 `a contributor` through `a contributor`. These appeared in per-annotator label
 files, in module docstring attribution lines of the form
- **The owning account and repository slug**, with `ANONYMIZED`.

No logic, threshold, seed, item, label, or reported number was changed. The
five content digests pinned in `PREREGISTRATION.md` were recomputed, because
scrubbing the attribution lines changes the files they bind; the
pre-anonymization digests are recorded at the end of that file so the change
can be checked.

## Verified after scrubbing

- No occurrence of any contributor name, the account name, or an email address
 remains in any text file.
- No API key, token, or absolute path containing a username remains.
- `verify_all.py` passes exactly the checks it passes in the source
 repository: 26 of 28, with the same two failures for the same reason (see
 the note in `README.md`).
