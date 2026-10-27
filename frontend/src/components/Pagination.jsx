import { formatNumber } from "../utils/format";

export const PAGE_SIZE_OPTIONS = [10, 20];

export default function Pagination({ page, pages, total, pageSize, onPageChange, onPageSizeChange }) {
  const first = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const last = Math.min(page * pageSize, total);

  return (
    <nav className="pagination" aria-label="Pagination">
      <span className="muted">
        Showing {formatNumber(first)}–{formatNumber(last)} of {formatNumber(total)}
      </span>

      <div className="pagination__controls">
        <label className="pagination__size">
          Rows per page
          <select value={pageSize} onChange={(event) => onPageSizeChange(Number(event.target.value))}>
            {PAGE_SIZE_OPTIONS.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          className="button button--secondary"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
        >
          Previous
        </button>
        <span aria-live="polite">
          Page {page} of {Math.max(pages, 1)}
        </span>
        <button
          type="button"
          className="button button--secondary"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= pages}
        >
          Next
        </button>
      </div>
    </nav>
  );
}
