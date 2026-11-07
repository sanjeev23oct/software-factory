export const OPEN_STAGES = ['Lead', 'Qualified', 'Proposal', 'Negotiation'];

export function isOpenStage(stage) {
  return OPEN_STAGES.includes(stage);
}

function toNumber(value) {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0;
}

export function formatCurrency(value) {
  const amount = toNumber(value);
  const cents = Math.round(amount * 100);
  const whole = cents % 100 === 0;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: whole ? 0 : 2,
    maximumFractionDigits: whole ? 0 : 2,
  }).format(cents / 100);
}

export function computeTotals(customers) {
  let openCents = 0;
  let won = 0;
  for (const customer of customers) {
    if (isOpenStage(customer.stage)) {
      openCents += Math.round(toNumber(customer.value) * 100);
    } else if (customer.stage === 'Won') {
      won += 1;
    }
  }
  return { customers: customers.length, openValue: openCents / 100, won };
}
