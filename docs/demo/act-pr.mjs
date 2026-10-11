import { open } from './drive.mjs';
const page = await open();
await page.goto('https://github.com/sanjeev23oct/factory-demo-ui/pull/2', 9000);
console.log(await page.run("document.title + ' | h: ' + [...document.querySelectorAll('h2,h3')].map((e) => e.textContent.trim()).slice(0, 8).join(' / ')"));
await page.shot('p6-ui-pr', {
  'Closes the issue': 'js:[...document.querySelectorAll("p")].find((e) => e.textContent.trim().startsWith("Closes #1"))',
  'Every evidence file, linked': 'js:[...document.querySelectorAll("h2,h3")].find((e) => e.textContent.trim() === "Evidence")?.nextElementSibling',
  'One commit per stop': 'js:[...document.querySelectorAll("a")].find((e) => e.textContent.trim().startsWith("requirements: Show"))' },
  'js:[...document.querySelectorAll("p")].find((e) => e.textContent.trim().startsWith("Closes #1"))');
await page.close();
