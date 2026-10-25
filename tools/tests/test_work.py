import copy

from tools.scholarship import state as m_state
from tools.scholarship import work
from tools.scholarship.state import CollegeError
from tools.tests.helpers import D0, WithState, graded

CRITERIA_14 = {"Design": [5, 6], "ADR": [3, 4], "Tests": [3, 4], "Clarity": [2, 3], "Course": [1, 3]}


def criteria(value):
    """Rubric out of 20 whose obtained points sum to `value`."""
    return {"All": [value, 20]}


class TestWork(WithState):
    def add(self, id="LAB1.1", type="lab", **kw):
        kw.setdefault("hours", 4)
        return work.add_work(self.state, id, type, "M1", "Title", f"assignments/M1/{id}/assignment.md",
                             D0, self.rules, **kw)

    def submit(self, id="LAB1.1"):
        return work.submit(self.state, id, f"work/{id}", D0, self.rules)

    def test_constants(self):
        self.assertEqual((work.SCALE_TOTAL, work.PASS_MARK), (20, 10))

    def test_add_defaults(self):
        lab = self.add()
        self.assertEqual((lab["blocking"], lab["coef"], lab["status"]), (True, 2, "todo"))
        self.assertEqual(lab["hours"], 4)
        self.assertEqual(lab["created_on"], D0.isoformat())
        self.assertNotIn("due", lab)
        self.assertFalse([k for k in lab if "due" in k])
        reading = self.add("RD1.1", "reading")
        self.assertEqual((reading["blocking"], reading["coef"]), (False, 0))

    def test_add_override_defaults(self):
        hw = self.add("HW1.1", "homework", blocking=True, coef=3)
        self.assertEqual((hw["blocking"], hw["coef"]), (True, 3))

    def test_add_duplicate_id(self):
        self.add()
        with self.assertRaises(CollegeError) as cm:
            self.add()
        self.assertIn("LAB1.1", str(cm.exception))

    def test_unknown_type(self):
        with self.assertRaises(CollegeError):
            self.add(type="quiz")

    def test_absurd_hours_refused(self):
        for hours in (float("nan"), float("inf"), 0, -2):
            with self.subTest(hours=hours), self.assertRaises(CollegeError):
                self.add(f"LAB{hours}", hours=hours)

    def test_negative_coef_refused(self):
        with self.assertRaises(CollegeError):
            self.add(coef=-1)

    def test_validated_by_refused_outside_reading(self):
        with self.assertRaises(CollegeError):
            self.add("HW1.1", "homework", validated_by="X")

    def test_submit_unknown_id(self):
        with self.assertRaises(CollegeError) as cm:
            work.submit(self.state, "XX9.9", "work/XX9.9", D0, self.rules)
        self.assertIn("XX9.9", str(cm.exception))

    def test_submit_attempt_number(self):
        self.add()
        self.assertEqual(self.submit(), 1)
        self.assertEqual(self.state["work"]["LAB1.1"]["status"], "submitted")

    def test_submit_refuses_third_attempt(self):
        self.add()
        for _ in range(2):
            self.submit()
            work.grade(self.state, "LAB1.1", criteria(10), "f.md")
        with self.assertRaises(CollegeError) as cm:
            self.submit()
        self.assertIn("2 attempts", str(cm.exception))

    def test_submit_refused_while_being_graded(self):
        self.add()
        self.submit()
        with self.assertRaises(CollegeError):
            self.submit()

    def test_exam_single_attempt(self):
        self.add("EXAM-WRITTEN-S1", "written-exam")
        self.submit("EXAM-WRITTEN-S1")
        work.grade(self.state, "EXAM-WRITTEN-S1", criteria(12), "f.md")
        with self.assertRaises(CollegeError) as cm:
            self.submit("EXAM-WRITTEN-S1")
        self.assertIn("1 attempt", str(cm.exception))
        self.assertNotIn("1 attempts", str(cm.exception))

    def test_submit_reading_refused(self):
        self.add("RD1.1", "reading")
        with self.assertRaises(CollegeError):
            work.submit(self.state, "RD1.1", "x", D0, self.rules)

    def test_grade_valid_rubric(self):
        self.add()
        self.submit()
        self.assertEqual(work.grade(self.state, "LAB1.1", CRITERIA_14, "feedback/LAB1.1-v1.md"), 14)
        lab = self.state["work"]["LAB1.1"]
        self.assertEqual(lab["status"], "graded")
        self.assertEqual(lab["attempts"][0]["feedback"], "feedback/LAB1.1-v1.md")
        self.assertEqual(lab["attempts"][0]["grade"], 14)

    def test_grade_refuses_total_not_20(self):
        self.add()
        self.submit()
        for bad in ({"A": [10, 19]}, {"A": [11, 10], "B": [5, 10]}, {"A": [-1, 20]}):
            with self.subTest(criteria=bad), self.assertRaises(CollegeError):
                work.grade(self.state, "LAB1.1", bad, "f.md")

    def test_grade_best_attempt(self):
        self.add()
        for value in (12, 9):
            self.submit()
            work.grade(self.state, "LAB1.1", criteria(value), "f.md")
        self.assertEqual(work.best_grade(self.state["work"]["LAB1.1"]), 12)

    def test_best_grade_without_grade(self):
        self.assertIsNone(work.best_grade(self.add()))

    def test_grade_without_submission(self):
        self.add()
        with self.assertRaises(CollegeError):
            work.grade(self.state, "LAB1.1", criteria(10), "f.md")

    def test_grade_malformed_criteria(self):
        self.add()
        self.submit()
        for bad in ([1, 2], {"a": 5, "b": 15}, {"a": [5, "x"]}, {"a": [5]}, {}, {"a": [True, 20]}):
            with self.subTest(criteria=bad), self.assertRaises(CollegeError):
                work.grade(self.state, "LAB1.1", bad, "f.md")
        self.assertEqual(self.state["work"]["LAB1.1"]["status"], "submitted")

    def test_finish_reading(self):
        self.add("RD1.1", "reading")
        work.finish(self.state, "RD1.1")
        self.assertEqual(self.state["work"]["RD1.1"]["status"], "done")

    def test_finish_refuses_non_reading(self):
        self.add()
        with self.assertRaises(CollegeError):
            work.finish(self.state, "LAB1.1")

    def test_step_done_idempotent(self):
        work.step_done(self.state, "L1.01")
        work.step_done(self.state, "L1.01")
        self.assertEqual(self.state["steps_done"], ["L1.01"])

    def test_custom_rules_change_defaults(self):
        rules = copy.deepcopy(self.rules)
        rules["coefficients"]["lab"] = 3
        rules["blocking"] = []
        lab = work.add_work(self.state, "LAB1.1", "lab", "M1", "T", "a.md", D0, rules, hours=2)
        self.assertEqual((lab["coef"], lab["blocking"]), (3, False))

    def test_custom_max_attempts(self):
        rules = copy.deepcopy(self.rules)
        rules["max_attempts"]["homework"] = 3
        work.add_work(self.state, "HW1.1", "homework", "M1", "T", "a.md", D0, rules, hours=2)
        for n in (1, 2, 3):
            self.assertEqual(work.submit(self.state, "HW1.1", "w", D0, rules), n)
            work.grade(self.state, "HW1.1", criteria(10), "f.md")
        with self.assertRaises(CollegeError):
            work.submit(self.state, "HW1.1", "w", D0, rules)

    def test_graded_helper(self):
        graded(self.state, self.rules, "HW1.1", "homework", "M1", 15)
        self.assertEqual(work.best_grade(self.state["work"]["HW1.1"]), 15)


class TestReadingValidatedByWork(WithState):
    def setUp(self):
        super().setUp()
        work.add_work(self.state, "RD1.1", "reading", "M1", "Reading", "c.md", D0, self.rules,
                      hours=1, validated_by="HW1.1")
        work.add_work(self.state, "HW1.1", "homework", "M1", "Homework", "s.md", D0, self.rules, hours=2)
        work.submit(self.state, "HW1.1", "work/HW1.1", D0, self.rules)

    def test_passing_grade_validates_reading(self):
        work.grade(self.state, "HW1.1", criteria(10), "f.md")
        self.assertEqual(self.state["work"]["RD1.1"]["status"], "done")

    def test_failing_grade_does_not_validate(self):
        work.grade(self.state, "HW1.1", criteria(9), "f.md")
        self.assertEqual(self.state["work"]["RD1.1"]["status"], "todo")

    def test_link_validates_if_already_passed(self):
        work.grade(self.state, "HW1.1", criteria(12), "f.md")
        work.add_work(self.state, "RD1.2", "reading", "M1", "R2", "c.md", D0, self.rules, hours=1)
        work.link(self.state, "RD1.2", "HW1.1")
        self.assertEqual(self.state["work"]["RD1.2"]["status"], "done")
