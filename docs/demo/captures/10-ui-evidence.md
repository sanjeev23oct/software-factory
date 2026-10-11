Status: PASS

| Check | Expected | Actual | Result |
|---|---|---|---|
| `grep -c 'class="due"' src/render.js` | at least 1 | 1 | PASS |
| `grep -c 'class="overdue-flag"' src/render.js` | at least 1 | 1 | PASS |
| `grep -c 'isOverdue' src/render.js` | at least 1 | 2 (import + call) | PASS |
| `grep -c 'data-testid="filter-overdue"' index.html` | 1 | 1 | PASS |
| `grep -c 'data-filter="overdue"' index.html` | 1 | 1 | PASS |
| `grep -c '\.due' styles.css` | at least 1 | 1 | PASS |
| `grep -c '\.overdue-flag' styles.css` | at least 1 | 1 | PASS |
| `grep -c 'summary(tasks, today)' src/main.js` | 1 | 1 | PASS |
| `grep -c 'visibleTasks(tasks, filter, today)' src/main.js` | 1 | 1 | PASS |
| Manual 3.1.1: `renderTask` imports `isOverdue` from `./board.js` | matches | `import { isOverdue } from './board.js';` at top of `src/render.js` | PASS |
| Manual 3.1.2: no `due` field (or `due: null`) → `<li>` markup byte-for-byte identical to today's output (AC 1.3) | matches | `dueSpan`/`overdueSpan` both resolve to `''` when `task.due == null`, producing `<li class="task open" data-testid="task-1"><span class="mark" aria-hidden="true"></span><span class="title">Renew the domain</span></li>` — identical to visual-spec.md's "Current markup" example | PASS |
| Manual 3.1.3: has `due` → adds `<span class="due" data-testid="due-${task.id}">${escapeHtml(task.due)}</span>` right after the title span (AC 1.1) | matches | code builds `...${escapeHtml(task.title)}</span>${dueSpan}${overdueSpan}</li>` with `dueSpan = `<span class="due" data-testid="due-${task.id}">${escapeHtml(task.due)}</span>`` — matches visual-spec.md's "New markup" example exactly | PASS |
| Manual 3.1.4: `isOverdue` true → `<li>` class becomes `task ${state} overdue`, `<span class="overdue-flag" data-testid="overdue-${task.id}">Overdue</span>` added right after the due span; otherwise neither added (AC 2.1–2.5) | matches | `class="task ${state}${overdue ? ' overdue' : ''}"` and `overdueSpan` placed immediately after `dueSpan`; when not overdue both the class suffix and `overdueSpan` are omitted — matches visual-spec.md's overdue example and non-overdue states | PASS |
| Manual 3.2.1: `renderList(tasks, today)` calls `renderTask(task, today)` for every item; empty-state branch unchanged | matches | `tasks.map((task) => renderTask(task, today)).join('')`; empty branch still returns `<li class="empty" data-testid="empty">Nothing here.</li>` unchanged | PASS |
| Manual 3.3.1: `renderSummary({ total, done, open, overdue })` text is exactly `` `${open} open · ${done} done · ${total} total · ${overdue} overdue` ``, `overdue` segment always present (AC 3.1, 3.2) | matches | `return `<span data-testid="summary">${open} open · ${done} done · ${total} total · ${overdue} overdue</span>`;` — segment interpolated directly, never conditionally omitted | PASS |
| Manual 3.4.1: `<button type="button" data-filter="overdue" data-testid="filter-overdue">Overdue</button>` appended to `.filters` in `index.html`, after the Done button (AC 4.1) | matches | `index.html` line 17, immediately after the `filter-done` button (line 16), before the closing `</div>` — matches visual-spec.md's Filter bar example | PASS |
| Manual 3.5.1: inside `draw()`, computes `const today = new Date().toLocaleDateString('en-CA');` | matches | `src/main.js` line 11, first statement inside `draw()` | PASS |
| Manual 3.5.2: calls `summary(tasks, today)`, `visibleTasks(tasks, filter, today)`, and passes `today` into `renderList(...)` (AC 3.3, 4.2, 4.3) | matches | `renderList(sortTasks(visibleTasks(tasks, filter, today)), today)` and `renderSummary(summary(tasks, today))` | PASS |
| Manual 3.6.1: `.task .due` and `.task .overdue-flag` rules added to `styles.css` per visual-spec.md § Styling; overdue signal is the word "Overdue" itself, never colour alone (AGENTS.md) | matches | `.task .due { color: var(--muted); font-size: 14px; }` and `.task .overdue-flag { font-weight: 700; font-size: 13px; color: var(--danger); }` — colour is reinforcement only; the visible text "Overdue" (rendered by `renderTask`) is the actual signal | PASS |
| `node --test` | all tests pass | 7 pass, 0 fail (tests: summary counts open and done; visibleTasks filters by state; sortTasks puts open tasks first and does not change its input; renderTask escapes the title; renderTask marks done tasks; renderList shows an empty state; renderSummary shows the counts) — `renderSummary shows the counts` now asserts the new 4-segment string `'<span data-testid="summary">2 open · 1 done · 3 total · 0 overdue</span>'`, confirming the maker's fix to the stale assertion is correct and no other regressions exist | PASS |
