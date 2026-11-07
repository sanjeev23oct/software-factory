// Records the second approval: accepted screens become baselines, and the merge request carries them.
import { GITLAB, PROJECT, gitlab, note, reply } from '../clients-demo/client.mjs';

const ISSUE = `${GITLAB}/${PROJECT}/-/issues/2`;
const page = await gitlab(9431);
const openIssue = async () => { await page.goto(ISSUE, 8000); await page.until('document.querySelectorAll("[data-testid=work-item-note-body]").length > 0', 90); };
await openIssue();
await reply(page, 'approve');
await page.wait(3000);
const mine = 'js:[...document.querySelectorAll("[data-testid=work-item-note-body]")].filter((e) => e.textContent.trim() === "approve").pop()';
await page.shot('v16-approve-screens', { 'Accepted: these screens become baselines': mine }, mine);
// The factory saves the baselines and opens the merge request on its next pass.
let link = null;
for (let i = 0; i < 40 && !link; i++) {
  await page.wait(20000);
  await openIssue();
  link = await page.run(`(() => { const n = ${note('Factory progress', 'Merge request opened').slice(3)}; return n && [...n.querySelectorAll('a')].map((a) => a.href).find((h) => h.includes('/merge_requests/')); })()`);
}
console.log('merge request', link);
const done = note('Factory progress', 'baselines');
await page.shot('v17-baselines-saved', { 'Approving saved the baselines': `js:[...(${done.slice(3)}).querySelectorAll('tr')].find((r) => r.textContent.includes('baselines'))`,
  'Merge request opened': `js:[...(${done.slice(3)}).querySelectorAll('tr')].find((r) => r.textContent.includes('Merge request opened'))` }, done);
await page.goto(link + '/diffs', 12000);
await page.until('document.body.innerText.includes("baselines")', 60);
await page.wait(3000);
await page.shot('v18-mr-baselines', { 'Baselines ship with the change': 'js:[...document.querySelectorAll("a, span, button")].find((e) => /baselines/.test(e.textContent) && e.textContent.length < 80)' });
await page.close();
