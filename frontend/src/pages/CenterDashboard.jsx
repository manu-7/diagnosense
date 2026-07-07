import { useEffect, useState } from "react";
import { api, apiErrorMessage } from "../api/client";
import { ErrorBanner, EmptyState, Spinner } from "../components/Feedback";
import StatusBadge from "../components/StatusBadge";

export default function CenterDashboard() {
  const [center, setCenter] = useState(null);
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [profileForm, setProfileForm] = useState({ center_name: "", address: "", city: "", license_number: "" });
  const [pkgForm, setPkgForm] = useState({ name: "", description: "", symptom_tags: "", test_type: "", price: "" });
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingPkg, setSavingPkg] = useState(false);

  async function loadCenter() {
    try {
      const { data } = await api.get("/centers/me");
      setCenter(data);
      const pkgs = await api.get(`/centers/${data.id}/packages`);
      setPackages(pkgs.data);
    } catch (err) {
      if (err.response?.status !== 404) {
        setError(apiErrorMessage(err, "Couldn't load your center profile."));
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCenter();
  }, []);

  async function handleCreateProfile(e) {
    e.preventDefault();
    setSavingProfile(true);
    setError("");
    try {
      const { data } = await api.post("/centers/me", profileForm);
      setCenter(data);
    } catch (err) {
      setError(apiErrorMessage(err, "Couldn't create your center profile."));
    } finally {
      setSavingProfile(false);
    }
  }

  async function handleCreatePackage(e) {
    e.preventDefault();
    setSavingPkg(true);
    setError("");
    try {
      const { data } = await api.post("/centers/me/packages", {
        ...pkgForm,
        price: parseFloat(pkgForm.price),
      });
      setPackages([...packages, data]);
      setPkgForm({ name: "", description: "", symptom_tags: "", test_type: "", price: "" });
    } catch (err) {
      setError(apiErrorMessage(err, "Couldn't add this package."));
    } finally {
      setSavingPkg(false);
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-24 text-muted">
        <Spinner className="h-6 w-6" />
      </div>
    );
  }

  if (!center) {
    return (
      <div className="max-w-md mx-auto px-4 py-14">
        <p className="eyebrow mb-2">Center setup</p>
        <h1 className="text-2xl font-semibold mb-1">Set up your center</h1>
        <p className="text-muted text-sm mb-7">
          Create your profile first — an admin needs to approve it before it's listed publicly.
        </p>
        <form onSubmit={handleCreateProfile} className="card p-6 space-y-4">
          <input
            required
            placeholder="Center name"
            value={profileForm.center_name}
            onChange={(e) => setProfileForm({ ...profileForm, center_name: e.target.value })}
            className="input"
          />
          <input
            required
            placeholder="Address"
            value={profileForm.address}
            onChange={(e) => setProfileForm({ ...profileForm, address: e.target.value })}
            className="input"
          />
          <input
            required
            placeholder="City"
            value={profileForm.city}
            onChange={(e) => setProfileForm({ ...profileForm, city: e.target.value })}
            className="input"
          />
          <input
            placeholder="License number (optional)"
            value={profileForm.license_number}
            onChange={(e) => setProfileForm({ ...profileForm, license_number: e.target.value })}
            className="input"
          />
          <ErrorBanner message={error} />
          <button disabled={savingProfile} className="btn-primary w-full">
            {savingProfile && <Spinner />}
            Create profile
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-14">
      <p className="eyebrow mb-2">Center dashboard</p>
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-2xl font-semibold">{center.center_name}</h1>
        <StatusBadge status={center.is_approved ? "CONFIRMED" : "PENDING"} />
      </div>
      <p className="text-muted text-sm mb-8">
        {center.address}, {center.city}
        {!center.is_approved && " — waiting on admin approval before patients can find you."}
      </p>

      <ErrorBanner message={error} />

      <h2 className="font-display font-semibold text-lg mt-4 mb-3">Test packages</h2>
      {packages.length === 0 ? (
        <EmptyState title="No packages yet" description="Add your first test package below." />
      ) : (
        <div className="space-y-2.5 mb-6">
          {packages.map((p) => (
            <div key={p.id} className="card flex items-center justify-between px-5 py-4">
              <div>
                <p className="font-display font-semibold text-sm">{p.name}</p>
                <p className="text-xs text-muted">{p.test_type}</p>
              </div>
              <p className="font-mono text-sm">₹{p.price.toFixed(0)}</p>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleCreatePackage} className="card p-6 space-y-3">
        <p className="text-sm font-semibold font-display">Add a package</p>
        <input
          required
          placeholder="Package name (e.g. Complete Blood Count)"
          value={pkgForm.name}
          onChange={(e) => setPkgForm({ ...pkgForm, name: e.target.value })}
          className="input"
        />
        <input
          required
          placeholder="Test type (e.g. blood, urine, imaging)"
          value={pkgForm.test_type}
          onChange={(e) => setPkgForm({ ...pkgForm, test_type: e.target.value })}
          className="input"
        />
        <input
          placeholder="Symptom tags (e.g. fatigue, dizziness, pale skin)"
          value={pkgForm.symptom_tags}
          onChange={(e) => setPkgForm({ ...pkgForm, symptom_tags: e.target.value })}
          className="input"
        />
        <textarea
          placeholder="Description (optional)"
          value={pkgForm.description}
          onChange={(e) => setPkgForm({ ...pkgForm, description: e.target.value })}
          rows={2}
          className="input resize-none"
        />
        <input
          required
          type="number"
          step="0.01"
          min="0.01"
          placeholder="Price (₹)"
          value={pkgForm.price}
          onChange={(e) => setPkgForm({ ...pkgForm, price: e.target.value })}
          className="input"
        />
        <button disabled={savingPkg} className="btn-primary">
          {savingPkg && <Spinner />}
          Add package
        </button>
      </form>
    </div>
  );
}
