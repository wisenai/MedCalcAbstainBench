#!/usr/bin/env python3
"""program_aided-specific scoring logic for .

Investigated by pulling ~2,580 real cached program_aided completions across
every condition/family/model before writing any of this. Findings that
shape the design:

- The prompt gives no output-format instruction at all (no FINAL:/ANSWER:
  line the way the other two formats have), so there is nothing to anchor
  extraction on the way score.py's regex does for open_ended.
- Abstention phrasing splits by vendor (opus/gemini/llama tend to echo the
  prompt's own "cannot be completed"; gpt-5/gpt-5-mini paraphrase "cannot
  compute") -- checked as a union of both phrase families, not one string.
- A defensive try/except in the code is not reliable evidence of an actual
  detected conflict -- a real example never entered its except branch
  (valid inputs) yet the model still silently computed and printed an
  answer that ignored a separately-stated conflict.

What this module deliberately does NOT do: extract or verify the specific
numeric answer. An earlier version tried to (needed for a value_correct
accuracy check), but every extraction pattern precise enough to pick out
"the one real answer" turned out to have a false-positive mode -- worst,
a markdown-bold-number pattern kept colliding with Python's ** exponent
operator (`height ** 2` misread as bold text starting with "2"), in enough
different code-formatting variants that no single regex fix held up.
Chasing exact-value extraction was solving a problem the paper doesn't
actually have: nothing downstream ever runs this code or acts on the
number it would produce -- the only thing that matters for the abstention
question is whether the model committed to an answer at all versus
declining. That only requires detecting *presence* of an attempted
computation, which is a much lower-risk check than picking out its exact
value, so that's all this module does now. Only the patterns validated
as safe (print() output, explicit Output:/Result: sections, \\boxed{},
\\mathbf{}) are used for presence; the bold-number-anywhere pattern that
caused every problem is dropped entirely, not patched again.
"""
import re

# Union of both vendor phrase families found in the investigation -- not
# split by model name, since the point is "does ANY abstention phrasing
# appear," not which specific vendor said it.
ABSTAIN_PHRASES = (
    "cannot be completed",
    "cannot compute",
    "cannot calculate",
    "cannot determine",
    "cannot be reliably",
    "unable to determine",
    "unable to compute",
    "insufficient",
    "ambiguous",
    "conflicting",
    "not explicitly present",
)


def _strip_code_fences(text):
    """Remove ```...``` fenced blocks. The prompt instructs models to
    always write a defensive "value not found" branch, so that phrasing
    shows up in the code on clean/resolvable items too, even though that
    branch never executes there -- real, confirmed on cached completions
    (a clean-item response containing an unreached else-branch with
    "Calculation cannot be completed" that would otherwise misclassify as
    committed_with_acknowledgment). Prose outside the fence is the
    model's actual stated conclusion, not a dead branch."""
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def _has_abstain_phrase(text):
    """Two-tier check: prefer a match in prose outside code fences
    (high-confidence -- this is the model's stated conclusion, not
    unreached defensive code). Only fall back to scanning inside the
    fences if there's no prose match at all, since some responses state
    their conclusion only via a returned/raised value in code with no
    prose summary -- a real pattern found on genuine Family C flags, not
    hypothetical. This fallback still carries the dead-branch risk, which
    is exactly why every program_aided row is marked low_confidence
    regardless of which tier matched."""
    prose = _strip_code_fences(text).lower()
    if any(p in prose for p in ABSTAIN_PHRASES):
        return True
    # Only fall back to scanning inside the code fences if there's
    # essentially NO prose at all (confirmed real pattern: some responses
    # narrate a conclusion in prose that doesn't happen to use one of
    # these exact phrases -- silence there is real evidence the model
    # didn't intend to flag, not a reason to go trust unreached code).
    # Strip markdown scaffolding before measuring, so leftover headers/
    # punctuation from the stripped fences don't count as "meaningful."
    meaningful_prose = re.sub(r"[\s#*:`\-]+", "", prose)
    if len(meaningful_prose) > 20:
        return False
    return any(p in text.lower() for p in ABSTAIN_PHRASES)


def has_computed_value(completion_text):
    """True iff the response contains an attempted numeric answer
    somewhere -- print() output, an explicit Output:/Result: section, or
    a \\boxed{}/\\mathbf{} expression. Deliberately does NOT try to pick
    out *which* number is "the" answer or verify it -- see module
    docstring for why. Only patterns confirmed safe on real data are
    used here; the bold-number-anywhere-in-text pattern is intentionally
    excluded, since it was the source of every false positive found
    during validation (it matches Python's ** exponent operator and
    bolded list/criteria labels that aren't stated answers at all).
    """
    for m in re.finditer(r"print\((.*?)\)([^\n]*)", completion_text, re.DOTALL):
        arg_text = re.sub(r"\{[^}]*\}", "", m.group(1))
        if re.search(r"-?\d+(?:\.\d+)?", arg_text):
            return True
        if re.search(r"#.*?-?\d+(?:\.\d+)?", m.group(2)):
            return True

    # Two-step, not one inline pattern: the labeled section (e.g.
    # "**Output:**") and its actual value are often several lines apart
    # (a fenced ``` block showing simulated output), so the digit check
    # has to span multiple lines (DOTALL to the next blank line), not
    # just the header's own line -- confirmed real, a single-line version
    # missed a genuine "**Output:**\n```\nMAP = 125.0 mm Hg\n```" case.
    for m in re.finditer(
        r"(?:\*\*[^*\n]*(?:Output|Result)[^*\n]*:?\*\*|#{1,3}\s*[^\n]*(?:Output|Result)[^\n]*)"
        r"\s*:?\s*(.*?)(?:\n\n|\Z)",
        completion_text, re.DOTALL,
    ):
        if re.search(r"-?\d+(?:\.\d+)?", m.group(1)):
            return True

    if re.search(r"\\boxed\{-?\d+(?:\.\d+)?\}", completion_text):
        return True

    if re.search(r"\\mathbf\{[^}]*?-?\d+(?:\.\d+)?[^}]*?\}", completion_text):
        return True

    # A bare line starting "Result:"/"Output:" with no bold/header markup
    # at all -- anchored to line-start (MULTILINE) so it can't match
    # "Result" appearing mid-sentence elsewhere (e.g. "As a result, ..."),
    # which is what keeps this safe without the header markup requirement.
    if re.search(r"^\s*(?:Result|Output)\s*:\s*.*?-?\d+(?:\.\d+)?", completion_text,
                  re.MULTILINE):
        return True

    return False


def classify_program_aided(completion_text):
    """Returns assigned_label only -- 'flagged' / 'committed_with_
    acknowledgment' / 'committed_silent' / 'unparseable'. No extracted
    value or correctness check is returned (see module docstring): the
    paper's abstention question only needs whether the model committed to
    an answer at all, not what that answer was, and 'presence of a
    computed value' is a far more reliable signal than 'the exact value'
    turned out to be. 'unparseable' means neither a computed value nor an
    abstention phrase was found -- genuinely nothing to classify from.
    """
    committed = has_computed_value(completion_text)
    has_phrase = _has_abstain_phrase(completion_text)

    if not committed:
        return "flagged" if has_phrase else "unparseable"
    elif has_phrase:
        return "committed_with_acknowledgment"
    else:
        return "committed_silent"
