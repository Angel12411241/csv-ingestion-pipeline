import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Link, useParams, useSearchParams } from "react-router-dom";

import { getErrorMessage } from "../api/client";
import { getDataset } from "../api/datasets";
import SalesBarChart from "../components/charts/SalesBarChart";
import DataTable from "../components/DataTable";
import Filters from "../components/Filters";
import Pagination from "../components/Pagination";
import StatusBadge from "../components/StatusBadge";
import { formatCurrency, formatDateRange, formatNumber } from "../utils/format";

// Table state lives in the URL so a view can be refreshed, bookmarked, or shared.
const DEFAULTS = {
  page: "1",
  page_size: "20",
  sort_by: "order_date",
  sort_dir: "asc",
  status: "",
  product_line: "",
  date_from: "",
  date_to: "",
};
const FILTER_KEYS = ["status", "product_line", "date_from", "date_to"];

function useTableParams() {
  const [searchParams, setSearchParams] = useSearchParams();
  const params = Object.fromEntries(Object.entries(DEFAULTS).map(([key, fallback]) => [key, searchParams.get(key) ?? fallback]));

  function update(changes, { resetPage = true } = {}) {
    const next = { ...params, ...(resetPage ? { page: DEFAULTS.page } : {}), ...changes };
    const nonDefault = Object.entries(next).filter(([key, value]) => value !== "" && String(value) !== DEFAULTS[key]);
    setSearchParams(Object.fromEntries(nonDefault), { replace: true });
  }

  return [params, update];
}

function StatTile({ label, value, detail }) {
  return (
    <div className="stat">
      <div className="stat__label">{label}</div>
      <div className="stat__value">{value}</div>
      {detail && <div className="stat__detail">{detail}</div>}
    </div>
  );
}

export default function DatasetDetailPage() {
  const { id } = useParams();
  const [params, updateParams] = useTableParams();

  const apiParams = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== ""));
  const query = useQuery({
    queryKey: ["dataset", id, apiParams],
    queryFn: () => getDataset(id, apiParams),
    placeholderData: keepPreviousData,
    refetchInterval: (q) => (q.state.data?.dataset.status === "processing" ? 1000 : false),
  });

  if (query.isPending) return <p className="muted">Loading dataset…</p>;
  if (query.isError) {
    return (
      <div className="stack">
        <Link to="/">← All datasets</Link>
        <p className="alert alert--error" role="alert">
          {getErrorMessage(query.error, "Could not load this dataset.")}
        </p>
      </div>
    );
  }

  const { dataset, records, aggregates, filter_options: filterOptions } = query.data;
  const filters = Object.fromEntries(FILTER_KEYS.map((key) => [key, params[key]]));
  const isFiltered = FILTER_KEYS.some((key) => params[key]);
  const breakdown = dataset.drop_breakdown ?? {};

  function handleSort(column) {
    const sameColumn = params.sort_by === column;
    updateParams({ sort_by: column, sort_dir: sameColumn && params.sort_dir === "asc" ? "desc" : "asc" });
  }

  return (
    <div className="stack">
      <div className="page-header">
        <Link to="/">← All datasets</Link>
        <h1>
          {dataset.filename} <StatusBadge status={dataset.status} />
        </h1>
      </div>

      {dataset.status === "processing" && (
        <p className="alert" role="status">
          This dataset is still processing ({dataset.progress}%). The page will update automatically.
        </p>
      )}
      {dataset.status === "failed" && (
        <p className="alert alert--error" role="alert">
          Processing failed: {dataset.error_message}
        </p>
      )}

      {dataset.status === "completed" && (
        <>
          <div className="stats">
            <StatTile
              label={isFiltered ? "Total sales (filtered)" : "Total sales"}
              value={formatCurrency(aggregates.total_sales)}
            />
            <StatTile
              label={isFiltered ? "Records (filtered)" : "Records"}
              value={formatNumber(aggregates.record_count)}
              detail={isFiltered ? `of ${formatNumber(dataset.row_count)}` : `from ${formatNumber(dataset.rows_in)} rows read`}
            />
            <StatTile
              label="Rows dropped"
              value={formatNumber(dataset.rows_dropped)}
              detail={`${breakdown.duplicates ?? 0} duplicates · ${breakdown.missing_required ?? 0} missing values · ${breakdown.invalid_date ?? 0} bad dates`}
            />
            <StatTile label="Date range" value={formatDateRange(dataset.date_min, dataset.date_max)} />
          </div>

          <section className="card">
            <Filters
              values={filters}
              options={filterOptions}
              onChange={(changes) => updateParams(changes)}
              onReset={() => updateParams(Object.fromEntries(FILTER_KEYS.map((key) => [key, ""])))}
            />
          </section>

          <section className="card">
            <h2 className="card__title">Sales by product line</h2>
            <SalesBarChart data={aggregates.sales_by_product_line} />
          </section>

          <section className="card">
            <h2 className="card__title">Records</h2>
            <DataTable
              rows={records.items}
              sortBy={params.sort_by}
              sortDir={params.sort_dir}
              onSort={handleSort}
              loading={query.isPlaceholderData}
            />
            <Pagination
              page={records.page}
              pages={records.pages}
              total={records.total}
              pageSize={records.page_size}
              onPageChange={(page) => updateParams({ page: String(page) }, { resetPage: false })}
              onPageSizeChange={(size) => updateParams({ page_size: String(size) })}
            />
          </section>
        </>
      )}
    </div>
  );
}
