import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, apiErrorMessage } from "../api/client";
import { ErrorBanner, EmptyState, Spinner } from "../components/Feedback";

export default function Centers() {
  const [centers, setCenters] = useState([]);
  const [city, setCity] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadCenters(cityFilter) {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get("/centers", { params: cityFilter ? { city: cityFilter } : {} });
      setCenters(data);
    } catch (err) {
      setError(apiErrorMessage(err, "Couldn't load centers."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCenters();
  }, []);

  return (
    <div className="max-w-3xl mx-auto px-4 py-14">
      <p className="eyebrow mb-2">Approved network</p>
      <h1 className="text-2xl font-semibold mb-1">Diagnostic centers</h1>
      <p className="text-muted text-sm mb-7">Approved centers you can book a test with.</p>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          loadCenters(city);
        }}
        className="flex gap-2 mb-8"
      >
        <input
          placeholder="Filter by city"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          className="input flex-1"
        />
        <button className="btn-secondary">Filter</button>
      </form>

      <ErrorBanner message={error} />

      {loading ? (
        <div className="flex justify-center py-16 text-muted">
          <Spinner className="h-6 w-6" />
        </div>
      ) : centers.length === 0 ? (
        <EmptyState title="No approved centers found" description="Try a different city, or check back later." />
      ) : (
        <div className="space-y-3">
          {centers.map((center) => (
            <Link key={center.id} to={`/centers/${center.id}`} className="card card-hover block px-5 py-4">
              <p className="font-display font-semibold text-sm">{center.center_name}</p>
              <p className="text-xs text-muted mt-0.5">
                {center.address}, {center.city}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
