Status: PASS

# Evidence: section 2, page (`src/main.js`)

| Check | Expected | Found | Result |
| --- | --- | --- | --- |
| grep -c 'filterButtonText' src/main.js | at least 2 | 2 | PASS |
| grep -c 'filterButtonAriaLabel' src/main.js | at least 2 | 2 | PASS |
| grep -c "setAttribute('aria-label'" src/main.js | at least 1 | 1 | PASS |
| grep -c 'aria-pressed' src/main.js | at least 1 | 1 | PASS |
| grep -c 'summary(tasks)' src/main.js | at least 1 | 1 | PASS |
| node --test | all pass | 7 pass, 0 fail | PASS |

## Sub-item review (reading `src/main.js` and `git diff 418b537 e604a31 -- src/main.js`)

- 2.1.1: line 1 is exactly `import { filterButtonAriaLabel, filterButtonText, sortTasks, summary, visibleTasks } from './board.js';` — PASS
- 2.2.1: `const totals = summary(tasks);` is computed once, then `countsByFilter = { all: totals.total, open: totals.open, done: totals.done }`; each button's `count` is read from `countsByFilter[button.dataset.filter]`, never from `visibleTasks(tasks, filter)` — PASS
- 2.2.2: label is `button.dataset.filter.charAt(0).toUpperCase() + button.dataset.filter.slice(1)` (`'all'`→`'All'` etc.), and `button.textContent = filterButtonText(label, count)` — PASS
- 2.2.3: `button.setAttribute('aria-label', filterButtonAriaLabel(label, count))` uses the same `label`/`count` as 2.2.2 — PASS
- 2.2.4: `button.setAttribute('aria-pressed', String(button.dataset.filter === filter))` is unchanged from the prior version (same expression, same place); the click handler (`filter = button.dataset.filter; draw();`) is untouched in the diff; `counts.innerHTML = renderSummary(totals)` where `totals = summary(tasks)` is equivalent to the prior `renderSummary(summary(tasks))` — PASS
- 2.2.5: `draw()` never references `data-testid` or sets/removes `data-filter`; confirmed `index.html` lines 14-16 still carry both attributes, untouched by the diff — PASS

`git show --stat HEAD` confirms only `src/main.js` was changed (1 file, 14 lines) — nothing outside this section's named file was touched.

---
_Stamped by the factory: this evidence was written by the checker in session `c6b3fbbc`, a different session from the maker's (`1014d1e2`). It checks the maker's commit `e604a31`._
