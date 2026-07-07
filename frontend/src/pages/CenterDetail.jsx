import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api, apiErrorMessage } from "../api/client";
import { openRazorpayCheckout } from "../utils/razorpay";
import { ErrorBanner, EmptyState, Spinner } from "../components/Feedback";

export default function CenterDetail() {
  const { centerId } = useParams();
  const { isAuthenticated, role } = useAuth();
  const navigate = useNavigate();

  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [bookingPkgId, setBookingPkgId] = useState(null);
  const [scheduledDate, setScheduledDate] = useState("");
  const [statusMsg, setStatusMsg] = useState("");

  useEffect(() => {
    api
      .get(`/centers/${centerId}/packages`)
      .then(({ data }) => setPackages(data))
      .catch((err) => setError(apiErrorMessage(err, "Couldn't load packages.")))
      .finally(() => setLoading(false));
  }, [centerId]);

  async function handleBook(pkg) {
    if (!isAuthenticated) {
      navigate("/login");
      return;
    }
    if (role !== "patient") {
      setError("Only patient accounts can book tests.");
      return;
    }
    if (!scheduledDate) {
      setError("Pick a date and time first.");
      return;
    }
    setError("");
    setStatusMsg("Creating your booking…");
    try {
      const { data: booking } = await api.post("/bookings", {
        center_id: centerId,
        package_id: pkg.id,
        scheduled_date: new Date(scheduledDate).toISOString(),
      });

      setStatusMsg("Opening payment…");
      const { data: order } = await api.post(`/bookings/${booking.id}/create-order`);

      openRazorpayCheckout({
        order,
        patientName: "",
        patientEmail: "",
        onSuccess: async (verifyPayload) => {
          setStatusMsg("Verifying payment…");
          try {
            await api.post("/bookings/verify-payment", verifyPayload);
            setStatusMsg("Booked and paid. Redirecting to your bookings…");
            setTimeout(() => navigate("/bookings"), 1000);
          } catch (err) {
            setError(apiErrorMessage(err, "Payment verification failed. Contact support with your order ID."));
            setStatusMsg("");
          }
        },
        onDismiss: () => setStatusMsg(""),
      });
    } catch (err) {
      setError(apiErrorMessage(err, "Couldn't start booking."));
      setStatusMsg("");
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-14">
      <p className="eyebrow mb-2">Book a test</p>
      <h1 className="text-2xl font-semibold mb-1">Available test packages</h1>
      <p className="text-muted text-sm mb-7">Pick a package, choose a date, then pay to confirm your slot.</p>

      <ErrorBanner message={error} />
      {statusMsg && (
        <div className="text-sm text-pine-dark bg-pine-light rounded-xl2 px-5 py-3.5 my-4 border border-pine/10">
          {statusMsg}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-16 text-muted">
          <Spinner className="h-6 w-6" />
        </div>
      ) : packages.length === 0 ? (
        <EmptyState title="No packages listed yet" description="This center hasn't added any test packages." />
      ) : (
        <div className="space-y-3 mt-4">
          {packages.map((pkg) => (
            <div key={pkg.id} className="card px-5 py-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-display font-semibold text-sm">{pkg.name}</p>
                  <p className="text-xs text-muted mt-0.5">{pkg.test_type}</p>
                  {pkg.description && <p className="text-sm text-muted mt-2">{pkg.description}</p>}
                </div>
                <p className="font-mono text-sm font-medium whitespace-nowrap ml-4">₹{pkg.price.toFixed(0)}</p>
              </div>

              {bookingPkgId === pkg.id ? (
                <div className="flex gap-2 mt-4">
                  <input
                    type="datetime-local"
                    value={scheduledDate}
                    onChange={(e) => setScheduledDate(e.target.value)}
                    className="input flex-1"
                  />
                  <button onClick={() => handleBook(pkg)} className="btn-primary whitespace-nowrap">
                    Pay & confirm
                  </button>
                </div>
              ) : (
                <button onClick={() => setBookingPkgId(pkg.id)} className="btn-secondary mt-4">
                  Book this test
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
