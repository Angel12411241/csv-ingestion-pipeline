import { Link } from "react-router-dom";

import { formatCurrency, formatDateRange, formatNumber } from "../utils/format";
import StatusBadge from "./StatusBadge";

export default function DatasetList({ datasets }) {
  if (!datasets.length) {
    return <p className="empty">No datasets yet. Upload a CSV to get started.</p>;
  }

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>File</th>
            <th>Status</th>
            <th className="num">Rows</th>
            <th className="num">Dropped</th>
            <th>Date range</th>
            <th className="num">Total sales</th>
            <th>Uploaded</th>
          </tr>
        </thead>
        <tbody>
          {datasets.map((dataset) => (
            <tr key={dataset.id}>
              <td>
                <Link to={`/datasets/${dataset.id}`}>{dataset.filename}</Link>
              </td>
              <td>
                <StatusBadge status={dataset.status} />
                {dataset.status === "processing" && <span className="muted"> {dataset.progress}%</span>}
              </td>
              <td className="num">{formatNumber(dataset.row_count)}</td>
              <td className="num">{formatNumber(dataset.rows_dropped)}</td>
              <td>{formatDateRange(dataset.date_min, dataset.date_max)}</td>
              <td className="num">{formatCurrency(dataset.total_sales)}</td>
              <td className="muted">{new Date(dataset.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
