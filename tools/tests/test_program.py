import json
import tempfile
import unittest
from pathlib import Path

from tools.scholarship.program import DEFAULT_RULES, load_rules, load_sequence
from tools.scholarship.state import CollegeError


class Tmp(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, content):
        p = self.dir / name
        p.write_text(content if isinstance(content, str) else json.dumps(content))
        return p


class TestSequence(Tmp):
    def test_sequence_missing_is_empty(self):
        self.assertEqual(load_sequence(self.dir / "nope.json"), [])

    def test_sequence_malformed(self):
        p = self.write("seq.json", [{"id": "L1.01", "type": "lesson", "module": "M1", "title": "T"}])
        with self.assertRaises(CollegeError) as cm:
            load_sequence(p)
        self.assertIn("id, module, semester, title, type", str(cm.exception))

    def test_sequence_invalid_json(self):
        with self.assertRaises(CollegeError):
            load_sequence(self.write("seq.json", "["))


class TestRules(Tmp):
    def rules(self, content):
        return load_rules(self.write("course.json", content))

    def test_rules_missing_file_gives_defaults(self):
        self.assertEqual(load_rules(self.dir / "nope.json"), DEFAULT_RULES)

    def test_defaults_are_never_shared(self):
        load_rules(self.dir / "nope.json")["weights"]["modules"] = 0
        self.assertEqual(DEFAULT_RULES["weights"]["modules"], 0.6)

    def test_rules_partial_override(self):
        r = self.rules({"weights": {"modules": 0.5, "exams": 0.5}})
        self.assertEqual(r["weights"], {"modules": 0.5, "exams": 0.5})
        self.assertEqual(r["blocking"], DEFAULT_RULES["blocking"])
        self.assertEqual(r["coefficients"], DEFAULT_RULES["coefficients"])
        self.assertEqual(r["max_attempts"], DEFAULT_RULES["max_attempts"])

    def test_rules_invalid_json(self):
        with self.assertRaises(CollegeError):
            self.rules("{")

    def test_rules_unknown_key_refused(self):
        with self.assertRaises(CollegeError) as cm:
            self.rules({"weight": {"modules": 0.5, "exams": 0.5}})
        self.assertIn("weight", str(cm.exception))

    def test_rules_unknown_type_refused(self):
        with self.assertRaises(CollegeError) as cm:
            self.rules({"coefficients": {"tp": 2}})
        self.assertIn("tp", str(cm.exception))

    def test_rules_coefficients_must_cover_all_types(self):
        coefs = {k: v for k, v in DEFAULT_RULES["coefficients"].items() if k != "lab"}
        with self.assertRaises(CollegeError) as cm:
            self.rules({"coefficients": coefs})
        self.assertIn("lab", str(cm.exception))

    def test_rules_blocking_must_be_known_types(self):
        for bad in ("lab", ["tp"]):
            with self.subTest(bad=bad), self.assertRaises(CollegeError):
                self.rules({"blocking": bad})

    def test_rules_weights_must_sum_to_one(self):
        with self.assertRaises(CollegeError):
            self.rules({"weights": {"modules": 0.6, "exams": 0.5}})

    def test_rules_negative_coef_refused(self):
        with self.assertRaises(CollegeError):
            self.rules({"coefficients": {**DEFAULT_RULES["coefficients"], "lab": -1}})

    def test_rules_attempts_must_be_positive_int(self):
        for bad in (0, 1.5, True):
            with self.subTest(bad=bad), self.assertRaises(CollegeError):
                self.rules({"max_attempts": {"lab": bad}})
