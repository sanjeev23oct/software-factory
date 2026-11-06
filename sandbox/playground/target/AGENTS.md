# Engineering guide for factory agents

## What this repository is

A client's web app in plain HTML, CSS and JavaScript modules, with no build
step and no dependencies. It starts as an empty page and grows one request at
a time; the first request decides what kind of app it is. The client is not an
engineer: they file issues in their own words, so read the issue for what they
want, not for how they phrase it.

## Layout

- `index.html` and `styles.css`: the page. Replace the "coming soon" panel
  when the first real screen lands.
- `src/`: logic as pure functions, one module per area (for example
  `src/customers.js`). Keep logic free of the DOM.
- `src/render.js`: turns data into HTML strings. Every piece of text from
  data passes through `escapeHtml`.
- `src/main.js`: the only file that touches the page.
- `data/`: the sample data the page loads, as JSON. Make it realistic enough
  to show every state, including an empty one.
- `test/`: `node --test` tests, one file per module.

## Rules

- No dependencies, no build step, no network calls other than loading files
  from `data/`. The page must keep working when served as static files from a
  sub-folder (the preview serves it at `/<item>/`), so use relative paths only.
- Text a person types, or that comes from data, is never inserted into the
  page as markup.
- Every new behavior in `src/` other than `main.js` lands with tests.
- Keep changes small and focused on the issue. No restyling of unrelated parts.
- Do not touch `.gitlab/`: the issue templates belong to the people filing issues.

## Verification

`presubmit` runs `node --test`. It cannot see the page; the client at the
`approve-screens` gate looks at it through the preview link.
