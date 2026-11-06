// Records the hand-over: the merge request, the status page when done, and the whole history on the issue.
import { SITE, gitlab, note, openIssue, site } from './client.mjs';

const page = await gitlab(9381);
await openIssue(page);
const done = note('Factory progress', 'Merge request opened');
const link = await page.run(`[...(${done.slice(3)}).querySelectorAll('a')].map((a) => a.href).find((h) => h.includes('/merge_requests/'))`);
console.log('merge request', link);

await page.goto(link, 9000);
await page.until('!!document.querySelector("[data-testid=title-content], h1")', 60);
await page.shot('c18-merge-request', { 'Opened by the factory': '[data-testid=title-content], h1',
  'Linked to the request, with the specs and the evidence': 'js:[...document.querySelectorAll(".description .md, [data-testid=description-content]")].pop()',
  'Yours to review and merge': 'js:[...document.querySelectorAll("button, a")].find((e) => /^(Merge|Ready to merge)/.test(e.textContent.trim()) || /Changes/.test(e.textContent.trim()))' });

const status = await site(9382);
await status.goto(`${SITE}/status/`, 3000);
await status.shot('c19-status-done', { 'Done': '.pill', 'Every step ticked': 'ol',
  'The conversation, the change to try, and the finished work': '.links' });
await status.close();

await openIssue(page);
await page.run('document.querySelector("[data-testid=work-item-note-body]")?.scrollIntoView()');
await page.shot('c20-history', { 'Every step, in the open': note('Factory progress', 'Picked up the issue'),
  'Every approval': 'js:[...document.querySelectorAll("[data-testid=work-item-note-body]")].find((e) => e.textContent.trim() === "approve")' },
  note('Factory progress', 'Picked up the issue'));
await page.close();
