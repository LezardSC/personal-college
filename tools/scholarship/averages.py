"""Module and semester averages, module completion."""
from tools.scholarship.program import EXAMS
from tools.scholarship.work import PASS_MARK, best_grade


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


def module_complete(state: dict, sequence: list[dict], module: str, rules: dict) -> bool:
    lessons = [s["id"] for s in sequence if s["type"] == "lesson" and s["module"] == module]
    if not lessons or any(lesson not in state["steps_done"] for lesson in lessons):
        return False
    # A non-blocking homework never submitted must not keep the module open (the resit
    # would never trigger); it simply stays ungraded.
    # A graded item below the pass mark with attempts left keeps the module open only while the
    # student is still inside it (the retry window): once a step after the module's last lesson
    # is done, or the whole sequence is, it counts as settled so the resit can trigger.
    ids = [s["id"] for s in sequence]
    last = max(ids.index(l) for l in lessons)
    left_module = all(i in state["steps_done"] for i in ids) or \
        any(i in state["steps_done"] for i in ids[last + 1:])

    def settled(item: dict) -> bool:
        if item["status"] == "todo":
            return not item["blocking"]
        if item["status"] != "graded":
            return False
        retry_left = len(item["attempts"]) < rules["max_attempts"].get(item["type"], 1)
        return left_module or not (best_grade(item) < PASS_MARK and retry_left)

    return all(settled(item) for item in state["work"].values()
               if item["module"] == module and item["coef"] > 0 and item["type"] != "resit")


def semester_average(state: dict, sequence: list[dict], semester: str, rules: dict) -> tuple[float | None, bool]:
    """(average, provisional) — provisional until every expected exam is graded."""
    averages = [m for m in (module_average(state, mod) for mod in semester_modules(sequence, semester))
                if m is not None]
    # Exam items carry the semester id (`S<n>`) in `module`. Each counts with the coef stored at
    # creation; mock orals have coef 0 by default, hence are excluded unless the rules say otherwise.
    in_semester = [i for i in state["work"].values() if i["module"] == semester and best_grade(i) is not None]
    counted = [i for i in in_semester if i["type"] in EXAMS + ("mock-oral",) and i["coef"] > 0]
    weight = sum(i["coef"] for i in counted)
    exam_mean = sum(best_grade(i) * i["coef"] for i in counted) / weight if weight else None
    graded_exams = sum(1 for i in in_semester if i["type"] in EXAMS)
    expected = sum(1 for s in sequence if s["semester"] == semester and s["type"] in EXAMS)
    module_mean = _mean(averages)
    if exam_mean is None:
        return module_mean, True
    if module_mean is None:
        return exam_mean, True
    weights = rules["weights"]
    return weights["modules"] * module_mean + weights["exams"] * exam_mean, graded_exams < expected
