export default function ProgressBar({ value, label }) {
  const clamped = Math.max(0, Math.min(100, Math.round(value)));
  return (
    <div className="progress">
      <div className="progress__meta">
        <span>{label}</span>
        <span>{clamped}%</span>
      </div>
      <div
        className="progress__track"
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={clamped}
      >
        <div className="progress__fill" style={{ width: `${clamped}%` }} />
      </div>
    </div>
  );
}
