# Personal College

Personal College turns [Claude Code](https://claude.com/claude-code) into a personal university: one student, one subject, a full curriculum. You get written lessons, assigned work, readings, homework, labs, written and oral exams, grades out of 20 against a rubric written before your copy is seen, resits, and a student record that remembers everything.

It started as a single-subject prototype built for a self-taught developer with lots of practice, little theory and a poor memory for past work. The goal was to learn to make a technical decision and defend it, in writing and in interviews. This repository is the subject-independent engine extracted from that prototype, so you can run the same experience on your own books and links.

## Requirements

- [Claude Code](https://claude.com/claude-code)
- Python 3.10 or later (developed and tested on 3.14)
- git
- Docker (optional, only if your labs need services)
- `gh` (GitHub CLI), only if your course reuses former projects from GitHub

## Create a course

This repository is the **engine**, not a course. Never run `/enroll` inside it (it refuses). Each course is a separate clone of the engine, in its own folder, with one subject and one student. A clone keeps the engine's git history, so engine updates can be pulled later. Do not use GitHub's "template" button: it drops the history and updates would fail with "unrelated histories".

### 1. Clone the engine under the course's name

Run this from a parent folder, not from inside the engine:

```bash
git clone https://github.com/LezardSC/Personal-College.git my-course && cd my-course
git remote rename origin engine               # required: this is what `git pull engine main` uses later
git remote add origin <your private repo>     # optional
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

Replace `my-course` with your course's name. If you already have a local copy of the engine, you can clone from its path instead of the URL. The original is left untouched, so you can create as many courses as you like.

### 2. Prepare your material

`/enroll` asks for these. Having them ready makes it faster:

| What | Required? | Format |
|---|---|---|
| Books | No, but recommended | A folder of PDF files. Under WSL, a Windows folder is `/mnt/c/Users/<you>/...`. |
| Links | No | A text or Markdown file, one URL per line (docs, tutorials, repositories). Without it, the course uses the books only. |
| Intake notes | No | A free-form file: what you want to learn, why, your current level, what you already know. The more it says, the fewer questions `/enroll` asks. |

The books and links are copied into `resources/` inside the course. Your originals are never moved or modified.

### 3. Start Claude Code and enroll

```bash
claude
```

Then type `/enroll`. The three inputs above can be given as arguments, in this order: `/enroll <pdf folder> <links file> <intake notes>`. Anything you leave out, it asks for. It then:

1. extracts the text of each PDF;
2. catalogues your sources;
3. interviews you, one question at a time (goal, teaching language, starting level, tools, oral exam format, ...);
4. proposes a program structure for your approval;
5. has the professor write the syllabus.

It is resumable: if it is interrupted, run `/enroll` again and it picks up where it stopped. When it is done, `/lesson` is ready (see [Commands](#commands) and [A typical day](#a-typical-day)).

Nothing is ever pushed automatically. Pushing your course to your own repository is your decision.

## Update the engine

```bash
git pull engine main
```

This only works if the course was created by cloning the engine (shared history, see above). An update only touches engine-owned files, so it never conflicts with your course. **Never edit these files:**

- `CLAUDE.md`, `README.md`, `.gitignore`
- `.claude/agents/` and `.claude/skills/`
- `tools/`
- `requirements.txt`
- `templates/`
- `docs/` and `LICENSE`

A course-specific need goes through `course.md` (the subject, § Special rules) or `program/rules.json` (the scholarship rules); personal notes go in `CLAUDE.local.md` (git-ignored). If none can express it, the engine itself should evolve.

Course-specific ignore rules (large datasets, local files) go in a course-owned `work/.gitignore` or in `.git/info/exclude`, never in the engine `.gitignore`. The engine `.gitignore` already covers secrets (`.env`) and model weights (`*.gguf`, `*.safetensors`, `*.pt`, …) so that the automatic commits never record them.

## Subagent model

The professor, designer and grader subagents run on **Sonnet** by default. If your subscription allows it you can switch to Opus (stronger, noticeably more expensive in usage) or Haiku: edit the `## Subagent model` section of `profile.md` (`sonnet`, `opus` or `haiku`). The skills read it each time they launch an agent.

## Commands

Everything is typed inside Claude Code, from the repository root.

| Command | What it does | When |
|---|---|---|
| `/enroll` | Creates the course: sources, interview, program, syllabus. Resumable. | Once, in a freshly cloned course. |
| `/lesson` | The professor writes **the next lesson** in `lessons/M<n>/` and gives the **work to prepare**. Also launches the written exams and the resits. Refuses to move on while a blocking item is not submitted. | At the start of a session, when nothing is waiting to be handed in. |
| `/submit <folder>` | Hands in your work: the grader runs it, **grades it out of 20** against the rubric and writes commented feedback in `feedback/`. | When a lab or homework is finished, e.g. `/submit work/LAB1.1`. |
| `/ask <question>` | Office hours: the teaching assistant helps you with progressive hints, **never the solution**. Answers course questions normally. | When you are stuck, or have a question about the course. |
| `/oral [id]` | An interactive oral exam in the form of a technical interview: the semester's oral exam, then transcribed and graded. With no argument and nothing pending, it runs a **mock oral** on a topic you have already seen. | End of semester, or to practise before a real interview. |

To finish a **reading**, just say so: "I finished reading RD1.1". It is routed to `/submit`'s reading path, which runs `python3 tools/college.py finish RD1.1`.

## Where things are

| File or folder | What it contains |
|---|---|
| `AGENDA.md` | What is waiting to be handed in, with estimated workload, the next step and the latest grades. **Look at it first.** |
| `student/transcript.md` | Your grades, module averages and semester averages. |
| `lessons/` | The lessons, as `lessons/M<n>/L<n>.<nn>-<slug>.md`. Open them in a Markdown preview to see the Mermaid diagrams. |
| `assignments/` | The assignments and their instructions: `assignments/<M<n>\|S<n>>/<id>/assignment.md`. |
| `work/<id>/` | **Where you work** (starter code, decision record template). |
| `feedback/` | Your graded copies: `feedback/<id>-v<k>.md`. |
| `student/decision-log.md` | Your recorded technical decisions, good stories for interviews. |
| `student/record.md`, `student/office-hours.md`, `student/orals/` | Your student record, the log of office hours, the oral transcripts. |
| `program/syllabus.md` | The complete program. Also `sequence.json`, `sources.md` and `rules.json` in the same folder. |
| `course.md`, `profile.md` | The subject and the student, written by `/enroll`. |
| `resources/` | Your books, their extracted text and the web snapshots. |

IDs: modules `M<n>`, lessons `L<m>.<nn>`, labs `LAB<m>.<n>`, homework `HW<m>.<n>`, readings `RD<m>.<n>`, exams `EXAM-WRITTEN-S<n>` and `EXAM-ORAL-S<n>`, resits `RESIT-M<n>`, mock orals `MOCK-ORAL-<YYYYMMDD>`.

## Rules

Defaults are in `templates/rules.json`; a course can override them in `program/rules.json`.

- Labs and homework: **2 attempts** at most, the best grade counts. Each top-level block you override in `program/rules.json` replaces the default block wholesale: copy it from `templates/rules.json` and edit it. Every other kind of work: 1 attempt.
- **No due dates, no lateness, no penalties.** You progress at your own pace, and may alternate between several courses.
- A lab, a written exam, an oral exam or a resit that is not submitted **blocks** `/lesson`. Readings and homework don't block.
- A reading linked to a lab or homework is validated automatically when that work is graded 10/20 or more. Saying you finished it also works.
- A module completed below 10/20 gives a **resit**; the module average is the better of the average and the resit.
- Semester = 0.6 × module average + 0.4 × exam average (written and oral).
- The scale is 20 points and the pass mark is 10, fixed in the engine.
- **Do not open `.faculty/`**: it holds the grading rubrics and the oral guides. It is git-ignored by design (so you cannot read them in the git history), and therefore **not backed up**: losing the folder loses them.
- Every command ends with a local git commit, which is your progress backup. Never edit `state/state.json` by hand.

## A typical day

1. Open `AGENDA.md`.
2. If work is waiting, do it in `work/<id>/` (use `/ask` if you are stuck), then `/submit work/<id>` and read the feedback.
3. Otherwise, `/lesson`: read the lesson, take notes, and note the work to prepare.
4. Do the assigned readings, and say when you have finished one.

## Tests

```bash
.venv/bin/python -m unittest discover -s tools/tests -t .
```

## Licence

MIT — see [LICENSE](LICENSE).
