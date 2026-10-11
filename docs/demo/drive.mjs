// Drives a real Chrome window for the demo recording: clicks, typing, and screenshots.
// Each screenshot is saved with the on-screen position of the elements worth pointing at,
// so the video can draw a highlight exactly where the thing is.
//
//   import { open } from './drive.mjs';
//   const page = await open();
//   await page.goto('http://127.0.0.1:8787/');
//   await page.click('#new');
//   await page.shot('c1-add', { 'The form': '#newpanel' });
//   await page.close();

import { spawn } from 'node:child_process';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
export const WIDTH = 1208, HEIGHT = 596;   // the picture area of one video frame
const sleep = (ms) => new Promise((done) => setTimeout(done, ms));

export async function open(port = 9333) {
  const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${port}`, '--hide-scrollbars', '--disable-gpu',
    `--user-data-dir=${mkdtempSync(join(tmpdir(), 'factory-demo-'))}`, 'about:blank'], { stdio: 'ignore' });
  let target;
  for (let i = 0; i < 50 && !target; i++) {
    await sleep(200);
    try { target = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find((t) => t.type === 'page'); } catch { /* not up yet */ }
  }
  if (!target) throw new Error('Chrome did not start');
  const socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((done) => socket.addEventListener('open', done));
  let next = 0;
  const pending = new Map();
  socket.addEventListener('message', (event) => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) { pending.get(message.id)(message); pending.delete(message.id); }
  });
  const send = (method, params = {}) => new Promise((done, fail) => {
    const id = ++next;
    pending.set(id, (m) => (m.error ? fail(new Error(`${method}: ${m.error.message}`)) : done(m.result)));
    socket.send(JSON.stringify({ id, method, params }));
  });
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: WIDTH, height: HEIGHT, deviceScaleFactor: 2, mobile: false });

  const run = async (expression) => {
    const out = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
    if (out.exceptionDetails) throw new Error(out.exceptionDetails.exception?.description || out.exceptionDetails.text);
    return out.result.value;
  };
  // A selector is CSS, `text:Some words` for the smallest element with exactly that text, or `js:` and an expression.
  const find = (selector) => (selector.startsWith('js:') ? `(${selector.slice(3)})` : selector.startsWith('text:')
    ? `[...document.querySelectorAll('body *')].filter((e) => e.children.length < 3 && e.textContent.trim() === ${JSON.stringify(selector.slice(5))}).pop()`
    : `document.querySelector(${JSON.stringify(selector)})`);

  return {
    run,
    wait: sleep,
    // Through a blank page first, so a change of #fragment alone still loads the page afresh.
    async goto(url, settle = 1500) { await send('Page.navigate', { url: 'about:blank' }); await sleep(150); await send('Page.navigate', { url }); await sleep(settle); },
    async until(expression, seconds = 30) {
      for (let i = 0; i < seconds * 4; i++) { if (await run(expression)) return true; await sleep(250); }
      throw new Error(`gave up waiting for: ${expression}`);
    },
    async click(selector, settle = 500) {
      await run(`(() => { const e = ${find(selector)}; if (!e) throw new Error('nothing matches ${selector.replace(/'/g, '')}'); e.scrollIntoView({ block: 'center' }); e.click(); })()`);
      await sleep(settle);
    },
    async type(selector, text) {
      await run(`(() => { const e = ${find(selector)}; if (!e) throw new Error('nothing matches ${selector.replace(/'/g, '')}'); e.focus(); e.value = ${JSON.stringify(text)};
        e.dispatchEvent(new Event('input', { bubbles: true })); e.dispatchEvent(new Event('change', { bubbles: true })); })()`);
      await sleep(150);
    },
    // Scroll so `top` is near the top of the picture, take the screenshot, and record where each mark is.
    async shot(name, marks = {}, top = null) {
      if (top) await run(`(() => { const e = ${find(top)}; if (e) window.scrollTo(0, e.getBoundingClientRect().top + window.scrollY - 150); })()`);
      else await run('window.scrollTo(0, 0)');
      await sleep(1200);   // let sticky headers settle, or the marks land a row off
      const boxes = [];
      for (const [label, selector] of Object.entries(marks)) {
        const box = await run(`(() => { const e = ${find(selector)}; if (!e) return null; const r = e.getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; })()`);
        if (box) boxes.push({ label, box }); else console.error(`  (no element for mark "${label}")`);
      }
      const picture = await send('Page.captureScreenshot', { format: 'png' });
      writeFileSync(join(HERE, 'shots', `${name}.png`), Buffer.from(picture.data, 'base64'));
      writeFileSync(join(HERE, 'shots', `${name}.json`), JSON.stringify(boxes));
      console.log(`shot ${name}  (${boxes.length} marks)`);
    },
    async close() { socket.close(); chrome.kill(); await sleep(300); },
  };
}
