"""Load the program files: sequence.json and the rules of course.json."""
import copy
import json
import math
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


def load_sequence(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        sequence = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise CollegeError(f"Sequence corrupted: {path} ({e}).") from None
    if not isinstance(sequence, list) or not all(isinstance(s, dict) and SEQUENCE_KEYS <= s.keys() for s in sequence):
        raise CollegeError(f"Sequence malformed: {path} (each step needs {', '.join(sorted(SEQUENCE_KEYS))}).")
    return sequence


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
