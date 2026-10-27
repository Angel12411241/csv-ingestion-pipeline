import { formatCurrency, formatDate, formatNumber } from "../utils/format";

export const COLUMNS = [
  { key: "order_date", label: "Order date", format: formatDate },
  { key: "order_number", label: "Order #" },
  { key: "product_code", label: "Product" },
  { key: "product_line", label: "Product line" },
  { key: "customer_name", label: "Customer" },
  { key: "country", label: "Country" },
  { key: "status", label: "Status" },
  { key: "quantity_ordered", label: "Qty", numeric: true, format: formatNumber },
  { key: "price_each", label: "Price each", numeric: true, format: formatCurrency },
  { key: "sales", label: "Sales", numeric: true, format: formatCurrency },
  { key: "total_sales", label: "Qty × price", numeric: true, format: formatCurrency },
];

function SortIndicator({ active, direction }) {
  if (!active) return <span className="sort-indicator" aria-hidden="true">↕</span>;
  return (
    <span className="sort-indicator sort-indicator--active" aria-hidden="true">
      {direction === "asc" ? "↑" : "↓"}
    </span>
  );
}

export default function DataTable({ rows, sortBy, sortDir, onSort, loading = false }) {
  return (
    <div className={`table-wrap${loading ? " table-wrap--loading" : ""}`}>
      <table className="table">
        <thead>
          <tr>
            {COLUMNS.map((column) => {
              const active = column.key === sortBy;
              return (
                <th
                  key={column.key}
                  className={column.numeric ? "num" : undefined}
                  aria-sort={active ? (sortDir === "asc" ? "ascending" : "descending") : "none"}
                >
                  <button type="button" className="sort-button" onClick={() => onSort(column.key)}>
                    {column.label}
                    <SortIndicator active={active} direction={sortDir} />
                  </button>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={COLUMNS.length} className="empty">
                No records match the current filters.
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row.id}>
                {COLUMNS.map((column) => (
                  <td key={column.key} className={column.numeric ? "num" : undefined}>
                    {column.format ? column.format(row[column.key]) : (row[column.key] ?? "—")}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
