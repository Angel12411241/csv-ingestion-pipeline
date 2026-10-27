import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatCompactCurrency } from "../../utils/format";
import ChartTooltip from "./ChartTooltip";

const AXIS_TICK = { fill: "var(--text-secondary)", fontSize: 12 };
const ROW_HEIGHT = 28;

/**
 * Single-series horizontal bar chart of sales per category. Horizontal bars keep long
 * category labels (product lines, countries) readable instead of colliding on an x-axis.
 * `data` is expected pre-sorted (the API returns categories by sales, descending).
 */
export default function SalesBarChart({ data }) {
  const height = Math.max(200, data.length * ROW_HEIGHT + 40);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 24, bottom: 4, left: 8 }}>
        <CartesianGrid horizontal={false} stroke="var(--grid)" />
        <XAxis type="number" tickFormatter={formatCompactCurrency} tick={AXIS_TICK} axisLine={false} tickLine={false} />
        <YAxis
          type="category"
          dataKey="label"
          width={120}
          tick={AXIS_TICK}
          axisLine={{ stroke: "var(--axis)" }}
          tickLine={false}
          interval={0}
        />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: "var(--hover-band)" }} />
        <Bar dataKey="total_sales" fill="var(--series-1)" radius={[0, 4, 4, 0]} maxBarSize={20} animationDuration={500} />
      </BarChart>
    </ResponsiveContainer>
  );
}
