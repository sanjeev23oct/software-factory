// Turns tasks into HTML strings. Text from a task is always escaped.

export function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

export function renderTask(task) {
  const state = task.done ? 'done' : 'open';
  return `<li class="task ${state}" data-testid="task-${task.id}">` +
    `<span class="mark" aria-hidden="true">${task.done ? '✓' : ''}</span>` +
    `<span class="title">${escapeHtml(task.title)}</span></li>`;
}

export function renderList(tasks) {
  if (tasks.length === 0) return '<li class="empty" data-testid="empty">Nothing here.</li>';
  return tasks.map(renderTask).join('');
}

export function renderSummary({ total, done, open }) {
  return `<span data-testid="summary">${open} open · ${done} done · ${total} total</span>`;
}
