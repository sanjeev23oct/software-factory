// Records the first gate of a visual request: the reference, the region contract, and the approval.
import { GITLAB, PROJECT, gitlab, note, reply } from '../clients-demo/client.mjs';

const ISSUE = `${GITLAB}/${PROJECT}/-/issues/2`, SPEC = 'specs/2-build-this-customer-dashboard-matching-t';
const BLOB = `${GITLAB}/${PROJECT}/-/blob/factory/GL2/${SPEC}`;
const page = await gitlab(9411);
const openIssue = async () => { await page.goto(ISSUE, 8000); await page.until('document.querySelectorAll("[data-testid=work-item-note-body]").length > 0', 90); };
await openIssue();
const progress = note('Factory progress', 'visual-spec'), gate = note('waiting for you', 'approve-requirements');
const row = (words) => `js:[...(${progress.slice(3)}).querySelectorAll('tr')].find((r) => r.textContent.includes(${JSON.stringify(words)}))`;
await page.shot('v03-progress', { 'The reference is saved from the issue': row('read-issue'),
  'The visual spec writes the contract': row('visual-spec') }, progress);
await page.shot('v04-gate', { 'Approve the contract with the requirements': gate }, gate);
await page.goto(`${BLOB}/reference/customers.json`, 8000);
await page.until('!!document.querySelector(".blob-content, .file-content, pre, table")', 60);
await page.wait(1500);
await page.shot('v05-contract', { 'Each region: the element, its box, its words, its colour': 'js:[...document.querySelectorAll(".line, td.line_content, span")].find((e) => e.textContent.includes("regions"))' });
await page.goto(`${BLOB}/reference/customers.png`, 8000);
await page.wait(2500);
await page.shot('v06-reference', { 'The reference screen, kept with the spec': 'js:document.querySelector(".file-content img, .image img, img[alt*=customers]")' });
await openIssue();
await reply(page, 'approve');
await page.wait(3000);
const mine = 'js:[...document.querySelectorAll("[data-testid=work-item-note-body]")].filter((e) => e.textContent.trim() === "approve").pop()';
await page.shot('v07-approve', { 'The client approves the contract': mine }, mine);
await page.close();
