# Tasks: Show how many tasks are in each filter

> **Maker and checker.** Each task is built by a maker, using the skill named on the task.
> A checker then verifies the section in a separate session: it did not see the maker work,
> it runs the gate against what was built, and it alone writes the evidence.
> Nothing is ticked until the checker's evidence says PASS.

Resolves the one open "Needs clarification" item so the build is deterministic:

- **Accessible-name wording for a count of 1 and for `All`**: per the requirements' own assumption, every button (including `All`) uses the same `"<Label>, <count> task"` / `"<Label>, <count> tasks"` pattern, singular only when the count is exactly 1. No separate wording for `All`, no mention of "total".

## Section 1 — Logic (`src/board.js`)

Satisfies: AC 1.1, AC 3.1, AC 3.2, AC 3.3, AC 4.1, AC 4.2, and the correctness property that a count is never computed from the filtered/visible list (these functions only format a label and a count they are given)

- [x] 1.1 `filterButtonText(label, count)` in `src/board.js`     → run: `/build-ui-logic`
  - [x] 1.1.1 new exported pure function: returns `` `${label} ${count}` ``, e.g. `filterButtonText('All', 3) === 'All 3'`, `filterButtonText('Done', 0) === 'Done 0'` (AC 1.1, 3.1, 3.2, 3.3)
- [x] 1.2 `filterButtonAriaLabel(label, count)` in `src/board.js` → run: `/build-ui-logic`
  - [x] 1.2.1 new exported pure function: returns `` `${label}, ${count} task` `` when `count === 1`, otherwise `` `${label}, ${count} tasks` ``, e.g. `filterButtonAriaLabel('Done', 1) === 'Done, 1 task'`, `filterButtonAriaLabel('Open', 2) === 'Open, 2 tasks'`, `filterButtonAriaLabel('All', 0) === 'All, 0 tasks'` (AC 4.1, 4.2)

### 1.X — Gate

> **CHECKER (Cat 1):** every check in `loop/1-logic-checker.md` returns its EXPECTED value.
> **CHECKER (Cat 2):** write `evidence/1-logic-gate.md` as a tick sheet.
> **CHECKER (Cat 3):** run `node --test`; EXPECTED: all pass.

## Section 2 — Page (`src/main.js`)

Satisfies: AC 1.1, AC 1.2, AC 1.3, AC 1.4, AC 1.5, AC 2.1, AC 2.2, AC 3.4, AC 4.1, AC 4.2, and the correctness properties that the count always comes from `summary(tasks)` over the full list (never the filtered list), that selecting a filter never changes any button's count, and that the `#summary` line is unaffected

- [x] 2.1 import the two new functions into `src/main.js`          → run: `/build-ui-page`
  - [x] 2.1.1 `import { filterButtonAriaLabel, filterButtonText, sortTasks, summary, visibleTasks } from './board.js';` (adds the two new names to the existing import)
- [x] 2.2 `draw()` in `src/main.js` sets each filter button's text and accessible name → run: `/build-ui-page`
  - [x] 2.2.1 inside `draw()`, after computing `summary(tasks)`, read each button's count from the matching field of that same `summary(tasks)` result — `total` for the button with `data-filter="all"`, `open` for `data-filter="open"`, `done` for `data-filter="done"` — never from `visibleTasks(tasks, filter)` (AC 1.2, 1.3, 1.4, 2.1, correctness property on the count's source)
  - [x] 2.2.2 for each filter button, derive its label by capitalizing its `data-filter` value (`'all'` → `'All'`, `'open'` → `'Open'`, `'done'` → `'Done'`) and set `button.textContent = filterButtonText(label, count)` (AC 1.1, 3.1, 3.2, 3.3)
  - [x] 2.2.3 for each filter button, set `button.setAttribute('aria-label', filterButtonAriaLabel(label, count))` using the same `label` and `count` as 2.2.2 (AC 4.1, 4.2)
  - [x] 2.2.4 the existing `aria-pressed` assignment, the filter buttons' click handler (which only reassigns `filter` and calls `draw()`), and the `counts.innerHTML = renderSummary(summary(tasks))` line are otherwise unchanged (AC 2.2, 3.4, correctness properties that selecting a filter only changes `aria-pressed`/the listed tasks, and that the `#summary` line keeps its current format)
  - [x] 2.2.5 `draw()` never sets or removes a button's `data-testid` or `data-filter` attribute (AC 1.5)

### 2.X — Gate

> **CHECKER (Cat 1):** every check in `loop/2-page-checker.md` returns its EXPECTED value.
> **CHECKER (Cat 2):** write `evidence/2-page-gate.md` as a tick sheet.
> **CHECKER (Cat 3):** run `node --test`; EXPECTED: all pass.

## Section 3 — Tests

Satisfies: every acceptance criterion and correctness property in `requirements.md`

- [x] 3.1 `test/board.test.js` covers `filterButtonText` and `filterButtonAriaLabel` → run: `/build-tests`
  - [x] 3.1.1 `filterButtonText('All', 3) === 'All 3'`, `filterButtonText('Open', 2) === 'Open 2'`, `filterButtonText('Done', 1) === 'Done 1'`, `filterButtonText('Done', 0) === 'Done 0'` (AC 1.1, 3.1, 3.2, 3.3)
  - [x] 3.1.2 `filterButtonAriaLabel` singular: `filterButtonAriaLabel('Done', 1) === 'Done, 1 task'` (AC 4.1)
  - [x] 3.1.3 `filterButtonAriaLabel` plural, including zero: `filterButtonAriaLabel('Open', 2) === 'Open, 2 tasks'`, `filterButtonAriaLabel('All', 0) === 'All, 0 tasks'` (AC 4.1, 3.1, 3.2, 3.3)

> No section gate — this section is itself the tests.
