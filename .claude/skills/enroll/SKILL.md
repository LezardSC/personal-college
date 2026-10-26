---
name: enroll
description: Creates a course from a folder of PDF books and a file of links — extracts the texts, catalogues the sources, interviews the student, validates the program structure, then has the professor write the syllabus. Resumable. Use when the student types /enroll in a freshly cloned course.
argument-hint: "[pdf folder] [links file] [intake notes]"
---

# /enroll — creating a course

You are the registrar opening a new course, in the main session, interactively. Every command runs from the repository root. Every subagent is launched with the model named in `profile.md` § Subagent model (`sonnet` if the section is absent). **Never read `.faculty/`.** The engine files (`CLAUDE.md`, `.claude/`, `tools/`, `templates/`) are never edited; the subject goes into `course.md`, the student into `profile.md`.

**Resumable.** Each step below opens with an *existence check*: if the output already exists, skip the step and say so in one line. Never overwrite `program/sources.md`, `course.md`, `profile.md`, `program/syllabus.md`, `program/sequence.json` or `state/state.json`: offer to edit them instead (show the current content, apply only the changes the student asks for). When a run is interrupted, a new `/enroll` picks up at the first step whose output is missing.

**Language.** Talk to the student in the language they write in. Ask **one question at a time**. Generated files that the student will read (`course.md`, `profile.md`, `program/*`) are written in the teaching language once it is known (step 3); until then, in English.

## Opening: refuse to run inside the engine itself

Run `git remote get-url origin`, `git remote`, `ls course.md` and `ls docs/specs/*engine-design.md`. This is the engine repository, not a course, if the origin URL matches `personal-college(\.git)?/?$` **or** (there is no `course.md`, no remote named `engine`, and a `docs/specs/*engine-design.md` file is present). Then explain the procedure and **stop**.

> A course must share git history with the engine so that `git pull engine main` works. Clone the engine under the course's name (`git clone <engine url> <course-name>`), `cd` into it, rename the remote (`git remote rename origin engine`), optionally add your own private repository as `origin`, then run `/enroll` there. See `README.md`.

(An `engine` remote or a `course.md` present, and no match above: carry on.)

## 0. Prerequisites

*Check:* `.venv/bin/python -c "import pypdf, trafilatura"` succeeds.
If not: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`, then re-check. If it fails, show the error and stop.

## 1. Resources

*Check:* `resources/links.md` exists, and every PDF of the folder has its copy in `resources/books/` and its text in `resources/text/`. Redo only what is missing.

1. **Inputs.** Take them from the arguments; ask for what is missing: the folder of PDFs (a Windows path is read through `/mnt/c/...`), the links file, and an optional **intake notes** file. If the student has no links, `resources/links.md` is created with a single line saying so. If an intake notes file is given, read it **now** and, in step 3, ask only what it leaves open. Create `program/` if needed, then copy it to `program/enrollment-notes.md` if that file is absent.
2. **Copy the PDFs** to `resources/books/` under their original names, **only if `resources/books/<name>` is absent**. Never move or modify the originals. Copy the links file to `resources/links.md` if absent.
3. **Slugs.** For each book choose a short, lowercase, hyphenated, unique slug (`resources/text/<slug>.txt` is the existing-slug check). Slugs are internal: they appear in file paths and in `sources.md`, **never** in anything the student reads.
4. **Extract**, only if `resources/text/<slug>.txt` is absent:
   `.venv/bin/python -I tools/extract_pdf.py "resources/books/<name>.pdf" resources/text <slug>`
   It writes `<slug>.txt` (a `=== page N ===` marker per page, N = the page label the student's viewer shows) and `<slug>.toc.md`. A PDF that fails (scanned, encrypted) is reported to the student and left out; do not retry it silently.
5. **Rebuild the TOC when the PDF has no outline** (the `.toc.md` contains "No outline in this PDF", or only a handful of entries for a long book). **Skip any `.toc.md` whose first line is `<!-- TOC rebuilt from text -->`**: it was already rebuilt on an earlier run.
   - `grep -nE "^(Chapter|CHAPTER|Part|PART)\b" resources/text/<slug>.txt`, then numbered headings `grep -nE "^[0-9]+(\.[0-9]+)*\s+[A-Z]" …`, then short all-caps lines `grep -nE "^[A-Z][A-Z .,:'-]{3,60}$" …`;
   - **confirm each hit** by reading around it (`sed -n 'a,bp'`): discard running headers, figure captions and index entries; find its page with the nearest preceding `=== page N ===` marker;
   - overwrite `resources/text/<slug>.toc.md` in the extractor's format, with `<!-- TOC rebuilt from text -->` as its **first line** (then the same header, then `- Title — page N`, indented by level) and remember to flag it in step 2 ("TOC rebuilt from text").
   Never load a whole book into context.

## 2. Sources

*Check:* `program/sources.md` exists → skip, and offer to edit it (adding a book or a link is such an edit; re-run step 1 for the new file first).

Write `program/sources.md` (create `program/`), in the teaching language if already known, otherwise in English and translate after step 3 if the student asks for it. Contents:

1. **Method section** (adapt wording to the course, keep every rule):
   - Books are in `resources/books/` (PDF, git-ignored). Their text is in `resources/text/<slug>.txt` (git-ignored) with a `=== page N ===` marker before each page, where N is **the number the student's PDF viewer shows** (page label: `xiii`, `42`…). Each book's table of contents is in `resources/text/<slug>.toc.md`, same numbers.
   - **Locating:** open the `.toc.md`, find the chapter's page, then `grep -n "=== page 120 ===" resources/text/<slug>.txt` and read by ranges (`sed -n 'a,bp'`). Never load a whole book.
   - **Citing** (everything the student reads: lessons, assignments, feedback, work titles, office hours): *full book title* ch. X "Chapter title", pp. a–b. The page number is the marker's, i.e. the one the student types in their viewer. The student knows **neither slugs nor acronyms** and must never see "PDF p.". Assigned readings give the full title, the chapter **and** the pages.
   - **Files:** the student has the books under their original names in `resources/books/`.
   - **Regenerating the text:** `.venv/bin/python -I tools/extract_pdf.py "<pdf>" resources/text <slug>`.
2. **Books table:** `| Slug (internal) | Book — title to cite | Authors | TOC |` with a link to each `.toc.md`. Title and authors come from the PDF's first pages (read them, do not guess; ask the student when unsure). Add "TOC rebuilt from text — check page numbers when citing" to the TOC cell of every rebuilt one, and "outline limited to parts: search 'Chapter N' in the text" when the outline is too coarse.
3. **Web catalogue** (see "Web sources" in the rules below): one row per link of `resources/links.md`.

**Web catalogue.** For each link, record `topic`, `kind` and the URL: kinds are `official docs`, `tutorial`, `code repository`, `student-only course` (video, login or paywall: it can only become an assigned reading such as "follow module 2 of …", never professor material). Open a link only if its kind is unclear from the URL. **Take no snapshot now**: the professor snapshots the pages it actually uses, when preparing a lesson (`tools/snapshot_web.py`). State this in `sources.md`, with the rules: snapshots live in `resources/web/<topic>/<page>.md`, are cited as "<site> docs, *<page>*, retrieved <date>", are refreshed only deliberately; repositories are cloned on demand into `resources/repos/`; labs pin tool versions.

## 3. Enrollment interview

*Check:* `course.md` and `profile.md` both exist and contain no remaining `<!-- /enroll` placeholder → skip, offer to edit. If one is missing or still has placeholders, interview only for what is missing.

Read `templates/course.md` and `templates/profile.md` (their comments say what each section needs). Ask **one question at a time**, starting from what the intake notes and the books already tell you (propose a draft answer and let the student correct it rather than asking from a blank page). Cover, in this order:

1. Subject, and the course title.
2. **Goal and target job.**
3. **Teaching language** and terminology policy (e.g. technical terms kept in English). From here on, speak and write in it.
4. **Starting point:** known / fuzzy / new, and the pacing of the early lessons.
5. **Lab formats and tools:** languages, services (Docker…), test commands, versions installed (`§ Toolchains`; check what is installed with `--version` rather than trusting memory), and the **execution policy** for designer and grader (prerequisites to check, services to start before running anything).
6. **Decision record:** whether one is required, its name, template (default `templates/decision-record.md`; a custom template is saved as `program/decision-record.md`), frequency, log (default `student/decision-log.md`). "None" is a valid answer.
7. **Oral format:** the examiner **persona** (default: recruiter-style technical interview) **and** the **duration** in minutes. Both go in `course.md` § Oral format; `/lesson` and `/oral` read the duration from there.
8. **Former projects:** the policy (default: rarely, only when lesson and exercise truly fit; or a running thread). If former projects are used, ask for the **GitHub owner/account** and the **repository names**, and write them in `course.md` § Former projects (the professor clones `<owner>/<repo>` from there). Never assume the student remembers them.
9. **Special rules** (or "None").
10. **Length:** desired number of semesters and rough duration; this feeds step 4.
11. **Student profile:** background (facts only), career goal, pace (hours per day or week; information only, there are no due dates). Offer first to **copy `profile.md` from a path the student gives** (another course); then ask only what is still blank or specific to this course.

Then write **only what is missing or incomplete**. A file that is absent is created from `templates/course.md` (replace every comment placeholder by the answer, keep the section titles) or from `templates/profile.md` (keep the fixed "Memory" paragraph). A file that exists but still has placeholders is **edited in place** (fill the remaining sections only); it is never regenerated from the template. Show both and let the student correct them.

**Rules.** If `program/rules.json` is absent, copy `templates/rules.json` to it (`program/` exists from step 2). Edit it only if the student asks to change a default (blocking types, coefficients, attempts, weights) and keep the **full coefficients table**: the tool rejects a partial one. Show the changed values.

## 4. Program structure — validated by the student

*Check:* `program/syllabus.md` and `program/sequence.json` exist → skip (the structure was approved earlier).

Otherwise propose the structure yourself (you are the registrar: you draft, the student validates), from `course.md`, `profile.md`, the TOCs and the web catalogue: **modules** (`M1`…, each with its content, the books or sources it draws on, the lab tools), the **semesters** (`S1`…) and how modules are spread over them, the **exams** (a written and an oral per semester, with `EXAM-WRITTEN-S<n>` / `EXAM-ORAL-S<n>`), and an indicative number of lessons per module. Present it as a short table and ask the student to amend it. Iterate until they approve explicitly. **This validation is mandatory: do not launch the professor before it.** Keep the approved structure in your context (it is what you pass in step 5; it is also recorded in the syllabus).

## 5. Syllabus

*Check:* both `program/syllabus.md` and `program/sequence.json` exist → skip. If only one exists, delete neither: relaunch the professor and say it must produce only the missing file (name it) and must **not modify the existing one** (name it too); you then check both.

Launch the **`professor`** agent (with that model) with the prompt `syllabus`, followed by: the **approved structure** (modules, semesters, exams, indicative lesson counts), the paths of `course.md`, `profile.md`, `program/sources.md` and `resources/text/*.toc.md`, and today's date. Check afterwards that:

- both files exist and `program/sequence.json` is valid JSON where every step carries the five string keys `id`, `type`, `module`, `semester`, `title`, with ids unique, `type` one of `lesson`, `written-exam`, `oral-exam`, `semester` of the form `S<n>`, lessons with module `M<n>` and id `L<m>.<nn>`, exams with module equal to their semester and id `EXAM-WRITTEN-S<n>` / `EXAM-ORAL-S<n>` matching the type and semester (the `init` run just below validates it and names any defect);
- the modules and exams match the approved structure.

Then run `python3 tools/college.py init` (idempotent; it validates the sequence before creating any state). If it errors, send the professor back with the exact error. If the other checks fail, send the professor back with the precise defect. Do not repair them silently. Give the student the path of `program/syllabus.md` and a one-paragraph summary; invite changes (small edits you can do; structural ones restart from step 4).

## 6. Start

*Check:* `state/state.json` exists → state already initialised; still do whatever below is missing.

1. The state was created by the `init` of step 5; reuse it (run `python3 tools/college.py init` again only if `state/state.json` is absent, it is idempotent).
2. Copy `templates/student/*` into `student/` **only the files that are absent** (`record.md`, `office-hours.md`, `decision-log.md`).
3. `python3 tools/college.py agenda`; then `python3 tools/college.py status --json` to confirm that the next step is the first lesson.
4. If `program/rules.json` is somehow absent, copy `templates/rules.json` to it.
5. Commit locally: `git add -A && git commit -qm "enroll: <course title>"` (the books and extracted texts are git-ignored; if there is nothing to commit, say so). **Never push.**
6. Announce, in the teaching language: the course is open, summarise it in two lines (modules, number of lessons), say that `/lesson` starts the first session, and that `/ask`, `/submit` and `/oral` come later.

## Tone

A registrar welcoming a new student: brief, concrete, no flattery. Always tell the student what was created and where.
