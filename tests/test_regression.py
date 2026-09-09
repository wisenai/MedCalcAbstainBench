#!/usr/bin/env python3
"""Regression suite: every extraction failure Week 1 actually hit.

Task owner: Annotator D -- Week 2.
Completed by Annotator D.

Each test below is a real failure, not a hypothetical one. The note text in each
case is the text that caused it, quoted from the corpus, and the docstring says
what went wrong and what the fix was. A regression suite whose cases cannot be
traced to a real failure decays into noise, so nothing speculative is added here.

The point of the suite is that it runs *before a build is accepted*. Several of
these failures were silent -- the build succeeded and produced items that were
wrong -- which is why the checks live outside the builder as well as inside it.

Run:  python3 tests/test_regression.py
"""
import collections
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "audit"))

import spans  # noqa: E402
import select_seeds  # noqa: E402
import construct  # noqa: E402
import checker  # noqa: E402

CRE_UNITS = ["mg/dL", "µmol/L", "mmol/L"]


class TestCreatinineAnchoring(unittest.TestCase):
    """Locating the creatinine the calculator actually consumes."""

    def test_does_not_step_over_an_intervening_value(self):
        """`BUN, 34.4 mg/dL; and creatinine, 1.4 mg/dL` (pmc-7671985-1).

        A proximity search anchored on the word "creatinine" picks up the BUN,
        which sits well inside any reasonable window. The gap between label and
        value must contain no digits.
        """
        note = ("blood urea nitrogen (BUN), 34.4 mg/dL; and creatinine, "
                "1.4 mg/dL. Serologic tests were negative.")
        rec = spans.find_measurement(note, 1.4, "mg/dL", "creatinine")
        self.assertEqual(rec["value_text"], "1.4")
        with self.assertRaises(spans.NotFound):
            spans.find_measurement(note, 34.4, "mg/dL", "creatinine")

    def test_value_without_a_unit_is_not_anchored(self):
        """`His recent creatinine is 2.13, BUN 38` (pmc-4736135-1 style).

        The unit is what identifies the quantity the calculator consumes. A bare
        number is not locatable, and the seed is rejected rather than guessed at.
        """
        note = "His recent creatinine is 2.13, BUN 38. This has been stable."
        self.assertEqual(spans.count_measurements(note, "creatinine", CRE_UNITS), [])

    def test_label_separated_from_value_by_a_sentence_break(self):
        """`both creatinine and sodium were within normal levels, i.e. 0.7 mg/dL`.

        The period in "i.e." ends the clause. Matching across it would attach the
        creatinine label to whichever value happened to come next.
        """
        note = ("Most notably, both creatinine and sodium were within normal "
                "levels, i.e. 0.7 mg/dL and 138 mmol/L.")
        with self.assertRaises(spans.NotFound):
            spans.find_measurement(note, 0.7, "mg/dL", "creatinine")

    def test_value_and_unit_with_no_space(self):
        """`creatinine 8mg/dL` (mdrd-159).

        Cost us a build failure when the guardrail reassembled the phrase as
        "8 mg/dL" and then could not find it in the note.
        """
        note = "the day on which renal function was measured (creatinine 8mg/dL)."
        rec = spans.find_measurement(note, 8.0, "mg/dL", "creatinine")
        self.assertEqual(note[rec["value_span"][0]:rec["unit_span"][1]], "8mg/dL")


class TestOtherInputAnchoring(unittest.TestCase):
    """Weight, height and age -- the inputs Cockcroft-Gault also consumes."""

    def test_historical_weight_makes_the_locate_ambiguous(self):
        """`weighed 67.2 kg ... last recorded weight in chart was 71.2 kg`.

        Two weights, and editing the wrong one produces an item where the
        contradiction we think we injected is not the one the calculator sees.
        Ambiguity must raise, not resolve itself.
        """
        note = ("the patient weighed 67.2 kg, and was 173 cm tall. Chart review "
                "showed he had lost weight, last recorded weight 71.2 kg")
        rec = spans.find_measurement(note, 67.2, "kg", "weight")
        self.assertEqual(rec["value_text"], "67.2")
        with self.assertRaises(spans.NotFound):
            spans.find_measurement(note, 99.9, "kg", "weight")

    def test_height_with_a_parenthetical_conversion(self):
        """`160 cm (5 ft 3 in) tall` (usmle-1002).

        The label "tall" follows the value, and the parenthetical between them
        contains digits, so the height pattern must allow that one case.
        """
        note = "She is 160 cm (5 ft 3 in) tall and weighs 105 kg (231 lb)."
        rec = spans.find_measurement(note, 160.0, "cm", "height")
        self.assertEqual(rec["value_text"], "160")

    def test_age_written_as_a_hyphenated_compound(self):
        note = "An 87-year-old man was admitted to our hospital for anorexia."
        rec = spans.find_age(note, 87)
        self.assertEqual(rec["value_text"], "87")


class TestRaceLocator(unittest.TestCase):
    """MDRD's race coefficient. The costliest false positive of Week 1."""

    def test_white_blood_cell_is_not_a_race(self):
        """`a white blood cell (WBC) count of 13,900/mm2` (mdrd-145).

        A bare \\bwhite\\b matched this in seven notes, so the freeze recorded
        race as confirmed in notes that never mention it. Race must be anchored
        to a person.
        """
        note = "Laboratory tests revealed a white blood cell (WBC) count of 13,900/mm2."
        with self.assertRaises(spans.NotFound):
            spans.find_word(note, spans.RACE_PATTERNS, "White", "race")

    def test_white_matter_is_not_a_race(self):
        """`bilateral symmetrical white matter hypodensity` (mdrd-154)."""
        note = "Computed tomography revealed bilateral symmetrical white matter hypodensity."
        with self.assertRaises(spans.NotFound):
            spans.find_word(note, spans.RACE_PATTERNS, "White", "race")

    def test_genuine_demographic_mentions_still_match(self):
        for note, key in (("A 73-year-old Caucasian male presented with CKD.", "White"),
                          ("A 50-year-old black woman was admitted with dyspnea.", "Black"),
                          ("A 56-year-old African American male with a history.", "Black"),
                          ("Race: White. Vital signs stable on admission.", "White")):
            with self.subTest(note=note):
                rec = spans.find_word(note, spans.RACE_PATTERNS, key, "race")
                self.assertEqual(rec["value"], key)


class TestFramingGates(unittest.TestCase):
    """Framing that would tell a reader which of two values belongs."""

    def test_international_normalized_ratio_is_not_a_trend(self):
        """`international normalized ratio (INR), 1.73`.

        "normalized" tripped the trend pattern and rejected good seeds. The INR
        appears in roughly half these notes.
        """
        sentence = ("prothrombin time (PT), 20.3 s; international normalized ratio "
                    "(INR), 1.73; and creatinine, 1.4 mg/dL.")
        self.assertEqual(select_seeds.attached_framing(sentence), [])

    def test_lipoprotein_names_are_not_findings(self):
        """`high-density lipoprotein` / `low-density lipoprotein` (cockcroft_gault-14).

        "high" and "low" are analyte names here, not characterizations of the
        creatinine.
        """
        sentence = ("Laboratory results: serum creatinine 1.27 mg/dL; total cholesterol "
                    "224 mg/dl, low-density lipoprotein cholesterol 119 mg/dL, "
                    "high-density lipoprotein cholesterol 41 mg/dL.")
        self.assertEqual(select_seeds.attached_framing(sentence), [])

    def test_framing_attached_to_the_creatinine_is_caught(self):
        """`an elevated creatinine of 1.4 mg/dL` (ckd_epi-33).

        The adjective sits on the label, so the note has characterized the value
        and an injected normal creatinine would contradict the note's own reading
        rather than the other value. Auto-rejected.
        """
        sentence = ("Initial laboratory analysis was remarkable for an elevated "
                    "creatinine of 1.4 mg/dL (normal 0.7-1.3 mg/dL).")
        self.assertEqual(select_seeds.attached_framing(sentence), ["elevated"])

    def test_framing_across_an_intervening_value_falls_to_the_human_gate(self):
        """`serum creatinine levels (8.9 mg/dL) were highly increased` (ckd_epi-32).

        The framing does describe the creatinine, but the parenthetical between
        label and verb contains a decimal point, and the attachment patterns
        refuse to match across one. So this is *not* auto-rejected; it surfaces as
        a review flag and was killed by hand.

        The test pins that split deliberately. The gate is two-tier on purpose --
        regex makes the unambiguous calls, people make the rest -- and a change
        that silently promoted this to an auto-rejection would also start
        rejecting the neighbouring-analyte cases above.
        """
        sentence = ("In kidney panel, serum urea (155.8 mg/dL) and serum creatinine "
                    "levels (8.9 mg/dL) were highly increased.")
        self.assertEqual(select_seeds.attached_framing(sentence), [])
        loose = {m.group(0).lower()
                 for m in select_seeds.TREND_FRAMING.finditer(sentence)}
        self.assertIn("increased", loose)
        self.assertIn("ckd_epi-32", select_seeds.load_hand_kills())

    def test_trend_participle_on_the_label_is_caught(self):
        """`serum creatinine decreasing to 1.6 mg/dL` (mdrd-143)."""
        sentence = ("After decompression, the patient had an improvement in renal "
                    "function with serum creatinine decreasing to 1.6 mg/dL.")
        self.assertTrue(select_seeds.attached_framing(sentence))

    def test_framing_about_a_neighbouring_analyte_is_not_attached(self):
        """`her acetone was elevated` (cockcroft_gault-20).

        Present in the sentence, but describing the acetone. This is a review
        flag, not an automatic rejection.
        """
        sentence = ("her blood urea nitrogen was 50 mg/dl with creatinine 1.7 mg/dl, "
                    "her acetone was elevated, and her hemoglobin A1C was 14.3%.")
        self.assertEqual(select_seeds.attached_framing(sentence), [])


class TestThirdPartyAttribution(unittest.TestCase):
    """Whose measurement is it? Found in the Week 2 pilot, not by any check we ran."""

    def test_a_relatives_measurement_is_rejected(self):
        """`The paternal grandmother developed renal failure at 77 years ... Kidney
        size was about 16 cm ... and serum creatinine was 180 umol/l` (mdrd-tr3279).

        MedCalc extracted that creatinine as the patient's. He is 45 with ESRD, for
        which 180 umol/L is far too low; the grandmother has "moderate renal
        insufficiency", for which it fits. The value is in the note and uniquely
        anchored to the word creatinine, so nothing else we run objects.
        """
        note = ("The paternal grandmother developed renal failure at 77 years and "
                "then was hemodialyzed. Kidney size was about 16 cm in diameter and "
                "serum creatinine was 180 mg/dL.")
        at = note.index("180")
        self.assertEqual(
            select_seeds.attributed_to_third_party(note, at).lower(), "grandmother")

    def test_a_relative_as_informant_is_not_an_attribution(self):
        """`Her husband endorsed good compliance ... for her OSA. Laboratory studies
        showed serum creatinine of 2.2 mg/dL` (mdrd-tr3282).

        The husband is an informant, not the subject. The intervening "her" is what
        says the lab is the patient's, and without counting pronouns the rule
        rejects this good seed too.
        """
        note = ("Her husband endorsed good compliance with medications and "
                "continuous positive airway pressure for her OSA. Laboratory "
                "studies showed serum creatinine of 2.2 mg/dL.")
        at = note.index("2.2")
        self.assertIsNone(select_seeds.attributed_to_third_party(note, at))

    def test_a_family_history_opener_does_not_reach_forward(self):
        """A note opening on family history must not disqualify the patient's own
        results further down. Paragraph scoping is what prevents that."""
        note = ("His 69-year-old father had ESRD at 52 because of polycystic "
                "kidneys.\nThe patient was admitted for evaluation. Laboratory "
                "studies showed serum creatinine of 1.4 mg/dL.")
        at = note.index("1.4")
        self.assertIsNone(select_seeds.attributed_to_third_party(note, at))


class TestDerivedRenalGate(unittest.TestCase):
    """A stated eGFR re-states the creatinine and breaks both defect conditions."""

    def test_egfr_is_rejected(self):
        """`serum creatinine: 1.42 mg/dL; eGFR: 49.1 mL/min/1.73 m2` (cockcroft_gault-8).

        Deleting the creatinine leaves the item answerable, and a reader can keep
        whichever injected value matches the eGFR.
        """
        note = ("impaired renal function [i.e., serum creatinine: 1.42 mg/dL; "
                "eGFR: 49.1 mL/min/1.73 m2] was observed after admission.")
        self.assertTrue(select_seeds.DERIVED_RENAL.search(note))

    def test_plain_note_is_not_rejected(self):
        note = "blood urea nitrogen, 34.4 mg/dL; and creatinine, 1.4 mg/dL."
        self.assertIsNone(select_seeds.DERIVED_RENAL.search(note))


class TestExcision(unittest.TestCase):
    """The missing condition: delete the value, leave the note coherent."""

    def _span(self, note):
        return spans.find_measurement(note, 1.4, "mg/dL", "creatinine")

    def test_seam_defect_trade_is_caught(self):
        """`renal function with serum creatinine decreasing to 1.6 mg/dL ().`

        Removing the measurement dropped a stray "()" and left "renal function
        with." -- one punctuation defect before, one after. A count-based check
        passed it; the multiset check does not.
        """
        note = "the patient had an improvement in renal function with creatinine, 1.4 mg/dL ()."
        rec = self._span(note)
        new, seam = construct.delete_measurement(note, rec)
        with self.assertRaises(construct.BuildError):
            construct.check_missing(note, new, {"input_spans": {"creatinine": rec}}, seam)

    def test_excision_keeps_the_rest_byte_identical(self):
        note = ("Laboratory findings: blood urea nitrogen, 34.4 mg/dL; and creatinine, "
                "1.4 mg/dL. Serologic tests were all negative.")
        rec = self._span(note)
        new, _ = construct.delete_measurement(note, rec)
        self.assertNotIn("1.4 mg/dL", new)
        self.assertIn("blood urea nitrogen, 34.4 mg/dL", new)
        self.assertIn("Serologic tests were all negative.", new)


class TestExcisionSeams(unittest.TestCase):
    """The nine damaged excisions the Week 2 spot-check found.

    Every automated check passed these: the excision was contiguous, it removed
    the creatinine, and the rest of the note was byte-identical. None of them
    asked whether the result reads. Eight were repaired; the ninth was rejected.
    """

    def _missing(self, note, value=1.4, unit="mg/dL"):
        rec = spans.find_measurement(note, value, unit, "creatinine")
        return construct.delete_measurement(note, rec)[0]

    def test_bracketed_reference_range_comes_out_too(self):
        """`urea 44 mg/dL [17-43], creatinine 0.62 mg/dL [0.51-0.95],` (mdrd-tr3249).

        Leaving the range behind orphans it against the previous analyte, giving
        `urea 44 mg/dL [17-43] [0.51-0.95]`.
        """
        note = ("urea 44 mg/dL [17-43], creatinine 0.62 mg/dL [0.51-0.95], "
                "aspartate aminotransferase 28 U/L [<35].")
        out = self._missing(note, 0.62)
        self.assertNotIn("[0.51-0.95]", out)
        self.assertIn("urea 44 mg/dL [17-43]", out)

    def test_bare_numeric_parenthetical_range_comes_out_too(self):
        """`creatinine of 1.53 mg/dL (0.50-1.05 mg/dL),` (mdrd-tr3281).

        The range carries no "normal" or "reference" label, so the labelled
        pattern alone left it stranded.
        """
        note = ("blood urea nitrogen of 31 mg/dL (6-23 mg/dL), creatinine of 1.53 mg/dL "
                "(0.50-1.05 mg/dL), C reactive protein of 31.44 mg/dL.")
        out = self._missing(note, 1.53)
        self.assertNotIn("(0.50-1.05 mg/dL)", out)

    def test_enclosing_bracket_is_balanced(self):
        """`hemoglobin (14.4 g/dL), serum creatinine (0.57 mg/dL), serum total`
        (cockcroft_gault-tr1).

        The span stops at the unit, inside the parenthesis, so the closing bracket
        was orphaned and produced `(14.4 g/dL)),`.
        """
        note = ("revealed normal levels of hemoglobin (14.4 g/dL), serum creatinine "
                "(0.57 mg/dL), serum total cholesterol (144 mg/dL).")
        out = self._missing(note, 0.57)
        self.assertNotIn("))", out)
        self.assertEqual(out.count("("), out.count(")"))

    def test_only_one_separator_is_absorbed(self):
        """`severely disturbed (creatinine = 5.4 mg/dL), and she had also` (ckd_epi-30).

        The enclosing-bracket rule ate the leading space and the trailing `, and `
        was taken as well, fusing the neighbours into `disturbedshe`.
        """
        note = ("Renal function test was severely disturbed (creatinine = 5.4 mg/dL), "
                "and she had also hyponatremia.")
        out = self._missing(note, 5.4)
        self.assertNotIn("disturbedshe", out)
        self.assertIn("severely disturbed", out)

    def test_leading_conjunction_with_no_punctuation(self):
        """`about 3 centimeters and serum creatinine was 180 umol/l.` (mdrd-tr3279).

        No separator to take, so the bare `and` was left dangling before the stop.
        """
        note = ("there were multiple cysts about 3 centimeters and serum creatinine "
                "was 180 µmol/L. Computed tomography was not performed.")
        out = self._missing(note, 180.0, "µmol/L")
        self.assertNotIn("and.", out)
        self.assertIn("about 3 centimeters.", out)

    def test_leading_conjunction_with_a_determiner(self):
        """`hyperlipidemia and a serum creatinine level of 3.0 mg/dL.` (mdrd-tr3359)."""
        note = ("laboratory tests reveal hyperlipidemia and a serum creatinine level "
                "of 3.0 mg/dL. 4.5 g of protein are excreted in the urine.")
        out = self._missing(note, 3.0)
        self.assertNotIn("and a.", out)
        self.assertIn("hyperlipidemia.", out)

    def test_trailing_conjunction_with_no_punctuation(self):
        """`showed serum creatinine of 2.2 mg/dL and blood urea nitrogen of 29`
        (mdrd-tr3282). Left `showed and blood urea nitrogen`.
        """
        note = ("Laboratory studies showed serum creatinine of 2.2 mg/dL and blood "
                "urea nitrogen of 29 mg/dL.")
        out = self._missing(note, 2.2)
        self.assertNotIn("showed and", out)
        self.assertIn("showed blood urea nitrogen of 29 mg/dL", out)

    def test_a_stranded_verb_object_is_rejected_not_repaired(self):
        """`panel revealed creatinine of 2.31 mg/dL from normal baseline (...)`
        (ckd_epi-38).

        The trailing qualifier belongs to the creatinine, and excising the
        measurement alone leaves `revealed from normal baseline`. No general rule
        recovers it, so the seed is rejected by hand rather than shipped.
        """
        note = ("Basic metabolic panel revealed creatinine of 2.31 mg/dL from normal "
                "baseline (Normal 0.6-1.3 mg/dL) and blood urea nitrogen of 28 mg/dL.")
        rec = spans.find_measurement(note, 2.31, "mg/dL", "creatinine")
        new, seam = construct.delete_measurement(note, rec)
        with self.assertRaises(construct.BuildError):
            construct.check_missing(note, new, {"input_spans": {"creatinine": rec}}, seam)
        self.assertIn("ckd_epi-38", select_seeds.load_hand_kills())


class TestInjection(unittest.TestCase):
    """The value-conflict condition: rewrite the value phrase and nothing else."""

    def _rec(self, note, value=1.4):
        return spans.find_measurement(note, value, "mg/dL", "creatinine")

    def test_reference_range_covering_both_values_is_allowed(self):
        """`creatinine of 1.7 and 3.74 mg/dL (normal range 0.6-1.2 mg/dL)` (ckd_epi-28).

        A range following both values says the same thing about each. The first
        version of the guardrail rejected this, which was wrong.
        """
        note = "investigations showed creatinine of 1.7 mg/dL (normal range 0.6-1.2 mg/dL), calcium 21 mg/dL."
        rec = self._rec(note, 1.7)
        new, replacement = construct.inject_conflict(note, rec, 3.74, "mg/dL")
        self.assertIn("1.7 and 3.74 mg/dL", new)
        self.assertIn("(normal range 0.6-1.2 mg/dL)", new)

    def test_edit_is_confined_to_the_value_phrase(self):
        note = ("Laboratory findings: blood urea nitrogen, 34.4 mg/dL; and creatinine, "
                "1.4 mg/dL. Serologic tests were all negative.")
        rec = self._rec(note)
        new, _ = construct.inject_conflict(note, rec, 3.64, "mg/dL")
        v0 = rec["value_span"][0]
        self.assertEqual(note[:v0], new[:v0])
        self.assertTrue(new.endswith("Serologic tests were all negative."))

    def test_injection_carries_no_recency_cue(self):
        note = "and creatinine, 1.4 mg/dL. Serologic tests were negative."
        _, replacement = construct.inject_conflict(note, self._rec(note), 3.64, "mg/dL")
        for cue in construct.CUE_BLOCKLIST:
            self.assertNotIn(cue, replacement.lower())


class TestChecker(unittest.TestCase):
    """The deterministic checker: what it must catch, and what it must not."""

    def test_catches_a_bmi_contradicting_its_components(self):
        note = "She is 180 cm tall and weighs 80 kg; BMI is 41 kg/m2."
        findings = checker.check(note)["findings"]
        self.assertTrue(any(f["quantity"] == "BMI" for f in findings))

    def test_catches_an_impossible_blood_pressure(self):
        findings = checker.check("Blood pressure 80/140 mmHg on arrival.")["findings"]
        self.assertTrue(any(f["check"] == "impossible_value" for f in findings))

    def test_a_target_is_not_a_stated_value(self):
        """`unable to maintain a mean arterial pressure above 65 mmHg` (pmc-7755652-1).

        Reading 65 as the patient's MAP inverts what the note says. Reported as a
        finding until the comparative guard was added.
        """
        note = ("He was unable to maintain a mean arterial pressure above 65 mmHg. "
                "Blood pressure was 50/35 mmHg.")
        self.assertEqual(checker.check(note)["findings"], [])

    def test_albumin_corrected_anion_gap_is_a_different_quantity(self):
        """`anion gap 25 mEq/L after correcting for albumin` (pmc-6957036-1)."""
        note = ("sodium 142 mEq/L, chloride 102 mEq/L, bicarbonate 15 mEq/L, "
                "anion gap 25 mEq/L after correcting for albumin.")
        self.assertEqual(checker.check(note)["findings"], [])

    def test_stays_silent_on_a_consistent_note(self):
        note = ("She is 160 cm tall and weighs 64 kg; BMI is 25 kg/m2. "
                "Blood pressure 120/80 mmHg.")
        self.assertEqual(checker.check(note)["findings"], [])


class TestBloodPressureLocator(unittest.TestCase):
    """Week 3, Family B. Every case here is a real form from the MAP rows.

    The locator was measured against all 948 before these were written: 826
    notes locate uniquely and pass the one-pressure gate. The cases that did not
    are the ones worth pinning, because each is a way the family could be built
    on a value the calculator never reads.
    """

    def test_the_three_unit_spellings(self):
        for text, sys_v, dia_v in (("blood pressure 138/90 mm Hg", 138, 90),
                                   ("BP of 140/80 mmHg", 140, 80),
                                   ("Blood pressure 120/70 mm of Hg", 120, 70)):
            note = f"On admission, {text}, and she was comfortable."
            rec = spans.find_blood_pressure(note, sys_v, dia_v)
            self.assertTrue(rec["has_unit"], text)
            self.assertEqual(rec["pair_text"], f"{sys_v}/{dia_v}")

    def test_glasgow_coma_score_is_not_a_blood_pressure(self):
        """A bare digit-slash-digit matches this, which is why the unit anchors."""
        note = "His Glasgow Coma Score was 15/15 and he was alert."
        self.assertEqual(spans.count_blood_pressures(note), [])
        with self.assertRaises(spans.NotFound):
            spans.find_blood_pressure(note, 15, 15)

    def test_parenthesised_abbreviation_form(self):
        note = "Vitals: blood pressure (BP) was 150/92 mmHg, pulse 88/min."
        rec = spans.find_blood_pressure(note, 150, 92)
        self.assertEqual(note[rec["sys_span"][0]:rec["sys_span"][1]], "150")
        self.assertEqual(note[rec["dia_span"][0]:rec["dia_span"][1]], "92")

    def test_pulse_rate_per_minute_is_not_absorbed(self):
        """`pulse rate - 96/min` sits next to the pressure in this register."""
        note = "On examination, blood pressure - 160/100 mmHg, pulse rate - 96/min."
        self.assertEqual(len(spans.count_blood_pressures(note)), 1)
        rec = spans.find_blood_pressure(note, 160, 100)
        self.assertEqual(rec["pair_text"], "160/100")

    def test_two_pressures_are_counted_as_two(self):
        note = ("Blood pressure was 122/80 mmHg on arrival and blood pressure "
                "135/92 mmHg the next morning.")
        self.assertEqual(len(spans.count_blood_pressures(note)), 2)

    def test_entity_disagreeing_with_the_note_is_not_found(self):
        """pmc-6637642-1: the note says 85/140, MedCalc's entities say 140/85.

        The extraction put an impossible pair back into plausible order. Locating
        on the entity value would silently seed from a pressure the note does not
        state, so the disagreement has to surface as NotFound.
        """
        note = ("On examination he weighed 67 kg, blood pressure 85/140 mmHg, "
                "pulse rate 60 pulses/min.")
        with self.assertRaises(spans.NotFound):
            spans.find_blood_pressure(note, 140, 85)
        rec = spans.find_blood_pressure(note, 85, 140)
        self.assertTrue(rec["impossible"])

    def test_impossible_flag_tracks_the_stated_order(self):
        ok = spans.find_blood_pressure("Blood pressure 140/80 mmHg.", 140, 80)
        self.assertFalse(ok["impossible"])
        bad = spans.find_blood_pressure("Blood pressure 45/80 mmHg.", 45, 80)
        self.assertTrue(bad["impossible"])

    def test_unitless_pressure_is_located_but_marked(self):
        note = "Vital signs: blood pressure 120/70, heart rate 88."
        rec = spans.find_blood_pressure(note, 120, 70)
        self.assertFalse(rec["has_unit"])
        self.assertIsNone(rec["unit_span"])

    def test_unit_bearing_match_wins_over_unitless(self):
        """Pooling the two would make a usable note look ambiguous."""
        note = ("Blood pressure 120/70 was recorded by the nurse; on review "
                "blood pressure 138/90 mm Hg was confirmed.")
        hits = spans.count_blood_pressures(note)
        self.assertEqual(len(hits), 1)
        self.assertTrue(spans.find_blood_pressure(note, 138, 90)["has_unit"])

    def test_spans_cover_only_the_digits(self):
        note = "Her blood pressure was 161/78 mmHg on arrival."
        rec = spans.find_blood_pressure(note, 161, 78)
        self.assertEqual(note[rec["sys_span"][0]:rec["sys_span"][1]], "161")
        self.assertEqual(note[rec["dia_span"][0]:rec["dia_span"][1]], "78")
        self.assertEqual(note[rec["unit_span"][0]:rec["unit_span"][1]], "mmHg")
        self.assertEqual(rec["pair_text"], "161/78")


class TestBmiLocator(unittest.TestCase):
    """Week 3, Family A. Every phrasing here is a real one from the corpus."""

    def test_the_common_phrasings(self):
        for text, want in (
                ("She is 160 cm tall and weighs 104 kg; BMI is 41 kg/m2.", 41.0),
                ("presented with a body mass index, 18.3, and no other findings", 18.3),
                ("with a body mass index of 22.1 kilograms per meter squared", 22.1),
                ("The patient was obese (175 cm, 95 kg, BMI (body mass index): 31.0)", 31.0),
                ("The patient's BMI was calculated as 41.7 kg/m2 at admission", 41.7)):
            self.assertEqual(spans.find_bmi(text)["value"], want, text)

    def test_the_unit_is_optional_but_recorded(self):
        with_unit = spans.find_bmi("BMI is 41 kg/m2 on admission.")
        without = spans.find_bmi("with a body mass index, 18.3, and no other findings")
        self.assertTrue(with_unit["has_unit"])
        self.assertFalse(without["has_unit"])
        self.assertIsNone(without["unit_span"])

    def test_two_documented_indices_are_ambiguous(self):
        """A note recording a trend has already made the point we would inject."""
        note = "BMI is 31 kg/m2 on admission and BMI is 29 kg/m2 at discharge."
        self.assertEqual(len(spans.count_bmis(note)), 2)
        with self.assertRaises(spans.Ambiguous):
            spans.find_bmi(note)

    def test_a_note_stating_only_components_has_no_bmi(self):
        self.assertEqual(spans.count_bmis("She is 160 cm tall and weighs 60 kg."), [])

    def test_span_covers_only_the_digits(self):
        note = "Her weight was 99 kg and her height was 179 cm with a BMI of 31 kg/m2."
        rec = spans.find_bmi(note)
        self.assertEqual(note[rec["value_span"][0]:rec["value_span"][1]], "31")

    def test_checker_catches_a_contradicted_index(self):
        """Family A's whole claim is that this fires. If it stops, the family is false."""
        note = "She is 160 cm tall and weighs 104 kg; BMI is 22 kg/m2."
        found = [f for f in checker.check(note)["findings"]
                 if f.get("check") == "derived_value"
                 and str(f.get("quantity")).lower() == "bmi"]
        self.assertTrue(found)
        self.assertAlmostEqual(found[0]["recomputed"], 40.625, places=2)

    def test_checker_stays_silent_when_the_index_agrees(self):
        note = "She is 160 cm tall and weighs 104 kg; BMI is 40.6 kg/m2."
        self.assertEqual([f for f in checker.check(note)["findings"]
                          if f.get("check") == "derived_value"], [])


class TestCriterionLocator(unittest.TestCase):
    """Week 3, Family C. Every case is a real sentence from the CHA2DS2-VASc rows."""

    def test_a_plain_assertion_is_found(self):
        note = ("An 85-year-old woman with a past medical history of hypertension, "
                "hyperlipidemia, and atrial fibrillation presented to the clinic.")
        self.assertEqual(spans.find_criterion(note, "hypertension")["value_text"].lower(),
                         "hypertension")

    def test_pulmonary_hypertension_is_a_different_condition(self):
        """`severe pulmonary hypertension` is not the systemic hypertension scored."""
        note = "Echocardiography revealed an LVEF of 20% and severe pulmonary hypertension."
        with self.assertRaises(spans.NotFound):
            spans.find_criterion(note, "hypertension")

    def test_portal_hypertension_is_a_different_condition(self):
        note = "By the age of two she had developed portal hypertension resulting in varices."
        with self.assertRaises(spans.NotFound):
            spans.find_criterion(note, "hypertension")

    def test_one_negator_denies_a_whole_list(self):
        """`no history of X, Y or Z` denies all three, not just the first."""
        note = "There was no history of hypertension, dyslipidaemia, diabetes mellitus or prior stroke."
        for key in ("hypertension", "diabetes", "stroke"):
            with self.assertRaises(spans.NotFound, msg=key):
                spans.find_criterion(note, key)

    def test_a_negation_does_not_survive_a_contrastive_conjunction(self):
        note = "She had no history of diabetes, but hypertension was documented in 2014."
        with self.assertRaises(spans.NotFound):
            spans.find_criterion(note, "diabetes")
        self.assertTrue(spans.find_criterion(note, "hypertension"))

    def test_a_negation_does_not_cross_a_sentence_boundary(self):
        note = "She had no history of diabetes. Hypertension was documented in 2014."
        self.assertTrue(spans.find_criterion(note, "hypertension"))

    def test_a_relatives_criterion_is_not_the_patients(self):
        """`Her family history is positive for hypertension` is the mother's.

        MedCalc records the criterion as present on this note. Same failure as the
        seed whose creatinine belonged to the patient's grandmother.
        """
        note = "Her family history is positive for hypertension and diabetes."
        with self.assertRaises(spans.NotFound):
            spans.find_criterion(note, "hypertension")

    def test_the_adjective_form_counts(self):
        note = "A 73-year-old obese hypertensive diabetic man presented with palpitations."
        self.assertTrue(spans.find_criterion(note, "hypertension"))
        self.assertTrue(spans.find_criterion(note, "diabetes"))

    def test_two_assertions_are_ambiguous(self):
        note = ("His history includes hypertension. Hypertension was again documented "
                "at the follow-up visit.")
        self.assertEqual(len(spans.count_criterion_mentions(note, "hypertension")), 2)
        with self.assertRaises(spans.Ambiguous):
            spans.find_criterion(note, "hypertension")

    def test_rejected_mentions_are_reported_not_hidden(self):
        note = ("She had no history of diabetes. Hypertension was documented, and "
                "pulmonary hypertension was noted on echocardiography.")
        rec = spans.find_criterion(note, "hypertension")
        self.assertTrue(any(r["why"] == "names a different condition"
                            for r in rec["rejected_mentions"]))

    def test_a_criterion_word_inside_an_instrument_name_is_not_an_assertion(self):
        """Found by reading the built items; every automated check had passed them.

        The word really is present, really is undenied, and really is about this
        admission -- it just names the measuring instrument rather than the
        patient's history.
        """
        for note, key in (
                ("The National Institutes of Health Stroke Scale (NIHSS) score was 12.", "stroke"),
                ("His NIH Stroke Scale/Score (NIHSS) was 2 on arrival.", "stroke"),
                ("Thrombolysis In Myocardial Infarction (TIMI) flow 3 was observed.",
                 "vascular_disease")):
            with self.assertRaises(spans.NotFound, msg=note):
                spans.find_criterion(note, key)

    def test_the_instrument_gate_does_not_swallow_real_assertions(self):
        self.assertTrue(spans.find_criterion(
            "He has a past medical history of stroke and atrial fibrillation.", "stroke"))
        self.assertTrue(spans.find_criterion(
            "His history includes myocardial infarction in 2015.", "vascular_disease"))

    def test_criteria_with_time_windows_are_not_usable(self):
        """A keyword cannot see `in the previous 4 weeks`; excluding them is the point."""
        for key in ("surgery_in_past4weeks", "immobilization_for_3days",
                    "malignancy_with_treatment", "previous_pe"):
            self.assertNotIn(key, spans.USABLE_CRITERIA)

    def test_every_usable_criterion_has_vocabulary(self):
        for key in spans.USABLE_CRITERIA:
            self.assertIn(key, spans.CRITERION_TERMS)


class TestAttachedFraming(unittest.TestCase):
    """Week 3. Framing written for the published value, contradicting our injection.

    Every case here was found by reading built items, not by a check. The pattern
    is the same in both families: a clinical judgement sits beside the value, our
    injection is required to cross a clinical boundary, and the judgement then
    contradicts the number it describes -- a second contradiction we did not build
    and a model may flag instead of ours.
    """

    def test_bmi_framing_is_caught(self):
        import family_a
        rx = family_a.DERIVED_SPECS["bmi"]["framing"]
        for text in ("weighed 91 kg (morbid obesity, body mass index 35.0 kg/m2)",
                     "moderately overweight (62.4 kg, body mass index [BMI] 26.52 kg/m2)",
                     "a cachectic man with a body mass index of 15.1"):
            self.assertTrue(re.search(rx, text, re.I), text)

    def test_bmi_framing_does_not_fire_on_a_plain_statement(self):
        import family_a
        rx = family_a.DERIVED_SPECS["bmi"]["framing"]
        self.assertIsNone(re.search(
            rx, "She is 160 cm tall and weighs 105 kg; BMI is 41 kg/m2.", re.I))

    def test_blood_pressure_framing_is_caught(self):
        import family_b
        for text in ("Physical examination was normal (BMI 23.0 kg/m2, blood pressure 125/70 mmHg)",
                     "vital signs were stable, blood pressure 132/80 mmHg"):
            self.assertTrue(re.search(family_b.FRAMING, text, re.I), text)

    def test_blood_pressure_framing_does_not_fire_on_a_plain_vitals_line(self):
        import family_b
        self.assertIsNone(re.search(
            family_b.FRAMING,
            "He was afebrile, with a pulse rate of 108/min, BP of 140/80 mmHg.", re.I))


class TestBreadthArms(unittest.TestCase):
    """Week 3 breadth: osmolality's checker rule and the LDL conflict arm."""

    def test_osmolality_fires_on_a_real_contradiction(self):
        note = ("Sodium 140 mEq/L, BUN 20 mg/dL, glucose 90 mg/dL. The calculated "
                "serum osmolality is reported as 400 mOsm/kg.")
        found = [f for f in checker.check(note)["findings"]
                 if f.get("quantity") == "serum osmolality"]
        self.assertTrue(found)
        self.assertAlmostEqual(found[0]["recomputed"], 292.1, places=0)

    def test_osmolality_stays_silent_when_it_agrees(self):
        note = ("Sodium 140 mEq/L, BUN 20 mg/dL, glucose 90 mg/dL. The calculated "
                "serum osmolality is 292 mOsm/kg.")
        self.assertEqual([f for f in checker.check(note)["findings"]
                          if f.get("quantity") == "serum osmolality"], [])

    def test_an_osmolal_gap_is_not_an_arithmetic_error(self):
        """A measured osmolality differing from the calculated one is a finding."""
        note = ("Sodium 140 mEq/L, BUN 20 mg/dL, glucose 90 mg/dL, measured serum "
                "osmolality 320 mOsm/kg.")
        self.assertEqual([f for f in checker.check(note)["findings"]
                          if f.get("quantity") == "serum osmolality"], [])

    def test_urine_osmolality_is_a_different_quantity(self):
        note = ("Sodium 140 mEq/L, BUN 20 mg/dL, glucose 90 mg/dL. Urine osmolality "
                "600 mOsm/kg.")
        self.assertEqual([f for f in checker.check(note)["findings"]
                          if f.get("quantity") == "serum osmolality"], [])
        with self.assertRaises(spans.NotFound):
            spans.find_derived("Urine osmolality 600 mOsm/kg", "osmolality")

    def test_the_osmolality_locator_does_not_grab_specific_gravity(self):
        """`... were found as 1,007, 323 mOsm/kg ...` -- 1.007 is the gravity."""
        note = "urine specific gravity, serum and urine osmolality were found as 1,007, 323 mOsm/kg"
        try:
            got = spans.find_derived(note, "osmolality")["value"]
        except (spans.NotFound, spans.Ambiguous):
            got = None
        self.assertNotEqual(got, 1.007)

    def test_electrolytes_anchor_in_either_unit(self):
        """mEq/L and mmol/L are the same number for these ions, and notes use both."""
        for text, value, label in (("sodium, 125 meq/l; potassium, 3.8 meq/l", 125, "sodium"),
                                   ("chloride 101 mmol/L, bicarbonate 24 mmol/L", 101, "chloride"),
                                   ("bicarbonate 17 mEq/L on arrival", 17, "bicarbonate")):
            rec = spans.find_measurement(text, value, "mEq/L", label)
            self.assertEqual(rec["value"], float(value))

    def test_a_component_the_note_contradicts_is_not_usable(self):
        """One anion gap note says `bicarbonate 24` where MedCalc records 17.

        Anchoring only the component being conflicted left that invisible, and the
        clean answer we would have published was not the answer the note supports.
        """
        note = "sodium 136 mEq/L, chloride 101 mEq/L, bicarbonate 24 mEq/L"
        with self.assertRaises(spans.NotFound):
            spans.find_measurement(note, 17, "mEq/L", "bicarbonate")
        self.assertTrue(spans.find_measurement(note, 24, "mEq/L", "bicarbonate"))

    def test_hdl_is_located_without_matching_ldl(self):
        self.assertEqual(spans.find_measurement("HDL 39 mg/dL, LDL 96 mg/dL",
                                                39, "mg/dL", "hdl")["value"], 39.0)
        self.assertEqual(spans.count_measurements("LDL 96 mg/dL", "hdl", ["mg/dL"]), [])

    def test_a_two_value_hdl_phrase_is_no_longer_singly_anchored(self):
        """The gap forbids digits, so a conflict phrase must not anchor at all.

        Asserting the opposite -- that the note now states two HDLs -- failed all
        twenty builds, because the locator is designed never to step over an
        intervening value.
        """
        self.assertEqual(
            spans.count_measurements("HDL 39 and 72 mg/dL", "hdl", ["mg/dL"]), [])


class TestFamilyCSelection(unittest.TestCase):
    """Week 3. The round-robin that stops one criterion dominating the family."""

    @classmethod
    def setUpClass(cls):
        import family_c
        cls.family_c = family_c

    @staticmethod
    def _cands(spec):
        out = []
        for key, (n_test, n_train) in spec.items():
            for i in range(n_test):
                out.append({"criterion": key, "split": "test", "note_id": f"{key}-t{i}"})
            for i in range(n_train):
                out.append({"criterion": key, "split": "train", "note_id": f"{key}-r{i}"})
        return out

    def test_a_common_criterion_does_not_take_the_whole_family(self):
        """Corpus order gave 15 hypertension of 30; rotation is what fixes it."""
        cands = self._cands({"hypertension": (200, 100), "diabetes": (5, 5),
                             "stroke": (4, 4), "chf": (3, 3)})
        picked = self.family_c.round_robin(cands, 20)
        counts = collections.Counter(c["criterion"] for c in picked)
        self.assertEqual(len(picked), 20)
        self.assertLessEqual(counts["hypertension"], 8,
                             f"one criterion dominates: {dict(counts)}")
        self.assertEqual(set(counts), {"hypertension", "diabetes", "stroke", "chf"})

    def test_test_split_is_taken_before_train_within_a_criterion(self):
        cands = self._cands({"hypertension": (2, 5)})
        picked = self.family_c.round_robin(cands, 3)
        self.assertEqual([c["split"] for c in picked], ["test", "test", "train"])

    def test_it_does_not_invent_items_when_supply_runs_out(self):
        cands = self._cands({"confusion": (2, 1)})
        self.assertEqual(len(self.family_c.round_robin(cands, 10)), 3)

    def test_a_scarce_criterion_is_not_starved(self):
        cands = self._cands({"hypertension": (50, 50), "hemoptysis": (1, 0)})
        picked = self.family_c.round_robin(cands, 6)
        self.assertIn("hemoptysis", {c["criterion"] for c in picked})

    def test_every_denial_reads_as_a_denial_not_a_second_assertion(self):
        """If the injected sentence parsed as an assertion the note would have two."""
        for key, sentence in self.family_c.DENIALS.items():
            self.assertEqual(spans.count_criterion_mentions(sentence, key), [],
                             f"{key}: {sentence!r} reads as an assertion")

    def test_every_usable_criterion_has_a_denial(self):
        for key in spans.USABLE_CRITERIA:
            self.assertIn(key, self.family_c.DENIALS)


class TestRuleBasedCriteriaMapping(unittest.TestCase):
    """Week 3, Family C. The mapping table itself, checked without the substrate.

    Whether each criterion actually moves the score is a behavioural question and
    is answered by `verify_criteria.py`, which needs MedCalc downloaded and runs in
    the pipeline workflow. What is checked here is the part that can rot silently
    in an edit: names, coverage, and the collisions that would make two criteria
    read as one.
    """

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(ROOT, "audit"))
        import entities
        cls.entities = entities

    def test_the_three_rule_based_scores_are_mapped(self):
        self.assertEqual(set(self.entities.CRITERIA), {4, 45, 8})

    def test_every_criterion_maps_to_a_distinct_internal_name(self):
        """Two display keys colliding on one internal name would silently drop one."""
        for calc_id, table in self.entities.CRITERIA.items():
            names = list(table.values())
            self.assertEqual(len(names), len(set(names)),
                             f"calc {calc_id} maps two criteria to the same name")

    def test_the_upstream_misspelling_is_preserved(self):
        """`Congestive Heart Faliure` is misspelled in MedCalc's own entities.

        Correcting it here would map to a key that never appears in the data, and
        `.get()` would read the criterion as absent without raising.
        """
        self.assertIn("Congestive Heart Faliure", self.entities.CRITERIA[4])
        self.assertNotIn("Congestive Heart Failure", self.entities.CRITERIA[4])

    def test_criterion_counts_match_what_the_implementations_read(self):
        self.assertEqual(len(self.entities.CRITERIA[4]), 7)    # CHA2DS2-VASc
        self.assertEqual(len(self.entities.CRITERIA[45]), 1)   # CURB-65
        self.assertEqual(len(self.entities.CRITERIA[8]), 8)    # Wells' PE

    def test_continuous_inputs_are_separate_from_criteria(self):
        """age and sex are scored but are not boolean criteria; they must not mix."""
        for calc_id, table in self.entities.CRITERIA.items():
            for internal in table.values():
                self.assertNotIn(internal, ("age", "sex"),
                                 f"calc {calc_id} lists a continuous input as a criterion")
        self.assertEqual(set(self.entities.RULE_BASED_REQUIRED), {4, 45, 8})

    def test_rule_based_scores_stay_out_of_the_audit_population(self):
        """REQUIRED defines the Week 1 label audit; widening it changes a reported number."""
        for calc_id in self.entities.CRITERIA:
            self.assertNotIn(calc_id, self.entities.REQUIRED)


if __name__ == "__main__":
    unittest.main(verbosity=2)
