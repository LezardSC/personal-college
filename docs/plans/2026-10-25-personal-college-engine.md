# Personal-College Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract a subject-independent, English-first "personal university" engine from the private prototype `~/engineer-class`, so any technical course can be created from it with `/enroll` and updated with `git pull`.

**Architecture:** A stdlib-only Python scholarship tool (`tools/college.py`) keeps all state; Claude Code agents (`professor`, `designer`, `grader`) and skills (`/lesson`, `/submit`, `/ask`, `/oral`, `/enroll`) drive the curriculum; everything subject-specific lives in course-owned files (`course.md`, `profile.md`, `program/`) that the engine never ships. Code and prompts are translated and adapted from the prototype, never written from scratch.

**Tech Stack:** Python 3.14 (stdlib for the tool), `unittest`, `pypdf` and `trafilatura` in a local `.venv` (PDF extraction, web snapshots), Claude Code agents/skills in Markdown.

**Spec:** `docs/specs/2026-10-25-personal-college-engine-design.md` — read it before any task. Section numbers (§) below refer to it.

## Global Constraints

- **Never modify `~/engineer-class`.** Read only. The only commands allowed there are reads (`cat`, `grep`, `git log/status`, `python3 outils/scol.py statut|moyennes`). (§2)
- **No personal data** in any file of this repository, including this plan's follow-ups and commit messages: no real student name, handle, school, or former-project names. Checked against a private pattern file outside the repo (Task 1).
- All engine files, identifiers, CLI output and prompts are **in English**. Student-facing *content* (lessons, assignments, feedback, orals) is written in the teaching language read from `course.md`. (§3)
- Names exactly as in §4.3 (commands, IDs, types, statuses, folders, tool subcommands).
- `tools/scholarship/` and `tools/college.py` use the **standard library only** (agents run them with plain `python3`).
- Fixed in code: 20-point scale (`SCALE_TOTAL = 20`), pass mark `PASS_MARK = 10`, module average = max(average, resit). (§6.2)
- Default rules = prototype values exactly (§6.2, Task 2).
- All subagents declared with `model: sonnet`.
- Command commits are local; **never push** (the owner decides the first push).
- Work on branch `engine-v1` (create it from `main` before Task 1).
- Tests: `.venv/bin/python -m unittest discover -s tools/tests -t .` (the venv is needed only for the snapshot/PDF tests; the tool itself needs none).

## Review Focus

1. A `program/rules.json` with a typo'd or unknown key, a type outside the engine's types, or weights not summing to 1 → a clear `CollegeError` naming the problem, never silent defaults. (test in Task 2)
2. A `state.json` written by a **newer** engine (`version` > `VERSION`) → clear error telling the user to `git pull engine main`; an older version → migrated in place and saved. (test in Task 2)
3. A web page whose main content extracts to nothing (JS-rendered docs) → error, **no empty snapshot file written**; an existing snapshot is never overwritten without `--refresh`. (test in Task 6)
4. `/enroll` interrupted and re-run → resumes; never overwrites an existing `course.md`, `profile.md`, `program/syllabus.md` or copied PDF. (verification in Task 10)
5. An engine update pulled into a course that has its own content and commits → merges with no conflict. (verification in Task 12)

## Glossary — prototype → engine identifiers

Use these everywhere (code, JSON keys, prompts, tests). Anything not listed: translate literally to English.

| Prototype | Engine |
|---|---|
| `etat`, `travaux`, `travail` | `state`, `work` (dict of items), `item` |
| keys `version inscription rythme_h_jour etapes_faites travaux` | `version enrolled_on` — *(dropped)* — `steps_done work` |
| item keys `id type ue titre sujet cree_le echeance charge_h bloquant coef statut tentatives valide_par` | `id type module title assignment created_on` — *(dropped)* — `hours blocking coef status attempts validated_by` |
| attempt keys `date chemin note criteres correction` | `date path grade criteria feedback` |
| statuses `a_faire rendu corrige fait` | `todo submitted graded done` |
| types `lecon lecture devoir tp partiel-ecrit partiel-oral oral-blanc rattrapage` | `lesson reading homework lab written-exam oral-exam mock-oral resit` |
| sequence keys `id type ue semestre titre` | `id type module semester title` |
| `ErreurScolarite` | `CollegeError` |
| `note_retenue moyenne_ue ues_du_semestre ue_terminee moyenne_semestre` | `best_grade module_average semester_modules module_complete semester_average` |
| `ajouter_travail terminer lier rendre noter etape_faite statut` | `add_work finish link submit grade step_done status` |
| `cahier_de_textes bulletin` | `agenda transcript` |
| status keys `prochaine_etape epreuve_a_passer en_correction bloquants rattrapages_requis peut_avancer fin_de_cursus` | `next_step exam_to_take being_graded blocking resits_required can_advance course_complete` |
| resit id `RA-{ue}` | `RESIT-{module}` |
| env `SCOL_RACINE` | `COLLEGE_ROOT` |

## File Structure

```
.gitignore  requirements.txt  CLAUDE.md  README.md
.claude/agents/   professor.md  designer.md  grader.md
.claude/skills/   lesson/ submit/ ask/ oral/ enroll/   (SKILL.md each)
tools/__init__.py
tools/college.py                 entry point (adds repo root to sys.path, calls cli.main)
tools/scholarship/__init__.py
tools/scholarship/state.py       load/save/init/migrate state.json, CollegeError
tools/scholarship/program.py     load_sequence, load_rules, DEFAULT_RULES, TYPES, EXAMS
tools/scholarship/work.py        work-item lifecycle
tools/scholarship/averages.py    module/semester averages, module completion
tools/scholarship/status.py      computed status view
tools/scholarship/documents.py   AGENDA.md and student/transcript.md
tools/scholarship/cli.py         argparse CLI
tools/extract_pdf.py             PDF → text with page markers + TOC
tools/snapshot_web.py            URL → verbatim Markdown snapshot
tools/tests/  helpers.py test_state.py test_program.py test_work.py test_averages.py
              test_status.py test_documents.py test_cli.py test_snapshot.py test_engine_files.py
templates/    course.md profile.md rules.json decision-record.md
              student/record.md student/office-hours.md student/decision-log.md
```

---

### Task 1: Scaffolding and privacy guard

**Files:**
- Create: `.gitignore`, `requirements.txt`, `tools/__init__.py`, `tools/scholarship/__init__.py`, `tools/tests/__init__.py`
- Create (outside the repo, never committed): `~/college-private-terms.txt`

- [ ] **Step 1: Create branch** `git switch -c engine-v1`.
- [ ] **Step 2: Write `.gitignore`**: `.faculty/`, `resources/books/`, `resources/text/`, `resources/repos/`, `former-projects/`, `.venv/`, `*:Zone.Identifier`, `__pycache__/`, `target/`, `node_modules/`, `.superpowers/`. (Note: `resources/web/` is **not** ignored — snapshots are course content worth versioning.)
- [ ] **Step 3: Write `requirements.txt`**: `pypdf` and `trafilatura` (unpinned major-compatible: `pypdf>=5`, `trafilatura>=2`). Create the venv: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`. If `trafilatura` fails to install on Python 3.14, replace it with `beautifulsoup4` + `markdownify` and adapt Task 6 accordingly; note the substitution in the commit message.
- [ ] **Step 4: Create `~/college-private-terms.txt`**, one case-insensitive pattern per line: the prototype student's first name, last name, GitHub handle, personal website domain, school name, and each former project name — all read from `~/engineer-class/CLAUDE.md` and `~/engineer-class/etudiant/dossier.md`. Use distinctive phrases, never a bare number or common word (e.g. the school as its full two-word name). Verify: `grep -rniIf ~/college-private-terms.txt . --exclude-dir=.git --exclude-dir=.venv` prints nothing.
- [ ] **Step 5: Commit** `git add -A && git commit -m "chore: scaffolding"`.

### Task 2: State and program files

**Files:**
- Create: `tools/scholarship/state.py`, `tools/scholarship/program.py`, `tools/tests/helpers.py`, `tools/tests/test_state.py`, `tools/tests/test_program.py`
- Source to translate: `~/engineer-class/outils/scolarite/etat.py`, `cli.py:_sequence`, `outils/tests/aide.py`, state tests in `outils/tests/test_travaux.py`

**Interfaces:**
- Produces (`state.py`): `class CollegeError(Exception)`; `VERSION = 1`; `MIGRATIONS: dict[int, Callable[[dict], dict]] = {}` (key = version migrated *from*); `init(path: Path, today: date) -> dict`; `load(path: Path) -> dict`; `save(state: dict, path: Path) -> None`.
- Produces (`program.py`): `TYPES = ("reading", "homework", "lab", "written-exam", "oral-exam", "mock-oral", "resit")`; `EXAMS = ("written-exam", "oral-exam")`; `DEFAULT_RULES: dict`; `load_sequence(path: Path) -> list[dict]`; `load_rules(path: Path) -> dict`.
- Produces (`helpers.py`): `D0 = date(2026, 10, 25)`; `class WithState(unittest.TestCase)` (temp dir, `self.root`, `self.path = root/"state"/"state.json"`, `self.state = init(...)`, `self.rules = DEFAULT_RULES`); `SEQUENCE` (prototype `SEQUENCE` translated: modules `M1`, `M2`, exams `EXAM-WRITTEN-S1`, `EXAM-ORAL-S1`); `graded(state, rules, id, type, module, value, today=D0, **kw)` (add with `hours=2`, submit, grade `{"All": [value, 20]}`).

`DEFAULT_RULES` (prototype values, exactly):
```json
{"blocking": ["lab", "written-exam", "oral-exam", "resit"],
 "coefficients": {"lab": 2, "homework": 1, "written-exam": 1, "oral-exam": 1, "resit": 1, "reading": 0, "mock-oral": 0},
 "max_attempts": {"lab": 2, "homework": 2},
 "weights": {"modules": 0.6, "exams": 0.4}}
```
Types absent from `max_attempts` get 1.

- [ ] **Step 1: Port state tests** into `test_state.py`: `test_init_idempotent`, `test_save_then_load`, `test_save_failure_leaves_no_temp`, `test_load_missing_message` (mentions `college.py init`), `test_load_corrupt_message` (mentions `git checkout -- state/state.json`), `test_load_malformed_state`, `test_corruption_message_does_not_promise_git` — translated from their prototype counterparts. Required keys: `version` int, `enrolled_on` str, `steps_done` list, `work` dict.
- [ ] **Step 2: Add migration tests**:
  - `test_newer_version_refused`: write a state with `"version": VERSION + 1`; `load` raises `CollegeError` whose message contains `git pull engine main`.
  - `test_older_version_migrated_and_saved`: patch `state.VERSION` to 2 and `state.MIGRATIONS` to `{1: lambda s: {**s, "extra": True}}` (use `unittest.mock.patch.object`); `load` returns `extra is True`, `version == 2`, and the file on disk now has `"version": 2`.
- [ ] **Step 3: Write program tests** in `test_program.py`:
  - `test_sequence_missing_is_empty`, `test_sequence_malformed` (step missing `semester` → `CollegeError` listing `id, module, semester, title, type`), `test_sequence_invalid_json`.
  - `test_rules_missing_file_gives_defaults` → `load_rules(nonexistent) == DEFAULT_RULES`.
  - `test_rules_partial_override`: file `{"weights": {"modules": 0.5, "exams": 0.5}}` → weights replaced, other keys default.
  - `test_rules_unknown_key_refused`: `{"weight": {...}}` → `CollegeError` containing `weight`.
  - `test_rules_unknown_type_refused`: `{"coefficients": {"tp": 2}}` → error containing `tp`.
  - `test_rules_weights_must_sum_to_one`: `{"weights": {"modules": 0.6, "exams": 0.5}}` → error.
  - `test_rules_negative_coef_refused`, `test_rules_attempts_must_be_positive_int` (`0` and `1.5` refused).
- [ ] **Step 4: Run** `.venv/bin/python -m unittest tools.tests.test_state tools.tests.test_program -v` → FAIL (modules missing).
- [ ] **Step 5: Implement `state.py`** (translate `etat.py`; drop pace; in `load`, after validation: if `version > VERSION` raise; while `version < VERSION` apply `MIGRATIONS[version]`, set `version += 1`; save if anything migrated) **and `program.py`** (`load_sequence` from prototype `_sequence`; `load_rules`: top-level keys replace defaults one by one, then validate: allowed keys, types ⊂ `TYPES`, coefficients finite ≥ 0, attempts int ≥ 1, `blocking` list of types, `abs(modules + exams - 1) < 1e-9`). Return a fresh dict (never mutate `DEFAULT_RULES`).
- [ ] **Step 6: Run** the same command → PASS.
- [ ] **Step 7: Commit** `feat(tool): state with migrations, sequence and rules loading`.

### Task 3: Work-item lifecycle

**Files:**
- Create: `tools/scholarship/work.py`, `tools/tests/test_work.py`
- Source: `~/engineer-class/outils/scolarite/travaux.py`, work tests of `outils/tests/test_travaux.py`

**Interfaces:**
- Consumes: `CollegeError`, `TYPES`, rules dict (Task 2).
- Produces: `SCALE_TOTAL = 20`; `PASS_MARK = 10`; `add_work(state, id, type, module, title, assignment, today, rules, *, hours: float, blocking: bool | None = None, coef: float | None = None, validated_by: str | None = None) -> dict`; `finish(state, id) -> None`; `link(state, reading_id, work_id) -> None`; `submit(state, id, path, today, rules) -> int`; `grade(state, id, criteria: dict, feedback: str) -> float`; `best_grade(item: dict) -> float | None`; `step_done(state, id) -> None`.

- [ ] **Step 1: Port tests** from `test_travaux.py`, renamed per Glossary, passing `rules=DEFAULT_RULES`: `test_add_defaults` (lab → blocking True, coef 2; item has `hours`, `created_on`, status `todo`, no due-date key), `test_add_duplicate_id`, `test_add_override_defaults`, `test_absurd_hours_refused` (0, negative, inf, nan), `test_negative_coef_refused`, `test_unknown_type`, `test_validated_by_refused_outside_reading`, `test_finish_reading`, `test_finish_refuses_non_reading`, `test_link_validates_if_already_passed`, `test_passing_grade_validates_reading`, `test_failing_grade_does_not_validate`, `test_best_grade_without_grade`, `test_grade_valid_rubric`, `test_grade_malformed_criteria`, `test_grade_best_attempt`, `test_grade_refuses_total_not_20`, `test_grade_without_submission`, `test_exam_single_attempt`, `test_submit_unknown_id`, `test_submit_reading_refused`, `test_submit_attempt_number`, `test_submit_refused_while_being_graded`, `test_submit_refuses_third_attempt`, `test_step_done_idempotent`. **Do not port** due-date and pace tests (`test_echeance_*`, `test_changer_rythme*`).
- [ ] **Step 2: Add rules-driven tests**: `test_custom_rules_change_defaults` (rules with `coefficients.lab = 3`, `blocking = []` → new lab has coef 3, blocking False); `test_custom_max_attempts` (`max_attempts.homework = 3` → third homework submission accepted, fourth refused).
- [ ] **Step 3: Run** `.venv/bin/python -m unittest tools.tests.test_work -v` → FAIL.
- [ ] **Step 4: Implement `work.py`** by translating `travaux.py`: `hours` required and finite > 0; blocking default `type in rules["blocking"]`; coef default `rules["coefficients"][type]`; max attempts `rules["max_attempts"].get(type, 1)`; error messages in English, still naming the ID and the reason.
- [ ] **Step 5: Run** → PASS.
- [ ] **Step 6: Commit** `feat(tool): work lifecycle driven by course rules`.

### Task 4: Averages and status

**Files:**
- Create: `tools/scholarship/averages.py`, `tools/scholarship/status.py`, `tools/tests/test_averages.py`, `tools/tests/test_status.py`
- Source: `calculs.py`, `statut.py`, `test_calculs.py`, `test_statut.py`

**Interfaces:**
- Consumes: `best_grade`, `PASS_MARK` (Task 3), `EXAMS` (Task 2).
- Produces: `module_average(state, module) -> float | None`; `semester_modules(sequence, semester) -> list[str]`; `module_complete(state, sequence, module) -> bool`; `semester_average(state, sequence, semester, rules) -> tuple[float | None, bool]`; `status(state, sequence) -> dict` with keys `next_step, exam_to_take, being_graded, blocking, resits_required, can_advance, course_complete`.

- [ ] **Step 1: Port every test** of `test_calculs.py` and `test_statut.py` per Glossary, **except** `test_statut_retard_*` (lateness is gone). `status` takes no date. `test_status_is_pure` keeps checking the state is not mutated.
- [ ] **Step 2: Add** `test_semester_average_uses_rule_weights`: one module at 10, both exams at 20, rules weights `0.5/0.5` → `(15.0, False)`.
- [ ] **Step 3: Run** `.venv/bin/python -m unittest tools.tests.test_averages tools.tests.test_status -v` → FAIL.
- [ ] **Step 4: Implement** by translation; `exam_to_take` = next step's id when its type is in `EXAMS`; resit id `f"RESIT-{module}"`; weights from `rules["weights"]`.
- [ ] **Step 5: Run** → PASS.
- [ ] **Step 6: Commit** `feat(tool): averages and status without due dates`.

### Task 5: Documents and CLI

**Files:**
- Create: `tools/scholarship/documents.py`, `tools/scholarship/cli.py`, `tools/college.py`, `tools/tests/test_documents.py`, `tools/tests/test_cli.py`
- Source: `documents.py`, `cli.py`, `outils/scol.py`, `test_documents.py`, `test_cli.py`

**Interfaces:**
- Consumes: everything from Tasks 2–4.
- Produces: `agenda(state, sequence, today) -> str`; `transcript(state, sequence, rules) -> str`; `main(argv=None) -> int` (exit 0, or 2 on `CollegeError` with `Error: …` on stderr, no traceback). Paths relative to root (`COLLEGE_ROOT` or repo root): `state/state.json`, `program/sequence.json`, `program/rules.json`, `AGENDA.md`, `student/transcript.md`.
- CLI (`python3 tools/college.py …`): `init`; `status [--json]`; `step-done ID`; `add-work --id --type --module --title --assignment --hours [--blocking | --non-blocking] [--coef] [--validated-by] [--if-absent]`; `finish ID`; `link READING WORK`; `submit ID --path P`; `grade ID --criteria JSON --feedback P`; `averages [--json]`; `agenda` (regenerates both documents). Every state-changing command rewrites both documents, as in the prototype.

Agenda layout (English, generated header comment `<!-- Generated by \`python3 tools/college.py agenda\`: do not edit by hand. -->`): `# Agenda`, `*Updated on YYYY-MM-DD.*`, `## To do` table `| Id | Type | Title | Hours | Blocking | Assignment |` in **state insertion order** (else "Nothing to submit right now."), `Being graded: …`, `## Next step` (exam line names `/oral` for `oral-exam`, else `/lesson`; blocked line says `/lesson` is blocked), `## Resits`, `## Recently graded` (5 latest). Transcript: as prototype, headings `## Semester N — average: …`, `### M1`, `### Exams and orals S1`, `## Outside the program`; verdicts `passed` / `not passed`, `(provisional)`, `(in progress)`.

- [ ] **Step 1: Port document tests** (`test_cahier_*` → `test_agenda_*`, `test_bulletin_*` → `test_transcript_*`), dropping `test_cahier_marque_retard` and replacing `test_cahier_trie_par_echeance` with `test_agenda_keeps_creation_order` (add `LAB1.2` then `HW1.1` → `LAB1.2` row appears first) and adding `test_agenda_shows_hours` (`| 4 |` present for `hours=4`).
- [ ] **Step 2: Port CLI tests** (subprocess on `tools/college.py` with `COLLEGE_ROOT` = temp dir), dropping pace: `test_cli_error_without_traceback`, `test_cli_full_cycle` (asserts `AGENDA.md` and `student/transcript.md` exist), `test_cli_business_error_code_2`, `test_cli_invalid_criteria_json`, `test_cli_if_absent`, `test_cli_grade_missing_feedback`, `test_cli_sequence_read`, `test_cli_malformed_sequence`, `test_cli_status_text_exam`, plus `test_cli_averages_json` and `test_cli_rules_file_applied` (write `program/rules.json` with `{"coefficients": {"lab": 3, "homework": 1, "written-exam": 1, "oral-exam": 1, "resit": 1, "reading": 0, "mock-oral": 0}}`, `add-work` a lab, then read `state/state.json` → its coef is 3).
- [ ] **Step 3: Run** `.venv/bin/python -m unittest tools.tests.test_documents tools.tests.test_cli -v` → FAIL.
- [ ] **Step 4: Implement** by translation. `averages` lists modules from lesson steps plus work items whose module starts with `M`.
- [ ] **Step 5: Run the whole suite** → PASS. Also `python3 tools/college.py --help` works with the system `python3` (no venv).
- [ ] **Step 6: Commit** `feat(tool): agenda, transcript and CLI`.

### Task 6: Source tools — PDF extraction and web snapshots

**Files:**
- Create: `tools/extract_pdf.py`, `tools/snapshot_web.py`, `tools/tests/test_snapshot.py`
- Source: `~/engineer-class/outils/extraire_pdf.py`

**Interfaces:**
- Produces: `extract(pdf: Path, out_dir: Path, slug: str) -> None` (translation; TOC file header in English; when no outline: `*No outline in this PDF: rebuild the TOC from the text's headings (see /enroll).*`). Usage: `.venv/bin/python -I tools/extract_pdf.py <pdf> resources/text <slug>`.
- Produces: `to_markdown(html: str, url: str, retrieved_on: date) -> str` (raises `ValueError` if the extracted body is empty or whitespace); `write_snapshot(root: Path, topic: str, name: str, content: str, refresh: bool = False) -> Path` (writes `resources/web/<topic>/<name>.md`; raises `FileExistsError` if it exists and not `refresh`). CLI: `.venv/bin/python -I tools/snapshot_web.py <url> <topic> <name> [--refresh]`, exit 2 with a one-line message on fetch failure, empty extraction or existing file.
- Snapshot format: first lines `<!-- source: <url> -->`, `<!-- retrieved: YYYY-MM-DD -->`, blank line, then the Markdown body from `trafilatura.extract(html, output_format="markdown", include_formatting=True, include_links=True, include_tables=True)`. Fetch with `trafilatura.fetch_url(url)`.

- [ ] **Step 1: Write tests** (no network): `test_markdown_has_header_and_code` (HTML with an `<h1>`, a paragraph of ≥ 3 sentences and a `<pre><code>x = 1</code></pre>` → output starts with the two header comments and contains `x = 1`); `test_empty_page_raises` (`<html><body><script>app()</script></body></html>` → `ValueError`); `test_write_creates_topic_dir`; `test_existing_snapshot_not_overwritten` (`FileExistsError`, file content unchanged); `test_refresh_overwrites`; `test_empty_page_writes_nothing` (CLI-level function path: after the `ValueError`, `resources/web/<topic>/` contains no file — exercise via a `main(argv, fetch=...)` seam that accepts a fake fetcher).
- [ ] **Step 2: Run** `.venv/bin/python -m unittest tools.tests.test_snapshot -v` → FAIL.
- [ ] **Step 3: Implement** both scripts (`snapshot_web.main(argv=None, fetch=trafilatura.fetch_url) -> int`).
- [ ] **Step 4: Run** → PASS. Manual smoke test: `.venv/bin/python -I tools/snapshot_web.py https://modelcontextprotocol.io/docs/getting-started/intro mcp intro` in a scratch copy (`/tmp` dir with `COLLEGE_ROOT`-style cwd), then delete the output. Extract one real PDF into a scratch dir and check `=== page` markers appear.
- [ ] **Step 5: Commit** `feat(tools): PDF extraction and web snapshots`.

### Task 7: CLAUDE.md, templates and engine-file checks

**Files:**
- Create: `CLAUDE.md`, `templates/course.md`, `templates/profile.md`, `templates/rules.json`, `templates/decision-record.md`, `templates/student/record.md`, `templates/student/office-hours.md`, `templates/student/decision-log.md`, `tools/tests/test_engine_files.py`
- Source: `~/engineer-class/CLAUDE.md`, `etudiant/dossier.md`, `etudiant/permanence.md`, `etudiant/journal-adr.md`, `travail/TP1.1/ADR-001.md`

**Interfaces:**
- Produces: the shared contract every prompt relies on — paths, IDs, roles, and the `course.md` section headings below (agents refer to them by name).

`CLAUDE.md` (English, short): first lines `@course.md` and `@profile.md` (imports); then sections **Roles and who reads what** (prototype table translated: professor `/lesson` never reads `.faculty/`; designer writes it; grader reads rubrics; TA `/ask` never; examiner `/oral` only `.faculty/oral-guides/<id>-guide.md`), **Language** (engine names English; student-facing content in the teaching language of `course.md`), **Scholarship rules** (blocking/attempts/coefficients/weights come from `program/rules.json`, defaults in `templates/rules.json`; fixed: 20 points, pass mark 10, resit when a completed module < 10, module average = max(average, resit); a reading linked with `validated_by` is validated when that work is graded ≥ 10; no due dates), **IDs and paths** (§4.3 table plus: lessons `lessons/M<n>/L<n>.<nn>-<slug>.md`, assets `lessons/M<n>/assets/`; assignments `assignments/<M<n>|S<n>>/<id>/assignment.md`; student copy `work/<id>/`; feedback `feedback/<id>-v<k>.md`; rubrics `.faculty/rubrics/<id>.md`, hidden tests `.faculty/rubrics/<id>-tests/`; oral guides `.faculty/oral-guides/<id>-guide.md`; transcripts `student/orals/<id>.md`; program `program/`; sources `resources/`), **State tool** (subcommands; never edit `state/state.json` by hand; every command ends with a local commit, never push), **Tests** (command above). The prototype's student description and toolchains go nowhere here (they belong in `profile.md` / `course.md`).

`templates/course.md` — sections, each with a one-line instruction comment for `/enroll`: `# <Course title>`, `## Subject and professor role`, `## Teaching language`, `## Student goal and target job`, `## Starting point`, `## Decision record` (name, template path, frequency, log file), `## Lab formats and execution policy`, `## Oral format`, `## Former projects`, `## Special rules`, `## Toolchains`.
`templates/profile.md` — `# Student profile`, `## Background`, `## Memory` (pre-filled: "The system keeps all state; nothing is assumed remembered between sessions; former projects are never assumed known."), `## Career goal`, `## Pace`.
`templates/rules.json` = `DEFAULT_RULES`. `templates/decision-record.md` = ADR template (Title, Status, Context, Decision, Alternatives considered, Consequences). Student files = prototype structures translated (`# Student record` with `## Profile`, `## Strengths`, `## Recurring weaknesses`, `## To review` table `| Concept | Lesson | Seen on | Last reviewed | Missed? |`; office-hours table `| Date | Work | Question (summary) | Hint level reached (1-3) | Concept |`; decision log `| Work | Record | Decision | Grade |`) — empty, no personal content.

- [ ] **Step 1: Write `test_engine_files.py`**: `test_templates_rules_equal_defaults` (`json.load(templates/rules.json) == DEFAULT_RULES`); `test_claude_md_imports_course_files` (first two non-empty lines are `@course.md`, `@profile.md`); `test_agents_run_on_sonnet` (every `.claude/agents/*.md` frontmatter has `model: sonnet`; passes vacuously until Task 8); `test_skills_have_frontmatter` (every `.claude/skills/*/SKILL.md` has `name:` equal to its folder and a `description:`); `test_no_subject_obligations` — engine files (`CLAUDE.md`, `.claude/**`, `tools/**/*.py` except this test, `README.md`) contain none of: `refactoring.guru`, `scol.py`, `outils/`, `etudiant/`, `.enseignants`, `UE1`, `génie`, `cursus`, `/cours`, `/rendu`, `/question` (case-insensitive).
- [ ] **Step 2: Run** `.venv/bin/python -m unittest tools.tests.test_engine_files -v` → FAIL.
- [ ] **Step 3: Write** `CLAUDE.md` and the templates as specified.
- [ ] **Step 4: Run** → PASS; run the private-terms grep (Task 1 Step 4) → nothing.
- [ ] **Step 5: Commit** `feat: shared contract and course templates`.

### Task 8: Agents — professor, designer, grader

**Files:**
- Create: `.claude/agents/professor.md`, `.claude/agents/designer.md`, `.claude/agents/grader.md`
- Source: `~/engineer-class/.claude/agents/professeur.md`, `concepteur.md`, `correcteur.md`

Rule for this task and the next two: **translate every sentence faithfully**, then apply only these substitutions (spec §7). Keep section order and every prohibition. Each agent's opening says: read `CLAUDE.md` (which imports `course.md` and `profile.md`) before anything; write student-facing files in the teaching language of `course.md`.

| Prototype content | Replace with |
|---|---|
| "professor of software engineering", student description | "You are the professor described in `course.md` § Subject and professor role"; student from `profile.md` |
| code example languages, lab languages per module | `course.md` § Lab formats and execution policy |
| "every TP requires an ADR", ADR template | the decision record from `course.md` § Decision record (template path given there; default `templates/decision-record.md`) |
| `etudiant/journal-adr.md` | the decision log named in `course.md` (default `student/decision-log.md`) |
| refactoring.guru via WebFetch | web sources from `program/sources.md`: read snapshots in `resources/web/` first; when a needed page is missing or a newer version matters, snapshot it with `tools/snapshot_web.py` and cite "<site> docs, *<page>*, retrieved <date>" (§8.2) |
| *(new, designer)* | labs pin tool versions (e.g. `requirements.txt`) so code matches the snapshots used; code repositories from `sources.md` are cloned on demand into `resources/repos/` |
| former projects of the prototype student's GitHub account | `course.md` § Former projects (clone into `former-projects/<repo>`) |
| "Rust/TS/Python", "SQL in UE4", "backend in Rust" | removed |
| example rubric "Conception /6, ADR /4…" | neutral example "Design /6, Decision record /4, Tests /4, Clarity /3, Course questions /3 (e.g. for a lab)" |
| "check the code compiles (`cargo build`, `npx tsx`…)" | "check provided material runs according to `course.md` § Lab formats and execution policy, including starting required services" |
| grader "run the code" | run it per the execution policy; if a prerequisite is unavailable, report `CANNOT GRADE: <reason>` and grade nothing |
| `IMPOSSIBLE DE CORRIGER` | `CANNOT GRADE:` |
| "En entretien" box | "In an interview" box (kept; written in the teaching language) |
| all paths, IDs, commands, JSON keys | §4.3 names and Glossary (`add-work --hours`, `grade --criteria --feedback`, report keys `lesson`, `work[{id,type,module,title,assignment,hours,brief}]`, `readings[{id,title,module,source,pages,hours,validated_by}]`) |

Additionally: professor `syllabus` mode reads `course.md` § Starting point and applies its pacing to early lessons; lesson-history reading stays (previous lessons, 3 latest feedback files, record, office hours).

- [ ] **Step 1: Write the three agents.**
- [ ] **Step 2: Verify**: `.venv/bin/python -m unittest tools.tests.test_engine_files -v` → PASS; for each prototype agent, list its `##` headings and check each has a counterpart (`grep -n '^##' ~/engineer-class/.claude/agents/professeur.md .claude/agents/professor.md`); private-terms grep → nothing.
- [ ] **Step 3: Commit** `feat: generic professor, designer and grader agents`.

### Task 9: Skills — /lesson, /submit, /ask, /oral

**Files:**
- Create: `.claude/skills/lesson/SKILL.md`, `.claude/skills/submit/SKILL.md`, `.claude/skills/ask/SKILL.md`, `.claude/skills/oral/SKILL.md`
- Source: `~/engineer-class/.claude/skills/{cours,rendu,question,oral}/SKILL.md`

Same translation rule and substitution table as Task 8, plus:
- `/lesson`: remove every due-date mention (announce workload and blocking status instead of "échéance"); late-work line removed; still stops on `resits_required`, then `blocking`, then `course_complete`; resumption logic kept; commit `lesson: <id>`.
- `/submit`: commit `submit: <id> v<k>`; "a reading done" path uses `finish`.
- `/ask`: hint ladder, prohibitions and exam-period rule unchanged; book citation example becomes neutral ("*<full book title>* ch. 5, p. 44–54"); commit `office-hours: <id or lesson>`.
- `/oral`: the examiner persona comes from `course.md` § Oral format (recruiter-style technical interview if absent); mock orals `MOCK-ORAL-<YYYYMMDD>`; commit `oral: <id>`.

- [ ] **Step 1: Write the four skills.**
- [ ] **Step 2: Verify** as in Task 8 Step 2 (tests, heading counterparts, private-terms grep), plus `grep -rniE 'due|late|deadline|échéance' .claude/skills` → nothing.
- [ ] **Step 3: Commit** `feat: generic lesson, submit, ask and oral skills`.

### Task 10: /enroll skill

**Files:**
- Create: `.claude/skills/enroll/SKILL.md`

Implements spec §9 in the main session (interactive). Required content:
- Opening: refuse to run inside the engine repository itself — if `git remote get-url origin` ends with `Personal-College.git` and no `engine` remote exists, explain the §4.2 clone procedure and stop.
- Step 0: ensure `.venv` with `requirements.txt` installed.
- Steps 1–6 as in §9, each beginning with an existence check and skipping when its output exists: PDFs copied only if `resources/books/<name>` is absent; extraction only if `resources/text/<slug>.txt` is absent; `program/sources.md`, `course.md`, `profile.md`, `program/syllabus.md`, `program/sequence.json`, `state/state.json` never overwritten (offer to edit instead).
- Slugs: short, lowercase, hyphenated, unique; never shown to the student (citation rules as in the prototype `programme/sources.md`, translated — copy that method section into the generated `program/sources.md`).
- TOC rebuild for outline-less PDFs: grep heading candidates (`^(Chapter|CHAPTER|Part|PART)\b`, numbered `^\d+(\.\d+)*\s+[A-Z]`, all-caps short lines) in `resources/text/<slug>.txt`, confirm by reading around each hit, write `<slug>.toc.md` in the extractor's format, and flag "TOC rebuilt from text" in `sources.md`.
- Web catalogue: each link → topic + kind (`official docs`, `tutorial`, `code repository`, `student-only course`); no snapshots at enrollment (professor snapshots on demand).
- Optional intake notes file: read it first and only ask what it leaves open; it is copied to `docs/enrollment-notes.md` in the course.
- Interview: one question at a time, in the student's language; produces `course.md` from `templates/course.md`, `profile.md` from `templates/profile.md` (or copied from a path the student gives), `program/rules.json` only if the student changes a default.
- Structure validation (step 4) is mandatory before launching `professor` in `syllabus` mode (pass it the approved structure, `course.md` and the sources).
- Step 6: `python3 tools/college.py init`, copy `templates/student/*` into `student/` if absent, `python3 tools/college.py agenda`, `git add -A && git commit -m "enroll: <course>"`, announce `/lesson`.

- [ ] **Step 1: Write the skill.**
- [ ] **Step 2: Dry-run review** — walk the skill against Review Focus 4: for each step, name the file that proves it already ran and confirm the skill checks it. Fix any step without a check. Run the engine-file tests and private-terms grep.
- [ ] **Step 3: Commit** `feat: /enroll skill`.

### Task 11: README

**Files:**
- Create: `README.md`
- Source: `~/engineer-class/LISEZMOI.md` (structure), spec §4

Sections: what it is (anonymous origin story from spec §1, two sentences); requirements (Claude Code, Python 3.14+, git, optional Docker); **create a course** (exact commands: `git clone <engine url> my-course && cd my-course && git remote rename origin engine && git remote add origin <your private repo>` (optional) `&& python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && claude` then `/enroll`); **update the engine** (`git pull engine main`; never edit engine-owned files — list them); **commands** table (`/lesson`, `/submit <folder>`, `/ask <question>`, `/oral [id]`, `/enroll`, "I finished reading RD1.1"); **where things are** table (AGENDA.md first, transcript, lessons, assignments, work, feedback, decision log, syllabus); **rules** (attempts, no due dates, resits, semester formula from rules, `.faculty/` is off-limits); **a typical day**. No licence text (owner's decision).

- [ ] **Step 1: Write README.md.**
- [ ] **Step 2: Verify**: engine-file tests pass; every command and path in the README exists in §4.3 / CLAUDE.md; private-terms grep → nothing.
- [ ] **Step 3: Commit** `docs: README`.

### Task 12: Acceptance checks

No new files in the repo.

- [ ] **Step 1: Full suite** `.venv/bin/python -m unittest discover -s tools/tests -t .` → all pass.
- [ ] **Step 2: Conflict-free update** (scratch, outside the repo): `git clone ~/Personal-College /tmp/pc-course && cd /tmp/pc-course && git switch engine-v1 && git remote rename origin engine`; create course-owned files (`course.md`, `profile.md`, `program/sequence.json` with two lessons, run `python3 tools/college.py init` and one `add-work`), commit. In `~/Personal-College` on `engine-v1`, make a dummy commit touching `README.md` and `.claude/skills/lesson/SKILL.md`. In `/tmp/pc-course`: `git pull engine engine-v1` → merge without conflict; `python3 tools/college.py status` still works. Then `git -C ~/Personal-College reset --hard HEAD~1` to drop the dummy commit and `rm -rf /tmp/pc-course`.
- [ ] **Step 3: Prototype untouched**: `git -C ~/engineer-class status --short` → empty, and `git -C ~/engineer-class log --since=2026-10-25 --format=%s` shows no commit from this work (the student's own `lesson`/`submit`-style commits in French are fine).
- [ ] **Step 4: Privacy and neutrality**: private-terms grep → nothing; `test_no_subject_obligations` passes; `grep -rn 'model:' .claude/agents` → three `model: sonnet`.
- [ ] **Step 5: Report** to the owner: test count, the update check result, and that nothing was pushed. Do not merge `engine-v1` into `main` or push without the owner's go-ahead (use superpowers:finishing-a-development-branch).

The real first enrollment (applied AI, from the owner's private intake notes) is the next project and the engine's acceptance test (§10.6); it is not part of this plan.
