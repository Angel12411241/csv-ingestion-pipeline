const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 });
const compactCurrency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  notation: "compact",
  maximumFractionDigits: 1,
});
const number = new Intl.NumberFormat("en-US");

export const formatCurrency = (value) => (value == null ? "—" : currency.format(value));
export const formatCompactCurrency = (value) => (value == null ? "—" : compactCurrency.format(value));
export const formatNumber = (value) => (value == null ? "—" : number.format(value));

/** Format an ISO date string (YYYY-MM-DD) without timezone shifting. */
export function formatDate(value) {
  if (!value) return "—";
  const [year, month, day] = value.slice(0, 10).split("-").map(Number);
  return new Date(year, month - 1, day).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateRange(start, end) {
  if (!start && !end) return "—";
  return `${formatDate(start)} – ${formatDate(end)}`;
}
