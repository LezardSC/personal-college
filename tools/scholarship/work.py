"""Work-item lifecycle: add, submit, grade, finish."""
import math
from datetime import date

from tools.scholarship.program import TYPES
from tools.scholarship.state import CollegeError

SCALE_TOTAL = 20
PASS_MARK = 10


def _item(state: dict, id: str) -> dict:
    try:
        return state["work"][id]
    except KeyError:
        raise CollegeError(f"Unknown work item: {id}. Check the agenda.") from None


def add_work(state: dict, id: str, type: str, module: str, title: str, assignment: str, today: date,
             rules: dict, *, hours: float, blocking: bool | None = None, coef: float | None = None,
             validated_by: str | None = None) -> dict:
    if type not in TYPES:
        raise CollegeError(f"Unknown type: {type}. Possible types: {', '.join(TYPES)}.")
    if id in state["work"]:
        raise CollegeError(f"Work item {id} already exists.")
    if not (isinstance(hours, (int, float)) and not isinstance(hours, bool)
            and math.isfinite(hours) and hours > 0):
        raise CollegeError(f"{id}: invalid hours: {hours} (a strictly positive number is expected).")
    if coef is not None and not (math.isfinite(coef) and coef >= 0):
        raise CollegeError(f"{id}: invalid coefficient: {coef} (zero or positive expected).")
    if validated_by is not None and type != "reading":
        raise CollegeError(f"{id}: validated_by only applies to readings.")
    item = {
        "id": id, "type": type, "module": module, "title": title, "assignment": assignment,
        "created_on": today.isoformat(), "hours": hours,
        "blocking": type in rules["blocking"] if blocking is None else blocking,
        "coef": rules["coefficients"][type] if coef is None else coef,
        "status": "todo", "attempts": [],
    }
    if validated_by is not None:
        item["validated_by"] = validated_by
    state["work"][id] = item
    return item


def finish(state: dict, id: str) -> None:
    item = _item(state, id)
    if item["type"] != "reading":
        raise CollegeError(f"{id} is not a reading: submit it with /submit.")
    item["status"] = "done"


def link(state: dict, reading_id: str, work_id: str) -> None:
    """A reading is validated as soon as `work_id` is graded at or above the pass mark."""
    reading = _item(state, reading_id)
    if reading["type"] != "reading":
        raise CollegeError(f"{reading_id} is not a reading.")
    reading["validated_by"] = work_id
    if _passed(state, work_id):
        reading["status"] = "done"


def _passed(state: dict, id: str) -> bool:
    item = state["work"].get(id)
    grade = best_grade(item) if item else None
    return grade is not None and grade >= PASS_MARK


def submit(state: dict, id: str, path: str, today: date, rules: dict) -> int:
    item = _item(state, id)
    if item["type"] == "reading":
        raise CollegeError(f"{id} is a reading: nothing to submit, mark it as finished.")
    if item["status"] == "submitted":
        raise CollegeError(f"{id} is already submitted and awaiting grading.")
    maximum = rules["max_attempts"].get(item["type"], 1)
    if len(item["attempts"]) >= maximum:
        plural = "s" if maximum > 1 else ""
        raise CollegeError(f"{id}: {maximum} attempt{plural} maximum, already used.")
    item["attempts"].append({"date": today.isoformat(), "path": path,
                             "grade": None, "criteria": None, "feedback": None})
    item["status"] = "submitted"
    return len(item["attempts"])


def _is_number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _check_shape(criteria) -> None:
    expected = 'expected: {"Criterion": [obtained, max], ...}'
    if not isinstance(criteria, dict) or not criteria:
        raise CollegeError(f"Malformed criteria ({expected}).")
    for name, value in criteria.items():
        if not (isinstance(value, list) and len(value) == 2 and all(map(_is_number, value))):
            raise CollegeError(f"Criterion \"{name}\" malformed: {value!r} ({expected}).")


def grade(state: dict, id: str, criteria: dict, feedback: str) -> float:
    item = _item(state, id)
    if item["status"] != "submitted":
        raise CollegeError(f"{id} is not awaiting grading (status: {item['status']}).")
    _check_shape(criteria)
    total_max = 0
    for name, (obtained, maximum) in criteria.items():
        if not 0 <= obtained <= maximum:
            raise CollegeError(f"Criterion \"{name}\": {obtained} outside [0, {maximum}].")
        total_max += maximum
    if total_max != SCALE_TOTAL:
        raise CollegeError(f"The rubric totals {total_max} points instead of {SCALE_TOTAL}.")
    value = sum(obtained for obtained, _ in criteria.values())
    item["attempts"][-1].update(grade=value, criteria=criteria, feedback=feedback)
    item["status"] = "graded"
    if value >= PASS_MARK:
        for reading in state["work"].values():
            if reading["type"] == "reading" and reading.get("validated_by") == id:
                reading["status"] = "done"
    return value


def best_grade(item: dict) -> float | None:
    grades = [a["grade"] for a in item["attempts"] if a["grade"] is not None]
    return max(grades) if grades else None


def step_done(state: dict, id: str) -> None:
    if id not in state["steps_done"]:
        state["steps_done"].append(id)
