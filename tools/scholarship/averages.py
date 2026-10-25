"""Module and semester averages, module completion."""
from tools.scholarship.program import EXAMS
from tools.scholarship.work import best_grade


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def module_average(state: dict, module: str) -> float | None:
    """Weighted average of the module's graded work; a resit can only raise it."""
    total, weight = 0.0, 0.0
    for item in state["work"].values():
        grade = best_grade(item)
        if item["module"] == module and item["type"] != "resit" and item["coef"] > 0 and grade is not None:
            total += grade * item["coef"]
            weight += item["coef"]
    average = total / weight if weight else None
    resit = state["work"].get(f"RESIT-{module}")
    resit_grade = best_grade(resit) if resit else None
    if resit_grade is not None:
        return resit_grade if average is None else max(average, resit_grade)
    return average


def semester_modules(sequence: list[dict], semester: str) -> list[str]:
    modules = []
    for step in sequence:
        if step["type"] == "lesson" and step["semester"] == semester and step["module"] not in modules:
            modules.append(step["module"])
    return modules


def module_complete(state: dict, sequence: list[dict], module: str) -> bool:
    lessons = [s["id"] for s in sequence if s["type"] == "lesson" and s["module"] == module]
    if not lessons or any(lesson not in state["steps_done"] for lesson in lessons):
        return False
    # A non-blocking homework never submitted must not keep the module open (the resit
    # would never trigger); it simply stays ungraded.
    return all(item["status"] == "graded" or (item["status"] == "todo" and not item["blocking"])
               for item in state["work"].values()
               if item["module"] == module and item["coef"] > 0 and item["type"] != "resit")


def semester_average(state: dict, sequence: list[dict], semester: str, rules: dict) -> tuple[float | None, bool]:
    """(average, provisional) — provisional until every expected exam is graded."""
    averages = [m for m in (module_average(state, mod) for mod in semester_modules(sequence, semester))
                if m is not None]
    exams = [best_grade(item) for item in state["work"].values()
             if item["module"] == semester and item["type"] in EXAMS and best_grade(item) is not None]
    expected = sum(1 for s in sequence if s["semester"] == semester and s["type"] in EXAMS)
    module_mean, exam_mean = _mean(averages), _mean(exams)
    if exam_mean is None:
        return module_mean, True
    if module_mean is None:
        return exam_mean, True
    weights = rules["weights"]
    return weights["modules"] * module_mean + weights["exams"] * exam_mean, len(exams) < expected
