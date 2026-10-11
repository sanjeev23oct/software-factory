# Tasks: Find a task by typing

Resolves the three open "Needs clarification" items so the build is deterministic:

- **"Nothing matches" wording**: reuse the existing generic empty-state markup and text unchanged — `<li class="empty" data-testid="empty">Nothing here.</li>` — for both the pre-existing "filter has no tasks" case and the new "search has no matches" case, per AC 3.1's own assumption. No new copy is added.
- **Whitespace in the search box**: matched literally, not trimmed. The ACs describe a plain substring check (AC 1.2–1.4) and no AC calls for trimming; trimming would be behavior the spec does not ask for.
- **Label/placeholder**: the input gets `placeholder="Search tasks"` as a visible hint and `aria-label="Search tasks"` for assistive tech, matching the existing `.filters` group's use of `aria-label`. No separate visible `<label>` element is added.

## Section 1 — Logic (`src/board.js`)

Satisfies: AC 1.2, AC 1.3, AC 1.4, AC 1.5, AC 2.1, AC 2.2, AC 2.3, AC 2.5, and the correctness properties on substring matching, empty search, and search-combines-with-filter

- [x] 1.1 `matchesSearch(task, search)`                                → run: `/build-ui`
  - [x] 1.1.1 new exported pure function in `src/board.js`: returns `true` when `task.title.toLowerCase()` contains `search.toLowerCase()` as a substring (AC 1.3, 1.4); considers `title` only, no other field (correctness property)
  - [x] 1.1.2 a falsy or empty `search` (`''`, `undefined`) returns `true` for every task, imposing no restriction (AC 1.5, correctness property)
- [x] 1.2 `visibleTasks(tasks, filter, search)` gains the search parameter → run: `/build-ui`
  - [x] 1.2.1 new third parameter `search`, defaulting to `''`; the existing `'open'`, `'done'` and default/`'all'` branches are unchanged and are applied first, exactly as today (AC 2.1–2.3)
  - [x] 1.2.2 the status-filtered result is further filtered by `matchesSearch(task, search)`, so a task is returned only when it satisfies both the status filter and the search term (AC 2.1, 2.2, 2.3, 2.5, correctness property "visible only if satisfies both")

### 1.X — Gate

> **CHECKER (Cat 1):** every check in `loop/1-logic-checker.md` returns its EXPECTED value.
> **CHECKER (Cat 2):** write `evidence/1-logic-gate.md` as a tick sheet.
> **CHECKER (Cat 3):** run `node --test`; EXPECTED: all pass.

## Section 2 — UI (`index.html`, `src/main.js`)

Satisfies: AC 1.1, AC 2.4, AC 3.1, AC 3.2, AC 4.1, AC 4.2, and the correctness property that search never changes the summary or the active filter button

- [x] 2.1 search input in `index.html`                                 → run: `/build-ui`
  - [x] 2.1.1 add `<input type="text" id="search" data-testid="search" placeholder="Search tasks" aria-label="Search tasks">` inside `<main>`, after the `.filters` group and before `<ul id="tasks">` (AC 1.1)
  - [x] 2.1.2 the three filter buttons and `<ul id="tasks">` are otherwise unchanged
- [x] 2.2 wire `src/main.js`                                           → run: `/build-ui`
  - [x] 2.2.1 add `let search = '';` module-level state alongside the existing `let filter = 'all';`
  - [x] 2.2.2 add an `input` event listener on the search box that sets `search` to the input's current value and calls `draw()`
  - [x] 2.2.3 inside `draw()`, call `visibleTasks(tasks, filter, search)` in place of today's `visibleTasks(tasks, filter)` (AC 2.1–2.3, 2.5)
  - [x] 2.2.4 the filter buttons' click handler and `aria-pressed` wiring are unchanged: clicking a filter button only reassigns `filter` and calls `draw()`; it never reads or resets `search` (AC 2.4)
  - [x] 2.2.5 `draw()`'s call to `summary(tasks)` is unchanged: it keeps receiving the full, unfiltered `tasks` array, never `search`-filtered (AC 4.1, 4.2)
  - [x] 2.2.6 the search box's raw value is only ever read into the `search` variable and passed to `visibleTasks`; it is never written into `list.innerHTML` or any other markup (correctness property on escaping — only task titles pass through `escapeHtml`)

### 2.X — Gate

> **CHECKER (Cat 1):** every check in `loop/2-ui-checker.md` returns its EXPECTED value.
> **CHECKER (Cat 2):** write `evidence/2-ui-gate.md` as a tick sheet.
> **CHECKER (Cat 3):** run `node --test`; EXPECTED: all pass.

## Section 3 — Tests

Satisfies: every acceptance criterion and correctness property in `requirements.md`

- [x] 3.1 `test/board.test.js` covers `matchesSearch` and the new `visibleTasks` behavior → run: `/build-tests`
  - [x] 3.1.1 `matchesSearch`: case-insensitive match both ways — `search: "MILK"` against `title: "Buy milk"` is `true`, and `search: "milk"` against `title: "Buy MILK"` is `true` (AC 1.3); substring (not whole-word) match — `search: "ilk"` against `title: "Buy milk"` is `true` (AC 1.4); a non-matching substring is `false`; an empty `search` is `true` for every task (AC 1.5)
  - [x] 3.1.2 `visibleTasks(tasks, 'open', search)` excludes a done task whose title matches the search term (AC 2.1); `visibleTasks(tasks, 'done', search)` excludes a not-done task whose title matches (AC 2.2); `visibleTasks(tasks, 'all', search)` returns both done and not-done matches (AC 2.3)
  - [x] 3.1.3 `visibleTasks(tasks, filter, '')` (or no third argument) returns exactly what `visibleTasks(tasks, filter)` returns today, for each of `'all'`, `'open'`, `'done'` (AC 1.5, 2.5 at the logic level)
  - [x] 3.1.4 a search term matching no task under the active filter returns `[]` (AC 3.1, 3.2 at the logic level, feeding `renderList`'s existing empty-state branch)

> No section gate — this section is itself the tests.
