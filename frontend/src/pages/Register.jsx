import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { apiErrorMessage } from "../api/client";
import { ErrorBanner, Spinner } from "../components/Feedback";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", phone: "", password: "", role: "patient" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(form);
      setSuccess(true);
      setTimeout(() => navigate("/login"), 1200);
    } catch (err) {
      setError(apiErrorMessage(err, "Couldn't create your account."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-16 px-4">
      <div className="card p-8">
        <p className="eyebrow mb-2">Get started</p>
        <h1 className="text-2xl font-semibold mb-1">Create an account</h1>
        <p className="text-muted text-sm mb-6">
          Patients book tests. Centers list packages and manage bookings.
        </p>

        <div className="grid grid-cols-2 gap-2 mb-6">
          {["patient", "center"].map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => setForm({ ...form, role: r })}
              className={`rounded-lg border py-2.5 text-sm font-medium capitalize transition-colors ${
                form.role === r ? "border-pine bg-pine-light text-pine-dark" : "border-line text-muted hover:border-pine/30"
              }`}
            >
              {r === "patient" ? "I'm a patient" : "I run a center"}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Full name</label>
            <input
              required
              minLength={2}
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="input"
            />
          </div>
          <div>
            <label className="label">Email</label>
            <input
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="input"
            />
          </div>
          <div>
            <label className="label">Phone (optional)</label>
            <input
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              className="input"
            />
          </div>
          <div>
            <label className="label">Password</label>
            <input
              type="password"
              required
              minLength={8}
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="input"
            />
            <p className="text-xs text-muted mt-1.5">At least 8 characters.</p>
          </div>

          <ErrorBanner message={error} />
          {success && (
            <div className="rounded-lg bg-status-okBg text-status-ok px-4 py-3 text-sm font-medium border border-status-ok/15">
              Account created — redirecting to log in.
            </div>
          )}

          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading && <Spinner />}
            Create account
          </button>
        </form>
      </div>

      <p className="text-sm text-muted mt-6 text-center">
        Already registered?{" "}
        <Link to="/login" className="text-pine font-medium">
          Log in
        </Link>
      </p>
    </div>
  );
}
