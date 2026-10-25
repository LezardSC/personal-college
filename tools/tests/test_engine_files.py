import json
import re
import unittest
from pathlib import Path

from tools.scholarship.program import DEFAULT_RULES

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN = [re.compile(r) for r in (
    r"(?<![\w/.])/cours\b", r"(?<![\w/.])/rendu\b", r"(?<![\w/.])/question\b",
    r"\bcursus\b", r"\bgénie\b", r"refactoring\.guru", r"\bscol\.py\b",
    r"\boutils/", r"\betudiant/", r"\.enseignants",
)]
FORBIDDEN_CASE_SENSITIVE = re.compile(r"\bUE\d+\b")


def forbidden_hits(text: str) -> list[str]:
    text_l = text.lower()
    hits = [p.pattern for p in FORBIDDEN if p.search(text_l)]
    if FORBIDDEN_CASE_SENSITIVE.search(text):
        hits.append(FORBIDDEN_CASE_SENSITIVE.pattern)
    return hits


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

    def test_skills_use_configurable_subagent_model(self):
        for skill in sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md")):
            text = skill.read_text(encoding="utf-8")
            self.assertNotRegex(text, r'model:\s*"sonnet"', f"{skill.parent.name} hard-codes the model")
            if re.search(r"(?i)launch|subagent|`(?:professor|designer|grader)` agent", text):
                self.assertIn("Subagent model", text, skill.parent.name)

    def test_skills_have_frontmatter(self):
        skills = sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md"))
        self.assertEqual({s.parent.name for s in skills}, {"lesson", "submit", "ask", "oral", "enroll"})
        for skill in skills:
            text = skill.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---"), f"{skill} must start with '---' (frontmatter)")
            front = text.split("---")[1]
            self.assertRegex(front, rf"(?m)^name:\s*{re.escape(skill.parent.name)}\s*$", str(skill))
            self.assertRegex(front, r"(?m)^description:\s*\S", str(skill))

    def test_no_subject_obligations(self):
        for path in engine_files():
            text = path.read_text(encoding="utf-8", errors="ignore")
            self.assertEqual(forbidden_hits(text), [], str(path.relative_to(ROOT)))

    def test_matcher_is_token_based(self):
        for ok in ("templates/course.md", "value1 queue1", "see /course", "the course"):
            self.assertEqual(forbidden_hits(ok), [], ok)
        for bad in ("run /cours now", "UE1", "scol.py", "/rendu x"):
            self.assertNotEqual(forbidden_hits(bad), [], bad)


if __name__ == "__main__":
    unittest.main()
