// Records creating a factory from scratch in the editor, for real: a fast lane for bug reports on the API repository.
import { open } from './drive.mjs';
import { homedir } from 'node:os';

const page = await open();
await page.goto('http://127.0.0.1:8787/#factory-demo-api');
await page.shot('c1-start', { 'Start here': '#new' });

await page.click('#new');
await page.type('#n_name', 'factory-demo-api-bugs');
await page.type('#n_repo', `${homedir()}/personal-repos/factory-demo-api`);
await page.shot('c2-form', { 'Name it': '#n_name', 'Point it at a repository': '#n_repo' });

await page.click('input[name=sample][value=bugfix]');
await page.shot('c3-start-point', { 'A starting point, not a project type': 'input[name=sample][value=bugfix] + em', 'Or start empty': '.sample.blank' }, '#samples');

await page.click('#create', 2500);
await page.until(`document.querySelector('#target').value === 'factory-demo-api-bugs'`);
await page.shot('c4-created', { 'Its pipeline: stages, and a gate': '#draw', 'A new factory': '#target' });

await page.run(`(() => { const s = document.querySelector('#stype'); s.value = 'github'; s.dispatchEvent(new Event('change', { bubbles: true })); })()`);
await page.type('#s_repo', 'sanjeev23oct/factory-demo-api');
await page.type('#s_label', 'bug');
await page.type('#s_assignee', 'sanjeev23oct');
await page.shot('c5-source', { 'The label that triggers it': '#s_label', 'Only when assigned to this person': '#s_assignee' }, '#source');

// Switch on the stop that opens a pull request at the end of the route.
await page.run(`(() => { const rows = [...document.querySelectorAll('.stop')]; const row = rows.find((r) => r.querySelector('input[data-k=id]').value === 'pull-request');
  const box = row.querySelector('input[data-k=enabled]'); box.click(); })()`);
await page.wait(400);
const gate = `[...document.querySelectorAll('.stop')].find((r) => r.querySelector('input[data-k=id]').value === 'approve-fix')`;
const pull = `[...document.querySelectorAll('.stop')].find((r) => r.querySelector('input[data-k=id]').value === 'pull-request')`;
await page.run(`(${gate}).id = 'demo-gate'; (${pull}).id = 'demo-pull';`);
await page.shot('c6-stops', { 'The gate: a person approves the fix': '#demo-gate', 'Switched on: open a pull request': '#demo-pull' }, '#demo-gate');

await page.type('#guide', `# Engineering guide: factory-demo-api

A small tasks API in Python. Standard library only.

- api/store.py owns the data. api/app.py owns routing and validation.
- Every error is JSON {"error": "<message>"} with a 4xx status.
- A bug fix comes with a test that fails without the fix.
- Change only what the bug needs.

python3 -m unittest discover -s tests must pass.`);
await page.type('#presubmit', '#!/bin/sh\nset -e\npython3 -m unittest discover -s tests\n');
await page.shot('c7-rules', { 'Your rules, in your words': '#guide', 'The commands that prove a change': '#presubmit' }, '#guide');

await page.click('#auto');
await page.click('#save', 1200);
await page.shot('c8-live', { 'Switched on: it now runs by itself': '.switch', 'Saved': '#state' }, '#source');
await page.close();
