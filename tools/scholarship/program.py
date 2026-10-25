"""Load the program files: program/sequence.json and program/rules.json."""
import copy
import json
import math
import re
from pathlib import Path

from tools.scholarship.state import CollegeError

TYPES = ("reading", "homework", "lab", "written-exam", "oral-exam", "mock-oral", "resit")
EXAMS = ("written-exam", "oral-exam")
DEFAULT_RULES: dict = {
    "blocking": ["lab", "written-exam", "oral-exam", "resit"],
    "coefficients": {"lab": 2, "homework": 1, "written-exam": 1, "oral-exam": 1, "resit": 1, "reading": 0, "mock-oral": 0},
    "max_attempts": {"lab": 2, "homework": 2},
    "weights": {"modules": 0.6, "exams": 0.4},
}
SEQUENCE_KEYS = {"id", "type", "module", "semester", "title"}
STEP_TYPES = ("lesson", "written-exam", "oral-exam")
SEMESTER_RE = re.compile(r"S(\d+)")
MODULE_RE = re.compile(r"M\d+")
LESSON_ID_RE = re.compile(r"L\d+\.\d+")
EXAM_ID_RE = re.compile(r"EXAM-(WRITTEN|ORAL)-S(\d+)")


def load_sequence(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        sequence = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise CollegeError(f"Sequence corrupted: {path} ({e}).") from None
    if not isinstance(sequence, list) or not all(isinstance(s, dict) and SEQUENCE_KEYS <= s.keys() for s in sequence):
        raise CollegeError(f"Sequence malformed: {path} (each step needs {', '.join(sorted(SEQUENCE_KEYS))}).")
    _validate_sequence(sequence, path)
    return sequence


def _validate_sequence(sequence: list[dict], path: Path) -> None:
    seen = set()
    for step in sequence:
        sid = step["id"]

        def bad(problem: str) -> CollegeError:
            return CollegeError(f"Sequence {path}: step \"{sid}\": {problem}.")

        if not all(isinstance(step[k], str) for k in SEQUENCE_KEYS):
            raise bad("every field must be a string")
        if sid in seen:
            raise bad("duplicate id")
        seen.add(sid)
        if step["type"] not in STEP_TYPES:
            raise bad(f"unknown type \"{step['type']}\" (known: {', '.join(STEP_TYPES)})")
        sem = SEMESTER_RE.fullmatch(step["semester"])
        if not sem:
            raise bad(f"semester \"{step['semester']}\" must look like S1")
        if step["type"] == "lesson":
            if not MODULE_RE.fullmatch(step["module"]):
                raise bad(f"module \"{step['module']}\" must look like M1")
            if not LESSON_ID_RE.fullmatch(sid):
                raise bad("a lesson id must look like L1.01")
        else:
            if step["module"] != step["semester"]:
                raise bad("an exam's module must equal its semester")
            exam = EXAM_ID_RE.fullmatch(sid)
            kind = "WRITTEN" if step["type"] == "written-exam" else "ORAL"
            if not exam or exam.group(1) != kind or exam.group(2) != sem.group(1):
                raise bad(f"an exam id must look like EXAM-{kind}-{step['semester']}")


def _number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _check_types(names, where: str, path: Path) -> None:
    for name in names:
        if name not in TYPES:
            raise CollegeError(f"Rules {path}: unknown type \"{name}\" in {where} (known: {', '.join(TYPES)}).")


def _validate(rules: dict, path: Path) -> None:
    blocking = rules["blocking"]
    if not isinstance(blocking, list):
        raise CollegeError(f"Rules {path}: \"blocking\" must be a list of types.")
    _check_types(blocking, "blocking", path)
    if len(set(blocking)) != len(blocking):
        raise CollegeError(f"Rules {path}: \"blocking\" lists a type twice.")

    coefs = rules["coefficients"]
    if not isinstance(coefs, dict):
        raise CollegeError(f"Rules {path}: \"coefficients\" must be an object.")
    _check_types(coefs, "coefficients", path)
    for name in TYPES:
        if name not in coefs:
            raise CollegeError(f"Rules {path}: \"coefficients\" is missing type \"{name}\".")
    for name, value in coefs.items():
        if not _number(value) or value < 0:
            raise CollegeError(f"Rules {path}: coefficient of \"{name}\" must be a finite number >= 0.")

    attempts = rules["max_attempts"]
    if not isinstance(attempts, dict):
        raise CollegeError(f"Rules {path}: \"max_attempts\" must be an object.")
    _check_types(attempts, "max_attempts", path)
    for name, value in attempts.items():
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise CollegeError(f"Rules {path}: max attempts of \"{name}\" must be an integer >= 1.")

    weights = rules["weights"]
    if not isinstance(weights, dict) or set(weights) != {"modules", "exams"} \
            or not all(_number(v) and v >= 0 for v in weights.values()):
        raise CollegeError(f"Rules {path}: \"weights\" needs finite \"modules\" and \"exams\" numbers >= 0.")
    if abs(weights["modules"] + weights["exams"] - 1) >= 1e-9:
        raise CollegeError(f"Rules {path}: weights must sum to 1.")


def load_rules(path: Path) -> dict:
    """Default rules, overridden key by key by the file's top-level keys."""
    rules = copy.deepcopy(DEFAULT_RULES)
    if path.exists():
        try:
            given = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise CollegeError(f"Rules corrupted: {path} ({e}).") from None
        if not isinstance(given, dict):
            raise CollegeError(f"Rules malformed: {path} (a JSON object is expected).")
        for key in given:
            if key not in DEFAULT_RULES:
                raise CollegeError(f"Rules {path}: unknown key \"{key}\" (allowed: {', '.join(DEFAULT_RULES)}).")
        rules.update(copy.deepcopy(given))
    _validate(rules, path)
    return rules
