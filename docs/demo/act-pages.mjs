// Captures the pages the rest of the demo points at, with the position of what matters on each.
import { open } from './drive.mjs';
const page = await open();
const gh = 'https://github.com/sanjeev23oct';
const cell = (text) => `js:[...document.querySelectorAll('td')].find((e) => e.textContent.trim() === ${JSON.stringify(text)})?.parentElement`;

await page.goto('http://127.0.0.1:8787/#factory-demo-api', 2500);
await page.run("(() => { const g = [...document.querySelectorAll('.node.gate')]; g[0].id = 'g1'; g[1].id = 'g2'; })()");
await page.shot('p1-api-route', { 'Gate 1: approve the requirements': '#g1', 'Gate 2: approve the design': '#g2' });
await page.goto('http://127.0.0.1:8787/#factory-demo-ui', 2500);
await page.run("(() => { const g = [...document.querySelectorAll('.node.gate')]; g[g.length - 1].id = 'g2'; })()");
await page.shot('p2-ui-route', { 'A different route: the gate is at the end, to look at the screens': '#g2' });

await page.goto(`${gh}/factory-demo-api/issues/1`, 6000);
await page.shot('p3-api-issue', { 'The label': 'text:factory', 'Assigned': 'text:sanjeev23oct' });

await page.goto('http://127.0.0.1:8092/', 1500);
await page.shot('p4-ui-before', {});
await page.goto('http://127.0.0.1:8091/', 1500);
await page.shot('p5-ui-after', { 'Marked in words, not colour alone': '[data-testid=overdue-1]', 'Counted': '[data-testid=summary]', 'A new filter': '[data-testid=filter-overdue]' });

await page.goto(`${gh}/factory-demo-ui/pull/2`, 6000);
await page.shot('p6-ui-pr', { 'Closes the issue': 'text:Closes #1', 'Every evidence file, linked': 'js:[...document.querySelectorAll("h2,h3")].find((e) => e.textContent.trim() === "Evidence")?.nextElementSibling',
  'One commit per stop': 'js:[...document.querySelectorAll("a")].find((e) => e.textContent.trim().startsWith("requirements:"))' }, 'text:Closes #1');

await page.goto(`${gh}/factory-demo-api/pull/3`, 6000);
await page.shot('p7-quick-hack', { 'No spec': cell('Spec before code'), 'No test': cell('Automated tests for api changes'), 'The team’s own rule': cell('No print statements in the API'),
  'So no agent was used': 'js:[...document.querySelectorAll("p")].find((e) => e.textContent.includes("The code was not reviewed"))' },
  'js:[...document.querySelectorAll("h2")].find((e) => e.textContent.includes("Process check"))');

await page.goto(`${gh}/factory-demo-api/pull/2`, 6000);
await page.shot('p8-factory-built', { 'All 11 checks pass': 'js:[...document.querySelectorAll("h2")].find((e) => e.textContent.includes("Process check"))',
  'So an agent reviewed the code': 'js:[...document.querySelectorAll("h2")].find((e) => e.textContent.includes("Code review"))' },
  'js:[...document.querySelectorAll("h2")].find((e) => e.textContent.includes("Process check"))');

await page.goto(`${gh}/factory-demo-api/pull/5`, 6000);
await page.shot('p9-bug-pr', { 'Opened by the background job after the approval': 'js:document.querySelector(".gh-header-title, h1.gh-header-title, bdi.js-issue-title")', 'Closes the bug': 'text:Closes #4' });

await page.goto('http://127.0.0.1:8787/rules', 2500);
await page.run("(() => { document.querySelectorAll('.row')[0].id = 'r1'; const rule = [...document.querySelectorAll('.rule')].find((e) => e.querySelector('input').value.includes('print')); rule.id = 'r2'; })()");
await page.shot('p10-rules-checks', { 'Each check: fail, warn, or off': '#r1 .seg' });
await page.shot('p11-rules-own', { 'A rule this team added, as a sentence': '#r2' }, '#r2');
await page.close();
