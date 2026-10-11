// Records one idea going through the feature route: picked up in the background, approved at the gate, built.
import { open } from './drive.mjs';
const page = await open();
const item = "[...document.querySelectorAll('.item')].find((e) => e.textContent.includes('Find a task by typing'))";
const card = "[...document.querySelectorAll('.wait')].find((e) => e.textContent.includes('Find a task by typing'))";
const tag = async () => { await page.run("(() => { const i = " + item + "; if (i) i.id = 'demo-item'; const c = " + card + "; if (c) c.id = 'demo-card'; })()"); };

await page.goto('https://github.com/sanjeev23oct/factory-demo-ui/issues/3', 8000);
await page.shot('r1-issue', { 'The label this route watches for': 'text:feature', 'Assigned to the right person': 'text:sanjeev23oct' });

await page.goto('http://127.0.0.1:8787/activity', 2500);
await page.shot('r2-idle', { 'The factory is already running': '#pulse' });
await page.click('#pass', 2000);
await page.until('!!' + item, 180);
await page.wait(5000); await tag();
await page.shot('r3-picked-up', { 'A pass is running': '#pulse-title', 'Picked up without anyone asking': '#demo-item .item-top', 'An agent is writing the requirements': '#demo-item .track .now' });

await page.until('!!' + card, 600); await tag();
await page.shot('r4-gate', { 'The route has stopped at a gate': '#demo-card .tag', 'What the agent wrote': '#demo-card .doc', 'Waiting for a person': '#demo-card .btn.go' });
await page.click('#demo-card .doc summary', 700); await tag();
await page.shot('r5-read', { 'Read the requirements before approving': '#demo-card .doc pre' }, '#demo-card');
await page.run("document.querySelector('#demo-card .doc').open = false");
await page.click('#demo-card input[data-skip]', 400); await tag();
await page.shot('r6-approve', { 'Optional stop: skipped for a small change': '#demo-card label', 'The human decision': '#demo-card .btn.go' });
await page.click('#demo-card .btn.go', 2000);
await page.until('!' + card, 90);
await page.until("(() => { const i = " + item + "; return i && [...i.querySelectorAll('.track .now')].some((n) => n.textContent.trim() === 'build'); })()", 900);
await page.wait(4000); await tag();
await page.shot('r7-building', { 'Approved: the gate is behind it': 'js:[...document.querySelectorAll("#demo-item .track span")].find((n) => n.textContent.includes("gate: requirements"))', 'Agents are building now': '#demo-item .track .now', 'Nobody is at the keyboard': '#pulse-title' });

await page.until('!!' + card, 2400); await tag();
await page.shot('r8-gate2', { 'Built, checked and tested': 'js:[...document.querySelectorAll(".item")].find((e) => e.textContent.includes("Find a task by typing")).querySelector(".track")', 'Stopped again: look at the screens': '#demo-card .tag' });
await page.close();
