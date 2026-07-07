const STYLES = {
  CONFIRMED: "bg-status-okBg text-status-ok",
  PAID: "bg-status-okBg text-status-ok",
  COMPLETED: "bg-status-okBg text-status-ok",
  PENDING_PAYMENT: "bg-status-pendingBg text-status-pending",
  PENDING: "bg-status-pendingBg text-status-pending",
  FAILED: "bg-status-dangerBg text-status-danger",
  CANCELLED: "bg-status-dangerBg text-status-danger",
  high: "bg-status-dangerBg text-status-danger",
  low: "bg-status-warnBg text-status-warn",
};

export default function StatusBadge({ status }) {
  const label = String(status).replaceAll("_", " ").toLowerCase();
  const style = STYLES[status] || "bg-status-pendingBg text-status-pending";
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium capitalize ${style}`}>
      {label}
    </span>
  );
}
