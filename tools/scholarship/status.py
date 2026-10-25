"""Where the student stands: next step, blocking items, required resits."""
from tools.scholarship.averages import module_average, module_complete
from tools.scholarship.program import EXAMS
from tools.scholarship.work import PASS_MARK


def status(state: dict, sequence: list[dict]) -> dict:
    """Computed view; never modifies the state."""
    remaining = [s for s in sequence if s["id"] not in state["steps_done"]]
    items = state["work"].values()
    blocking = [i["id"] for i in items if i["blocking"] and i["status"] == "todo"]
    modules = dict.fromkeys(s["module"] for s in sequence if s["type"] == "lesson")
    resits = [m for m in modules
              if module_complete(state, sequence, m)
              and (avg := module_average(state, m)) is not None and avg < PASS_MARK
              and f"RESIT-{m}" not in state["work"]]
    next_step = remaining[0] if remaining else None
    return {
        "next_step": next_step,
        "exam_to_take": next_step["id"] if next_step and next_step["type"] in EXAMS else None,
        "being_graded": [i["id"] for i in items if i["status"] == "submitted"],
        "blocking": blocking,
        "resits_required": resits,
        "can_advance": not blocking and not resits,
        "course_complete": bool(sequence) and not remaining,
    }
