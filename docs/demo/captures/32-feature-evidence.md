Status: PASS

| Check | Expected | Actual | Result |
|---|---|---|---|
| `grep -c 'data-testid="search"' index.html` | 1 | 1 | PASS |
| `grep -c 'let search' src/main.js` | 1 | 1 | PASS |
| `grep -c "addEventListener('input'" src/main.js` | at least 1 | 1 | PASS |
| `grep -c 'visibleTasks(tasks, filter, search)' src/main.js` | 1 | 1 | PASS |
| `grep -c 'summary(tasks)' src/main.js` | 1 | 1 | PASS |
| Manual: search `<input>` has `data-testid="search"`, sits inside `<main>`, after `.filters` group and before `<ul id="tasks">`; three filter buttons and `<ul id="tasks">` otherwise unchanged | matches spec (2.1.1, 2.1.2, AC 1.1) | `index.html:18` adds `<input type="text" id="search" data-testid="search" placeholder="Search tasks" aria-label="Search tasks">` between the `.filters` `</div>` (line 17) and `<ul id="tasks"></ul>` (line 19); the three filter buttons (lines 14-16) and the `<ul>` are byte-identical to the pre-feature structure | PASS |
| Manual: `src/main.js` has `let search = '';` module-level state alongside `let filter = 'all';` | matches spec (2.2.1) | `src/main.js:9-10`: `let filter = 'all';` then `let search = '';` | PASS |
| Manual: `input` event listener sets `search` to the input's current value (not trimmed) and calls `draw()` | matches spec (2.2.2, no trimming per tasks.md clarification) | `src/main.js:20`: `searchInput.addEventListener('input', () => { search = searchInput.value; draw(); });` — raw `.value`, no `.trim()` | PASS |
| Manual: inside `draw()`, `visibleTasks(tasks, filter, search)` called in place of old two-arg call | matches spec (2.2.3) | `src/main.js:13`: `list.innerHTML = renderList(sortTasks(visibleTasks(tasks, filter, search)));` | PASS |
| Manual: filter buttons' click handler and `aria-pressed` wiring unchanged — only reassigns `filter` and calls `draw()`, never reads/resets `search` | matches spec (2.2.4, AC 2.4) | `src/main.js:18`: `filters.forEach((button) => button.addEventListener('click', () => { filter = button.dataset.filter; draw(); }));` — no reference to `search`; `aria-pressed` set inside `draw()` from `filter` only (line 15) | PASS |
| Manual: `draw()`'s call to `summary(tasks)` unchanged — receives full unfiltered `tasks`, never `search`-filtered | matches spec (2.2.5, AC 4.1, 4.2) | `src/main.js:14`: `counts.innerHTML = renderSummary(summary(tasks));` — argument is the module-level `tasks` array, not `visibleTasks(...)` output | PASS |
| Manual: search box's raw value only ever read into `search` and passed to `visibleTasks`; never written into `list.innerHTML` or other markup | matches spec (2.2.6, no XSS concern) | Only reference to `searchInput.value` is line 20 assignment to `search`; `list.innerHTML` (line 13) is built solely from `renderList(sortTasks(visibleTasks(tasks, filter, search)))`, which renders task titles via `escapeHtml` in `render.js`, not the raw search string | PASS |
| `node --test` | all pass | `tests 7, pass 7, fail 0, cancelled 0, skipped 0` | PASS |
