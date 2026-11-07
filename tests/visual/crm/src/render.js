// Turns data into HTML strings. Text from data is always escaped.

import { formatCurrency } from './customers.js';

export function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

export function renderTotals(totals) {
  return `<dl class="totals">
  <div class="total"><dt>Customers</dt><dd data-testid="total-customers">${escapeHtml(totals.customers)}</dd></div>
  <div class="total"><dt>Open deal value</dt><dd data-testid="total-open-value">${escapeHtml(formatCurrency(totals.openValue))}</dd></div>
  <div class="total"><dt>Deals won</dt><dd data-testid="total-won">${escapeHtml(totals.won)}</dd></div>
</dl>`;
}

function renderCustomerRow(customer) {
  return `<tr data-testid="customer-row">
  <td>${escapeHtml(customer.name)}</td>
  <td>${escapeHtml(customer.company)}</td>
  <td>${escapeHtml(customer.stage)}</td>
  <td class="value">${escapeHtml(formatCurrency(customer.value))}</td>
</tr>`;
}

export function renderCustomerTable(customers) {
  if (customers.length === 0) {
    return '<p data-testid="empty-state">No customers yet.</p>';
  }
  return `<table>
<thead><tr><th>Customer</th><th>Company</th><th>Deal stage</th><th>Deal value</th></tr></thead>
<tbody>
${customers.map(renderCustomerRow).join('\n')}
</tbody>
</table>`;
}

export function renderLoadError() {
  return '<p data-testid="load-error" role="alert">Could not load customers.</p>';
}
