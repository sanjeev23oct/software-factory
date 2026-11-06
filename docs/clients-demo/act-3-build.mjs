// Records the build and the second gate: maker and checker at work, the plan, the evidence, and the change to try.
import { GITLAB, PROJECT, SITE, gitlab, note, openIssue, reply, site } from './client.mjs';

const BRANCH = `${GITLAB}/${PROJECT}/-/blob/factory/GL1`;
const spec = process.argv[2];   // e.g. specs/1-build-a-crm-dashboard-for-my-customers
const evidence = process.argv[3];   // one evidence file under the spec, e.g. evidence/1-logic-gate.md

const page = await gitlab(9371);
await openIssue(page);
const progress = note('Factory progress', 'maker'), gate = note('waiting for you', 'approve-screens');
const row = (words) => `js:[...(${progress.slice(3)}).querySelectorAll('tr')].find((r) => r.textContent.includes(${JSON.stringify(words)}))`;
await page.shot('c10-maker-checker', { 'One agent builds a section': row('maker session started'),
  'A separate agent checks it': row('checker session started'), 'Only a pass moves on': row('checker passed') }, progress);
await page.shot('c11-checks', { 'Then the whole change is checked again': row('check-evidence'), 'The tests run': row('verify'),
  'And it is put online to try': row('preview') }, row('Every task built'));
await page.shot('c12-gate-try-it', { 'The client\'s turn again': gate, 'A link to the working change': `js:[...(${gate.slice(3)}).querySelectorAll('a')].find((a) => a.textContent.includes('factory.justpush.cloud'))` }, gate);

await page.goto(`${BRANCH}/${spec}/tasks.md`, 8000);
await page.until('!!document.querySelector(".md h1, article h1, .blob-viewer h1")', 60);
await page.shot('c13-tasks', { 'The work, split into sections': 'js:[...document.querySelectorAll("h2")].find((e) => /Section 1/.test(e.textContent))',
  'Each section ends in a check': 'js:[...document.querySelectorAll("blockquote, h3")].find((e) => /CHECKER|Gate/.test(e.textContent))' },
  'js:[...document.querySelectorAll("h2")].find((e) => /Section 1/.test(e.textContent))');
await page.goto(`${BRANCH}/${spec}/${evidence}`, 8000);
await page.until('!!document.querySelector(".md table, article table, .blob-viewer table")', 60);
await page.shot('c14-evidence', { 'What the checker ran, expected and found': '.md table, article table, .blob-viewer table',
  'Its verdict': 'js:[...document.querySelectorAll(".md p, article p")].find((e) => /Status/.test(e.textContent))' });

const status = await site(9372);
await status.goto(`${SITE}/status/`, 3000);
await status.shot('c15-status-try-it', { 'The client\'s turn again': '.pill', 'Built and checked': 'ol', 'Try it, from here too': 'js:[...document.querySelectorAll(".links a")].find((a) => a.textContent === "Try it")' });
await status.goto(`${SITE}/GL1/`, 4000);
await status.shot('c16-try-it', {});
await status.shot('c16b-try-it-totals', { 'How many customers': 'js:document.querySelector("[data-testid=total-customers]").parentElement', 'Value of open deals': 'js:document.querySelector("[data-testid=total-open-value]").parentElement',
  'Deals won': 'js:document.querySelector("[data-testid=total-won]").parentElement', 'Odd text is shown safely, never run as code': 'js:[...document.querySelectorAll("[data-testid=customer-row]")].find((r) => r.textContent.includes("<b>"))' });
await status.close();

await openIssue(page);
await reply(page, 'approve');
await page.wait(3000);
const mine = 'js:[...document.querySelectorAll("[data-testid=work-item-note-body]")].filter((e) => e.textContent.trim() === "approve").pop()';
await page.shot('c17-approve-again', { 'Happy with it: approve again': mine }, mine);
await page.close();
