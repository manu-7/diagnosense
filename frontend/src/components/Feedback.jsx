export function Spinner({ className = "" }) {
  return (
    <svg
      className={`animate-spin h-4 w-4 ${className}`}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
      <path className="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
    </svg>
  );
}

export function ErrorBanner({ message }) {
  if (!message) return null;
  return (
    <div className="rounded-lg bg-status-dangerBg text-status-danger px-4 py-3 text-sm font-medium border border-status-danger/15">
      {message}
    </div>
  );
}

export function EmptyState({ title, description }) {
  return (
    <div className="text-center py-16 px-6 border border-dashed border-line rounded-xl2 bg-surface/50">
      <p className="font-display font-semibold text-ink text-lg">{title}</p>
      {description && <p className="text-sm text-muted mt-1.5 max-w-sm mx-auto">{description}</p>}
    </div>
  );
}
