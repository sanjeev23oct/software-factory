// Records the second gate of the maker-checker run: a person looks at the result, approves, and a pull request opens.
import { open } from './drive.mjs';
const page = await open();
const T = 'Show how many tasks are in each filter';
const item = "[...document.querySelectorAll('.item')].find((e) => e.textContent.includes('" + T + "'))";
const card = "[...document.querySelectorAll('.wait')].find((e) => e.textContent.includes('" + T + "'))";

await page.goto('http://127.0.0.1:8092/', 1500);
await page.shot('m9-before', { 'No way to tell how many tasks are behind each filter': '.filters' });
await page.goto('http://127.0.0.1:8091/', 1500);
console.log('labels:', await page.run("[...document.querySelectorAll('[data-filter]')].map((b) => b.textContent.trim() + ' | ' + b.getAttribute('aria-label')).join(' ; ')"));
await page.shot('m10-after', { 'Each filter now shows its count': '.filters', 'The summary is unchanged, as asked': '[data-testid=summary]' });

await page.goto('http://127.0.0.1:8787/activity', 2500);
await page.until('!!' + card, 60);
await page.shot('m11-gate2', { 'Gate: the screens': 'js:(' + card + ").querySelector('.tag')", 'The human decision': 'js:(' + card + ").querySelector('.btn.go')" });
await page.run('(' + card + ").querySelector('.btn.go').click()"); await page.wait(2500);
await page.until("(() => { const i = " + item + "; return i && i.querySelector('.state.done') && i.querySelector('.meta a'); })()", 240);
await page.wait(1500);
await page.shot('m12-done', { 'Finished': 'js:(' + item + ").querySelector('.state')", 'Every stop done': 'js:(' + item + ").querySelector('.track')", 'A pull request is open': 'js:(' + item + ").querySelector('.meta a')" });
const link = await page.run('(' + item + ").querySelector('.meta a').href");
console.log('link', link);
await page.goto(link, 9000);
await page.shot('m13-pr', {
  'Closes the issue': 'js:[...document.querySelectorAll("p")].find((e) => e.textContent.trim().startsWith("Closes #"))',
  'The checker’s evidence, linked': 'js:[...document.querySelectorAll("h2,h3")].find((e) => e.textContent.trim() === "Evidence")?.nextElementSibling' },
  'js:[...document.querySelectorAll("p")].find((e) => e.textContent.trim().startsWith("Closes #"))');
await page.goto(link + '/commits', 9000);
await page.shot('m14-commits', { 'Maker and checker commits alternate': 'js:[...document.querySelectorAll("a")].find((e) => e.textContent.trim().startsWith("check (checker)"))?.closest("li, div[class*=Row], div")' });
await page.close();
