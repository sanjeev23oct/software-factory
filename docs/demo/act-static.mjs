// Re-takes every editor picture that does not depend on a run in progress.
import { open } from './drive.mjs';
import { homedir } from 'node:os';
const page = await open();
const R = 'factory-demo-ui-features';
const stage = (id) => `js:[...document.querySelectorAll('.stop')].find((r) => r.querySelector('input[data-k=id]').value === '${id}')`;
const node = (text) => `js:[...document.querySelectorAll('.node')].find((n) => n.textContent.trim() === '${text}')`;
const card = (name) => `js:document.querySelector('.skill[data-name="${name}"]')`;

await page.goto('http://127.0.0.1:8787/#factory-demo-api');
await page.shot('s4-add', { 'Add a repository': '#new', 'Pipelines already in this factory': '.pick' });
await page.click('#new');
await page.type('#n_name', R);
await page.type('#n_repo', `${homedir()}/personal-repos/factory-demo-ui`);
await page.shot('s5-form', { 'A name for the pipeline': '#n_name', 'Where the code is': '#n_repo' });
await page.click('input[name=sample][value=ui-app]');
await page.shot('s6-start', { 'An example to start from and edit': 'js:document.querySelector("input[name=sample][value=ui-app]").closest(".sample")', 'Or start from nothing': '.sample.blank' }, '#samples');

await page.goto(`http://127.0.0.1:8787/#${R}`, 2500);
await page.shot('s7-created', { 'The pipeline: its stages and gates': '#draw', 'Listed in the factory': '.pick' });
await page.shot('s8-trigger', { 'Issues with this label': '#s_label', 'Assigned to this person': '#s_assignee', 'In this repository': '#s_repo' }, '#source');
await page.shot('s9-route', { 'Gate: a person approves the requirements': node('Gate: requirements'), 'Gate: a person looks at the screens': node('Gate: screens'), 'Ends by opening a pull request': node('pull request') });
await page.shot('s9b-stops', { 'A stage an agent does': stage('requirements'), 'A gate: it waits for a person': stage('approve-requirements'), 'Reorder with the arrows': 'js:' + stage('requirements').slice(3) + '.querySelector(".order")' }, stage('requirements'));
await page.shot('k6-separate', { 'A checker in a separate session writes the evidence': 'js:' + stage('build').slice(3) + '.querySelector("input[data-k=checker]").closest("label")' }, stage('build'));
await page.shot('s10-rules', { 'The team’s rules, in plain words': '#guide', 'The commands that prove a change works': '#presubmit', 'Programs agents may run': '#tools' }, '#guide');
await page.shot('s11-live', { 'Automatic pickup is on': '.switch', 'Save': '#save' }, '#source');

await page.goto(`http://127.0.0.1:8787/skills#${R}`, 2500);
await page.shot('k1-skills', { 'Maker skills: the ones a task can name': '#makers', 'Skills for the stages': '#stops' });
await page.shot('k2-library', { 'Ready-made skills': '#lib', 'Or the team’s own, from the repository': '#repo', 'Or write one': '#newname' }, 'js:document.querySelector(".adds")');
await page.run(`document.querySelector('.skill[data-name="build-ui-logic"]').open = true`); await page.wait(300);
await page.shot('k3-files', { 'What the skill is for': '.skill[data-name="build-ui-logic"] [data-f=description]', 'The files it is for': '.skill[data-name="build-ui-logic"] [data-f=applies_to]',
  'The instructions an agent follows': '.skill[data-name="build-ui-logic"] textarea' }, card('build-ui-logic'));
await page.run(`document.querySelector('.skill[data-name="build-ui-logic"]').open = false`);
await page.shot('k4-makers', { 'Tests': card('build-tests'), 'Logic': card('build-ui-logic'), 'Page': card('build-ui-page'), 'View': card('build-ui-view') }, card('build-tests'));
await page.shot('k5-checker', { 'The maker’s skill': card('build-tasks'), 'The checker’s skill, for a separate session': card('check-tasks') }, card('build-tasks'));

await page.goto('http://127.0.0.1:8787/#factory-demo-api', 2500);
await page.run("(() => { const g = [...document.querySelectorAll('.node.gate')]; g[0].id = 'g1'; g[1].id = 'g2'; })()");
await page.shot('p1-api-route', { 'Gate 1: requirements': '#g1', 'Gate 2: design': '#g2' });
await page.close();
