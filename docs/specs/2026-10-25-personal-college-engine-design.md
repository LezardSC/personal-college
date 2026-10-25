# Personal-College — Engine Design

*Date: 2026-10-25*

## 1. Intent

Personal-College turns Claude Code into a **personal university**: for one student, on one subject, it delivers a full curriculum that feels like real higher education, not like chatting with a bot. Written lessons, assigned work, readings, homework, labs, written and oral exams, grades out of 20 against a rubric written *before* the student's copy is seen, resits, spaced revision, and a student record that remembers everything.

It was born as a single-subject prototype (a software engineering curriculum, in a private repository called `engineer-class`) built for a self-taught developer: lots of practice, no theory, a poor memory for past work, and one goal — get hired by learning to **make a technical decision and defend it**, in writing and in interviews. The prototype works. Its student now wants the same experience for other subjects, starting with applied AI (LLMs, agents, automation), and wants to open-source it so others can do the same with their own books and links.

This document specifies the **engine**: everything subject-independent, extracted from the prototype into this repository. Each curriculum ("course") is a separate repository created from the engine.

Two projects follow, in order:
1. **The engine** (this document).
2. **The first real enrollment** of a course built with the engine (applied AI). It is the engine's acceptance test. Its course-specific decisions live in that course's own repository, not here.

## 2. Hard constraint: the prototype is never touched

- `~/engineer-class` is a **read-only source**: files are read, then translated and adapted here. Nothing there is edited, committed, or written by any command (its `scol.py` may only be run read-only: `statut`, `moyennes`).
- Checkable at the end: `git -C ~/engineer-class status` is clean and its history contains no commit from this work.
- Migrating the software engineering course onto the engine is a **separate, later project**, at the student's discretion. The engine does not need to read the prototype's state.

## 3. Goals, non-goals, anti-goals

**Goals**
- Reproduce the **whole** prototype experience: the four daily commands, the four roles, the isolation of faculty-only files, 20-point rubrics written with the assignment, resits, exams, spaced revision, the student record, and a local git commit at the end of every command as progress backup.
- A new `/enroll` command that creates a course from a folder of PDFs and a list of web links.
- A subject is described by **a few course-owned files**. Agents, skills and tools contain nothing subject-specific.
- Updating the engine inside an existing course is a plain `git pull`, **with no conflicts**.
- **No due dates, no lateness**: the student progresses at their own pace and may alternate between several courses.
- **English-first and open-source ready**: all engine files, names and messages are in English. The **teaching language** is a per-course setting (lessons, assignments, feedback and orals are written in it; the tool-generated `AGENDA.md` and transcript stay in English, like every other engine name).

**Non-goals**
- Arbitrary subjects. The target is **technical courses** (software, AI and neighbours) whose labs are code or written documents. Other subjects aren't blocked on purpose, but aren't tested.
- Several courses in one repository; a cross-course dashboard.
- A Claude Code plugin (maybe later).
- Localised command, folder or ID names. Everything the student types or browses is in English; the README is the cheat sheet.
- A web UI: everything stays Markdown, JSON and Claude Code.

**Anti-goals — failure even if it "works"**
- Any change to the prototype.
- **Diluted quality**: vaguer lessons, a softer grader, less concrete assignments than the prototype. Generalising and translating must not remove a single requirement. The prototype's anti-goals stand: no lenient grading (a 16 must be worth a 16), lessons are not book summaries, the TA never gives the solution, no state loss, no chatbot feel.
- Prompts made unreadable by subject conditionals ("if the subject is X…"). The subject is read from `course.md`; prompts stay short.
- An engine `git pull` that overwrites or conflicts with course content.
- Personal data of any real student in the engine repository.

## 4. Architecture: engine and courses

### 4.1 Ownership

Rule: **every file belongs either to the engine or to the course, never both.** This is what makes pulls conflict-free.

| Engine-owned (versioned in Personal-College) | Course-owned (never present in the engine) |
|---|---|
| `CLAUDE.md` (generic; imports `@course.md` and `@profile.md`) | `course.md` — the subject (§5) |
| `README.md` (install, course creation, update, cheat sheet of commands and files) | `profile.md` — the student |
| `.claude/agents/`, `.claude/skills/` | `program/` — `syllabus.md`, `sequence.json`, `sources.md`, `rules.json` |
| `tools/` (scholarship tool, PDF extraction, web snapshots, tests) | `resources/` — `books/`, `text/`, `web/`, `repos/`, `links.md` |
| `.gitignore` (also covers secrets `.env*` and model weights; course-specific ignores go in a course-owned `work/.gitignore` or `.git/info/exclude`), `requirements.txt` | `lessons/`, `assignments/`, `work/`, `feedback/`, `student/`, `state/`, `AGENDA.md`, `.faculty/` (git-ignored) |
| `templates/` — what `/enroll` copies and fills (`course.md`, `profile.md`, `rules.json`, empty `student/` files, a decision-record template…) | course-level docs, if any |
| `docs/` (engine design and plans), `LICENSE` | |

- `CLAUDE.md` is auto-loaded by Claude Code. It holds the shared rules (roles, who reads what, scholarship rules, IDs, paths, state tool, commits) and imports `course.md` and `profile.md`. Agents already read `CLAUDE.md` first and will follow the imports.
- A course never edits an engine file. A course-specific need goes through `course.md` or `rules.json`; if that's impossible, the engine evolves, in Personal-College.
- **Why course folders are not git-ignored by the engine:** a course is a clone of the engine and inherits its `.gitignore`. Ignoring `lessons/` or `state/` there would silently stop backing up the student's progress. The engine repository stays clean by construction, because course content is only ever created inside course repositories.

### 4.2 Creating and updating a course

- A course must **share git history** with the engine, or `git pull` fails ("unrelated histories"); GitHub's *template* button does not share history. Procedure: clone Personal-College under the course's name, rename the remote to `engine`, optionally add the student's own (private) repository as `origin`. Documented in `README.md`.
- Update: `git pull engine main`. Engine updates only touch engine-owned files.
- Command commits stay **local**. Nothing is ever pushed automatically.

### 4.3 Names (all English)

| Concept (prototype name) | Engine name |
|---|---|
| Commands `/cours`, `/rendu`, `/question`, `/oral`, *(new)* | `/lesson`, `/submit`, `/ask`, `/oral`, `/enroll` |
| UE (teaching unit) | module `M<n>` |
| Lesson `L<ue>.<nn>` | `L<m>.<nn>` |
| TP / DV / LE (lab / homework / reading) | `LAB<m>.<n>` / `HW<m>.<n>` / `RD<m>.<n>` |
| Written / oral exam `PE-S<n>` / `PO-S<n>` | `EXAM-WRITTEN-S<n>` / `EXAM-ORAL-S<n>` |
| Resit `RA-UE<n>` / mock oral `OB-<date>` | `RESIT-M<n>` / `MOCK-ORAL-<YYYYMMDD>` |
| Types `tp devoir lecture partiel-ecrit partiel-oral oral-blanc rattrapage` | `lab homework reading written-exam oral-exam mock-oral resit` |
| Statuses `a_faire rendu corrige` | `todo submitted graded` |
| `cours/ devoirs/ travail/ corrections/` | `lessons/ assignments/ work/ feedback/` |
| `etudiant/dossier.md bulletin.md permanence.md journal-adr.md oraux/` | `student/record.md transcript.md office-hours.md decision-log.md orals/` |
| `.enseignants/grilles/ oraux/` | `.faculty/rubrics/ oral-guides/` |
| `etat/scolarite.json`, `CAHIER-DE-TEXTES.md` | `state/state.json`, `AGENDA.md` |
| `outils/scol.py` and its subcommands | `tools/college.py`: `init status step-done add-work finish link submit grade averages agenda` |

Fixed conventions, free quantities: the ID and path patterns above are fixed; the number of modules, of semesters, and whether there is a final project are free and come from `sequence.json` (the tool already derives semesters from it).

## 5. `course.md` — what describes a subject

Written by `/enroll` with the student, from `templates/course.md`. At least:

- **Subject and title**, and the professor's role ("professor of …").
- **Teaching language** and terminology policy (e.g. French, technical terms kept in English).
- **The student's goal** for this course and the target job — drives assignment contexts and the "In an interview" boxes.
- **Starting point**: what is considered known, fuzzy, new; pacing instructions for early lessons.
- **Decision record**: name, template, frequency (both planned courses: an ADR in every lab, graded). Feeds `student/decision-log.md`.
- **Lab formats**: languages, tools, services (Docker…), test commands, and the **execution policy** for designer and grader (prerequisites to check before running anything).
- **Oral format** (both planned courses: recruiter-style technical interview).
- **Former projects** policy (rarely used by default, or a running thread for named projects).
- **Course-specific rules** (e.g. local LLM vs paid API for an AI course).

`profile.md` holds what concerns the student whatever the course: background, memory (the system keeps all state), career goal. `/enroll` offers to copy it from an existing course.

## 6. The scholarship tool

Start from the prototype's `outils/scolarite/` (~580 lines, `unittest` suite), translate names and messages to English, and make three changes.

### 6.1 No due dates

- Remove the due-date field and option, lateness in `status`, the pace command and its state field.
- Keep `hours` (estimated workload) as information; shown in the agenda.
- The agenda lists open work **in creation order**, with workload and whether it blocks, then the next step and the latest grades.
- Blocking logic is unchanged: an unsubmitted blocking item stops `/lesson`.

### 6.2 Per-course rules — `program/rules.json`

- Replaces hard-coded constants: blocking types, coefficients, max attempts, module/exam weights (prototype: `travaux.py` `BLOQUANTS COEFS TENTATIVES_MAX`, `calculs.py` `POIDS_UE POIDS_PARTIELS`).
- `templates/rules.json` holds **exactly** the prototype values (labs coef 2 and 2 attempts, homework 2 attempts, semester = 0.6 × module average + 0.4 × exam average…).
- Validated on load (required keys, weights summing to 1, coefficients ≥ 0…); defaults apply when absent.
- Exam and mock-oral coefficients are applied (weighted exam mean; a mock oral counts only if its coefficient is > 0). The `resit` coefficient is unused (the resit replaces the module average when higher). A module is complete only once no work in it can still be resubmitted (remaining attempts), so a resit is not triggered early. That retry window is bounded: a failed item with attempts left stops holding its module open once any sequence step after the module's last lesson is done (or the whole sequence is), so a student who never resubmits still gets the resit.
- Fixed in the engine, not configurable: the 20-point scale, the 10/20 threshold for resits and for auto-validating a linked reading (`--validated-by`), and "module average = max(average, resit)".

### 6.3 State versioning

`state.json` carries a `version`. Any engine update that changes the state or `rules.json` format bumps it and ships a tested automatic migration on load. A course must never break after `git pull`.

### 6.4 Tests

Port the existing suite; add tests for rules (defaults, custom, invalid) and migration; drop due-date tests. Run: `.venv/bin/python -m unittest discover -s tools/tests -t .`

## 7. Agents and skills

Start from the prototype's `professeur`, `concepteur`, `correcteur` agents and `/cours`, `/rendu`, `/question`, `/oral` skills (≈440 lines of French prompts). They become `professor`, `designer`, `grader` and `/lesson`, `/submit`, `/ask`, `/oral`. **Every substantive rule is translated faithfully**; only subject-specific content is removed and replaced by "see `course.md`". Each prompt states that student-facing output is written in the course's teaching language.

| File | What becomes generic |
|---|---|
| `professor.md` | role from `course.md`; languages of code examples and labs → `course.md`; "every lab requires an ADR" → the decision record; the prototype's single website → web sources (§8.2); student description → `profile.md`; JSON report examples neutralised. `syllabus` mode also receives `course.md` and the starting point (early-lesson pacing). |
| `designer.md` | "a real engineering problem" → a realistic context for the subject; ADR template → decision-record template; "check the provided code compiles" → the lab formats of `course.md`, including starting required services; example rubric → neutral. |
| `grader.md` | "run the code" → the execution policy of `course.md`. A missing execution prerequisite (unreachable service) is reported as `CANNOT GRADE:` like a missing rubric — better no grade than a wrong one. |
| `/lesson`, `/submit`, `/ask`, `/oral` | generic descriptions; no due dates; oral format from `course.md` (recruiter-style as default). |

Unchanged: who reads `.faculty/` (only designer and grader read rubrics; the examiner reads only the oral guide; professor and TA never), subagents run on `sonnet` by default, configurable in `profile.md` § Subagent model (`sonnet`, `opus`, `haiku`; skills pass it when launching an agent), rubrics total exactly 20, grader runs in an isolated context with only the ID, path and attempt, the TA's three-level hint ladder and never giving solutions, oral transcribed after every exchange, local commit at the end of each command, student record updates, "In an interview" boxes, Mermaid diagrams, book citations (full title, chapter, pages — never an internal slug).

**Prompt examples**: prompts are neutral. A concrete example is allowed if presented as an example ("e.g. an ADR in a software course"), never as a rule. Filled-in examples live in `templates/`.

## 8. Sources

### 8.1 Books (as in the prototype)

PDFs are copied to `resources/books/`; `tools/extract_pdf.py` (`pypdf`, in a local `.venv`, no OCR) writes `resources/text/<slug>.txt` with a `=== page N ===` marker per page (N = the page label the student's viewer shows) and `<slug>.toc.md`. Agents read the TOC, then page ranges — never a whole book. **When a PDF has no embedded outline**, `/enroll` rebuilds the TOC from the text's headings in the same format and flags it in `sources.md`.

### 8.2 Web sources (new)

The prototype simply fetched one stable site live. For fast-moving documentation that breaks down: three agents could read three versions of a page, WebFetch returns a processed rather than verbatim page, some links are videos or behind logins, others are git repositories.

1. **Catalogue at enrollment.** `/enroll` classifies every link in `sources.md` by topic and kind: *official docs*, *tutorial*, *code repository*, *student-only course* (video/login — becomes an assigned reading like "follow module 2 of …", never professor material).
2. **Fetch live, then snapshot.** When preparing a lesson, the professor reads docs live and **saves the pages actually used** to `resources/web/<topic>/<page>.md` (verbatim Markdown conversion, with URL and date header). Designer, grader, `/ask` and later lessons read that same snapshot, as with books. A small helper in `tools/` does the fetch-and-convert; a snapshot may be refreshed deliberately, never silently.
3. **Dated citations**: "LangGraph docs, *Persistence*, retrieved 2026-11-03".
4. **Repositories** are cloned on demand into `resources/repos/` (git-ignored).
5. **Pinned versions**: labs pin tool versions (e.g. `requirements.txt`) so code matches the snapshot.

## 9. `/enroll` — creating a course

A skill, run in a freshly cloned course (§4.2), in the main session (interactive). **Resumable**: each step checks whether its output already exists.

0. Check prerequisites (`.venv` with `pypdf`; create it if missing).
1. **Resources.** The student gives a folder of PDFs (possibly a Windows path, read via `/mnt/c/...`) and a links file, plus optionally an intake notes file. PDFs are **copied** (originals untouched), links copied to `resources/links.md`, text and TOCs extracted (§8.1).
2. **Sources.** Write `program/sources.md`: slug → full title, authors, TOC; the reading and citation method; the web catalogue (§8.2).
3. **Enrollment interview**, one question at a time, seeded by the intake notes if given: goal and target job, teaching language, starting point, early pacing, lab formats and tools, decision record, oral format, former projects, special rules, desired length and semesters. Then write `course.md` and `profile.md`; adjust `rules.json` if asked.
4. **Program structure — validated by the student before going further.** The registrar (the `/enroll` skill) drafts the structure; it proposes modules (content, sources, lab tools), semesters and exams; the student amends and approves.
5. **Syllabus.** `professor` in `syllabus` mode → `program/syllabus.md` and `program/sequence.json`. The sequence must satisfy the tool's validation: types `lesson`/`written-exam`/`oral-exam`, unique ids, `S<n>` semesters, `M<n>` modules for lessons, exam module = semester, ids `L<m>.<nn>` / `EXAM-WRITTEN-S<n>` / `EXAM-ORAL-S<n>`.
6. **Start.** `college.py init`, agenda generation, `student/` files from `templates/`, local commit `enroll: <course>`. Announce that `/lesson` is ready.

## 10. Done criteria

1. Tool tests pass.
2. The prototype is untouched (§2).
3. No engine file imposes anything subject-specific (software engineering, a programming language, a given website, ADRs as an obligation) — checked by `grep` outside `docs/` and outside assumed examples in `templates/`.
4. No personal data of a real student in the engine (`grep` for the prototype student's name, handle, former project names).
5. A test course created with §4.2, then updated by `git pull engine main` after a dummy engine commit, updates without conflict.
6. The real first enrollment (applied AI) runs through to its first `/lesson` included. It is the second project but also the engine's acceptance test: defects it reveals are fixed in the engine.

## 11. Left to the builder

- Exact wording of the generic prompts, provided §7's substantive rules are intact.
- Exact schema of `rules.json` and section layout of `course.md`.
- TOC reconstruction method (§8.1) and the web snapshot helper's implementation (§8.2).
- A small script automating §4.2, if useful.
- `README.md` wording.
- Licence choice and the first push to GitHub are the owner's decision.
