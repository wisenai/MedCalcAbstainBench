# Mitigation arm — results

> **NOT COMPARABLE TO THE UNPROMPTED HEADLINE.** Both arms cue inconsistency by design. These rates measure whether a *cued* model can act on a contradiction, not whether an *uncued* one notices. They belong beside the headline as a diagnostic, never inside it.

## Table 1 — benefit and cost, together

*Cued by design — not comparable to the unprompted headline. Diagnostic only.*

Flag rate on contradictions is the benefit. False-flag rate on the matched consistent control — same patient, same prose, same question, defect removed — is the cost. Same row, because reading one without the other is how a useless mitigation gets published.

**anthropic/claude-opus-4.8**

| arm | prompt | flag rate on contradictions ↑ | committed-silent ↓ | FALSE-FLAG on consistent controls ↓ |
|---|---|---|---|---|
| baseline (unprompted) | neutral_exit | 0/36 (0.0% [0.0% - 9.6%]) | 9/36 (25.0% [13.8% - 41.1%]) | 0/30 (0.0% [0.0% - 11.4%]) |
| baseline (unprompted) | open_ended | 4/36 (11.1% [4.4% - 25.3%]) | 7/36 (19.4% [9.8% - 35.0%]) | 1/30 (3.3% [0.6% - 16.7%]) |
| inline consistency | inline_consistency | 14/36 (38.9% [24.8% - 55.1%]) | 1/36 (2.8% [0.5% - 14.2%]) | 0/30 (0.0% [0.0% - 11.4%]) |
| verifier pass, GATING | neutral_exit | 33/36 (91.7% [78.2% - 97.1%]) | 1/36 (2.8% [0.5% - 14.2%]) | 8/30 (26.7% [14.2% - 44.4%]) |
| verifier pass, GATING | open_ended | 33/36 (91.7% [78.2% - 97.1%]) | 0/36 (0.0% [0.0% - 9.6%]) | 8/30 (26.7% [14.2% - 44.4%]) |
| verifier, advisory | neutral_exit | 0/36 (0.0% [0.0% - 9.6%]) | 1/36 (2.8% [0.5% - 14.2%]) | 0/30 (0.0% [0.0% - 11.4%]) |
| verifier, advisory | open_ended | 4/36 (11.1% [4.4% - 25.3%]) | 0/36 (0.0% [0.0% - 9.6%]) | 1/30 (3.3% [0.6% - 16.7%]) |

## Table 2 — by contradiction family

*Cued by design — not comparable to the unprompted headline. Diagnostic only.*

C is the family no arithmetic can reach, so a mitigation that only works on A and B is a mitigation for the cases that never needed a model.

**anthropic/claude-opus-4.8**

| arm | prompt | family | flag ↑ | false-flag ↓ |
|---|---|---|---|---|
| baseline (unprompted) | neutral_exit | A | 0/12 (0.0% [0.0% - 24.2%]) | 0/12 (0.0% [0.0% - 24.2%]) |
| baseline (unprompted) | neutral_exit | B | 0/12 (0.0% [0.0% - 24.2%]) | 0/6 (0.0% [0.0% - 39.0%]) |
| baseline (unprompted) | neutral_exit | C | 0/12 (0.0% [0.0% - 24.2%]) | 0/12 (0.0% [0.0% - 24.2%]) |
| baseline (unprompted) | open_ended | A | 0/12 (0.0% [0.0% - 24.2%]) | 0/12 (0.0% [0.0% - 24.2%]) |
| baseline (unprompted) | open_ended | B | 0/12 (0.0% [0.0% - 24.2%]) | 0/6 (0.0% [0.0% - 39.0%]) |
| baseline (unprompted) | open_ended | C | 4/12 (33.3% [13.8% - 60.9%]) | 1/12 (8.3% [1.5% - 35.4%]) |
| inline consistency | inline_consistency | A | 0/12 (0.0% [0.0% - 24.2%]) | 0/12 (0.0% [0.0% - 24.2%]) |
| inline consistency | inline_consistency | B | 8/12 (66.7% [39.1% - 86.2%]) | 0/6 (0.0% [0.0% - 39.0%]) |
| inline consistency | inline_consistency | C | 6/12 (50.0% [25.4% - 74.6%]) | 0/12 (0.0% [0.0% - 24.2%]) |
| verifier pass, GATING | neutral_exit | A | 12/12 (100.0% [75.8% - 100.0%]) | 3/12 (25.0% [8.9% - 53.2%]) |
| verifier pass, GATING | neutral_exit | B | 12/12 (100.0% [75.8% - 100.0%]) | 2/6 (33.3% [9.7% - 70.0%]) |
| verifier pass, GATING | neutral_exit | C | 9/12 (75.0% [46.8% - 91.1%]) | 3/12 (25.0% [8.9% - 53.2%]) |
| verifier pass, GATING | open_ended | A | 12/12 (100.0% [75.8% - 100.0%]) | 3/12 (25.0% [8.9% - 53.2%]) |
| verifier pass, GATING | open_ended | B | 12/12 (100.0% [75.8% - 100.0%]) | 2/6 (33.3% [9.7% - 70.0%]) |
| verifier pass, GATING | open_ended | C | 9/12 (75.0% [46.8% - 91.1%]) | 3/12 (25.0% [8.9% - 53.2%]) |
| verifier, advisory | neutral_exit | A | 0/12 (0.0% [0.0% - 24.2%]) | 0/12 (0.0% [0.0% - 24.2%]) |
| verifier, advisory | neutral_exit | B | 0/12 (0.0% [0.0% - 24.2%]) | 0/6 (0.0% [0.0% - 39.0%]) |
| verifier, advisory | neutral_exit | C | 0/12 (0.0% [0.0% - 24.2%]) | 0/12 (0.0% [0.0% - 24.2%]) |
| verifier, advisory | open_ended | A | 0/12 (0.0% [0.0% - 24.2%]) | 0/12 (0.0% [0.0% - 24.2%]) |
| verifier, advisory | open_ended | B | 0/12 (0.0% [0.0% - 24.2%]) | 0/6 (0.0% [0.0% - 39.0%]) |
| verifier, advisory | open_ended | C | 4/12 (33.3% [13.8% - 60.9%]) | 1/12 (8.3% [1.5% - 35.4%]) |

## Table 3 — the verifier pass on its own

*Cued by design — not comparable to the unprompted headline. Diagnostic only.*

Before the gate. Unreadable verdicts leave the denominator rather than counting as a non-detection.

| model | sensitivity on contradictions ↑ | false-positive on controls ↓ | unreadable |
|---|---|---|---|
| anthropic/claude-opus-4.8 | 33/36 (91.7% [78.2% - 97.1%]) | 8/30 (26.7% [14.2% - 44.4%]) | 0/72 |

## Table 4 — paired shift vs baseline (McNemar, exact)

*Cued by design — not comparable to the unprompted headline. Diagnostic only.*

Same note, same model, same prompt, with and without the mitigation. `→flag` is what the mitigation moved into flagging, `→commit` what it moved out. Exploratory: this arm is not in the pre-registered analysis.

| model | prompt | arm | population | n | →flag | →commit | p (exact) |
|---|---|---|---|---|---|---|---|
| anthropic/claude-opus-4.8 | neutral_exit | inline consistency | contradictions | 36 | 14 | 0 | 0.0001 * |
| anthropic/claude-opus-4.8 | neutral_exit | inline consistency | consistent controls | 30 | 0 | 0 | 1.0000 |
| anthropic/claude-opus-4.8 | neutral_exit | verifier pass, GATING | contradictions | 36 | 33 | 0 | 0.0000 * |
| anthropic/claude-opus-4.8 | neutral_exit | verifier pass, GATING | consistent controls | 30 | 8 | 0 | 0.0078 * |
| anthropic/claude-opus-4.8 | neutral_exit | verifier, advisory | contradictions | 36 | 0 | 0 | 1.0000 |
| anthropic/claude-opus-4.8 | neutral_exit | verifier, advisory | consistent controls | 30 | 0 | 0 | 1.0000 |
| anthropic/claude-opus-4.8 | open_ended | inline consistency | contradictions | 36 | 10 | 0 | 0.0020 * |
| anthropic/claude-opus-4.8 | open_ended | inline consistency | consistent controls | 30 | 0 | 1 | 1.0000 |
| anthropic/claude-opus-4.8 | open_ended | verifier pass, GATING | contradictions | 36 | 29 | 0 | 0.0000 * |
| anthropic/claude-opus-4.8 | open_ended | verifier pass, GATING | consistent controls | 30 | 7 | 0 | 0.0156 |
| anthropic/claude-opus-4.8 | open_ended | verifier, advisory | contradictions | 36 | 0 | 0 | 1.0000 |
| anthropic/claude-opus-4.8 | open_ended | verifier, advisory | consistent controls | 30 | 0 | 0 | 1.0000 |

## Table 5 — against the deterministic checker

*Not a mitigation result: no model and no prompt are involved, so this table is comparable to anything.*

No model involved. Near-perfect on A and B, structurally zero on C — stated as our own limit rather than left for a reviewer to find.

| family | checker catch rate on contradictions |
|---|---|
| A | 12/12 (100.0% [75.8% - 100.0%]) |
| B | 12/12 (100.0% [75.8% - 100.0%]) |
| C | 0/12 (0.0% [0.0% - 24.2%]) |

> **NOT COMPARABLE TO THE UNPROMPTED HEADLINE.** Both arms cue inconsistency by design. These rates measure whether a *cued* model can act on a contradiction, not whether an *uncued* one notices. They belong beside the headline as a diagnostic, never inside it.

