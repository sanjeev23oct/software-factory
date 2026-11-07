// Records the build and the screens gate of a visual request: the inner loop's failures, the plan's
// visual gate, reference vs built, and the result running.
import { GITLAB, PROJECT, SITE, gitlab, note, site } from '../clients-demo/client.mjs';

const ISSUE = `${GITLAB}/${PROJECT}/-/issues/2`, SPEC = 'specs/2-build-this-customer-dashboard-matching-t';
const BLOB = `${GITLAB}/${PROJECT}/-/blob/factory/GL2/${SPEC}`;
const page = await gitlab(9421);
const openIssue = async () => { await page.goto(ISSUE, 8000); await page.until('document.querySelectorAll("[data-testid=work-item-note-body]").length > 0', 90); };
await openIssue();
const build = note('Factory progress', 'checker failed'), gate = note('waiting for you', 'approve-screens');
const row = (words, nth = 0) => `js:[...(${build.slice(3)}).querySelectorAll('tr')].filter((r) => r.textContent.includes(${JSON.stringify(words)}))[${nth}]`;
await page.shot('v08-inner-loop', { 'Checker fails the page: measured': row('checker failed', 0),
  'Fails it again: judged by eye': row('checker failed', 1), 'Third maker: passes': row('checker passed', 0) }, row('checker failed', 0));
await page.shot('v09-outer-loop', { 'Evidence re-checked by script': row('check-evidence', 1),
  'Visual verify: every region passes': row('visual-verify'), 'Then a preview': row('preview') }, row('Every task built'));
await page.shot('v10-gate', { 'Reference vs built, in the gate notice': `js:(${gate.slice(3)}).querySelector('img')`,
  'Try it': `js:[...(${gate.slice(3)}).querySelectorAll('a')].find((a) => a.textContent.includes('factory.justpush.cloud'))` }, gate);

await page.goto(`${BLOB}/tasks.md`, 8000);
await page.until('!!document.querySelector(".md h1, article h1, .blob-viewer h1")', 60);
const cat4 = 'js:[...document.querySelectorAll("blockquote p, blockquote")].find((e) => /Cat 4/.test(e.textContent))';
await page.shot('v11-visual-gate', { 'The plan gives the page a visual gate': cat4 }, cat4);
await page.goto(`${GITLAB}/${PROJECT}/-/raw/factory/GL2/${SPEC}/evidence/visual/customers/compare.png`, 6000);
await page.shot('v12-compare', {});
await page.goto(`${BLOB}/evidence/visual/customers/findings.json`, 8000);
await page.wait(2500);
await page.shot('v13-findings', {});
await page.close();

const s = await site(9422);
await s.goto(`${SITE}/GL2/`, 4000);
await s.shot('v14-built', {});
await s.goto(`${SITE}/status/`, 3000);
await s.shot('v15-status', { 'Two requests: one done, one waiting': 'main' });
await s.close();
