// Records a person at the gate: reading what the agents did, then approving.
import { open } from './drive.mjs';
const page = await open();
await page.goto('http://127.0.0.1:8787/activity', 2500);
await page.until("document.querySelector('.wait')");
await page.shot('a1-waiting', { 'The factory stopped here and is waiting': '.wait .tag', 'What the agents produced, to read first': '.wait .doc' });

await page.click('.wait .doc summary', 600);
await page.shot('a2-read', { 'The reproduction and the fix, in the agents’ words': '.wait .doc pre' }, '.wait');

await page.run("document.querySelector('.wait .doc').open = false");
await page.shot('a3-approve', { 'A person decides': '.wait .btn.go' });

await page.click('.wait .btn.go', 1500);
await page.until("!document.querySelector('.wait')", 60);
await page.until("[...document.querySelectorAll('.item')].some((e) => e.textContent.includes('trailing slash') && e.querySelector('.state.done'))", 180);
await page.wait(1500);
await page.run("(() => { const i = [...document.querySelectorAll('.item')].find((e) => e.textContent.includes('trailing slash')); i.id = 'demo-item'; i.querySelector('.meta a').id = 'demo-link'; })()");
await page.shot('a4-approved', { 'Approved: the route finished': '#demo-item .state', 'A pull request is open': '#demo-link' });
await page.close();
