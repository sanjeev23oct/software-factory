// Shared by the acts: a signed-in GitLab page, the client's preview area, and the issue's comments.
// The logins come from the environment and never land in the repository.
import { open } from '../demo/drive.mjs';

export const GITLAB = 'https://gitlab.justpush.cloud', PROJECT = 'clients/factory-demo';
export const SITE = 'https://factory.justpush.cloud/factory-demo', ISSUE = `${GITLAB}/${PROJECT}/-/issues/1`;
const { GITLAB_USER, GITLAB_PASSWORD, SITE_USER, SITE_PASSWORD } = process.env;

export async function gitlab(port) {
  const page = await open(port);
  await page.goto(`${GITLAB}/users/sign_in`, 5000);
  if (await page.run('!!document.querySelector("#user_login")')) {
    await page.type('#user_login', GITLAB_USER);
    await page.type('#user_password', GITLAB_PASSWORD);
    await page.click('button[type=submit], input[type=submit]', 3000);
    await page.until('!location.pathname.startsWith("/users/sign_in")', 60);
  }
  return page;
}

export async function site(port) {
  const page = await open(port);
  await page.headers({ Authorization: 'Basic ' + Buffer.from(`${SITE_USER}:${SITE_PASSWORD}`).toString('base64') });
  return page;
}

// The last comment whose text holds every one of `words`. GitLab drops the factory's hidden markers when it renders.
export const note = (...words) => `js:[...document.querySelectorAll('[data-testid=work-item-note-body]')].filter((e) => ${JSON.stringify(words)}.every((w) => e.textContent.includes(w))).pop()`;

export async function openIssue(page) {
  await page.goto(ISSUE, 8000);
  await page.until('document.querySelectorAll("[data-testid=work-item-note-body]").length > 0', 90);
}

// Reply on the issue the way a client does: type into the comment box and press Comment.
export async function reply(page, text) {
  const box = '#work-item-add-or-edit-comment';
  await page.click(box, 800);
  await page.type(box, text);
  await page.click('js:[...document.querySelectorAll("#content-body button")].filter((b) => b.textContent.trim() === "Comment").pop()', 6000);
}
