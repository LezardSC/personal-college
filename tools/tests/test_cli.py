import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


class TestCli(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def college(self, *args):
        env = dict(os.environ, COLLEGE_ROOT=str(self.dir))
        return subprocess.run([sys.executable, str(REPO / "tools" / "college.py"), *args],
                              capture_output=True, text=True, env=env)

    def add_lab(self, id="LAB1.1", *extra):
        return self.college("add-work", "--id", id, "--type", "lab", "--module", "M1", "--title", "First lab",
                            "--assignment", f"assignments/M1/{id}/assignment.md", "--hours", "4", *extra)

    def write_program(self, name, content):
        (self.dir / "program").mkdir(exist_ok=True)
        (self.dir / "program" / name).write_text(content)

    def test_cli_error_without_traceback(self):
        r = self.college("status")
        self.assertEqual(r.returncode, 2)
        self.assertIn("Error:", r.stderr)
        self.assertIn("init", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_cli_full_cycle(self):
        self.assertEqual(self.college("init").returncode, 0)
        r = self.add_lab()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(json.loads(self.college("status", "--json").stdout)["can_advance"])
        self.assertIn("attempt 1", self.college("submit", "LAB1.1", "--path", "work/LAB1.1").stdout)
        (self.dir / "feedback").mkdir()
        (self.dir / "feedback" / "LAB1.1-v1.md").write_text("# Feedback")
        r = self.college("grade", "LAB1.1", "--criteria", '{"A": [12, 15], "B": [3, 5]}',
                         "--feedback", "feedback/LAB1.1-v1.md")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("15", r.stdout)
        self.assertTrue(json.loads(self.college("status", "--json").stdout)["can_advance"])
        self.assertTrue((self.dir / "AGENDA.md").exists())
        self.assertIn("15", (self.dir / "student" / "transcript.md").read_text())

    def test_cli_business_error_code_2(self):
        self.college("init")
        r = self.college("submit", "XX9.9", "--path", "work/XX9.9")
        self.assertEqual(r.returncode, 2)
        self.assertIn("XX9.9", r.stderr)

    def test_cli_invalid_criteria_json(self):
        self.college("init")
        r = self.college("grade", "LAB1.1", "--criteria", "{not json", "--feedback", "f.md")
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)

    def test_cli_if_absent(self):
        self.college("init")
        args = ["add-work", "--id", "RD1.1", "--type", "reading", "--module", "M1", "--title", "R",
                "--assignment", "a", "--hours", "1", "--if-absent"]
        self.assertEqual(self.college(*args).returncode, 0)
        r = self.college(*args)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("already exists", r.stdout)

    def test_cli_grade_missing_feedback(self):
        self.college("init")
        self.add_lab()
        self.college("submit", "LAB1.1", "--path", "work/LAB1.1")
        r = self.college("grade", "LAB1.1", "--criteria", '{"A": [10, 20]}', "--feedback", "feedback/missing.md")
        self.assertEqual(r.returncode, 2)
        self.assertIn("missing.md", r.stderr)

    def test_cli_sequence_read(self):
        self.college("init")
        self.write_program("sequence.json", json.dumps(
            [{"id": "L1.01", "type": "lesson", "module": "M1", "semester": "S1", "title": "T"}]))
        st = json.loads(self.college("status", "--json").stdout)
        self.assertEqual(st["next_step"]["id"], "L1.01")
        self.college("step-done", "L1.01")
        self.assertTrue(json.loads(self.college("status", "--json").stdout)["course_complete"])

    def test_cli_malformed_sequence(self):
        self.college("init")
        self.write_program("sequence.json", '[{"id": "L1.01"}]')
        r = self.college("status")
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)

    def test_cli_status_text_exam(self):
        self.college("init")
        self.write_program("sequence.json", json.dumps(
            [{"id": "EXAM-WRITTEN-S1", "type": "written-exam", "module": "S1", "semester": "S1",
              "title": "Written exam S1"}]))
        self.assertIn("Exam to take: EXAM-WRITTEN-S1", self.college("status").stdout)

    def test_cli_averages_json(self):
        self.college("init")
        self.write_program("sequence.json", json.dumps(
            [{"id": "L1.01", "type": "lesson", "module": "M1", "semester": "S1", "title": "T"}]))
        r = self.college("averages", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertIn("M1", data["modules"])
        self.assertIn("S1", data["semesters"])

    def test_cli_broken_rules_never_mutate_state(self):
        self.college("init")
        self.add_lab()
        self.college("submit", "LAB1.1", "--path", "work/LAB1.1")
        (self.dir / "feedback").mkdir()
        (self.dir / "feedback" / "LAB1.1-v1.md").write_text("# Feedback")
        state_file = self.dir / "state" / "state.json"
        before = state_file.read_text()
        self.write_program("rules.json", json.dumps({"weights": {"modules": 0.6, "exams": 0.5}}))
        r = self.college("grade", "LAB1.1", "--criteria", '{"A": [12, 20]}', "--feedback", "feedback/LAB1.1-v1.md")
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("/20", r.stdout)
        self.assertEqual(state_file.read_text(), before)
        self.assertEqual(json.loads(before)["work"]["LAB1.1"]["status"], "submitted")

    def test_cli_init_with_broken_rules_writes_nothing(self):
        self.write_program("rules.json", "{")
        r = self.college("init")
        self.assertEqual(r.returncode, 2)
        self.assertFalse((self.dir / "state").exists())

    def test_cli_rules_file_applied(self):
        self.college("init")
        self.write_program("rules.json", json.dumps({"coefficients": {
            "lab": 3, "homework": 1, "written-exam": 1, "oral-exam": 1, "resit": 1, "reading": 0, "mock-oral": 0}}))
        self.assertEqual(self.add_lab().returncode, 0)
        state = json.loads((self.dir / "state" / "state.json").read_text())
        self.assertEqual(state["work"]["LAB1.1"]["coef"], 3)


if __name__ == "__main__":
    unittest.main()
