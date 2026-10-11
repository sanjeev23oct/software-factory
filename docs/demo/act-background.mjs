// Records the factory running in the background: a bug is filed, and the scheduled job picks it up.
import { open } from './drive.mjs';
const page = await open();
await page.goto('http://127.0.0.1:8787/activity', 2500);
await page.shot('b1-background', { 'No one is at the keyboard': '#pulse' });

await page.goto('https://github.com/sanjeev23oct/factory-demo-api/issues/4', 6000);
await page.run("window.scrollTo(0, 0)");
await page.shot('b2-issue', { 'The label the factory watches for': 'text:bug', 'Assigned to the right person': 'text:sanjeev23oct' });

await page.goto('http://127.0.0.1:8787/activity', 2500);
await page.click('#pass', 2000);
await page.until("[...document.querySelectorAll('.item-top b')].some((b) => b.textContent.includes('trailing slash'))", 120);
await page.wait(6000);
await page.run("(() => { const i = [...document.querySelectorAll('.item')].find((e) => e.textContent.includes('trailing slash')); i.id = 'demo-item'; })()");
await page.shot('b3-picked-up', { 'A pass is running': '#pulse', 'Picked up, and an agent is already at work': '#demo-item' });
await page.close();
