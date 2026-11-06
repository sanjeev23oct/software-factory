// Records the client's side of the start: the empty app, their project, and filing a request.
//   DEMO_SHOTS=docs/clients-demo/shots GITLAB_USER=... GITLAB_PASSWORD=... SITE_USER=... SITE_PASSWORD=... node act-1-ask.mjs
// The logins come from the environment and never land in the repository.
import { open } from '../demo/drive.mjs';

const { GITLAB_USER, GITLAB_PASSWORD, SITE_USER, SITE_PASSWORD } = process.env;
const GITLAB = 'https://gitlab.justpush.cloud', PROJECT = 'clients/factory-demo', SITE = 'https://factory.justpush.cloud/factory-demo';

const site = await open(9341);
await site.headers({ Authorization: 'Basic ' + Buffer.from(`${SITE_USER}:${SITE_PASSWORD}`).toString('base64') });
await site.goto(`${SITE}/main/`, 2500);
await site.shot('c01-empty-app', { 'An empty page, waiting for the first request': '[data-testid=coming-soon]' });
await site.close();

const page = await open(9342);
await page.goto(`${GITLAB}/users/sign_in`, 4000);
if (await page.run('!!document.querySelector("#user_login")')) {
  await page.type('#user_login', GITLAB_USER);
  await page.type('#user_password', GITLAB_PASSWORD);
  await page.click('button[type=submit], input[type=submit]', 6000);
}
await page.goto(`${GITLAB}/${PROJECT}`, 6000);
await page.until('!!document.querySelector("table, [data-testid=file-tree-table]")', 60);
await page.shot('c02-project', { 'The client\'s own private project': 'h1, [data-testid=project-name-content]', 'Nothing in it yet but an empty app': '#tree-holder, .tree-holder, [data-testid=file-tree-table], table' });

await page.goto(`${GITLAB}/${PROJECT}/-/issues/new?issuable_template=Feature`, 10000);
await page.until('!!document.querySelector("[data-testid=work-item-title-input]") && !!document.querySelector("#content-body textarea")', 30);
await page.type('[data-testid=work-item-title-input]', 'Build a CRM dashboard for my customers');
await page.type('#content-body textarea', [
  '## What should change',
  '',
  'Build a CRM dashboard: my customers in a table with their company, deal stage and deal value.',
  'Show totals at the top: how many customers, the total value of open deals, and how many deals we won.',
  '',
  '## How will we know it works?',
  '',
  'I can see every customer at a glance, and the totals add up.',
  '',
  '<!-- Leave the line below as it is. It hands the issue to the factory. -->',
  '/label ~factory',
].join('\n'));
await page.shot('c03-new-issue', { 'A title, in plain words': '[data-testid=work-item-title-input]', 'What they want, the way they would tell a colleague': '#content-body textarea' });
await page.click('js:[...document.querySelectorAll("#content-body button")].find((b) => b.textContent.trim() === "Create issue")', 10000);
console.log('issue url', await page.run('location.href'));
await page.shot('c04-issue-filed', { 'Filed, with the factory label': '[data-testid=issue-title], h1', 'Handed to the factory': 'js:[...document.querySelectorAll("a, span")].find((e) => e.textContent.trim() === "factory")' });
await page.close();
