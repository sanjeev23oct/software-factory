# Test drive app

A small task board that the [software factory](https://github.com/sanjeev23oct/software-factory)
works on in the leadership test drive. File an issue with the **Feature**
template and the factory takes it from there: it writes the requirements,
waits for your `/approve`, builds the change with a separate checker, posts a
link where you can try it, and opens a merge request when you approve.

No build step and no dependencies: plain HTML, CSS and JavaScript modules.

    python3 -m http.server 8081     # then open http://127.0.0.1:8081
    node --test                     # run the tests

`src/board.js` holds the logic as pure functions. `src/render.js` turns tasks
into HTML strings. `src/main.js` is the only file that touches the page. Tests
cover `board.js` and `render.js`.

## Ideas to try

- Add a search box that narrows the list as you type.
- Let me add a task from the page.
- Show a due date on each task and highlight the overdue ones.
- Let me mark a task done by clicking it.
