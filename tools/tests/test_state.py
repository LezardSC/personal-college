import json
from datetime import date
from unittest import mock

from tools.scholarship import state as m_state
from tools.scholarship.state import VERSION, CollegeError
from tools.tests.helpers import WithState


class TestState(WithState):
    def test_init_idempotent(self):
        before = self.path.read_text()
        m_state.init(self.path, date(2027, 1, 1))
        self.assertEqual(self.path.read_text(), before)
        self.assertEqual(m_state.load(self.path)["enrolled_on"], "2026-10-25")

    def test_save_then_load(self):
        self.state["steps_done"].append("L1.01")
        m_state.save(self.state, self.path)
        self.assertEqual(m_state.load(self.path)["steps_done"], ["L1.01"])

    def test_save_failure_leaves_no_temp(self):
        with self.assertRaises(TypeError):
            m_state.save({"x": object()}, self.path)
        self.assertEqual([p.name for p in self.path.parent.iterdir()], ["state.json"])

    def test_load_missing_message(self):
        with self.assertRaises(CollegeError) as cm:
            m_state.load(self.root / "nope.json")
        self.assertIn("college.py init", str(cm.exception))

    def test_load_corrupt_message(self):
        self.path.write_text("{")
        with self.assertRaises(CollegeError) as cm:
            m_state.load(self.path)
        self.assertIn("corrupted", str(cm.exception))
        self.assertIn("git checkout -- state/state.json", str(cm.exception))

    def test_load_malformed_state(self):
        for content in ("{}", "[]", '{"version": 1, "work": {}}'):
            self.path.write_text(content)
            with self.subTest(content=content), self.assertRaises(CollegeError) as cm:
                m_state.load(self.path)
            self.assertIn("corrupted", str(cm.exception))

    def test_corruption_message_does_not_promise_git(self):
        # The message must say "last commit" (restore from what exists), not claim a commit is guaranteed.
        self.path.write_text("{")
        with self.assertRaises(CollegeError) as cm:
            m_state.load(self.path)
        self.assertIn("last commit", str(cm.exception))


class TestMigrations(WithState):
    def test_newer_version_refused(self):
        self.path.write_text(json.dumps({**self.state, "version": VERSION + 1}))
        with self.assertRaises(CollegeError) as cm:
            m_state.load(self.path)
        self.assertIn("git pull engine main", str(cm.exception))

    def test_older_version_migrated_and_saved(self):
        with mock.patch.object(m_state, "VERSION", 2), \
                mock.patch.object(m_state, "MIGRATIONS", {1: lambda s: {**s, "extra": True}}):
            loaded = m_state.load(self.path)
        self.assertIs(loaded["extra"], True)
        self.assertEqual(loaded["version"], 2)
        self.assertEqual(json.loads(self.path.read_text())["version"], 2)
