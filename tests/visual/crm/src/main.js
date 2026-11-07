// The only file that touches the page: loads the sample data and renders it.

import { computeTotals } from './customers.js';
import { renderTotals, renderCustomerTable, renderLoadError } from './render.js';

const totalsEl = document.getElementById('totals');
const customersEl = document.getElementById('customers');

async function load() {
  try {
    const response = await fetch('data/customers.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const customers = await response.json();
    if (!Array.isArray(customers)) throw new Error('Expected a list of customers');
    totalsEl.innerHTML = renderTotals(computeTotals(customers));
    customersEl.innerHTML = renderCustomerTable(customers);
  } catch {
    totalsEl.innerHTML = '';
    customersEl.innerHTML = renderLoadError();
  }
}

load();
