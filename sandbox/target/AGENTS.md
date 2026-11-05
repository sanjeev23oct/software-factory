# Engineering guide for factory agents

## What this repository is

A small task board in plain HTML, CSS and JavaScript modules, with no build
step and no dependencies. It is the sandbox app for the leadership test drive:
people who are not engineers file issues here, so read the issue for what
they want, not for how they phrase it.

## Layout

- `index.html` and `styles.css`: the page.
- `src/board.js`: the logic, as pure functions. Keep it free of the DOM.
- `src/render.js`: turns tasks into HTML strings. Every task title passes
  through `escapeHtml`.
- `src/main.js`: the only file that touches the page.
- `data/tasks.json`: the example tasks the page loads.
- `test/`: `node --test` tests, one file per module.

## Rules

- No dependencies, no build step, no network calls other than loading
  `data/tasks.json`. The page must keep working when served as static files
  from a sub-folder (the preview serves it at `/<item>/`), so use relative
  paths only.
- Text a person types is never inserted into the page as markup.
- Every new behavior in `board.js` or `render.js` lands with tests.
- Keep changes small and focused on the issue. No restyling of unrelated parts.
- Do not touch `.gitlab/`: the issue templates belong to the people filing issues.

## Verification

`presubmit` runs `node --test`. It cannot see the page; the person at the
`approve-screens` gate looks at it through the preview link.
