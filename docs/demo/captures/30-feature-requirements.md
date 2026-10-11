# Requirements: Find a task by typing

## Overview

The board has no text search today: `index.html` holds only three filter buttons (All, Open, Done) wired through `visibleTasks(tasks, filter)` (`src/board.js:8-12`, `index.html:13-17`), and `renderList` shows every task returned by that filter, falling back to a fixed `data-testid="empty"` / "Nothing here." message only when the list is empty (`src/render.js:14-17`). The summary line is computed from the full, unfiltered `tasks` array (`src/board.js:3-6`, `src/render.js:19-21`), independent of the active filter. This feature adds a search box above the list that narrows the visible tasks to those whose title contains the typed text, case-insensitively, combined with (not replacing) the existing status filter, while leaving the summary counting every task as it does today.

## User stories

### Story 1: Narrow the list by typing a title

As someone scanning a long board,
I want to type into a search box and see only tasks whose title contains what I typed,
So that I can find a task without scrolling through everything.

- AC 1.1: A text input exists above the task list with `data-testid="search"`.
- AC 1.2: Typing text into the search box shows only tasks whose `title` contains that text as a substring; a task whose title does not contain it is removed from the list.
- AC 1.3: Matching is case-insensitive: typing `"MILK"` matches a task titled `"Buy milk"`, and typing `"milk"` matches a task titled `"Buy MILK"`.
- AC 1.4: The match is a plain substring check, not a whole-word match: typing `"ilk"` matches a task titled `"Buy milk"`.
- AC 1.5: Clearing the search box back to an empty string shows every task allowed by the current status filter, exactly as if no search had been typed.

### Story 2: Search combines with the existing status filters

As someone scanning the board,
I want the search box to narrow within the All/Open/Done filter I already picked, not replace it,
So that I can, for example, find an open task by title without seeing matching done tasks too.

- AC 2.1: With the Open filter active and a search term typed, a task is shown only if it is not done AND its title contains the search term; a done task whose title matches the search term is not shown.
- AC 2.2: With the Done filter active and a search term typed, a task is shown only if it is done AND its title contains the search term.
- AC 2.3: With the All filter active, a search term narrows by title alone (no status restriction), matching both done and not-done tasks.
- AC 2.4: Typing or clearing a search term does not change which filter button has `aria-pressed="true"`; the active status filter (All, Open or Done) stays selected exactly as it was.
- AC 2.5: Switching the status filter while a search term is already typed re-applies that same search term to the newly selected filter's tasks, without the user retyping it.

### Story 3: Say so plainly when nothing matches

As someone scanning the board,
I want to be told clearly when my search found nothing,
So that I know to try a different word instead of wondering if the board is broken.

- AC 3.1: When the active filter and search term together match zero tasks, the list shows the existing empty-state element (`data-testid="empty"`) instead of an empty `<ul>`.
- AC 3.2: The empty-state element from AC 3.1 is shown whenever a non-empty search term matches no task under the active filter, including when the board has tasks overall but none of their titles contain the search term.

### Story 4: The summary keeps counting everything

As someone scanning the board,
I want the open/done/total counts to reflect the whole board, not just what the search is currently showing,
So that I always know the true size of my task list, not a filtered view of it.

- AC 4.1: The summary element (`data-testid="summary"`) text is unaffected by the search box: it always reads `{open} open · {done} done · {total} total` computed over every task, regardless of the typed search term.
- AC 4.2: Typing a search term that matches zero tasks does not change the summary's counts; they still reflect all tasks.

## Correctness properties

- Search narrows within the active status filter; the two never substitute for each other (AC 2.1–2.3). A task is visible only if it satisfies both the status filter and the search term.
- The search match is a case-insensitive substring containment check against `title` alone — no other task field is considered, and no fuzzy or whole-word matching is applied.
- An empty search term is equivalent to no search term: it imposes no restriction beyond the active status filter.
- The summary counts (`open`, `done`, `total`) are a pure function of the full task list and never change because of the search term or the active status filter, consistent with their existing behavior today.
- The existing empty-state markup and text are what signal "nothing matches," for both the pre-existing "filter has no tasks" case and the new "search has no matches" case — there is no blank list state.
- Text typed into the search box is never inserted into the page as markup; only existing task titles continue to pass through `escapeHtml` as they do today.

## Out of scope

- Matching against anything other than a task's title (e.g. its id or done state).
- Highlighting the matched substring within the rendered title.
- Debouncing, throttling, or any other performance handling of the search input.
- Persisting the typed search term across a page reload.
- A keyboard shortcut to focus or clear the search box.
- Searching by multiple words with AND/OR semantics — only a single contiguous substring match, per AC 1.2–1.4.

## Needs clarification

- The exact wording for the "nothing matches" state: whether it should reuse the current generic "Nothing here." text (AC 3.1 assumes it does, for minimal change) or show a more specific message naming the search term (e.g. "No tasks match “abc”.").
- Whether leading/trailing whitespace typed into the search box should be trimmed before matching, or matched literally (e.g. a trailing space in the box could make an otherwise-matching title fail to match).
- Whether the search box needs a visible label or placeholder text, and if so, its exact wording.
