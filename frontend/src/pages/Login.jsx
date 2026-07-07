import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { apiErrorMessage } from "../api/client";
import { ErrorBanner, Spinner } from "../components/Feedback";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const role = await login(form.email, form.password);
      const redirectTo = location.state?.from?.pathname;
      if (redirectTo) navigate(redirectTo, { replace: true });
      else navigate(role === "center" ? "/center/dashboard" : "/symptom-check", { replace: true });
    } catch (err) {
      setError(apiErrorMessage(err, "Couldn't log in. Check your email and password."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-16 px-4">
      <div className="card p-8">
        <p className="eyebrow mb-2">Welcome back</p>
        <h1 className="text-2xl font-semibold mb-1">Log in</h1>
        <p className="text-muted text-sm mb-7">Book tests and view your reports.</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="input"
            />
          </div>
          <div>
            <label className="label" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="input"
            />
          </div>

          <ErrorBanner message={error} />

          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading && <Spinner />}
            Log in
          </button>
        </form>
      </div>

      <p className="text-sm text-muted mt-6 text-center">
        No account yet?{" "}
        <Link to="/register" className="text-pine font-medium">
          Register
        </Link>
      </p>
    </div>
  );
}
