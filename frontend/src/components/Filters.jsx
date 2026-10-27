export default function Filters({ values, options, onChange, onReset }) {
  const hasFilters = Object.values(values).some(Boolean);

  return (
    <div className="filters" role="search" aria-label="Filter records">
      <label className="field">
        <span>Status</span>
        <select value={values.status} onChange={(event) => onChange({ status: event.target.value })}>
          <option value="">All statuses</option>
          {options.statuses.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span>Product line</span>
        <select value={values.product_line} onChange={(event) => onChange({ product_line: event.target.value })}>
          <option value="">All product lines</option>
          {options.product_lines.map((line) => (
            <option key={line} value={line}>
              {line}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span>From</span>
        <input
          type="date"
          value={values.date_from}
          max={values.date_to || undefined}
          onChange={(event) => onChange({ date_from: event.target.value })}
        />
      </label>

      <label className="field">
        <span>To</span>
        <input
          type="date"
          value={values.date_to}
          min={values.date_from || undefined}
          onChange={(event) => onChange({ date_to: event.target.value })}
        />
      </label>

      <button type="button" className="button button--secondary" onClick={onReset} disabled={!hasFilters}>
        Clear filters
      </button>
    </div>
  );
}
