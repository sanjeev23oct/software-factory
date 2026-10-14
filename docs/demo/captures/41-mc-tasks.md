> **Maker and checker.** Each task is built by a maker, using the skill named on the task.
> A checker then verifies the section in a separate session: it did not see the maker work,
> it runs the gate against what was built, and it alone writes the evidence.
> Nothing is ticked until the checker's evidence says PASS.

## Section 1 — Logic (`src/board.js`)

Satisfies: AC 1.1, AC 1.2, AC 1.4, AC 2.1, AC 2.2, AC 3.1, AC 3.2

- [x] 1.1 `dueText(task, today)` in `src/board.js`  → run: `/build-ui-logic`
  - [x] 1.1.1 given a task with no `due` property (or `due: null`/`undefined`), returns `null`
  - [x] 1.1.2 given a task whose `due` equals `today` (both `"YYYY-MM-DD"` strings), returns exactly `due today`
  - [x] 1.1.3 given a task with `due: "2026-11-03"` and a `today` that is not `"2026-11-03"`, returns exactly `due 3 Nov` (day of month with no leading zero, a space, a three-letter month abbreviation, no year)
  - [x] 1.1.4 the day-of-month and month come from parsing the `due` string's own `"YYYY-MM-DD"` components (e.g. splitting on `-`), never from constructing a `Date` and reading timezone-shifted fields, so the result does not change with the caller's local timezone
  - [x] 1.1.5 does not modify `summary`, `visibleTasks`, or `sortTasks`; their existing behavior is unchanged

### 1.X — Gate

> **CHECKER (Cat 1):** every check in `loop/logic-checker.md` returns its EXPECTED value.
> **CHECKER (Cat 2):** write `evidence/1-logic-gate.md` as a tick sheet.
> **CHECKER (Cat 3):** run `node --test`; EXPECTED: all pass.

## Section 2 — View (`src/render.js`)

Satisfies: AC 1.3, AC 1.4, AC 1.5, AC 2.1

- [x] 2.1 `renderTask(task, today)` in `src/render.js` imports and uses `dueText` from `./board.js`  → run: `/build-ui-view`
  - [x] 2.1.1 when `dueText(task, today)` is non-`null`, adds `<span class="due" data-testid="due-${task.id}">${escapeHtml(dueText(task, today))}</span>` inside the `<li>`, after the title span, so it sits next to the title (AC 1.3, AC 1.5)
  - [x] 2.1.2 when `dueText(task, today)` is `null`, adds no due element at all, and the rest of the markup (`data-testid="task-<id>"`, the mark, the title) is byte-for-byte identical to today's output for that task (AC 1.4)
  - [x] 2.1.3 the due text passes through `escapeHtml` like every other piece of task text
- [x] 2.2 `renderList(tasks, today)` threads `today` through to every call of `renderTask`  → run: `/build-ui-view`
  - [x] 2.2.1 the empty-state branch (`data-testid="empty"`) is unchanged

### 2.X — Gate

> **CHECKER (Cat 1):** every check in `loop/view-checker.md` returns its EXPECTED value.
> **CHECKER (Cat 2):** write `evidence/2-view-gate.md` as a tick sheet.
> **CHECKER (Cat 3):** run `node --test`; EXPECTED: all pass.

## Section 3 — Page (`src/main.js`, `data/tasks.json`, `styles.css`)

Satisfies: AC 2.2, AC 3.2, AC 4.1, AC 4.2

- [x] 3.1 Compute `today` once per `draw()` call in `src/main.js` and pass it to `renderList(...)`  → run: `/build-ui-page`
  - [x] 3.1.1 `today` is a `"YYYY-MM-DD"` string derived from UTC date components (e.g. `new Date().toISOString().slice(0, 10)`), never from local-timezone components (AC 3.2)
  - [x] 3.1.2 the same `today` value is used for every task rendered in that call, so no two same-dated tasks in one render disagree on "due today" (AC 2.2)
  - [x] 3.1.3 the existing wiring of `#tasks`, `#summary`, and the filter buttons' `aria-pressed` and click handling is unchanged
- [x] 3.2 `data/tasks.json` demonstrates all three due states  → run: `/build-ui-page`
  - [x] 3.2.1 task `id: 1` ("Renew the domain", `done: false`) gets a `due` value in the future relative to when the file is read (AC 4.1)
  - [x] 3.2.2 task `id: 3` ("Book the venue", `done: false`) gets a `due` value equal to today's date on the day this spec is implemented, so it renders as "due today" (AC 4.1)
  - [x] 3.2.3 task `id: 2` ("Send the invoice", `done: true`) keeps no `due` field at all (AC 4.1)
  - [x] 3.2.4 every task's `id`, `title`, and `done` fields are unchanged; only `due` fields are added (AC 4.2)
  - [x] 3.2.5 keeps the file's existing one-task-per-line formatting
- [x] 3.3 Add a `.task .due` style to `styles.css`, using the existing colour variables (e.g. `--muted`)  → run: `/build-ui-page`

### 3.X — Gate

> **CHECKER (Cat 1):** every check in `loop/page-checker.md` returns its EXPECTED value.
> **CHECKER (Cat 2):** write `evidence/3-page-gate.md` as a tick sheet.
> **CHECKER (Cat 3):** run `node --test`; EXPECTED: all pass.

## Section 4 — Tests (`test/*.js`)

Satisfies: AC 1.1, AC 1.2, AC 1.3, AC 1.4, AC 1.5, AC 2.1, AC 2.2, AC 3.1, AC 3.2, AC 4.1, AC 4.2, all correctness properties

- [x] 4.1 Tests for `dueText(task, today)` in `test/board.test.js`  → run: `/build-tests`
  - [x] 4.1.1 covers: no `due` → `null`; `due` equal to `today` → `due today`; `due: "2026-11-03"` with a different `today` → `due 3 Nov`; a second month/day combination (e.g. `due: "2026-01-09"`) → `due 9 Jan`, to show the result is derived from the string's own components and not a `Date` conversion
- [x] 4.2 Tests for `renderTask`/`renderList` in `test/render.test.js`  → run: `/build-tests`
  - [x] 4.2.1 covers: a task with a future `due` renders a `due-<id>` span with the formatted text; a task with `due` equal to `today` renders `due today`; a task with no `due` renders no `due-<id>` element and markup identical to the no-due-date case; due text containing HTML-sensitive characters is escaped; the empty-state and existing `renderSummary` tests continue to pass unchanged
