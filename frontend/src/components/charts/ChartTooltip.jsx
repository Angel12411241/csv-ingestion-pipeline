import { formatCurrency, formatNumber } from "../../utils/format";

/** Shared Recharts tooltip: label, sales value, and record count. */
export default function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip__label">{label ?? point.label}</div>
      <div className="chart-tooltip__value">{formatCurrency(point.total_sales)}</div>
      <div className="chart-tooltip__meta">{formatNumber(point.count)} records</div>
    </div>
  );
}
