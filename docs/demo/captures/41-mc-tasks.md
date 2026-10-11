> **Maker and checker.** Each task is built by a maker, using the skill named on the task.
> A checker then verifies the section in a separate session: it did not see the maker work,
> it runs the gate against what was built, and it alone writes the evidence.
> Nothing is ticked until the checker's evidence says PASS.

## Section 1 — Logic (`src/board.js`)

Satisfies: AC 1.1, AC 1.2, AC 1.3, AC 1.4, correctness properties 1–3

- [x] 1.1 `progress(tasks)` in `src/board.js`  → run: `/build-ui-logic`
  - [x] 1.1.1 given `[]`, returns a whole-number `percent` of `0` and `label` exactly `No tasks yet`
  - [x] 1.1.2 given a non-empty list where every task is done, returns `percent` of `100` and `label` exactly `All done`
  - [x] 1.1.3 given a non-empty list where no task is done, returns `percent` of `0` and `label` exactly `{done} of {total} done` using the real counts (e.g. `0 of 3 done`), not `No tasks yet`
  - [x] 1.1.4 given 1 done of 3 total, returns `percent` of `33` (a whole number, rounded) and `label` exactly `1 of 3 done`
  - [x] 1.1.5 never returns `NaN` or `Infinity` for `percent` when `total` is `0`

### 1.X — Gate

> **CHECKER (Cat 1):** every check in `loop/logic-checker.md` returns its EXPECTED value.
> **CHECKER (Cat 2):** write `evidence/1-logic-gate.md` as a tick sheet.
> **CHECKER (Cat 3):** run `node --test`; EXPECTED: all pass.

## Section 2 — View (`src/render.js`)

Satisfies: AC 1.1, AC 1.2, AC 1.3, AC 1.4, AC 1.6, AC 2.1, AC 2.2

- [x] 2.1 `renderProgress({ percent, label })` in `src/render.js`  → run: `/build-ui-view`
  - [x] 2.1.1 renders an element with `data-testid="progress-bar"`, `role="progressbar"`, `aria-valuemin="0"`, `aria-valuemax="100"`, `aria-valuenow` equal to the given `percent`, and `aria-valuetext` equal to the given `label`
  - [x] 2.1.2 renders a fill inside the bar whose width reflects `percent` (e.g. an inline `width: {percent}%` style), so a `percent` of `33` fills about a third of the bar
  - [x] 2.1.3 renders an element with `data-testid="progress-label"` whose text is exactly the given `label`
  - [x] 2.1.4 still renders the bar and its `data-testid` when `percent` is `0` (never hidden or removed)
  - [x] 2.1.5 leaves `renderSummary` and `renderTask` unchanged in both markup and behavior

### 2.X — Gate

> **CHECKER (Cat 1):** every check in `loop/view-checker.md` returns its EXPECTED value.
> **CHECKER (Cat 2):** write `evidence/2-view-gate.md` as a tick sheet.
> **CHECKER (Cat 3):** run `node --test`; EXPECTED: all pass.

## Section 3 — Page (`index.html`, `src/main.js`, `styles.css`)

Satisfies: AC 1.5, AC 1.6

- [x] 3.1 Add a `#progress` container to `index.html`, placed directly after the `<h1>` and directly before `<p id="summary">`  → run: `/build-ui-page`
  - [x] 3.1.1 the existing `<h1>`, `#summary`, and the three filter buttons (`data-testid="filter-all"`, `"filter-open"`, `"filter-done"`) keep their current markup and order
- [x] 3.2 Wire `draw()` in `src/main.js` to compute `progress(tasks)` and set `#progress`'s `innerHTML` to `renderProgress(...)` on every draw  → run: `/build-ui-page`
  - [x] 3.2.1 the existing wiring of `#tasks`, `#summary`, and the filter buttons' `aria-pressed` and click handling is unchanged
- [x] 3.3 Add styles for the progress bar's track and fill to `styles.css`  → run: `/build-ui-page`
  - [x] 3.3.1 the bar has a visible track and a fill that sits inside it, using the existing colour variables (`--line`, `--accent`, etc.)

### 3.X — Gate

> **CHECKER (Cat 1):** every check in `loop/page-checker.md` returns its EXPECTED value.
> **CHECKER (Cat 2):** write `evidence/3-page-gate.md` as a tick sheet.
> **CHECKER (Cat 3):** run `node --test`; EXPECTED: all pass.

## Section 4 — Tests (`test/*.js`)

Satisfies: AC 1.1, AC 1.2, AC 1.3, AC 1.4, AC 2.1, AC 2.2, correctness properties 1–5

- [x] 4.1 Tests for `progress(tasks)` in `test/board.test.js`, covering the empty list, all-done, zero-done-not-empty, and a mixed count that rounds (e.g. 1 of 3 → 33)  → run: `/build-tests`
- [x] 4.2 Tests for `renderProgress({ percent, label })` in `test/render.test.js`, covering the `data-testid`s, the ARIA attributes (`role`, `aria-valuemin`, `aria-valuemax`, `aria-valuenow`, `aria-valuetext`), and that the bar still renders at `percent` `0`  → run: `/build-tests`
