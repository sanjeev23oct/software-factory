import assert from 'node:assert/strict';
import test from 'node:test';
import { renderList, renderSummary, renderTask } from '../src/render.js';

test('renderTask escapes the title', () => {
  const html = renderTask({ id: 1, title: '<b>x</b>', done: false });
  assert.ok(html.includes('&lt;b&gt;x&lt;/b&gt;'));
  assert.ok(html.includes('data-testid="task-1"'));
});

test('renderTask marks done tasks', () => {
  assert.ok(renderTask({ id: 2, title: 'a', done: true }).includes('class="task done"'));
});

test('renderList shows an empty state', () => {
  assert.ok(renderList([]).includes('data-testid="empty"'));
});

test('renderSummary shows the counts', () => {
  assert.equal(renderSummary({ total: 3, done: 1, open: 2 }), '<span data-testid="summary">2 open · 1 done · 3 total</span>');
});
