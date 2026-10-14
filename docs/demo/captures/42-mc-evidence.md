Status: PASS

# Evidence: section 2, view

| Check | Expected | Found | Result |
| --- | --- | --- | --- |
| grep -c "export function renderTask" src/render.js | 1 | 1 | PASS |
| grep -c "dueText" src/render.js | at least 1 | 2 | PASS |
| grep -c "import.*from './board.js'" src/render.js | 1 | 1 | PASS |
| grep -c 'data-testid="due-' src/render.js | 1 | 1 | PASS |
| grep -c 'class="due"' src/render.js | 1 | 1 | PASS |
| grep -c "export function renderList" src/render.js | 1 | 1 | PASS |
| grep -c "export function renderSummary" src/render.js | 1 | 1 | PASS |
| grep -c 'data-testid="empty"' src/render.js | 1 | 1 | PASS |
| node --test | all pass | 7 pass, 0 fail | PASS |

## Manual review of sub-items against src/render.js

| Sub-item | Requirement | Found | Result |
| --- | --- | --- | --- |
| 2.1 | `renderTask(task, today)` imports and uses `dueText` from `./board.js` | `import { dueText } from './board.js';` (line 3); `renderTask(task, today)` calls `dueText(task, today)` (line 11) | PASS |
| 2.1.1 | non-null `dueText` adds `<span class="due" data-testid="due-${task.id}">${escapeHtml(dueText(...))}</span>` inside `<li>`, after the title span | line 12 builds exactly this string; line 15 concatenates it immediately after the title span, before `</li>` | PASS |
| 2.1.2 | null `dueText` adds no due element; rest of markup byte-for-byte identical to prior output | `dueSpan` is `''` when `due == null` (line 12); diff vs. pre-change `render.js` (commit 240c0a4) shows no other alteration to the `<li>`/mark/title markup | PASS |
| 2.1.3 | due text passes through `escapeHtml` | line 12: `escapeHtml(due)` | PASS |
| 2.2 | `renderList(tasks, today)` threads `today` to every `renderTask` call | line 20: `tasks.map((task) => renderTask(task, today))` | PASS |
| 2.2.1 | empty-state branch unchanged | line 19 identical to pre-change `render.js` | PASS |

## Scope check

`git show --stat HEAD` (commit 1f3c23e): only `src/render.js` changed (8 insertions, 4 deletions), matching exactly the diff needed for 2.1/2.2. No unrelated files touched.

---
_Stamped by the factory: this evidence was written by the checker in session `edbbf5e0`, a different session from the maker's (`dd4051ea`). It checks the maker's commit `1f3c23e`._
