// Records the second gate: a person looks at the result, approves, and a pull request opens.
import { open } from './drive.mjs';
const page = await open();
const T = 'Show overall progress on the board';
const item = "[...document.querySelectorAll('.item')].find((e) => e.textContent.includes('" + T + "'))";
const card = "[...document.querySelectorAll('.wait')].find((e) => e.textContent.includes('" + T + "'))";
const bar = 'js:document.querySelector("[role=progressbar], progress, [data-testid*=progress]")';

await page.goto('http://127.0.0.1:8092/', 1500);
await page.shot('n9-before', { 'Only numbers: no sense of how far along': '#summary' });
await page.goto('http://127.0.0.1:8091/', 1500);
console.log('progress:', await page.run("(() => { const e = document.querySelector('[role=progressbar], progress, [data-testid*=progress]'); return e ? e.outerHTML.slice(0, 260) + ' || ' + (e.parentElement.textContent || '').trim().slice(0, 80) : 'none'; })()"));
await page.shot('n10-after', { 'A progress bar, built from that one issue': 'js:document.querySelector("[role=progressbar], progress, [data-testid*=progress]")?.parentElement', 'The existing summary is untouched': '[data-testid=summary]' });

await page.goto('http://127.0.0.1:8787/activity', 2500);
await page.until('!!' + card, 60);
await page.shot('n11-gate2', { 'Gate: the screens': 'js:(' + card + ").querySelector('.tag')", 'The human decision': 'js:(' + card + ").querySelector('.btn.go')" });
await page.run('(' + card + ").querySelector('.btn.go').click()"); await page.wait(2500);
await page.until("(() => { const i = " + item + "; return i && i.querySelector('.state.done') && i.querySelector('.meta a'); })()", 240);
await page.wait(1500);
await page.shot('n12-done', { 'Finished': 'js:(' + item + ").querySelector('.state')", 'Every stage done': 'js:(' + item + ").querySelector('.track')", 'A pull request is open': 'js:(' + item + ").querySelector('.meta a')" });
const link = await page.run('(' + item + ").querySelector('.meta a').href");
console.log('link', link);
await page.goto(link, 9000);
await page.shot('n13-pr', {
  'Closes the issue': 'js:[...document.querySelectorAll("p")].find((e) => e.textContent.trim().startsWith("Closes #"))',
  'The checker’s evidence, linked': 'js:[...document.querySelectorAll("h2,h3")].find((e) => e.textContent.trim() === "Evidence")?.nextElementSibling' },
  'js:[...document.querySelectorAll("p")].find((e) => e.textContent.trim().startsWith("Closes #"))');
await page.close();
