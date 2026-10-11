// Records creating a route for feature work on the UI repository, for real, in the editor.
import { open } from './drive.mjs';
import { homedir } from 'node:os';
const stop = (id) => `js:[...document.querySelectorAll('.stop')].find((r) => r.querySelector('input[data-k=id]').value === '${id}')`;
const node = (text) => `js:[...document.querySelectorAll('.node')].find((n) => n.textContent.trim() === '${text}')`;

const page = await open();
await page.goto('http://127.0.0.1:8787/#factory-demo-api');
await page.shot('s4-add', { 'Add a repository': '#new', 'Routes already in this factory': '.pick' });

await page.click('#new');
await page.type('#n_name', 'factory-demo-ui-features');
await page.type('#n_repo', `${homedir()}/personal-repos/factory-demo-ui`);
await page.shot('s5-form', { 'A name for the route': '#n_name', 'Where the code is': '#n_repo' });

await page.click('input[name=sample][value=ui-app]');
await page.shot('s6-start', { 'An example to start from and edit': 'js:document.querySelector("input[name=sample][value=ui-app]").closest(".sample")', 'Or start from nothing': '.sample.blank' }, '#samples');

await page.click('#create', 2500);
await page.until(`document.querySelector('#target').value === 'factory-demo-ui-features'`);
await page.shot('s7-created', { 'The new route': '#draw', 'Now listed in the factory': '.pick' });

await page.run(`(() => { const s = document.querySelector('#stype'); s.value = 'github'; s.dispatchEvent(new Event('change', { bubbles: true })); })()`);
await page.type('#s_repo', 'sanjeev23oct/factory-demo-ui');
await page.type('#s_label', 'feature');
await page.type('#s_assignee', 'sanjeev23oct');
await page.shot('s8-trigger', { 'Issues with this label': '#s_label', 'Assigned to this person': '#s_assignee', 'In this repository': '#s_repo' }, '#source');

await page.run(`(() => { const row = [...document.querySelectorAll('.stop')].find((r) => r.querySelector('input[data-k=id]').value === 'pull-request'); row.querySelector('input[data-k=enabled]').click(); })()`);
await page.wait(500);
await page.shot('s9-route', { 'Gate: a person approves the requirements': node('Gate: requirements'), 'Gate: a person looks at the screens': node('Gate: screens'), 'Ends by opening a pull request': node('pull request') });
await page.shot('s9b-stops', { 'A stop an agent does': stop('requirements'), 'A gate: it waits for a person': stop('approve-requirements'), 'Reorder with the arrows': 'js:' + stop('requirements').slice(3) + '.querySelector(".order")' }, stop('requirements'));

await page.type('#guide', `# Engineering guide: factory-demo-ui

A small task board. Plain HTML, CSS and JavaScript modules. No build step, no packages.

- src/board.js holds the logic as pure functions. It never touches the page.
- src/render.js turns tasks into HTML strings. Text from a task goes through escapeHtml.
- src/main.js is the only file that touches the page.
- Logic goes in board.js with a test. Markup goes in render.js with a test.
- Every interactive element has a data-testid.

node --test must pass.`);
await page.type('#presubmit', '#!/bin/sh\nset -e\nnode --test\n');
await page.type('#tools', 'node');
await page.shot('s10-rules', { 'The team’s rules, in plain words': '#guide', 'The commands that prove a change works': '#presubmit', 'Programs agents may run': '#tools' }, '#guide');

await page.click('#auto');
await page.shot('s11-live', { 'Switch it on': '.switch', 'Save': '#save' }, '#source');
await page.click('#save', 1500);
console.log('state:', await page.run("document.querySelector('#state').textContent"));
await page.close();
