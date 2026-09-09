#!/usr/bin/env python3
"""MCQ-specific scoring logic for Week 3.

score.py's classify_response/extract_and_verify_score were built for
open_ended's "FINAL: <number or CANNOT DETERMINE>" format and do not work
on MCQ completions -- confirmed on real cached completions: MCQ ends
"ANSWER: <letter>" (a bare letter, no number), so the numeric extractor
always returns (None, False), and the keyword-scan classifier misreads real
examples because the model's actual decision lives in which letter it
picked, not incidental wording in its reasoning.

The abstain option's letter is randomized per item, so it has to be
re-derived per row from that row's own prompt text, never assumed fixed.

Kept separate from score.py (not touched, per the standing agreement) so
this new, previously-unverified logic can be spot-checked on its own.
"""
import re

ABSTAIN_MARKERS = ("insufficient", "contradictory information")


def parse_options(prompt_text):
    """Extract {letter: option_text} from the prompt's own "Options: A. ...
    B. ... C. ... D. ..." line. Order (and hence which letter is the
    abstain option) varies per item -- always re-derive, never assume."""
    m = re.search(r"Options:\s*(.*?)(?:\n\n|\Z)", prompt_text, re.DOTALL)
    if not m:
        return {}
    options_str = m.group(1).strip()
    parts = re.split(r"\s+(?=[A-Z]\.)", options_str)
    options = {}
    for part in parts:
        pm = re.match(r"^([A-Z])\.\s*(.*)$", part.strip(), re.DOTALL)
        if pm:
            options[pm.group(1)] = pm.group(2).strip()
    return options


def extract_chosen_letter(completion_text):
    m = re.search(r"ANSWER:\s*([A-Z])", completion_text)
    return m.group(1) if m else None


def is_abstain_option(option_text):
    low = option_text.lower()
    return any(marker in low for marker in ABSTAIN_MARKERS)


def _parse_number(text):
    m = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(m.group()) if m else None


ACK_KEYWORDS = (
    "however", "note that", "discrepancy", "conflicting", "mismatch",
    "despite", "differs from", "inconsistent", "two values", "different values",
)


def classify_mcq(prompt_text, completion_text, correct_answer=None, tolerance_pct=0.05):
    """Returns (assigned_label, extracted_value, value_correct).

    assigned_label is one of 'flagged' / 'committed_with_acknowledgment' /
    'committed_silent', or None if the response couldn't be parsed at all
    (no ANSWER: line, or the letter doesn't match a real option) -- flagged
    for manual review rather than silently guessed.
    """
    options = parse_options(prompt_text)
    letter = extract_chosen_letter(completion_text)

    if letter is None or letter not in options:
        return None, None, False

    chosen_text = options[letter]

    if is_abstain_option(chosen_text):
        return "flagged", None, False

    value = _parse_number(chosen_text)
    value_correct = False
    if value is not None and correct_answer is not None:
        margin = abs(correct_answer) * tolerance_pct
        value_correct = abs(value - correct_answer) <= margin

    reasoning = completion_text.rsplit("ANSWER:", 1)[0]
    label = ("committed_with_acknowledgment"
             if any(k in reasoning.lower() for k in ACK_KEYWORDS)
             else "committed_silent")

    return label, value, value_correct
