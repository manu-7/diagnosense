import { useState } from "react";
import { Link } from "react-router-dom";
import { api, apiErrorMessage } from "../api/client";
import { ErrorBanner, EmptyState, Spinner } from "../components/Feedback";

export default function SymptomChecker() {
  const [symptoms, setSymptoms] = useState("");
  const [city, setCity] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const { data } = await api.post("/ai/symptom-check", { symptoms, city: city || undefined });
      setResult(data);
    } catch (err) {
      setError(apiErrorMessage(err, "Couldn't get recommendations right now."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-14">
      <p className="eyebrow mb-2">AI triage</p>
      <h1 className="text-2xl font-semibold mb-1">Symptom check</h1>
      <p className="text-muted text-sm mb-7">
        Describe what you're experiencing in plain language. This is triage, not a diagnosis.
      </p>

      <form onSubmit={handleSubmit} className="card p-6 space-y-4 mb-8">
        <textarea
          required
          minLength={3}
          maxLength={1000}
          rows={4}
          placeholder="e.g. Persistent fatigue, mild fever for 3 days, occasional dizziness"
          value={symptoms}
          onChange={(e) => setSymptoms(e.target.value)}
          className="input resize-none"
        />
        <input
          placeholder="City (optional)"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          className="input"
        />

        <ErrorBanner message={error} />

        <button type="submit" disabled={loading} className="btn-primary">
          {loading && <Spinner />}
          Get recommendations
        </button>
      </form>

      {result && (
        <div>
          <div className="rounded-xl2 bg-pine-light text-pine-dark px-5 py-4 text-sm mb-5 border border-pine/10">
            {result.ai_reasoning}
          </div>
          <p className="text-xs text-muted mb-4">{result.disclaimer}</p>

          {result.recommended_packages.length === 0 ? (
            <EmptyState
              title="No matching packages found"
              description="Try rephrasing your symptoms or removing the city filter."
            />
          ) : (
            <div className="space-y-3">
              {result.recommended_packages.map((pkg) => (
                <div key={pkg.package_id} className="card card-hover flex items-center justify-between px-5 py-4">
                  <div>
                    <p className="font-display font-semibold text-sm">{pkg.name}</p>
                    <p className="text-xs text-muted mt-0.5">
                      {pkg.center_name} · {pkg.test_type}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-mono text-sm font-medium">₹{pkg.price.toFixed(0)}</p>
                    <Link to="/centers" className="text-xs text-pine font-medium">
                      Book this test
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
