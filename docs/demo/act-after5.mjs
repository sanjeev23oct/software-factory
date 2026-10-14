// Re-takes the "after" picture for the due-date feature.
import { open } from './drive.mjs';
const page = await open();
await page.goto('http://127.0.0.1:8091/', 1500);
console.log(await page.run("[...document.querySelectorAll('.due')].map((e) => e.textContent).join(' | ')"));
await page.shot('q10-after', {
  'A due date next to the title': 'js:[...document.querySelectorAll(".due")].find((e) => !/today/i.test(e.textContent))',
  'Due today, in words': 'js:[...document.querySelectorAll(".due")].find((e) => /today/i.test(e.textContent))' });
await page.close();
