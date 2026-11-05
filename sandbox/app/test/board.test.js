import assert from 'node:assert/strict';
import test from 'node:test';
import { sortTasks, summary, visibleTasks } from '../src/board.js';

const tasks = [
  { id: 1, title: 'a', done: true },
  { id: 2, title: 'b', done: false },
  { id: 3, title: 'c', done: false },
];

test('summary counts open and done', () => {
  assert.deepEqual(summary(tasks), { total: 3, done: 1, open: 2 });
});

test('visibleTasks filters by state', () => {
  assert.deepEqual(visibleTasks(tasks, 'open').map((t) => t.id), [2, 3]);
  assert.deepEqual(visibleTasks(tasks, 'done').map((t) => t.id), [1]);
  assert.equal(visibleTasks(tasks, 'all').length, 3);
});

test('sortTasks puts open tasks first and does not change its input', () => {
  assert.deepEqual(sortTasks(tasks).map((t) => t.id), [2, 3, 1]);
  assert.deepEqual(tasks.map((t) => t.id), [1, 2, 3]);
});
