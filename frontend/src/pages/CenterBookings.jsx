import { useEffect, useState } from "react";
import { api, apiErrorMessage } from "../api/client";
import { ErrorBanner, EmptyState, Spinner } from "../components/Feedback";
import StatusBadge from "../components/StatusBadge";

function ReportRow({ booking }) {
  const [report, setReport] = useState(null);
  const [values, setValues] = useState("");
  const [generating, setGenerating] = useState(false);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get(`/reports/by-booking/${booking.id}`)
      .then(({ data }) => setReport(data))
      .catch(() => setReport(null));
  }, [booking.id]);

  async function handleGenerate() {
    let parsed;
    try {
      parsed = JSON.parse(values);
    } catch {
      setError('Enter valid JSON, e.g. {"hemoglobin": 10.2, "wbc": 12500}');
      return;
    }
    setGenerating(true);
    setError("");
    try {
      const { data } = await api.post(`/reports/${booking.id}/generate`, { extracted_values: parsed });
      setReport(data);
      setMsg("Report generated and sent to the patient.");
    } catch (err) {
      setError(apiErrorMessage(err, "Couldn't generate the report."));
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="card px-5 py-5 space-y-3.5">
      <div className="flex items-center justify-between">
        <p className="font-mono text-xs text-muted">Booking #{booking.id.slice(0, 8)}</p>
        <div className="flex gap-2">
          <StatusBadge status={booking.status} />
          <StatusBadge status={booking.payment_status} />
        </div>
      </div>
      <p className="text-sm">Scheduled for {new Date(booking.scheduled_date).toLocaleString()}</p>

      <ErrorBanner message={error} />
      {msg && (
        <div className="text-xs text-status-ok bg-status-okBg rounded-lg px-3.5 py-2.5 border border-status-ok/15">
          {msg}
        </div>
      )}

      {!report ? (
        <div className="space-y-2">
          <label className="label mb-0">Enter measured values</label>
          <div className="flex gap-2">
            <input
              placeholder='{"hemoglobin": 10.2, "wbc": 12500, "glucose_fasting": 95}'
              value={values}
              onChange={(e) => setValues(e.target.value)}
              className="input flex-1 font-mono"
            />
            <button onClick={handleGenerate} disabled={generating} className="btn-primary whitespace-nowrap">
              {generating && <Spinner />}
              Generate report
            </button>
          </div>
          <p className="text-xs text-muted">
            The system builds a clean PDF from these values automatically — no file upload needed.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          <p className="text-xs text-muted">
            Report generated: {report.original_filename}
            {report.anomalies?.length > 0 && ` — ${report.anomalies.length} value(s) flagged`}
          </p>
          <div className="flex gap-2">
            <input
              placeholder='Re-enter values to correct/regenerate'
              value={values}
              onChange={(e) => setValues(e.target.value)}
              className="input flex-1 font-mono"
            />
            <button onClick={handleGenerate} disabled={generating} className="btn-secondary whitespace-nowrap">
              {generating && <Spinner />}
              Regenerate
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function CenterBookings() {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/bookings/center")
      .then(({ data }) => setBookings(data))
      .catch((err) => setError(apiErrorMessage(err, "Couldn't load bookings.")))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-2xl mx-auto px-4 py-14">
      <p className="eyebrow mb-2">Center operations</p>
      <h1 className="text-2xl font-semibold mb-1">Bookings</h1>
      <p className="text-muted text-sm mb-7">
        Paid bookings at your center. Enter test values once results are ready — the system builds the report.
      </p>

      <ErrorBanner message={error} />

      {loading ? (
        <div className="flex justify-center py-16 text-muted">
          <Spinner className="h-6 w-6" />
        </div>
      ) : bookings.length === 0 ? (
        <EmptyState title="No paid bookings yet" description="Confirmed bookings will show up here once patients pay." />
      ) : (
        <div className="space-y-3">
          {bookings.map((b) => (
            <ReportRow key={b.id} booking={b} />
          ))}
        </div>
      )}
    </div>
  );
}
