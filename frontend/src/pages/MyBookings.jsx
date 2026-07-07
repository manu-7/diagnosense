import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, apiErrorMessage } from "../api/client";
import { ErrorBanner, EmptyState, Spinner } from "../components/Feedback";
import StatusBadge from "../components/StatusBadge";

export default function MyBookings() {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/bookings/me")
      .then(({ data }) => setBookings(data))
      .catch((err) => setError(apiErrorMessage(err, "Couldn't load your bookings.")))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-2xl mx-auto px-4 py-14">
      <p className="eyebrow mb-2">Your activity</p>
      <h1 className="text-2xl font-semibold mb-1">My bookings</h1>
      <p className="text-muted text-sm mb-7">Track upcoming tests, payment status, and reports.</p>

      <ErrorBanner message={error} />

      {loading ? (
        <div className="flex justify-center py-16 text-muted">
          <Spinner className="h-6 w-6" />
        </div>
      ) : bookings.length === 0 ? (
        <EmptyState title="No bookings yet" description="Run a symptom check or browse centers to book a test." />
      ) : (
        <div className="space-y-3">
          {bookings.map((b) => (
            <div key={b.id} className="card px-5 py-4">
              <div className="flex items-center justify-between">
                <p className="font-mono text-xs text-muted">Booking #{b.id.slice(0, 8)}</p>
                <div className="flex gap-2">
                  <StatusBadge status={b.status} />
                  <StatusBadge status={b.payment_status} />
                </div>
              </div>
              <p className="text-sm mt-2.5">Scheduled for {new Date(b.scheduled_date).toLocaleString()}</p>
              <Link to={`/bookings/${b.id}/report`} className="inline-block text-xs text-pine font-medium mt-2.5">
                View report →
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
