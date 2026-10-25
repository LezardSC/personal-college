import json
import re
import unittest
from pathlib import Path

from tools.scholarship.program import DEFAULT_RULES

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN = [
    "refactoring.guru", "scol.py", "outils/", "etudiant/", ".enseignants",
    "UE1", "génie", "cursus", "/cours", "/rendu", "/question",
]


def engine_files():
    files = [ROOT / "CLAUDE.md", ROOT / "README.md"]
    files += [p for p in (ROOT / ".claude").rglob("*") if p.is_file()]
    files += [p for p in (ROOT / "tools").rglob("*.py") if p != Path(__file__).resolve()]
    return [p for p in files if p.exists()]


class TestEngineFiles(unittest.TestCase):
    def test_templates_rules_equal_defaults(self):
        data = json.loads((ROOT / "templates" / "rules.json").read_text(encoding="utf-8"))
        self.assertEqual(data, DEFAULT_RULES)

    def test_claude_md_imports_course_files(self):
        lines = [l.strip() for l in (ROOT / "CLAUDE.md").read_text(encoding="utf-8").splitlines() if l.strip()]
        self.assertEqual(lines[:2], ["@course.md", "@profile.md"])

    def test_agents_run_on_sonnet(self):
        agents = sorted((ROOT / ".claude" / "agents").glob("*.md"))
        self.assertEqual({a.name for a in agents}, {"professor.md", "designer.md", "grader.md"})
        for agent in agents:
            text = agent.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---"), f"{agent.name} must start with '---' (frontmatter)")
            front = text.split("---")[1]
            self.assertRegex(front, r"(?m)^model:\s*sonnet\s*$", agent.name)

    def test_skills_have_frontmatter(self):
        for skill in (ROOT / ".claude" / "skills").glob("*/SKILL.md"):
            front = skill.read_text(encoding="utf-8").split("---")[1]
            self.assertRegex(front, rf"(?m)^name:\s*{re.escape(skill.parent.name)}\s*$", str(skill))
            self.assertRegex(front, r"(?m)^description:\s*\S", str(skill))

    def test_no_subject_obligations(self):
        for path in engine_files():
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for term in FORBIDDEN:
                self.assertNotIn(term.lower(), text, f"{path.relative_to(ROOT)} contains '{term}'")


if __name__ == "__main__":
    unittest.main()
