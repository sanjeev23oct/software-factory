// Records a request with a reference screenshot attached: the input to visual verification.
//   DEMO_SHOTS=docs/visual-demo/shots GITLAB_USER=... GITLAB_PASSWORD=... node act-v1-ask.mjs
import { GITLAB, PROJECT, gitlab } from '../clients-demo/client.mjs';

const IMAGE = '![customers](/uploads/ef6f323a6a28634d004a8c286fc3166e/customers.png)';
const page = await gitlab(9401);
await page.goto(`${GITLAB}/${PROJECT}/-/issues/new?issuable_template=Feature`, 10000);
await page.until('!!document.querySelector("[data-testid=work-item-title-input]") && !!document.querySelector("#content-body textarea")', 60);
await page.type('[data-testid=work-item-title-input]', 'Build this customer dashboard, matching the screenshot');
await page.type('#content-body textarea', [
  '## What should change',
  '',
  'Build the customer dashboard in the screenshot: the heading, the three totals in one row (customers, open deal value, deals won), and the customer table with company, deal stage and deal value.',
  '',
  IMAGE,
  '',
  '## How will we know it works?',
  '',
  'It looks like the screenshot: same layout, same words, same blue for the money.',
  '',
  '<!-- Leave the line below as it is. It hands the issue to the factory. -->',
  '/label ~factory',
].join('\n'));
await page.shot('v01-new-issue', { 'What they want, in plain words': '#content-body textarea' });
await page.click('js:[...document.querySelectorAll("#content-body button")].find((b) => b.textContent.trim() === "Create issue")', 10000);
console.log('issue url', await page.run('location.href'));
await page.until('!!document.querySelector("[data-testid=work-item-description] img, .description img, .md img")', 60);
await page.wait(2000);
await page.shot('v02-issue-with-reference', { 'The reference screenshot, attached': 'js:document.querySelector("[data-testid=work-item-description] img, .description img, .md img")',
  'Handed to the factory': 'js:[...document.querySelectorAll("a, span")].find((e) => e.textContent.trim() === "factory")' },
  'js:document.querySelector("[data-testid=work-item-description] img, .description img, .md img")');
await page.close();
