from tools.scholarship import status as s
from tools.scholarship import work as w
from tools.tests.helpers import D0, SEQUENCE, WithState, graded, regraded


class TestStatus(WithState):
    def status(self):
        return s.status(self.state, SEQUENCE, self.rules)

    def test_initial_status(self):
        st = self.status()
        self.assertEqual(st["next_step"]["id"], "L1.01")
        self.assertTrue(st["can_advance"])
        self.assertFalse(st["course_complete"])

    def test_status_is_pure(self):
        before = repr(self.state)
        self.status()
        self.assertEqual(repr(self.state), before)

    def test_blocking_item(self):
        w.add_work(self.state, "LAB1.1", "lab", "M1", "T", "a", D0, self.rules, hours=2)
        st = self.status()
        self.assertEqual(st["blocking"], ["LAB1.1"])
        self.assertFalse(st["can_advance"])

    def test_submitted_no_longer_blocks(self):
        w.add_work(self.state, "LAB1.1", "lab", "M1", "T", "a", D0, self.rules, hours=2)
        w.submit(self.state, "LAB1.1", "work/LAB1.1", D0, self.rules)
        self.assertTrue(self.status()["can_advance"])

    def test_resit_required(self):
        w.step_done(self.state, "L1.01")
        w.step_done(self.state, "L1.02")
        graded(self.state, self.rules, "LAB1.1", "lab", "M1", 8)
        self.assertEqual(self.status()["resits_required"], [])  # a resubmission could still raise it
        regraded(self.state, self.rules, "LAB1.1", 8)
        st = self.status()
        self.assertEqual(st["resits_required"], ["M1"])
        self.assertFalse(st["can_advance"])
        w.add_work(self.state, "RESIT-M1", "resit", "M1", "R", "a", D0, self.rules, hours=2)
        st = self.status()
        self.assertEqual(st["resits_required"], [])
        self.assertEqual(st["blocking"], ["RESIT-M1"])

    def test_failed_resit_is_not_requested_again(self):
        w.step_done(self.state, "L1.01")
        w.step_done(self.state, "L1.02")
        graded(self.state, self.rules, "LAB1.1", "lab", "M1", 8)
        regraded(self.state, self.rules, "LAB1.1", 8)
        graded(self.state, self.rules, "RESIT-M1", "resit", "M1", 7)
        st = self.status()
        self.assertEqual(st["resits_required"], [])
        self.assertTrue(st["can_advance"])

    def test_next_exam(self):
        for step_id in ("L1.01", "L1.02", "L2.01"):
            w.step_done(self.state, step_id)
        self.assertEqual(self.status()["next_step"]["type"], "written-exam")

    def test_course_complete(self):
        for step in SEQUENCE:
            w.step_done(self.state, step["id"])
        st = self.status()
        self.assertIsNone(st["next_step"])
        self.assertTrue(st["course_complete"])

    def test_empty_sequence(self):
        st = s.status(self.state, [], self.rules)
        self.assertIsNone(st["next_step"])
        self.assertFalse(st["course_complete"])


class TestStatusExams(WithState):
    def test_being_graded(self):
        w.add_work(self.state, "LAB1.1", "lab", "M1", "T", "a", D0, self.rules, hours=2)
        w.submit(self.state, "LAB1.1", "work/LAB1.1", D0, self.rules)
        self.assertEqual(s.status(self.state, SEQUENCE, self.rules)["being_graded"], ["LAB1.1"])

    def test_exam_to_take(self):
        for step_id in ("L1.01", "L1.02", "L2.01"):
            w.step_done(self.state, step_id)
        self.assertEqual(s.status(self.state, SEQUENCE, self.rules)["exam_to_take"], "EXAM-WRITTEN-S1")

    def test_no_exam_during_lessons(self):
        self.assertIsNone(s.status(self.state, SEQUENCE, self.rules)["exam_to_take"])
