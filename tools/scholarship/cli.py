"""Command-line interface: python3 tools/college.py <command>."""
import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

from tools.scholarship import work as w
from tools.scholarship.averages import module_average, semester_average
from tools.scholarship.documents import agenda, transcript
from tools.scholarship.program import TYPES, load_rules, load_sequence
from tools.scholarship.state import CollegeError, init, load, save
from tools.scholarship.status import status


def _root() -> Path:
    return Path(os.environ.get("COLLEGE_ROOT", Path(__file__).resolve().parents[2]))


def _paths(root: Path) -> tuple[Path, Path, Path]:
    return root / "state" / "state.json", root / "program" / "sequence.json", root / "program" / "rules.json"


def _write_documents(root: Path, state: dict, sequence: list[dict], rules: dict, today: date) -> None:
    (root / "AGENDA.md").write_text(agenda(state, sequence, today), encoding="utf-8")
    (root / "student").mkdir(exist_ok=True)
    (root / "student" / "transcript.md").write_text(transcript(state, sequence, rules), encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="college", description="Personal College: state and grades engine.")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="create the state if absent")
    sub.add_parser("status", help="next step, blocking items, resits").add_argument("--json", action="store_true")
    sub.add_parser("step-done", help="mark a sequence step as done").add_argument("id")
    a = sub.add_parser("add-work", help="record an assigned work item")
    a.add_argument("--id", required=True)
    a.add_argument("--type", required=True, choices=TYPES)
    a.add_argument("--module", required=True)
    a.add_argument("--title", required=True)
    a.add_argument("--assignment", required=True)
    a.add_argument("--hours", required=True, type=float, help="estimated workload in hours")
    blocking = a.add_mutually_exclusive_group()
    blocking.add_argument("--blocking", dest="blocking", action="store_true", default=None)
    blocking.add_argument("--non-blocking", dest="blocking", action="store_false")
    a.add_argument("--coef", type=float)
    a.add_argument("--validated-by", help="readings only: id of the work whose pass (>= 10) validates the reading")
    a.add_argument("--if-absent", action="store_true", help="do nothing if the id already exists (resume)")
    sub.add_parser("finish", help="mark a reading as done").add_argument("id")
    li = sub.add_parser("link", help="attach a reading to the work whose pass validates it")
    li.add_argument("reading")
    li.add_argument("work")
    s = sub.add_parser("submit", help="record a submission")
    s.add_argument("id")
    s.add_argument("--path", required=True)
    g = sub.add_parser("grade", help="record the grade of the latest attempt")
    g.add_argument("id")
    g.add_argument("--criteria", required=True, help='JSON {"criterion": [obtained, max], ...} totalling 20')
    g.add_argument("--feedback", required=True)
    sub.add_parser("averages", help="module and semester averages").add_argument("--json", action="store_true")
    sub.add_parser("agenda", help="regenerate the agenda and the transcript")
    return p


def _print_status(st: dict) -> None:
    step = st["next_step"]
    print("Next step:", f"{step['id']} — {step['title']} ({step['type']})" if step else
          ("course complete" if st["course_complete"] else "no program loaded"))
    if st["exam_to_take"]:
        print("Exam to take:", st["exam_to_take"])
    print("Blocking:", ", ".join(st["blocking"]) or "none")
    print("Being graded:", ", ".join(st["being_graded"]) or "none")
    print("Resits required:", ", ".join(st["resits_required"]) or "none")
    print("Can advance:", "yes" if st["can_advance"] else "no")


def execute(args, root: Path, today: date) -> None:
    state_path, sequence_path, rules_path = _paths(root)
    if args.command == "init":
        state = init(state_path, today)
        _write_documents(root, state, load_sequence(sequence_path), load_rules(rules_path), today)
        print(f"State ready: {state_path}")
        return
    state, sequence = load(state_path), load_sequence(sequence_path)
    changed = True
    if args.command == "status":
        changed = False
        st = status(state, sequence)
        print(json.dumps(st, ensure_ascii=False, indent=2)) if args.json else _print_status(st)
    elif args.command == "step-done":
        w.step_done(state, args.id)
    elif args.command == "add-work" and args.if_absent and args.id in state["work"]:
        changed = False
        print(f"{args.id} already exists, skipped.")
    elif args.command == "add-work":
        item = w.add_work(state, args.id, args.type, args.module, args.title, args.assignment, today,
                          load_rules(rules_path), hours=args.hours, blocking=args.blocking, coef=args.coef,
                          validated_by=args.validated_by)
        print(f"{item['id']} recorded ({item['hours']:g} h).")
    elif args.command == "finish":
        w.finish(state, args.id)
    elif args.command == "link":
        w.link(state, args.reading, args.work)
    elif args.command == "submit":
        print(f"{args.id}: attempt {w.submit(state, args.id, args.path, today, load_rules(rules_path))} recorded.")
    elif args.command == "grade":
        try:
            criteria = json.loads(args.criteria)
        except json.JSONDecodeError as e:
            raise CollegeError(f"--criteria is not valid JSON ({e}).") from None
        if not (root / args.feedback).is_file():
            raise CollegeError(f"Feedback file not found: {args.feedback}. Write it before recording the grade.")
        print(f"{args.id}: {w.grade(state, args.id, criteria, args.feedback):g}/20")
    elif args.command == "averages":
        changed = False
        rules = load_rules(rules_path)
        modules = list(dict.fromkeys([s["module"] for s in sequence if s["type"] == "lesson"] +
                                     [i["module"] for i in state["work"].values() if i["module"].startswith("M")]))
        semesters = list(dict.fromkeys(s["semester"] for s in sequence))
        if args.json:
            result = {"modules": {m: module_average(state, m) for m in modules},
                      "semesters": {s: dict(zip(("average", "provisional"),
                                                semester_average(state, sequence, s, rules))) for s in semesters}}
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(transcript(state, sequence, rules))
    if changed:
        save(state, state_path)
        _write_documents(root, state, sequence, load_rules(rules_path), today)


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    try:
        execute(args, _root(), date.today())
    except CollegeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    return 0
