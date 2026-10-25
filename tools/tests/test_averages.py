import copy
import unittest

from tools.scholarship import averages as a
from tools.scholarship import work as w
from tools.tests.helpers import D0, SEQUENCE, WithState, graded


class TestAverages(WithState):
    def test_module_average_empty(self):
        self.assertIsNone(a.module_average(self.state, "M1"))

    def test_module_average_weighted(self):
        graded(self.state, self.rules, "LAB1.1", "lab", "M1", 14)
        graded(self.state, self.rules, "HW1.1", "homework", "M1", 8)
        w.add_work(self.state, "RD1.1", "reading", "M1", "R", "a", D0, self.rules, hours=1)
        self.assertEqual(a.module_average(self.state, "M1"), 12.0)

    def test_module_average_ignores_other_modules_and_ungraded(self):
        graded(self.state, self.rules, "LAB1.1", "lab", "M1", 14)
        graded(self.state, self.rules, "LAB2.1", "lab", "M2", 4)
        w.add_work(self.state, "LAB1.2", "lab", "M1", "T", "a", D0, self.rules, hours=1)
        self.assertEqual(a.module_average(self.state, "M1"), 14.0)

    def test_module_average_resit_max(self):
        graded(self.state, self.rules, "LAB1.1", "lab", "M1", 8)
        graded(self.state, self.rules, "RESIT-M1", "resit", "M1", 11)
        self.assertEqual(a.module_average(self.state, "M1"), 11)

    def test_module_average_lower_resit(self):
        graded(self.state, self.rules, "LAB1.1", "lab", "M1", 8)
        graded(self.state, self.rules, "RESIT-M1", "resit", "M1", 6)
        self.assertEqual(a.module_average(self.state, "M1"), 8)

    def test_semester_average_provisional(self):
        graded(self.state, self.rules, "LAB1.1", "lab", "M1", 15)
        self.assertEqual(a.semester_average(self.state, SEQUENCE, "S1", self.rules), (15.0, True))

    def test_semester_average_with_exams(self):
        graded(self.state, self.rules, "LAB1.1", "lab", "M1", 15)
        graded(self.state, self.rules, "EXAM-WRITTEN-S1", "written-exam", "S1", 10)
        graded(self.state, self.rules, "EXAM-ORAL-S1", "oral-exam", "S1", 14)
        average, provisional = a.semester_average(self.state, SEQUENCE, "S1", self.rules)
        self.assertAlmostEqual(average, 13.8)
        self.assertFalse(provisional)

    def test_semester_average_excludes_mock_oral(self):
        graded(self.state, self.rules, "LAB1.1", "lab", "M1", 15)
        graded(self.state, self.rules, "MOCK-20261020", "mock-oral", "S1", 2)
        self.assertEqual(a.semester_average(self.state, SEQUENCE, "S1", self.rules), (15.0, True))

    def test_semester_average_empty(self):
        self.assertEqual(a.semester_average(self.state, SEQUENCE, "S1", self.rules), (None, True))

    def test_semester_average_uses_rule_weights(self):
        rules = copy.deepcopy(self.rules)
        rules["weights"] = {"modules": 0.5, "exams": 0.5}
        graded(self.state, rules, "LAB1.1", "lab", "M1", 10)
        graded(self.state, rules, "EXAM-WRITTEN-S1", "written-exam", "S1", 20)
        graded(self.state, rules, "EXAM-ORAL-S1", "oral-exam", "S1", 20)
        self.assertEqual(a.semester_average(self.state, SEQUENCE, "S1", rules), (15.0, False))

    def test_module_complete(self):
        self.assertFalse(a.module_complete(self.state, SEQUENCE, "M1"))
        w.step_done(self.state, "L1.01")
        w.step_done(self.state, "L1.02")
        w.add_work(self.state, "LAB1.1", "lab", "M1", "T", "a", D0, self.rules, hours=1)
        w.submit(self.state, "LAB1.1", "work/LAB1.1", D0, self.rules)
        self.assertFalse(a.module_complete(self.state, SEQUENCE, "M1"))
        w.grade(self.state, "LAB1.1", {"A": [10, 20]}, "f.md")
        self.assertTrue(a.module_complete(self.state, SEQUENCE, "M1"))

    def test_module_complete_ignores_readings(self):
        w.step_done(self.state, "L1.01")
        w.step_done(self.state, "L1.02")
        w.add_work(self.state, "RD1.1", "reading", "M1", "R", "a", D0, self.rules, hours=1)
        self.assertTrue(a.module_complete(self.state, SEQUENCE, "M1"))


class TestModuleCompleteUnsubmittedHomework(WithState):
    def test_never_submitted_homework_does_not_block_completion(self):
        w.step_done(self.state, "L1.01")
        w.step_done(self.state, "L1.02")
        graded(self.state, self.rules, "LAB1.1", "lab", "M1", 8)
        w.add_work(self.state, "HW1.1", "homework", "M1", "D", "a", D0, self.rules, hours=1)
        self.assertTrue(a.module_complete(self.state, SEQUENCE, "M1"))

    def test_unsubmitted_lab_blocks_completion(self):
        w.step_done(self.state, "L1.01")
        w.step_done(self.state, "L1.02")
        w.add_work(self.state, "LAB1.1", "lab", "M1", "T", "a", D0, self.rules, hours=1)
        self.assertFalse(a.module_complete(self.state, SEQUENCE, "M1"))


class TestProvisionalSemester(WithState):
    def test_single_graded_exam_stays_provisional(self):
        graded(self.state, self.rules, "LAB1.1", "lab", "M1", 15)
        graded(self.state, self.rules, "EXAM-WRITTEN-S1", "written-exam", "S1", 10)
        average, provisional = a.semester_average(self.state, SEQUENCE, "S1", self.rules)
        self.assertAlmostEqual(average, 0.6 * 15 + 0.4 * 10)
        self.assertTrue(provisional)
