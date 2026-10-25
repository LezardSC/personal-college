import tempfile
import unittest
from datetime import date
from pathlib import Path

from tools.scholarship import state as m_state
from tools.scholarship.program import DEFAULT_RULES

D0 = date(2026, 10, 25)


class WithState(unittest.TestCase):
    """Provides a fresh state in a temporary directory."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.path = self.root / "state" / "state.json"
        self.state = m_state.init(self.path, D0)
        self.rules = DEFAULT_RULES

    def tearDown(self):
        self._tmp.cleanup()


SEQUENCE = [
    {"id": "L1.01", "type": "lesson", "module": "M1", "semester": "S1", "title": "Complexity"},
    {"id": "L1.02", "type": "lesson", "module": "M1", "semester": "S1", "title": "Deep modules"},
    {"id": "L2.01", "type": "lesson", "module": "M2", "semester": "S1", "title": "Testing"},
    {"id": "EXAM-WRITTEN-S1", "type": "written-exam", "module": "S1", "semester": "S1", "title": "Written exam S1"},
    {"id": "EXAM-ORAL-S1", "type": "oral-exam", "module": "S1", "semester": "S1", "title": "Oral exam S1"},
]


def graded(state, rules, id, type, module, value, today=D0, **kw):
    """Add a work item, submit it and grade it `value`/20."""
    from tools.scholarship import work  # created by a later task; imported lazily
    work.add_work(state, id, type, module, id, f"assignments/{module}/{id}/assignment.md", today, rules,
                  hours=2, **kw)
    work.submit(state, id, f"work/{id}", today, rules)
    work.grade(state, id, {"All": [value, 20]}, f"feedback/{id}-v1.md")
