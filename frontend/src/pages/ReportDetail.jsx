import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, apiErrorMessage } from "../api/client";
import { ErrorBanner, EmptyState, Spinner } from "../components/Feedback";
import RangeBar from "../components/RangeBar";

export default function ReportDetail() {
  const { bookingId } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    api
      .get(`/reports/by-booking/${bookingId}`)
      .then(({ data }) => setReport(data))
      .catch((err) => {
        if (err.response?.status === 404) {
          setReport(null); // not uploaded yet - not really an "error"
        } else {
          setError(apiErrorMessage(err, "Couldn't load this report."));
        }
      })
      .finally(() => setLoading(false));
  }, [bookingId]);

  async function handleDownload() {
    setDownloading(true);
    setError("");
    try {
      const { data } = await api.get(`/reports/${report.id}/download`);
      window.open(data.signed_url, "_blank", "noopener,noreferrer");
    } catch (err) {
      setError(apiErrorMessage(err, "Couldn't generate a download link."));
    } finally {
      setDownloading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-24 text-muted">
        <Spinner className="h-6 w-6" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-14">
      <p className="eyebrow mb-2">Results</p>
      <h1 className="text-2xl font-semibold mb-1">Lab report</h1>
      <p className="text-muted text-sm mb-7">Values are shown against standard clinical reference ranges.</p>

      <ErrorBanner message={error} />

      {!report ? (
        <EmptyState
          title="No report yet"
          description="The diagnostic center hasn't uploaded results for this booking yet. Check back after your appointment."
        />
      ) : (
        <div className="space-y-6">
          <div className="card px-5 py-4 flex items-center justify-between">
            <div>
              <p className="font-display font-semibold text-sm">{report.original_filename}</p>
              <p className="text-xs text-muted mt-0.5">
                Uploaded {new Date(report.uploaded_at).toLocaleDateString()}
              </p>
            </div>
            <button onClick={handleDownload} disabled={downloading} className="btn-secondary">
              {downloading && <Spinner />}
              Download PDF
            </button>
          </div>

          {report.anomalies && report.anomalies.length > 0 ? (
            <div className="card px-5 py-2 divide-y divide-line">
              <p className="text-sm font-semibold font-display py-3">
                {report.anomalies.length} value{report.anomalies.length > 1 ? "s" : ""} outside normal range
              </p>
              {report.anomalies.map((a) => (
                <RangeBar
                  key={a.parameter}
                  parameter={a.parameter}
                  value={a.value}
                  normalRange={a.normal_range}
                  severity={a.severity}
                  direction={a.direction}
                />
              ))}
              {report.ai_explanation && (
                <div className="py-3">
                  <p className="text-sm text-ink leading-relaxed">{report.ai_explanation}</p>
                  {report.explanation_sources?.length > 0 && (
                    <p className="text-xs text-muted mt-2">
                      Referenced:{" "}
                      {[...new Set(report.explanation_sources.map((s) => s.source_title))].join(", ")}
                    </p>
                  )}
                </div>
              )}
              <p className="text-xs text-muted py-3">
                This is an automated flag against reference ranges, not a diagnosis. Discuss these
                results with your doctor.
              </p>
            </div>
          ) : report.extracted_values ? (
            <div className="rounded-xl2 bg-status-okBg text-status-ok px-5 py-4 text-sm font-medium border border-status-ok/15">
              All extracted values are within normal reference ranges.
            </div>
          ) : (
            <EmptyState
              title="Analysis pending"
              description="The center hasn't run anomaly analysis on this report yet."
            />
          )}
        </div>
      )}
    </div>
  );
}
