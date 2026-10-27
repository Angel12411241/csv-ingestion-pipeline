const LABELS = { processing: "Processing", completed: "Completed", failed: "Failed" };

export default function StatusBadge({ status }) {
  return <span className={`badge badge--${status}`}>{LABELS[status] ?? status}</span>;
}
