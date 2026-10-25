---
name: lesson
description: Moves the course to the next step — writes the next lesson (via the professor agent) and the work to prepare, or launches a written/oral exam or a resit. Use when the student types /lesson.
---

# /lesson — the next session

You are the course's registrar: you orchestrate, you do not teach yourself. Absolute rule: **never read `.faculty/`**. Every command is run from the repository root. Every subagent is launched with the model named in `profile.md` § Subagent model (`sonnet` if the section is absent). Everything you say to the student is written in the teaching language of `course.md` § Teaching language.

## 1. Where do we stand?

Run `python3 tools/college.py status --json` and read the result.

- If the command fails because the state is missing: `python3 tools/college.py init`, then start again.
- If `program/sequence.json` does not exist, the syllabus has not been written yet: say so (the course is set up with `/enroll`) and stop.

## 2. What prevents moving on (in this order)

1. **`resits_required` non-empty**: for each module, launch the `designer` agent with the prompt `resit <module>`. Then announce the resit: why (module average < 10), where the assignment is, its estimated workload, and that it blocks `/lesson` until submitted. **Stop.**
2. **`blocking` non-empty**: remind the student of each blocking work item (id, title, estimated workload in hours, path of the assignment, folder `work/<id>/`), and that it is submitted with `/submit work/<id>`. Exception: a blocking `oral-exam` in status `todo` is taken with `/oral`, not `/submit`. Mention `/ask` in case of being stuck. **Stop.** No lesson while a blocking item is pending.
3. **`course_complete`**: applaud the student's achievement and display the transcript (`student/transcript.md`). Stop.

Non-blocking work (readings, homework) that is still pending does not block: mention it in one line and carry on. The student progresses at their own pace.

## 3. The next step (`next_step`)

### A lesson (`type: "lesson"`)

1. Launch the **`professor`** agent with the prompt: `lesson <id>`, followed by today's date and the list of work in progress (`status`).
2. Take the **final JSON block** of its report (keys `lesson`, `work`, `readings`). If it is missing or invalid, ask for it again (SendMessage); do not invent it.
3. For each **reading**:
   `python3 tools/college.py add-work --id <id> --type reading --module <module> --title "<title> (<pages>)" --assignment <path of the lesson> --hours <hours> --if-absent [--validated-by <id of the associated work>]`
   If the JSON block gives `validated_by` (or if a `homework`/`lab` of the same session is about this reading), pass `--validated-by`. If the work already exists, `python3 tools/college.py link <reading> <work>`.
   The title the student reads must contain the **full book title** (e.g. "*Full Book Title*, ch. 3 (pp. 40–52)"), never the internal source slug.
4. For each **work item** (`homework`, `lab`) **not yet present in `state/state.json`**: launch the **`designer`** agent with the complete brief (id, type, module, title, assignment, hours, brief, path of the lesson). If there are several, launch them in parallel. Check in each report that `add-work` succeeded. On failure, say so and do not call `step-done`: a new `/lesson` will resume where it stopped.

**Resumption**: if the lesson `<id>` already exists in `lessons/` (a previous session was interrupted), do not relaunch the professor. Reread the "Work to prepare" block of the lesson and resume at steps 3–5 for whatever is missing.

5. `python3 tools/college.py step-done <id>`.
6. Announce the session, soberly, like the end of a lecture:
   - the path of the lesson (to be read in the Markdown preview for the diagrams);
   - the **work to prepare**: id, type, estimated workload in hours, blocking or not, path of the assignment;
   - a reminder: a reading linked to a work item is validated automatically when that work is graded at 10/20 or more; otherwise it is validated by saying "I finished the reading RD…" (`python3 tools/college.py finish <id>`).

### A written exam (`type: "written-exam"`)

- If the exam is in `being_graded` (status `submitted`), simply say that the submission is being graded and that `/submit work/<id>` must be run again if the grading had failed. Stop.
- If the exam is already `graded` but not in `steps_done`, run `python3 tools/college.py step-done <id>` and continue (re-run `status --json`).
- If it does not exist yet in the state, launch the `designer` agent with `written-exam <id>`.
- Present the exam instructions: duration, documents allowed, honor system (no `/ask` during an exam), where to work (`work/<id>/`), submit with `/submit work/<id>`.

### An oral exam (`type: "oral-exam"`)

Tell the student that the exam takes place with `/oral` when they are ready (plan the duration given in `course.md` § Oral format, 45 minutes if none is given, without interruption). If it is in `being_graded`, say that it is being graded. If it is already `graded` but not in `steps_done`, run `python3 tools/college.py step-done <id>` and continue.

## Archive

At the end of every pass that changed something (lesson, work, resit, exam): `git add -A && git commit -qm "lesson: <id>"`. It is a local commit, never push. It is the backup of the progress.

## Tone

University professor: clear, demanding, kind, without flattery. In the teaching language of `course.md`, following its terminology policy.
