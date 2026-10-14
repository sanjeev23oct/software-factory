// Continues the recording from the first gate: the person approves, agents build, and it stops at the second gate.
import { open } from './drive.mjs';
const page = await open();
const item = "[...document.querySelectorAll('.item')].find((e) => e.textContent.includes('Find a task by typing'))";
const card = "[...document.querySelectorAll('.wait')].find((e) => e.textContent.includes('Find a task by typing'))";
const C = (inner) => `js:(${card})?.querySelector(${JSON.stringify(inner)})`;
const I = (inner) => `js:(${item})?.querySelector(${JSON.stringify(inner)})`;

await page.goto('http://127.0.0.1:8787/activity', 2500);
await page.until('!!' + card, 60);
await page.shot('r4-gate', { 'The pipeline has stopped at a gate': C('.tag'), 'What the agent wrote': C('.doc'), 'Waiting for a person': C('.btn.go') });
await page.run(`(${card}).querySelector('.doc summary').click()`); await page.wait(700);
await page.shot('r5-read', { 'Read the requirements before approving': C('.doc pre') }, C('.wait-top'));
await page.run(`(${card}).querySelector('.doc').open = false`);
await page.run(`(${card}).querySelector('input[data-skip]').click()`); await page.wait(400);
await page.shot('r6-approve', { 'An optional stop, skipped for a small change': C('label'), 'The human decision': C('.btn.go') });
await page.run(`(${card}).querySelector('.btn.go').click()`); await page.wait(2500);
await page.until('!' + card, 120);
await page.until(`(() => { const i = ${item}; return i && [...i.querySelectorAll('.track .now')].some((n) => n.textContent.trim() === 'build'); })()`, 900);
await page.wait(4000);
await page.shot('r7-building', { 'Approved: the gate is behind it': `js:[...(${item}).querySelectorAll('.track span')].find((n) => n.textContent.includes('gate: requirements'))`,
  'Agents are building now': I('.track .now'), 'Nobody is at the keyboard': '#pulse-title' });
await page.until('!!' + card, 2400);
await page.wait(1500);
await page.shot('r8-gate2', { 'Built, checked and tested': I('.track'), 'Stopped again, for a person to look': C('.tag') });
await page.close();
