import assert from 'node:assert/strict';
import test from 'node:test';
import { escapeHtml } from '../src/render.js';

test('escapeHtml escapes markup and quotes', () => {
  assert.equal(escapeHtml('<b class="x">Tom & Jerry\'s</b>'), '&lt;b class=&quot;x&quot;&gt;Tom &amp; Jerry&#39;s&lt;/b&gt;');
});

test('escapeHtml accepts numbers', () => {
  assert.equal(escapeHtml(42), '42');
});
