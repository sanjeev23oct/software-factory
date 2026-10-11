// Records giving a route its skills, for real: adding them, saying which files each is for, and switching on the checker.
import { open } from './drive.mjs';
const page = await open();
const card = (name) => `js:document.querySelector('.skill[data-name="${name}"]')`;
const say = async () => console.log('  state:', await page.run("document.querySelector('#state').textContent"));

await page.goto('http://127.0.0.1:8787/skills#factory-demo-ui-features', 2500);
await page.shot('k1-skills', { 'The skills this route has': '#makers', 'Add more': 'js:document.querySelector(".adds")' });

for (const name of ['build-ui-logic', 'build-ui-view', 'build-ui-page', 'check-tasks']) {
  await page.run(`(() => { const s = document.querySelector('#lib'); s.value = '${name}'; })()`);
  if (name === 'build-ui-logic') await page.shot('k2-library', { 'Ready-made skills': '#lib', 'Or the team’s own, from the repository': '#repo', 'Or write one': '#newname' }, 'js:document.querySelector(".adds")');
  await page.click('button[data-add=library]', 1200); await say();
}
for (const name of ['build-backend', 'build-db', 'build-ui']) {
  await page.run(`(() => { const d = document.querySelector('.skill[data-name="${name}"]'); d.open = true; d.querySelector('[data-remove]').click(); })()`); await page.wait(900);
}
const files = { 'build-ui-logic': 'src/board.js', 'build-ui-view': 'src/render.js', 'build-ui-page': 'src/main.js, index.html, styles.css, data/*.json', 'build-tests': 'test/*.js' };
for (const [name, globs] of Object.entries(files)) {
  await page.run(`(() => { const d = document.querySelector('.skill[data-name="${name}"]'); d.open = true; })()`); await page.wait(200);
  await page.type(`.skill[data-name="${name}"] [data-f=applies_to]`, globs);
  if (name === 'build-ui-logic') await page.shot('k3-files', { 'What the skill is for': `.skill[data-name="${name}"] [data-f=description]`, 'The files it is for': `.skill[data-name="${name}"] [data-f=applies_to]`,
    'The instructions an agent follows': `.skill[data-name="${name}"] textarea` }, `.skill[data-name="${name}"]`);
  await page.click(`.skill[data-name="${name}"] [data-save]`, 1200); await say();
  await page.run(`(() => { const d = document.querySelector('.skill[data-name="${name}"]'); d.open = false; })()`);
}
await page.goto('http://127.0.0.1:8787/skills#factory-demo-ui-features', 2500);
await page.shot('k4-makers', { 'Logic': card('build-ui-logic'), 'View': card('build-ui-view'), 'Page': card('build-ui-page'), 'Tests': card('build-tests') });
await page.shot('k5-checker', { 'The maker’s skill': card('build-tasks'), 'The checker’s skill': card('check-tasks') }, card('build-tasks'));

await page.goto('http://127.0.0.1:8787/#factory-demo-ui-features', 2500);
const build = `[...document.querySelectorAll('.stop')].find((r) => r.querySelector('input[data-k=id]').value === 'build')`;
await page.run(`(${build}).querySelector('input[data-k=checker]').click()`); await page.wait(400);
await page.shot('k6-separate', { 'A checker in a separate session writes the evidence': `js:(${build}).querySelector('input[data-k=checker]').closest('label')` }, `js:${build}`);
await page.click('#save', 1500);
console.log('route:', await page.run("document.querySelector('#state').textContent"));
await page.close();
