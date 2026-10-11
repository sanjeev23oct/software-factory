import { open } from './drive.mjs';
const page = await open();
const card = (name) => `js:document.querySelector('.skill[data-name="${name}"]')`;
await page.goto('http://127.0.0.1:8787/skills#factory-demo-ui-features', 2500);
await page.shot('k5-checker', { 'The maker’s skill': card('build-tasks'), 'The checker’s skill, for a separate session': card('check-tasks') }, card('build-tasks'));
await page.shot('k4-makers', { 'Tests': card('build-tests'), 'Logic': card('build-ui-logic'), 'Page': card('build-ui-page'), 'View': card('build-ui-view') }, card('build-tests'));
await page.close();
