---
name: submit
description: Hand in a piece of work of the course (lab, homework, exam, resit) so that the grader agent grades it out of 20 and comments on it. Usage - /submit <folder path> [id]. Also use when the student says they finished a reading.
argument-hint: <path> [id]
---

# /submit — hand in your work

Arguments: `$ARGUMENTS` (a path, possibly followed by an id). You **never** read `.faculty/`, and you never show a rubric. The subagent is launched with `model: "sonnet"`. Everything you say to the student is written in the teaching language of `course.md` § Teaching language.

## 1. Identify the work

- The id is the explicit argument if there is one; otherwise the name of the folder (`work/LAB1.2` → `LAB1.2`).
- Check in `state/state.json` (read-only) that a work item has this id. If not, or if no path is given, list the submittable work: the items with status `todo`, plus the items with status `graded` whose type still has attempts left (`max_attempts` in `program/rules.json`, read-only; the number of attempts already used is in the state), which can be resubmitted. Then ask which one is being submitted. **Never invent an id.**
- Check that the path exists and is not empty. If not, say so and stop.
- If the work is in status **`submitted`** (a previous grading failed), do not run `submit` again: take `k = number of attempts` from the state and go directly to step 3.

## 2. According to the type

- **Reading**: `python3 tools/college.py finish <id>`, confirm, done.
- **Anything else**: first check that the rubric exists, with `test -f .faculty/rubrics/<id>.md` (a plain existence test, do not open the file). If it is missing, record nothing. Say that the assignment is incomplete on the teaching-team side, offer to relaunch the `designer` agent for this work, and stop. Otherwise: `python3 tools/college.py submit <id> --path <path>`.
  - If the command refuses (attempts used up, already being graded…), display its message as is and stop.
  - Otherwise, note the attempt number `k` that it prints.

## 3. Grading (separate context)

Launch the **`grader`** agent with **only**:

```
Grade the work <id>, attempt <k>. Submission: <path>.
```

Pass nothing else from the conversation: it must remain impartial.

- If its report begins with `CANNOT GRADE:`, pass the reason on to the student. The attempt stays recorded, in status `submitted`, without a grade. Once the problem is fixed, a new `/submit <path>` only relaunches the grading (see step 1). **Mark nothing as done.**
- If it is an exam (`EXAM-…`) that was **actually graded**: `python3 tools/college.py step-done <id>`.

## 4. Hand back the graded work

Display:
- the **grade /20** and the table of criteria (read from `feedback/<id>-v<k>.md`);
- the link to the complete feedback, to be read in full;
- if an attempt remains (the type allows more attempts than used, according to `max_attempts` in `program/rules.json`): resubmission is possible, and the best grade counts;
- what this unlocks: rerun `python3 tools/college.py status --json`. If nothing blocks any more, say that `/lesson` is available. If a resit becomes required, announce it.

## 5. Archive

`git add -A && git commit -qm "submit: <id> v<k>"` (local commit, never push).
