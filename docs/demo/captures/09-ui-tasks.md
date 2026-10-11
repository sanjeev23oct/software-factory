# Tasks: Show which tasks are overdue

Resolves the two open "Needs clarification" items so the build is deterministic:

- **"Today"**: the browser's local date, as `YYYY-MM-DD` (`new Date().toLocaleDateString('en-CA')`), computed once per `draw()` call and threaded through every function that needs it.
- **Due date display**: the raw stored string, shown as-is, matching `visual-spec.md`.

## Section 1 — Data

Satisfies: AC 5.1, AC 5.2, AC 5.3

- [x] 1.1 `data/tasks.json` shows every due-date case                 → run: `/build-ui`
  - [x] 1.1.1 task `id: 1` ("Renew the domain", `done: false`) gets `"due": "2020-01-01"` — overdue, and stays overdue for the life of this sample data
  - [x] 1.1.2 task `id: 3` ("Book the venue", `done: false`) gets `"due": "2099-12-31"` — far enough in the future to never become overdue
  - [x] 1.1.3 task `id: 2` ("Send the invoice", `done: true`) is left with no `due` field at all
  - [x] 1.1.4 keep the file's existing one-task-per-line formatting; change nothing else about the three tasks

### 1.X — Gate

> **CHECKER (Cat 1):** every check in `loop/1-data-checker.md` returns its EXPECTED value.
> **CHECKER (Cat 2):** write `evidence/1-data-gate.md` as a tick sheet.
> **CHECKER (Cat 3):** run `node --test`; EXPECTED: all pass (no existing test reads `due`, so nothing regresses).

## Section 2 — Logic (`src/board.js`)

Satisfies: AC 2.1, AC 2.2, AC 2.3, AC 2.4, AC 2.5, AC 3.1, AC 3.3, AC 4.1, AC 4.2, AC 4.3

- [x] 2.1 `isOverdue(task, today)`                                    → run: `/build-ui`
  - [x] 2.1.1 exported pure function in `src/board.js`; returns `true` exactly when `task.done === false` AND `task.due` is set (not `undefined`/`null`) AND `task.due < today` (plain string comparison — both are `YYYY-MM-DD`)
  - [x] 2.1.2 a task with no `due` field, or `done: true`, or `due >= today`, returns `false`
- [x] 2.2 `summary(tasks, today)` gains an `overdue` count            → run: `/build-ui`
  - [x] 2.2.1 returned object gains an `overdue` key: the count of tasks for which `isOverdue(task, today)` is `true`
  - [x] 2.2.2 `total`, `done`, `open` keep their current values and meaning
- [x] 2.3 `visibleTasks(tasks, filter, today)` gains the `'overdue'` filter → run: `/build-ui`
  - [x] 2.3.1 `filter === 'overdue'` returns `tasks.filter((task) => isOverdue(task, today))`
  - [x] 2.3.2 the existing `'open'`, `'done'` and default (`'all'`) branches are unchanged

### 2.X — Gate

> **CHECKER (Cat 1):** every check in `loop/2-logic-checker.md` returns its EXPECTED value.
> **CHECKER (Cat 2):** write `evidence/2-logic-gate.md` as a tick sheet.
> **CHECKER (Cat 3):** run `node --test`; EXPECTED: all pass.

## Section 3 — UI (`src/render.js`, `src/main.js`, `index.html`, `styles.css`)

Satisfies: AC 1.1, AC 1.2, AC 1.3, AC 2.1, AC 2.2, AC 2.3, AC 2.4, AC 2.5, AC 3.1, AC 3.2, AC 4.1, AC 4.2, AC 4.3, AC 4.4

- [x] 3.1 `renderTask(task, today)` renders the due date and the overdue flag → run: `/build-ui`
  - [x] 3.1.1 imports `isOverdue` from `./board.js`
  - [x] 3.1.2 no `due` field (or `due: null`): markup identical, character for character, to today's output (AC 1.3)
  - [x] 3.1.3 has `due`: adds `<span class="due" data-testid="due-${task.id}">${escapeHtml(task.due)}</span>` right after the title span (AC 1.1)
  - [x] 3.1.4 `isOverdue(task, today)` is `true`: the `<li>`'s class becomes `task ${state} overdue`, and a `<span class="overdue-flag" data-testid="overdue-${task.id}">Overdue</span>` is added right after the due span (AC 2.1); otherwise neither is added (AC 2.2–2.5)
- [x] 3.2 `renderList(tasks, today)` threads `today` through           → run: `/build-ui`
  - [x] 3.2.1 calls `renderTask(task, today)` for every item; the empty-state branch is unchanged
- [x] 3.3 `renderSummary({ total, done, open, overdue })`              → run: `/build-ui`
  - [x] 3.3.1 text becomes exactly `` `${open} open · ${done} done · ${total} total · ${overdue} overdue` ``, the `overdue` segment always present, never omitted (AC 3.1, 3.2)
- [x] 3.4 "Overdue" filter button                                    → run: `/build-ui`
  - [x] 3.4.1 append `<button type="button" data-filter="overdue" data-testid="filter-overdue">Overdue</button>` to `.filters` in `index.html`, after the Done button (AC 4.1)
- [x] 3.5 wire `src/main.js`                                          → run: `/build-ui`
  - [x] 3.5.1 inside `draw()`, compute `const today = new Date().toLocaleDateString('en-CA');`
  - [x] 3.5.2 call `summary(tasks, today)`, `visibleTasks(tasks, filter, today)` and pass `today` into `renderList(...)` (AC 3.3, 4.2, 4.3)
- [x] 3.6 `.due` / `.overdue-flag` styles                             → run: `/build-ui`
  - [x] 3.6.1 add `.task .due` and `.task .overdue-flag` rules to `styles.css` per `visual-spec.md` § Styling; the overdue signal is the word "Overdue" itself, never colour alone (AGENTS.md)

### 3.X — Gate

> **CHECKER (Cat 1):** every check in `loop/3-ui-checker.md` returns its EXPECTED value.
> **CHECKER (Cat 2):** write `evidence/3-ui-gate.md` as a tick sheet.
> **CHECKER (Cat 3):** run `node --test`; EXPECTED: all pass.

## Section 4 — Tests

Satisfies: every acceptance criterion and correctness property in `requirements.md`

- [x] 4.1 `test/board.test.js` covers `isOverdue`, `summary`, `visibleTasks` → run: `/build-tests`
  - [x] 4.1.1 `isOverdue`: not done + due in the past → `true`; not done + due today → `false`; not done + due in the future → `false`; done + due in the past → `false`; no `due` field → `false` (AC 2.1–2.5, correctness properties)
  - [x] 4.1.2 `summary`: `overdue` count matches the number of overdue tasks, independent of `total`/`done`/`open` (AC 3.1)
  - [x] 4.1.3 `visibleTasks(tasks, 'overdue', today)` returns only overdue tasks (AC 4.1–4.3)
- [x] 4.2 `test/render.test.js` covers `renderTask`, `renderList`, `renderSummary` → run: `/build-tests`
  - [x] 4.2.1 `renderTask`: no `due` → markup matches today's output exactly (AC 1.3); has `due`, not overdue → `.due` span present, no `.overdue-flag` (AC 1.1, 2.2, 2.3); overdue → `.due` span, `.overdue-flag` span and `overdue` class all present (AC 2.1); done task with a past `due` → no `overdue` class, no `.overdue-flag` (AC 2.4)
  - [x] 4.2.2 `renderSummary` includes the `overdue` segment, including when it is `0` (AC 3.1, 3.2)

