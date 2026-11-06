// Records the first gate: the factory picked the request up, wrote down what it understood, and waits for the client.
import { GITLAB, PROJECT, SITE, gitlab, note, openIssue, reply, site } from './client.mjs';

const page = await gitlab(9351);
await openIssue(page);
const progress = note('Factory progress'), gate = note('waiting for you', 'approve-requirements');
await page.shot('c05-picked-up', { 'The factory comments on the issue as it works': progress }, progress);
await page.shot('c06-gate', { 'Its turn is over: now it is the client\'s': gate,
  'What to read first': `js:(${gate.slice(3)}).querySelector('a')` }, gate);

const link = await page.run(`(${gate.slice(3)}).querySelector('a').href`);
console.log('requirements', link);
await page.goto(link, 8000);
await page.until('!!document.querySelector(".blob-viewer h1, .file-content h1, article h1, .md h1")', 60);
await page.shot('c07-requirements', { 'The request, written down as stories': 'js:[...document.querySelectorAll("h2,h3")].find((e) => /stor/i.test(e.textContent))',
  'Each one with checks it must pass': 'js:[...document.querySelectorAll("li")].find((e) => /^AC/.test(e.textContent.trim()))' },
  'js:[...document.querySelectorAll("h2,h3")].find((e) => /stor/i.test(e.textContent))');
await page.shot('c07b-requirements-top', { 'Written by an agent, from the client\'s words': '.blob-viewer h1, .file-content h1, article h1, .md h1' });

const status = await site(9352);
await status.goto(`${SITE}/status/`, 3000);
await status.shot('c08-status-your-turn', { 'Whose turn it is': '.pill', 'Where it stands': 'ol', 'One click to the conversation': 'a.main' });
await status.close();

await openIssue(page);
await reply(page, 'approve');
await page.wait(3000);
const mine = 'js:[...document.querySelectorAll("[data-testid=work-item-note-body]")].filter((e) => e.textContent.trim() === "approve").pop()';
await page.shot('c09-approve', { 'The client replies one word': mine }, mine);
await page.close();
