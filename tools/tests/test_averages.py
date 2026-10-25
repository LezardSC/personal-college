import copy
import unittest

from tools.scholarship import averages as a
from tools.scholarship import work as w
from tools.tests.helpers import D0, SEQUENCE, WithState, graded, regraded


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
        self.assertFalse(a.module_complete(self.state, SEQUENCE, "M1", self.rules))
        w.step_done(self.state, "L1.01")
        w.step_done(self.state, "L1.02")
        w.add_work(self.state, "LAB1.1", "lab", "M1", "T", "a", D0, self.rules, hours=1)
        w.submit(self.state, "LAB1.1", "work/LAB1.1", D0, self.rules)
        self.assertFalse(a.module_complete(self.state, SEQUENCE, "M1", self.rules))
        w.grade(self.state, "LAB1.1", {"A": [10, 20]}, "f.md")
        self.assertTrue(a.module_complete(self.state, SEQUENCE, "M1", self.rules))

    def test_module_complete_ignores_readings(self):
        w.step_done(self.state, "L1.01")
        w.step_done(self.state, "L1.02")
        w.add_work(self.state, "RD1.1", "reading", "M1", "R", "a", D0, self.rules, hours=1)
        self.assertTrue(a.module_complete(self.state, SEQUENCE, "M1", self.rules))


class TestModuleCompleteUnsubmittedHomework(WithState):
    def test_never_submitted_homework_does_not_block_completion(self):
        w.step_done(self.state, "L1.01")
        w.step_done(self.state, "L1.02")
        graded(self.state, self.rules, "LAB1.1", "lab", "M1", 8)
        regraded(self.state, self.rules, "LAB1.1", 8)
        w.add_work(self.state, "HW1.1", "homework", "M1", "D", "a", D0, self.rules, hours=1)
        self.assertTrue(a.module_complete(self.state, SEQUENCE, "M1", self.rules))

    def test_unsubmitted_lab_blocks_completion(self):
        w.step_done(self.state, "L1.01")
        w.step_done(self.state, "L1.02")
        w.add_work(self.state, "LAB1.1", "lab", "M1", "T", "a", D0, self.rules, hours=1)
        self.assertFalse(a.module_complete(self.state, SEQUENCE, "M1", self.rules))


class TestModuleCompleteResubmission(WithState):
    def setUp(self):
        super().setUp()
        w.step_done(self.state, "L1.01")
        w.step_done(self.state, "L1.02")

    def test_failed_item_with_attempts_left_keeps_module_open(self):
        graded(self.state, self.rules, "LAB1.1", "lab", "M1", 6)
        self.assertFalse(a.module_complete(self.state, SEQUENCE, "M1", self.rules))

    def test_failed_item_with_no_attempt_left_closes_module(self):
        graded(self.state, self.rules, "LAB1.1", "lab", "M1", 6)
        regraded(self.state, self.rules, "LAB1.1", 7)
        self.assertTrue(a.module_complete(self.state, SEQUENCE, "M1", self.rules))

    def test_passed_item_closes_module(self):
        graded(self.state, self.rules, "LAB1.1", "lab", "M1", 12)
        self.assertTrue(a.module_complete(self.state, SEQUENCE, "M1", self.rules))


class TestProvisionalSemester(WithState):
    def test_single_graded_exam_stays_provisional(self):
        graded(self.state, self.rules, "LAB1.1", "lab", "M1", 15)
        graded(self.state, self.rules, "EXAM-WRITTEN-S1", "written-exam", "S1", 10)
        average, provisional = a.semester_average(self.state, SEQUENCE, "S1", self.rules)
        self.assertAlmostEqual(average, 0.6 * 15 + 0.4 * 10)
        self.assertTrue(provisional)


class TestExamCoefficients(WithState):
    def rules_with(self, **coefs):
        rules = copy.deepcopy(self.rules)
        rules["coefficients"].update(coefs)
        return rules

    def test_exam_coefficients_weight_the_exam_part(self):
        rules = self.rules_with(**{"written-exam": 3, "oral-exam": 1})
        graded(self.state, rules, "LAB1.1", "lab", "M1", 10)
        graded(self.state, rules, "EXAM-WRITTEN-S1", "written-exam", "S1", 20)
        graded(self.state, rules, "EXAM-ORAL-S1", "oral-exam", "S1", 0)
        average, provisional = a.semester_average(self.state, SEQUENCE, "S1", rules)
        self.assertAlmostEqual(average, 0.6 * 10 + 0.4 * 15)
        self.assertFalse(provisional)

    def test_mock_oral_with_coef_counts(self):
        rules = self.rules_with(**{"mock-oral": 1})
        graded(self.state, rules, "LAB1.1", "lab", "M1", 10)
        graded(self.state, rules, "EXAM-WRITTEN-S1", "written-exam", "S1", 10)
        graded(self.state, rules, "EXAM-ORAL-S1", "oral-exam", "S1", 10)
        graded(self.state, rules, "MOCK-ORAL-20261020", "mock-oral", "S1", 20)
        average, provisional = a.semester_average(self.state, SEQUENCE, "S1", rules)
        self.assertAlmostEqual(average, 0.6 * 10 + 0.4 * (40 / 3))
        self.assertFalse(provisional)

    def test_mock_oral_with_zero_coef_is_ignored(self):
        graded(self.state, self.rules, "LAB1.1", "lab", "M1", 10)
        graded(self.state, self.rules, "EXAM-WRITTEN-S1", "written-exam", "S1", 10)
        graded(self.state, self.rules, "EXAM-ORAL-S1", "oral-exam", "S1", 10)
        graded(self.state, self.rules, "MOCK-ORAL-20261020", "mock-oral", "S1", 20)
        self.assertAlmostEqual(a.semester_average(self.state, SEQUENCE, "S1", self.rules)[0], 10.0)

    def test_mock_oral_alone_does_not_make_exams_complete(self):
        rules = self.rules_with(**{"mock-oral": 1})
        graded(self.state, rules, "LAB1.1", "lab", "M1", 10)
        graded(self.state, rules, "MOCK-ORAL-20261020", "mock-oral", "S1", 20)
        self.assertTrue(a.semester_average(self.state, SEQUENCE, "S1", rules)[1])

    def test_zero_total_weight_means_no_exam_part(self):
        rules = self.rules_with(**{"written-exam": 0})
        graded(self.state, rules, "LAB1.1", "lab", "M1", 15)
        graded(self.state, rules, "EXAM-WRITTEN-S1", "written-exam", "S1", 2)
        self.assertEqual(a.semester_average(self.state, SEQUENCE, "S1", rules), (15.0, True))
