@course.md
@profile.md

# Personal College — shared contract

This repository is a personal university driven by Claude Code. The engine (this file, `.claude/`, `tools/`, `templates/`) is subject-independent; the subject lives in `course.md`, the student in `profile.md`. Read both before acting.

## Roles and who reads what

| Role | Where | Reads `.faculty/`? |
|---|---|---|
| Professor (syllabus, lessons) | agent `professor` via `/lesson` | **never** |
| Designer (assignments + rubrics + oral guides) | agent `designer` | yes (writes it) |
| Grader (grades + feedback) | agent `grader` via `/submit`, `/oral` | yes (rubrics) |
| Teaching assistant (office hours) | skill `/ask`, main session | **never** |
| Examiner (oral exam) | skill `/oral`, main session | **only** `.faculty/oral-guides/<id>-guide.md`, never a rubric |

- All subagents run on `model: sonnet`.
- Every rubric totals **exactly 20 points** and is written together with the assignment, before any student work exists. The grader is never lenient: a 16 must be worth a 16.
- The teaching assistant **never** gives the solution (three-level hint ladder).
- Lessons teach (motivation, examples, counter-examples, code, Mermaid diagrams); they are not book summaries.
- Whichever role writes for the student writes in the teaching language (see Language).

## Language

Engine names (commands, IDs, types, statuses, folders, tool output) are English. Student-facing content (lessons, assignments, feedback, orals) is written in the teaching language set in `course.md`. `AGENDA.md` and `student/transcript.md` stay in English.

## Scholarship rules

- Blocking types, coefficients, maximum attempts and the module/exam weights come from `program/rules.json`; defaults are in `templates/rules.json`. A `program/rules.json` that overrides `coefficients` must list **every** work type (the tool rejects a partial table).
- Fixed in the engine: 20-point scale, pass mark 10, a resit when a completed module is below 10, module average = max(average, resit).
- A reading linked with `validated_by` to a lab/homework is validated automatically when that work is graded at 10/20 or more; `finish` also works by hand.
- Blocking items (by default `lab`, `written-exam`, `oral-exam`, `resit`) stop `/lesson` until submitted. Readings and homework don't block.
- **No due dates, no lateness, no penalties.** The student progresses at their own pace.

## IDs and paths

| Concept | Name |
|---|---|
| Commands | `/lesson`, `/submit`, `/ask`, `/oral`, `/enroll` |
| Module | `M<n>` |
| Lesson | `L<m>.<nn>` |
| Work | lab `LAB<m>.<n>` · homework `HW<m>.<n>` · reading `RD<m>.<n>` |
| Exams | `EXAM-WRITTEN-S<n>`, `EXAM-ORAL-S<n>` |
| Resit / mock oral | `RESIT-M<n>` / `MOCK-ORAL-<YYYYMMDD>` |
| Types | `lab homework reading written-exam oral-exam mock-oral resit` |
| Statuses | `todo submitted graded` |
| Tool | `tools/college.py` |

Paths:

- Lessons `lessons/M<n>/L<n>.<nn>-<slug>.md`; assets `lessons/M<n>/assets/`.
- Assignments `assignments/<M<n>|S<n>>/<id>/assignment.md`; student copy `work/<id>/`; feedback `feedback/<id>-v<k>.md`.
- Rubrics `.faculty/rubrics/<id>.md`, hidden tests `.faculty/rubrics/<id>-tests/`; oral guides `.faculty/oral-guides/<id>-guide.md` (git-ignored).
- Student folder `student/`: `record.md`, `transcript.md`, `office-hours.md`, `decision-log.md`, `orals/<id>.md` (oral transcripts).
- State `state/state.json`; agenda `AGENDA.md`; program `program/` (`syllabus.md`, `sequence.json`, `sources.md`, `rules.json`); sources `resources/`.

## State tool

`python3 tools/college.py <cmd>` with: `init`, `status [--json]`, `step-done <id>`, `add-work …`, `finish <id>`, `link <reading> <work>`, `submit <id> --path P`, `grade <id> --criteria '<json>' --feedback P`, `averages [--json]`, `agenda`. Never edit `state/state.json` by hand. Every command (`/lesson`, `/submit`, `/oral`, `/ask`) ends with a **local git commit**, which is the progress backup. Never push.

## Tests

`python3 -m unittest discover -s tools/tests -t .`
