#!/usr/bin/env python3
"""Checks on the cache-to-item join.

The join is exact rather than heuristic, which makes it worth testing: an exact
join that silently addresses the wrong cell produces a full, balanced, entirely
wrong table, and nothing downstream would notice. The two failures with teeth are
addressed here -- a key scheme that has drifted from `run.py`, and a pilot arm
that is short a cell but still looks symmetric.

Run:  python3 tests/test_assemble.py
"""
import hashlib
import re
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import assemble_pilot as ap  # noqa: E402


class TestCacheKey(unittest.TestCase):
    """The key must match run.py's scheme, tested against the cache itself."""

    def test_scheme_is_sha256_of_underscore_join(self):
        got = ap.cache_key("m", "i", "p", "f")
        self.assertEqual(got, hashlib.sha256(b"m_i_p_f").hexdigest())

    def test_key_addresses_a_real_cached_completion(self):
        """The strongest available check: a computed key must hit a real file.

        If run.py's scheme ever changes, this fails without anyone having to
        remember that these two files agree by convention rather than by import.
        (run.py cannot be imported here -- it does `from google.colab import
        userdata` at module level -- which is exactly why the convention needs a
        test rather than a shared function.)
        """
        cache = os.path.join(ROOT, "cache")
        if not os.path.isdir(cache):
            self.skipTest("no cache/ in this checkout")
        items = json.load(open(ap.ITEMS))["items"]
        seed = items[0]["seed_id"]
        key = ap.cache_key("anthropic/claude-opus-4.8", f"{seed}_clean",
                           "open_ended", "open_ended")
        self.assertTrue(os.path.exists(os.path.join(cache, key + ".json")),
                        f"computed key missed the cache for {seed}_clean")


class TestGroundTruth(unittest.TestCase):
    """missing and value_conflict have no correct number, by construction."""

    @classmethod
    def setUpClass(cls):
        cls.items = {i["seed_id"]: i for i in json.load(open(ap.ITEMS))["items"]}

    def test_declining_conditions_have_no_answer(self):
        item = next(iter(self.items.values()))
        for cond, action in (("missing", "decline"), ("value_conflict", "flag")):
            gt = ap.ground_truth(item, cond)
            self.assertIsNone(gt["ground_truth"], f"{cond} must have no answer")
            self.assertEqual(gt["correct_action"], action)

    def test_computing_conditions_have_an_answer(self):
        item = next(iter(self.items.values()))
        for cond in ("clean", "resolvable"):
            gt = ap.ground_truth(item, cond)
            self.assertIsNotNone(gt["ground_truth"], f"{cond} must have an answer")
            self.assertEqual(gt["correct_action"], "compute")

    def test_resolvable_answer_is_the_stated_value_not_the_injected_one(self):
        """The cue names the originally stated value, so resolvable == clean."""
        for item in self.items.values():
            self.assertEqual(ap.ground_truth(item, "resolvable")["ground_truth"],
                             ap.ground_truth(item, "clean")["ground_truth"])


def _rows(arm, seeds, conds):
    return [{"arm": arm, "seed_id": s, "condition": c} for s in seeds for c in conds]


class TestCoverage(unittest.TestCase):
    """A short pilot arm must not pass as complete just because it is balanced."""

    N = 40
    FULL = [f"s{i}" for i in range(40)]

    def test_complete_pilot_arm_passes(self):
        arms = [("open_ended", "m", "p", "f", ap.CONDITIONS)]
        cov = ap.coverage(_rows("open_ended", self.FULL, ap.CONDITIONS), arms, self.N)
        self.assertTrue(cov["open_ended"]["complete"])

    def test_balanced_but_short_pilot_arm_fails(self):
        """39 of 40 seeds, evenly across conditions: symmetric and still wrong."""
        arms = [("open_ended", "m", "p", "f", ap.CONDITIONS)]
        cov = ap.coverage(_rows("open_ended", self.FULL[:39], ap.CONDITIONS), arms, self.N)
        self.assertFalse(cov["open_ended"]["complete"])

    def test_one_missing_cell_fails(self):
        arms = [("open_ended", "m", "p", "f", ap.CONDITIONS)]
        rows = _rows("open_ended", self.FULL, ap.CONDITIONS)
        rows = [r for r in rows
                if not (r["seed_id"] == "s7" and r["condition"] == "resolvable")]
        cov = ap.coverage(rows, arms, self.N)
        self.assertFalse(cov["open_ended"]["complete"])

    def test_reasoning_arm_is_complete_on_the_cells_it_owns(self):
        """Partial coverage is the design here, not damage."""
        arms = [("reasoning", "m", "p", "f", ("value_conflict",))]
        cov = ap.coverage(_rows("reasoning", self.FULL, ("value_conflict",)),
                          arms, self.N)
        self.assertTrue(cov["reasoning"]["complete"])

    def test_out_of_scope_cells_are_reported_not_counted(self):
        arms = [("reasoning", "m", "p", "f", ("value_conflict",))]
        rows = (_rows("reasoning", self.FULL, ("value_conflict",))
                + _rows("reasoning", ["s0"], ("clean",)))
        cov = ap.coverage(rows, arms, self.N)
        self.assertTrue(cov["reasoning"]["complete"])
        self.assertEqual(cov["reasoning"]["seeds_outside_scope"], {"clean": 1})

    def test_smoke_arm_is_not_measured_against_all_forty(self):
        arms = [("smoke_open", "m", "p", "f", ap.CONDITIONS)]
        cov = ap.coverage(_rows("smoke_open", self.FULL[:5], ap.CONDITIONS),
                          arms, self.N)
        self.assertTrue(cov["smoke_open"]["complete"])


class TestPromptsAreFrozen(unittest.TestCase):
    """The six prompts are frozen, and this is what makes that enforceable.

    `run.py` keys the cache on hash(model, item_id, prompt_id, format) and NOT on
    the prompt text, so editing a prompt invalidates nothing: every completion
    generated under the old wording is silently reused as though it came from the
    new one. 240 cached completions carry the current `open_ended` text. Nothing
    else in the repo would notice.
    """

    LOCK = os.path.join(ROOT, "prompts", "PROMPTS.lock.json")
    YAML = os.path.join(ROOT, "prompts", "prompts.yaml")

    def _prompts(self):
        """Parsed with PyYAML, so the hash matches what run.py actually sends.

        Re-implementing block-scalar parsing here would let the test agree with
        my parser while disagreeing with the one the harness uses, which is the
        one failure mode a freeze check must not have.
        """
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed; the freeze check needs the real parser")
        return yaml.safe_load(open(self.YAML))

    def test_the_six_prompts_are_all_present(self):
        lock = json.load(open(self.LOCK))
        self.assertEqual(
            set(lock["prompts"]),
            {"open_ended", "mcq", "program_aided", "neutral_exit",
             "inline_consistency", "detector_only"})

    def test_no_prompt_has_changed_since_it_was_frozen(self):
        lock = json.load(open(self.LOCK))
        found = self._prompts()
        for name, expected in lock["prompts"].items():
            with self.subTest(prompt=name):
                self.assertIn(name, found, f"{name} is missing from prompts.yaml")
                got = hashlib.sha256(found[name].encode()).hexdigest()
                self.assertEqual(
                    got, expected,
                    f"{name} changed. Every cached completion for it is now "
                    f"mislabelled: the cache key does not include prompt text. "
                    f"Re-run the affected cells and update PROMPTS.lock.json in "
                    f"the same commit.")


class TestLabelsLeftEmpty(unittest.TestCase):
    """The scoring columns belong to score.py and must arrive unfilled."""

    def test_assembled_rows_carry_no_labels(self):
        out = os.path.join(ROOT, "data", "pilot_completions.json")
        if not os.path.exists(out):
            self.skipTest("run assemble_pilot.py first")
        rows = json.load(open(out))["rows"]
        self.assertTrue(rows, "no rows assembled")
        for field in ("assigned_label", "value_correct", "extracted_value",
                      "justification_span"):
            self.assertTrue(all(r[field] is None for r in rows),
                            f"{field} was filled in by the join; that is score.py's job")


if __name__ == "__main__":
    unittest.main(verbosity=2)
