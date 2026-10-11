// Records the second gate: a person looks at what was built, approves, and the route opens a pull request.
import { open } from './drive.mjs';
const page = await open();
const item = "[...document.querySelectorAll('.item')].find((e) => e.textContent.includes('Find a task by typing'))";
const card = "[...document.querySelectorAll('.wait')].find((e) => e.textContent.includes('Find a task by typing'))";

await page.goto('http://127.0.0.1:8092/', 1500);
await page.shot('r9-before', {});
await page.goto('http://127.0.0.1:8091/', 1500);
await page.shot('r10-after-empty', { 'A search box, as asked': 'input[type=search], input[data-testid*=search]' });
await page.type('input[type=search], input[data-testid*=search]', 'ven');
await page.wait(500);
await page.shot('r10-after', { 'Typing filters the list': 'input[type=search], input[data-testid*=search]', 'Only the matching task': '#tasks', 'The counts still cover everything': '[data-testid=summary]' });
await page.type('input[type=search], input[data-testid*=search]', 'zzz');
await page.wait(500);
await page.shot('r11-no-match', { 'It says so when nothing matches': '#tasks' });

await page.goto('http://127.0.0.1:8787/activity', 2500);
await page.until('!!' + card, 60);
await page.shot('r12-gate2', { 'Gate: the screens': `js:(${card}).querySelector('.tag')`, 'The human decision': `js:(${card}).querySelector('.btn.go')` });
await page.run(`(${card}).querySelector('.btn.go').click()`); await page.wait(2500);
await page.until(`(() => { const i = ${item}; return i && i.querySelector('.state.done') && i.querySelector('.meta a'); })()`, 240);
await page.wait(1500);
await page.shot('r13-done', { 'Finished': `js:(${item}).querySelector('.state')`, 'Every stop done': `js:(${item}).querySelector('.track')`, 'A pull request is open': `js:(${item}).querySelector('.meta a')` });
const link = await page.run(`(${item}).querySelector('.meta a').href`);
console.log('link', link);
await page.goto(link, 9000);
await page.shot('r14-pr', {
  'Closes the issue': 'js:[...document.querySelectorAll("p")].find((e) => e.textContent.trim().startsWith("Closes #"))',
  'The spec and the evidence, linked': 'js:[...document.querySelectorAll("h2,h3")].find((e) => e.textContent.trim() === "Evidence")?.nextElementSibling',
  'Yours to review and merge': 'js:[...document.querySelectorAll("span")].find((e) => e.textContent.trim() === "Open" && e.className.includes("State"))' },
  'js:[...document.querySelectorAll("p")].find((e) => e.textContent.trim().startsWith("Closes #"))');
await page.close();
