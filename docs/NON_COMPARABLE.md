# Non-comparability of the mitigation numbers — canonical wording

**Task owner:** Maia — Week 3, second clause: *"Label the mitigation results as
non-comparable to the unprompted headline everywhere they appear — those prompts
cue inconsistency by design and the point is diagnostic."*

Everywhere is the part that fails in practice. A banner at the top of one file
does not survive a table being pasted into Slack, a figure being dropped into the
Results section, or a number being quoted in a rebuttal. So the wording lives
here, the generated report stamps every table with it, and every CSV row carries
it in a `comparability` column.

**Use these verbatim.** Don't paraphrase — a softened version is how the caveat
quietly disappears.

---

## 1. Why (the argument, once)

The unprompted headline measures whether a model *notices* a contradiction when
nothing has drawn its attention to one. Both mitigation arms remove exactly that:

- `inline_consistency` names inconsistency in the instruction — the model is told
  to check before it computes.
- `detector_only` asks about nothing else — the entire prompt is "is this note
  internally consistent?"

So a mitigation flag rate answers a different question: **given that it has been
told to look, can the model act on what it finds?** That is a diagnostic about
mechanism, not a measurement of behaviour in the wild. Putting the two rates in
one table, or one sentence, invites the reader to treat a cued number as an
uncued one — which would overstate every model in the paper.

## 2. Table caption (use under every mitigation table)

> *Cued by design — not comparable to the unprompted headline. Diagnostic only.*

## 3. Slack / one-liner

> These are the mitigation arm — the prompts cue inconsistency by design, so the
> flag rates aren't comparable to our headline numbers. Diagnostic only.

## 4. Paper footnote

> Mitigation-arm rates are not comparable to the unprompted results reported in
> §X. Both mitigation prompts cue inconsistency by construction — the inline
> condition instructs the model to check internal consistency before computing,
> and the verifier condition asks only whether the note is consistent — so these
> rates measure whether a cued model acts on a contradiction, not whether an
> uncued model detects one. They are reported as a diagnostic of mechanism.

## 5. Discussion paragraph

> The mitigation results should be read as a diagnostic rather than as a
> performance claim. Both interventions tell the model, explicitly or by the
> shape of the task, that consistency is at issue; the unprompted condition does
> not. The comparison they license is therefore internal — inline instruction
> against a gating verifier, and each against its own matched consistent controls
> — and not against the headline flag rates. What they establish is that the
> failure documented in §X is not a detection failure: under cueing the same
> model identifies the contradiction it had previously computed straight past.
> The cost side is reported alongside for the same reason: an intervention that
> lifts flagging by refusing consistent notes has relocated the error rather than
> removed it.

## 6. What must NOT carry this label

The deterministic-checker table. `checker.py` uses no model and no prompt, so
nothing about it is cued; labelling it "cued by design" would be false. It gets
its own note instead:

> *Not a mitigation result: no model and no prompt are involved, so this table is
> comparable to anything.*

Applying the caveat indiscriminately is its own kind of inaccuracy, and a reader
who catches one misapplied label will discount the correctly applied ones.

## 7. Where the label currently lives

| surface | how |
|---|---|
| `docs/MITIGATION_RESULTS.md` | banner at top and bottom, plus §2 caption under every table |
| `data/mitigation_scores.csv` | `comparability` column, all 504 rows |
| paper §Results / §Discussion | §4 footnote and §5 paragraph above |
| Slack, review replies | §3 |

`check_labels.py` fails if a repo document reports mitigation numbers without it.
