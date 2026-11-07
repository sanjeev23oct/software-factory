#!/usr/bin/env node
// Checks a built screen against a reference screenshot: the measured layer of visual verification.
//
//   node factory/scripts/visual_verify.mjs --root CHECKOUT --contract reference/dashboard.json --out evidence/visual/dashboard
//   node factory/scripts/visual_verify.mjs --root CHECKOUT --contract reference/dashboard.json --capture shot.png
//
// --capture renders the screen, saves it, and prints each region's measured box: how a reference
// and its contract are made from a screen someone has already accepted.
//
// The contract names the reference image, the viewport, and regions: each region is an element
// (a CSS selector, or a data-testid) with the box it should fill on the reference, the text it
// must hold, and the colours it must use. The script serves CHECKOUT as static files, renders the
// screen in headless Chrome, measures every region, compares it with the reference, and writes:
//
//   actual.png    the screen as built
//   diff.png      a heatmap of where it differs from the reference
//   compare.png   reference, actual and diff side by side, with each region's box and result
//   report.json   every value, threshold and verdict
//
// Exit 0 when every region passes, 1 when any fails, 2 when it could not check at all.
// Only Node's built-ins and Chrome: Chrome renders the screen and does the image arithmetic.

import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { dirname, extname, join, normalize, resolve } from 'node:path';

const DEFAULTS = { iou: 0.8, similarity: 0.85, deltaE: 5 };
const FIXED_TIME = Date.UTC(2026, 0, 15, 12, 0, 0);   // pages that read the clock render the same every run
const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml', '.jpg': 'image/jpeg', '.woff2': 'font/woff2' };
const sleep = (ms) => new Promise((done) => setTimeout(done, ms));

function args() {
  const out = {};
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i += 2) out[argv[i].replace(/^--/, '')] = argv[i + 1];
  for (const need of ['root', 'contract']) if (!out[need]) fail(`missing --${need}`);
  if (!out.out && !out.capture) fail('missing --out (or --capture)');
  return out;
}

function fail(message) {
  console.error(`visual-verify: ${message}`);
  process.exit(2);
}

function chromePath() {
  const candidates = [process.env.CHROME, '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable'];
  const found = candidates.find((path) => path && existsSync(path));
  if (!found) fail('no Chrome found; set CHROME to its path');
  return found;
}

function serve(root) {
  const server = createServer((request, response) => {
    const path = normalize(decodeURIComponent(new URL(request.url, 'http://x').pathname)).replace(/^(\.\.[/\\])+/, '');
    const file = join(root, path.endsWith('/') ? join(path, 'index.html') : path);
    if (!file.startsWith(root) || !existsSync(file)) { response.writeHead(404); response.end(); return; }
    response.writeHead(200, { 'Content-Type': MIME[extname(file)] || 'application/octet-stream' });
    response.end(readFileSync(file));
  });
  return new Promise((done) => server.listen(0, '127.0.0.1', () => done(server)));
}

async function launch() {
  const profile = mkdtempSync(join(tmpdir(), 'visual-verify-'));
  // In a CI container Chrome can't set up its sandbox and /dev/shm is tiny; on a laptop it keeps both.
  const container = process.env.CI || (process.getuid && process.getuid() === 0);
  const chrome = spawn(chromePath(), ['--headless=new', '--remote-debugging-port=0', '--hide-scrollbars', '--disable-gpu',
    '--font-render-hinting=none', '--force-color-profile=srgb', '--no-first-run', `--user-data-dir=${profile}`,
    ...(container ? ['--no-sandbox', '--disable-dev-shm-usage'] : []), 'about:blank'],
  { stdio: 'ignore' });
  let port;
  for (let i = 0; i < 100 && !port; i++) {
    await sleep(100);
    try { port = readFileSync(join(profile, 'DevToolsActivePort'), 'utf8').split('\n')[0]; } catch { /* not up yet */ }
  }
  if (!port) fail('Chrome did not start');
  let target;
  for (let i = 0; i < 50 && !target; i++) {
    try { target = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find((t) => t.type === 'page'); } catch { await sleep(100); }
  }
  const socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((done) => socket.addEventListener('open', done));
  let next = 0;
  const pending = new Map();
  socket.addEventListener('message', (event) => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) { pending.get(message.id)(message); pending.delete(message.id); }
  });
  const send = (method, params = {}) => new Promise((done, reject) => {
    const id = ++next;
    pending.set(id, (m) => (m.error ? reject(new Error(`${method}: ${m.error.message}`)) : done(m.result)));
    socket.send(JSON.stringify({ id, method, params }));
  });
  const run = async (expression) => {
    const out = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
    if (out.exceptionDetails) throw new Error(out.exceptionDetails.exception?.description || out.exceptionDetails.text);
    return out.result.value;
  };
  // Chrome writes to its profile while it shuts down; remove the profile only after it has exited.
  const close = async () => {
    socket.close();
    const exited = new Promise((done) => chrome.once('exit', done));
    chrome.kill();
    await Promise.race([exited, sleep(3000)]);
    try { rmSync(profile, { recursive: true, force: true }); } catch { /* a stray lock file is harmless */ }
  };
  return { send, run, close };
}

// Measured in the page: where each region's element is, what it says, and the colours it uses.
const MEASURE = (regions) => `(() => {
  const out = [];
  for (const region of ${JSON.stringify(regions)}) {
    const selector = region.selector || '[data-testid="' + region.testid + '"]';
    const element = document.querySelector(selector);
    if (!element) { out.push({ found: false }); continue; }
    const box = element.getBoundingClientRect(), style = getComputedStyle(element);
    const visible = box.width > 0 && box.height > 0 && style.visibility !== 'hidden' && style.display !== 'none' && Number(style.opacity) > 0;
    out.push({ found: true, visible, box: [box.x, box.y, box.width, box.height],
      text: element.innerText || element.textContent || '', color: style.color, background: style.backgroundColor });
  }
  return out;
})()`;

// Run in a blank page: compares reference and actual, region by region, and draws the evidence.
const COMPARE = (reference, actual, regions, mask) => `(async () => {
  const load = (src) => new Promise((done) => { const i = new Image(); i.onload = () => done(i); i.src = src; });
  const [ref, act] = await Promise.all([load(${JSON.stringify(reference)}), load(${JSON.stringify(actual)})]);
  const W = act.width, H = act.height;
  const pixels = (image) => { const c = new OffscreenCanvas(W, H), g = c.getContext('2d'); g.drawImage(image, 0, 0, W, H); return g.getImageData(0, 0, W, H).data; };
  const a = pixels(ref), b = pixels(act);
  const masked = new Uint8Array(W * H);
  for (const [x, y, w, h] of ${JSON.stringify(mask)}) for (let j = Math.max(0, y); j < Math.min(H, y + h); j++) for (let i = Math.max(0, x); i < Math.min(W, x + w); i++) masked[j * W + i] = 1;
  const grey = (d, k) => 0.299 * d[k] + 0.587 * d[k + 1] + 0.114 * d[k + 2];
  // SSIM over 8x8 windows, greyscale; a window touching the mask is left out.
  const ssim = ([x0, y0, w0, h0]) => {
    const C1 = (0.01 * 255) ** 2, C2 = (0.03 * 255) ** 2;
    let total = 0, count = 0;
    for (let y = Math.max(0, Math.round(y0)); y + 8 <= Math.min(H, Math.round(y0 + h0)); y += 8) {
      for (let x = Math.max(0, Math.round(x0)); x + 8 <= Math.min(W, Math.round(x0 + w0)); x += 8) {
        let skip = false, ma = 0, mb = 0;
        const pa = [], pb = [];
        for (let j = 0; j < 8 && !skip; j++) for (let i = 0; i < 8; i++) {
          const p = (y + j) * W + x + i;
          if (masked[p]) { skip = true; break; }
          pa.push(grey(a, p * 4)); pb.push(grey(b, p * 4));
        }
        if (skip) continue;
        for (let n = 0; n < 64; n++) { ma += pa[n]; mb += pb[n]; }
        ma /= 64; mb /= 64;
        let va = 0, vb = 0, cov = 0;
        for (let n = 0; n < 64; n++) { va += (pa[n] - ma) ** 2; vb += (pb[n] - mb) ** 2; cov += (pa[n] - ma) * (pb[n] - mb); }
        va /= 63; vb /= 63; cov /= 63;
        total += ((2 * ma * mb + C1) * (2 * cov + C2)) / ((ma * ma + mb * mb + C1) * (va + vb + C2));
        count++;
      }
    }
    return count ? total / count : null;
  };
  const scores = ${JSON.stringify(regions)}.map((r) => ssim(r.box));
  // diff.png: the built screen, faded, with differences painted red by strength.
  const diff = new OffscreenCanvas(W, H), dg = diff.getContext('2d'), out = dg.createImageData(W, H);
  for (let p = 0; p < W * H; p++) {
    const k = p * 4, d = masked[p] ? 0 : Math.max(Math.abs(a[k] - b[k]), Math.abs(a[k + 1] - b[k + 1]), Math.abs(a[k + 2] - b[k + 2]));
    const base = 235 + grey(b, k) * 0.08;
    out.data[k] = Math.min(255, base + d); out.data[k + 1] = Math.max(0, base - d * 2); out.data[k + 2] = Math.max(0, base - d * 2); out.data[k + 3] = 255;
  }
  dg.putImageData(out, 0, 0);
  return { scores, diff: await (await diff.convertToBlob()).arrayBuffer().then((buf) => Array.from(new Uint8Array(buf))),
    size: [W, H], panel: { gap: 24, head: 44 } };
})()`;

// Boxes drawn on compare.png once the verdicts are known.
const DRAW = (base, size, panel, boxes) => `(async () => {
  const load = (src) => new Promise((done) => { const i = new Image(); i.onload = () => done(i); i.src = src; });
  const image = await load(${JSON.stringify(base)});
  const [W] = ${JSON.stringify(size)}, { gap, head } = ${JSON.stringify(panel)};
  const c = new OffscreenCanvas(image.width, image.height), g = c.getContext('2d');
  g.drawImage(image, 0, 0);
  for (const b of ${JSON.stringify(boxes)}) {
    const x = gap + b.panel * (W + gap) + b.box[0], y = head + b.box[1];
    g.strokeStyle = b.pass ? '#2fbf71' : '#ff4d4f'; g.lineWidth = 3; g.strokeRect(x, y, b.box[2], b.box[3]);
    g.font = 'bold 15px system-ui, sans-serif';
    const label = (b.pass ? '✓ ' : '✗ ') + b.name, w = g.measureText(label).width + 12;
    g.fillStyle = b.pass ? '#2fbf71' : '#ff4d4f'; g.fillRect(x, y - 22, w, 22);
    g.fillStyle = '#fff'; g.fillText(label, x + 6, y - 6);
  }
  return Array.from(new Uint8Array(await (await c.convertToBlob()).arrayBuffer()));
})()`;

// CIEDE2000 colour difference, from CSS rgb() strings or #hex.
function rgb(value) {
  if (!value) return null;
  const hex = value.match(/^#([0-9a-f]{6})$/i);
  if (hex) return [0, 2, 4].map((i) => parseInt(hex[1].slice(i, i + 2), 16));
  const m = value.match(/rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?\)/);
  return m && (m[4] === undefined || Number(m[4]) > 0) ? [Number(m[1]), Number(m[2]), Number(m[3])] : null;
}

function lab([r, g, b]) {
  const lin = (c) => { c /= 255; return c > 0.04045 ? ((c + 0.055) / 1.055) ** 2.4 : c / 12.92; };
  const [R, G, B] = [lin(r), lin(g), lin(b)];
  const xyz = [(R * 0.4124 + G * 0.3576 + B * 0.1805) / 0.95047, R * 0.2126 + G * 0.7152 + B * 0.0722, (R * 0.0193 + G * 0.1192 + B * 0.9505) / 1.08883];
  const f = (t) => (t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116);
  const [fx, fy, fz] = xyz.map(f);
  return [116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)];
}

export function deltaE2000(one, two) {
  const [L1, a1, b1] = lab(one), [L2, a2, b2] = lab(two);
  const rad = Math.PI / 180, C1 = Math.hypot(a1, b1), C2 = Math.hypot(a2, b2), Cm = (C1 + C2) / 2;
  const G = 0.5 * (1 - Math.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)));
  const a1p = a1 * (1 + G), a2p = a2 * (1 + G), C1p = Math.hypot(a1p, b1), C2p = Math.hypot(a2p, b2);
  const hue = (b, a) => { const h = Math.atan2(b, a) / rad; return h < 0 ? h + 360 : h; };
  const h1p = hue(b1, a1p), h2p = hue(b2, a2p), dLp = L2 - L1, dCp = C2p - C1p;
  let dhp = 0;
  if (C1p * C2p) dhp = Math.abs(h2p - h1p) <= 180 ? h2p - h1p : h2p - h1p > 180 ? h2p - h1p - 360 : h2p - h1p + 360;
  const dHp = 2 * Math.sqrt(C1p * C2p) * Math.sin((dhp / 2) * rad);
  const Lm = (L1 + L2) / 2, Cmp = (C1p + C2p) / 2;
  let hm = h1p + h2p;
  if (C1p * C2p) hm = Math.abs(h1p - h2p) <= 180 ? hm / 2 : hm < 360 ? (hm + 360) / 2 : (hm - 360) / 2;
  const T = 1 - 0.17 * Math.cos((hm - 30) * rad) + 0.24 * Math.cos(2 * hm * rad) + 0.32 * Math.cos((3 * hm + 6) * rad) - 0.2 * Math.cos((4 * hm - 63) * rad);
  const dTh = 30 * Math.exp(-(((hm - 275) / 25) ** 2)), Rc = 2 * Math.sqrt(Cmp ** 7 / (Cmp ** 7 + 25 ** 7));
  const Sl = 1 + (0.015 * (Lm - 50) ** 2) / Math.sqrt(20 + (Lm - 50) ** 2), Sc = 1 + 0.045 * Cmp, Sh = 1 + 0.015 * Cmp * T;
  const Rt = -Math.sin(2 * dTh * rad) * Rc;
  return Math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh));
}

function iou([ax, ay, aw, ah], [bx, by, bw, bh]) {
  const w = Math.max(0, Math.min(ax + aw, bx + bw) - Math.max(ax, bx)), h = Math.max(0, Math.min(ay + ah, by + bh) - Math.max(ay, by));
  const overlap = w * h, union = aw * ah + bw * bh - overlap;
  return union > 0 ? overlap / union : 0;
}

const round = (n, places = 3) => (n === null || n === undefined ? null : Math.round(n * 10 ** places) / 10 ** places);

async function main() {
  const opts = args();
  const root = resolve(opts.root), contractPath = resolve(opts.contract), out = opts.out && resolve(opts.out);
  const contract = JSON.parse(readFileSync(contractPath, 'utf8'));
  const [W, H] = contract.viewport || [1280, 800];
  const referencePath = resolve(dirname(contractPath), contract.reference || '');
  if (!opts.capture && !existsSync(referencePath)) fail(`no reference image at ${referencePath}`);
  const reference = opts.capture ? null : 'data:image/png;base64,' + readFileSync(referencePath).toString('base64');
  const mask = contract.mask || [];

  const server = await serve(root);
  const browser = await launch();
  let result;
  try {
    await browser.send('Page.enable');
    await browser.send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
    await browser.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
    await browser.send('Page.addScriptToEvaluateOnNewDocument', { source: `{ const T = ${FIXED_TIME}; const D = Date;
      Date = class extends D { constructor(...a) { super(...(a.length ? a : [T])); } static now() { return T; } }; }` });
    await browser.send('Page.navigate', { url: `http://127.0.0.1:${server.address().port}/${contract.url || 'index.html'}` });
    await browser.run(`new Promise((done) => { const ready = () => document.fonts.ready.then(() => setTimeout(done, ${contract.settle_ms ?? 400}));
      document.readyState === 'complete' ? ready() : addEventListener('load', ready); })`);
    const measured = await browser.run(MEASURE(contract.regions));
    const shot = await browser.send('Page.captureScreenshot', { format: 'png', clip: { x: 0, y: 0, width: W, height: H, scale: 1 } });
    if (opts.capture) {
      writeFileSync(resolve(opts.capture), Buffer.from(shot.data, 'base64'));
      console.log(JSON.stringify(contract.regions.map((r, n) => ({ name: r.name, found: measured[n].found,
        box: measured[n].box && measured[n].box.map((v) => round(v, 1)), color: measured[n].color, background: measured[n].background })), null, 2));
      return;
    }
    const actual = 'data:image/png;base64,' + shot.data;
    await browser.send('Page.navigate', { url: 'about:blank' });
    await sleep(200);
    const scored = await browser.run(COMPARE(reference, actual, contract.regions, mask));

    const regions = contract.regions.map((region, n) => {
      const m = measured[n], t = { ...DEFAULTS, ...region };
      const checks = {};
      const report = { name: region.name, selector: region.selector || `[data-testid="${region.testid}"]`, reference_box: region.box };
      checks.present = m.found && m.visible;
      if (!checks.present) return { ...report, found: m.found, visible: !!m.visible, checks, pass: false };
      report.box = m.box.map((v) => round(v, 1));
      report.iou = round(iou(region.box, m.box));
      checks.geometry = report.iou >= t.iou;
      if (region.text) {
        report.missing_text = region.text.filter((s) => !m.text.includes(s));
        checks.text = report.missing_text.length === 0;
      }
      report.colors = [];
      for (const [property, expected] of Object.entries({ color: region.color, background: region.background })) {
        if (!expected) continue;
        const delta = rgb(m[property]) && rgb(expected) ? deltaE2000(rgb(expected), rgb(m[property])) : Infinity;
        report.colors.push({ property, expected, actual: m[property], delta_e: round(delta, 2) });
      }
      if (report.colors.length) checks.color = report.colors.every((c) => c.delta_e <= t.deltaE);
      report.similarity = round(scored.scores[n]);
      if (report.similarity !== null && region.similarity !== false) checks.similarity = report.similarity >= t.similarity;
      report.thresholds = { iou: t.iou, similarity: region.similarity === false ? null : t.similarity, delta_e: t.deltaE };
      return { ...report, checks, pass: Object.values(checks).every(Boolean) };
    });

    mkdirSync(out, { recursive: true });
    writeFileSync(join(out, 'actual.png'), Buffer.from(shot.data, 'base64'));
    writeFileSync(join(out, 'diff.png'), Buffer.from(scored.diff));
    const panelBase = 'data:image/png;base64,' + Buffer.from(await browser.run(`(async () => {
      const load = (src) => new Promise((done) => { const i = new Image(); i.onload = () => done(i); i.src = src; });
      const [W, H] = ${JSON.stringify(scored.size)}, { gap, head } = ${JSON.stringify(scored.panel)};
      const imgs = await Promise.all([${JSON.stringify(reference)}, ${JSON.stringify(actual)}, ${JSON.stringify('data:image/png;base64,' + Buffer.from(scored.diff).toString('base64'))}].map(load));
      const c = new OffscreenCanvas(W * 3 + gap * 4, H + head + gap), g = c.getContext('2d');
      g.fillStyle = '#0b121c'; g.fillRect(0, 0, c.width, c.height);
      ['Reference', 'Built', 'Difference'].forEach((label, n) => { const x = gap + n * (W + gap);
        g.fillStyle = '#e8eef7'; g.font = 'bold 22px system-ui, sans-serif'; g.fillText(label, x, 30); g.drawImage(imgs[n], x, head, W, H); });
      return Array.from(new Uint8Array(await (await c.convertToBlob()).arrayBuffer()));
    })()`)).toString('base64');
    const boxes = [];
    regions.forEach((r) => {
      boxes.push({ panel: 0, box: r.reference_box, name: r.name, pass: r.pass });
      if (r.box) boxes.push({ panel: 1, box: r.box, name: r.name, pass: r.pass });
    });
    writeFileSync(join(out, 'compare.png'), Buffer.from(await browser.run(DRAW(panelBase, scored.size, scored.panel, boxes))));

    const failures = regions.filter((r) => !r.pass).map((r) => ({ region: r.name,
      failed: Object.entries(r.checks).filter(([, ok]) => !ok).map(([name]) => name) }));
    result = { screen: contract.name || 'screen', reference: contract.reference, viewport: [W, H], mask, regions, failures, pass: failures.length === 0 };
    writeFileSync(join(out, 'report.json'), JSON.stringify(result, null, 2) + '\n');
  } finally {
    await browser.close();
    server.close();
  }
  if (!result) return;
  for (const r of result.regions) {
    const failed = Object.entries(r.checks).filter(([, ok]) => !ok).map(([name]) => name);
    console.log(`${r.pass ? 'PASS' : 'FAIL'}  ${r.name.padEnd(16)} ${failed.length ? 'failed: ' + failed.join(', ') : ''}`.trimEnd());
  }
  console.log(result.pass ? 'visual-verify: PASS' : `visual-verify: FAIL (${result.failures.length} region(s))`);
  process.exit(result.pass ? 0 : 1);
}

if (import.meta.url === `file://${process.argv[1]}`) main().catch((e) => fail(e.stack || e.message));
