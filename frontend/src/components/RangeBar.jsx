/**
 * Signature visualization for the report anomaly detection feature.
 * Shows exactly where a lab value falls relative to its clinical normal
 * range, rather than a bare "HIGH/LOW" badge - so a patient can see at a
 * glance not just that something is off, but by how much.
 */
export default function RangeBar({ parameter, value, normalRange, severity, direction }) {
  // normalRange comes back from the API as a string like "13.0-17.0 g/dL"
  const match = normalRange?.match(/([\d.]+)\s*-\s*([\d.]+)\s*(.*)/);
  const low = match ? parseFloat(match[1]) : 0;
  const high = match ? parseFloat(match[2]) : 1;
  const unit = match ? match[3] : "";

  const span = Math.max(high - low, 0.0001);
  const displayMin = low - span * 0.6;
  const displayMax = high + span * 0.6;
  const total = displayMax - displayMin;

  const toPct = (v) => Math.min(100, Math.max(0, ((v - displayMin) / total) * 100));

  const zoneLeft = toPct(low);
  const zoneWidth = toPct(high) - toPct(low);
  const markerLeft = toPct(value);

  const severityColor =
    severity === "high" ? "bg-status-danger" : severity === "low" ? "bg-status-warn" : "bg-status-ok";
  const severityText =
    severity === "high" ? "text-status-danger" : severity === "low" ? "text-status-warn" : "text-status-ok";

  return (
    <div className="py-4">
      <div className="flex items-baseline justify-between mb-2.5">
        <span className="text-sm font-semibold text-ink capitalize font-display">
          {parameter.replaceAll("_", " ")}
        </span>
        <span className={`font-mono text-sm font-medium ${severityText}`}>
          {value} {unit}
          <span className="text-muted font-normal ml-1.5">
            ({direction === "above" ? "above" : "below"} range)
          </span>
        </span>
      </div>

      <div className="relative h-2.5 rounded-full bg-line">
        {/* Normal range zone */}
        <div
          className="absolute top-0 h-2.5 rounded-full bg-status-okBg border border-status-ok/30"
          style={{ left: `${zoneLeft}%`, width: `${zoneWidth}%` }}
        />
        {/* Value marker */}
        <div
          className={`absolute -top-1 w-4 h-4 rounded-full border-2 border-surface shadow-md ${severityColor}`}
          style={{ left: `calc(${markerLeft}% - 8px)` }}
          title={`${value} ${unit}`}
        />
      </div>

      <div className="flex justify-between text-[11px] text-muted font-mono mt-1.5">
        <span>{displayMin.toFixed(1)}</span>
        <span className="text-status-ok">
          normal: {low}–{high}
        </span>
        <span>{displayMax.toFixed(1)}</span>
      </div>
    </div>
  );
}
