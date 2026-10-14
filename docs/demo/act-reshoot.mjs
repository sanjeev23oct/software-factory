// Re-takes the pictures that needed the page scrolled, now clear of the sticky header.
import { open } from './drive.mjs';
import { homedir } from 'node:os';
const page = await open();
const gh = 'https://github.com/sanjeev23oct';
const cell = (text) => `js:[...document.querySelectorAll('td')].find((e) => e.textContent.trim() === ${JSON.stringify(text)})?.parentElement`;
const stop = (id) => `js:[...document.querySelectorAll('.stop')].find((r) => r.querySelector('input[data-k=id]').value === '${id}')`;

await page.goto('http://127.0.0.1:8787/#factory-demo-api');
await page.click('#new');
await page.type('#n_name', 'factory-demo-api-bugs');
await page.type('#n_repo', `${homedir()}/personal-repos/factory-demo-api`);
await page.click('input[name=sample][value=bugfix]');
await page.shot('c3-start-point', { 'An example to edit, not a fixed type': 'js:document.querySelector("input[name=sample][value=bugfix]").closest(".sample")', 'Or start from nothing': '.sample.blank' }, '#samples');

await page.goto('http://127.0.0.1:8787/#factory-demo-api-bugs', 2500);
await page.shot('c5-source', { 'The label that triggers it': '#s_label', 'Only when assigned to this person': '#s_assignee' }, '#source');
await page.shot('c6-stops', { 'The gate: a person approves the fix': stop('approve-fix'), 'Switched on: open a pull request': stop('pull-request') }, stop('review').slice(3) ? stop('review') : null);
await page.shot('c7-rules', { 'Your rules, in your words': '#guide', 'The commands that prove a change': '#presubmit' }, '#guide');
await page.shot('c8-live', { 'Switched on: from here it runs by itself': '.switch' }, '#source');

await page.goto('http://127.0.0.1:8787/#factory-demo-ui', 2500);
await page.run("(() => { const g = [...document.querySelectorAll('.node.gate')]; g[g.length - 1].id = 'g2'; })()");
await page.shot('p2-ui-route', { 'Here the gate is at the end: look at the screens': '#g2' });
await page.goto('http://127.0.0.1:8787/#factory-demo-api', 2500);
await page.run("(() => { const g = [...document.querySelectorAll('.node.gate')]; g[0].id = 'g1'; g[1].id = 'g2'; })()");
await page.shot('p1-api-route', { 'Gate 1: requirements': '#g1', 'Gate 2: design': '#g2' });

await page.goto('http://127.0.0.1:8091/', 1500);
await page.shot('p5-ui-after', { 'Marked in words, not colour alone': '[data-testid=overdue-1]', 'Counted': '[data-testid=summary]', 'A new filter': '[data-testid=filter-overdue]' });

await page.goto(`${gh}/factory-demo-ui/pull/2`, 9000);
await page.shot('p6-ui-pr', {
  'Closes the issue': 'js:[...document.querySelectorAll("p")].find((e) => e.textContent.trim().startsWith("Closes #1"))',
  'Every evidence file, linked': 'js:[...document.querySelectorAll("h2,h3")].find((e) => e.textContent.trim() === "Evidence")?.nextElementSibling',
  'One commit per stop': 'js:[...document.querySelectorAll("a")].find((e) => e.textContent.trim().startsWith("requirements: Show"))' },
  'js:[...document.querySelectorAll("p")].find((e) => e.textContent.trim().startsWith("Closes #1"))');

await page.goto(`${gh}/factory-demo-api/pull/3`, 9000);
await page.shot('p7-quick-hack', { 'No spec': cell('Spec before code'), 'No test': cell('Automated tests for api changes'),
  'So no agent was used': 'js:[...document.querySelectorAll("p")].find((e) => e.textContent.includes("The code was not reviewed"))' },
  'js:[...document.querySelectorAll("h2")].find((e) => e.textContent.includes("Process check"))');

await page.goto(`${gh}/factory-demo-api/pull/2`, 9000);
await page.shot('p8-factory-built', { 'All 11 checks pass': 'js:[...document.querySelectorAll("h2")].find((e) => e.textContent.includes("Process check"))?.nextElementSibling' },
  'js:[...document.querySelectorAll("h2")].find((e) => e.textContent.includes("Process check"))');
await page.shot('p8b-agent-review', { 'Only then: an agent reviews the code': 'js:[...document.querySelectorAll("h2")].find((e) => e.textContent.includes("Code review"))' },
  'js:[...document.querySelectorAll("h2")].find((e) => e.textContent.includes("Code review"))');

await page.goto('http://127.0.0.1:8787/activity', 2500);
await page.run("(() => { const i = [...document.querySelectorAll('.item')].find((e) => e.textContent.includes('trailing slash')); i.id = 'demo-item'; i.querySelector('.meta a').id = 'demo-link'; })()");
await page.shot('a4-approved', { 'Approved: the pipeline finished by itself': '#demo-item .track', 'A pull request is open': '#demo-link' });
await page.close();
