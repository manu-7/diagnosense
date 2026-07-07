import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/**
 * Signature hero visualization: a precision gauge with a marker settling
 * into the healthy zone. This is a direct callback to the real anomaly
 * RangeBar component patients see on their actual report page — the brand
 * identity is earned from the product's real feature, not decorative.
 */
function HeroGauge() {
  return (
    <div className="relative w-full max-w-md mx-auto">
      <svg viewBox="0 0 400 180" className="w-full h-auto" aria-hidden="true">
        <defs>
          <linearGradient id="zoneGradient" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#1F8A5F" stopOpacity="0.12" />
            <stop offset="50%" stopColor="#1F8A5F" stopOpacity="0.28" />
            <stop offset="100%" stopColor="#1F8A5F" stopOpacity="0.12" />
          </linearGradient>
        </defs>

        {/* track */}
        <rect x="20" y="86" width="360" height="10" rx="5" fill="#E5E3DD" />
        {/* healthy zone */}
        <rect x="130" y="86" width="140" height="10" rx="5" fill="url(#zoneGradient)" stroke="#1F8A5F" strokeOpacity="0.3" />

        {/* tick labels */}
        <text x="20" y="130" fontSize="11" fill="#63706A" fontFamily="IBM Plex Mono, monospace">4.2</text>
        <text x="188" y="130" fontSize="11" fill="#1F8A5F" fontFamily="IBM Plex Mono, monospace">normal range</text>
        <text x="358" y="130" fontSize="11" fill="#63706A" fontFamily="IBM Plex Mono, monospace" textAnchor="end">17.8</text>

        {/* moving marker */}
        <g>
          <circle cx="200" cy="91" r="9" fill="#0D4F45" stroke="#FAF9F6" strokeWidth="3">
            <animate attributeName="cx" values="245;200;245" dur="4.5s" repeatCount="indefinite" />
          </circle>
        </g>

        <text x="200" y="55" fontSize="15" fill="#14181A" fontFamily="Fraunces, serif" fontWeight="600" textAnchor="middle">
          Hemoglobin
        </text>
        <text x="200" y="150" fontSize="12" fill="#63706A" fontFamily="Inter, sans-serif" textAnchor="middle">
          exactly where you stand — not just a number
        </text>
      </svg>
    </div>
  );
}

export default function Home() {
  const { isAuthenticated, role } = useAuth();

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 pt-20 pb-28">
      <div className="text-center max-w-2xl mx-auto">
        <p className="eyebrow mb-4">AI-matched diagnostics</p>
        <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight leading-[1.1] text-ink">
          Describe your symptoms.
          <br />
          <span className="italic text-pine">Get matched to the right test.</span>
        </h1>
        <p className="text-muted text-base sm:text-lg mt-6 leading-relaxed">
          DiagnoSense matches free-text symptoms against real, bookable test
          packages at approved diagnostic centers — then shows you exactly where
          your results land, not just a number on a page.
        </p>

        <div className="flex items-center justify-center gap-3 mt-9">
          {!isAuthenticated && (
            <>
              <Link to="/register" className="btn-primary">
                Get started
              </Link>
              <Link to="/centers" className="btn-secondary">
                Browse centers
              </Link>
            </>
          )}
          {isAuthenticated && role === "patient" && (
            <Link to="/symptom-check" className="btn-primary">
              Start a symptom check
            </Link>
          )}
          {isAuthenticated && role === "center" && (
            <Link to="/center/dashboard" className="btn-primary">
              Go to dashboard
            </Link>
          )}
        </div>
      </div>

      <div className="mt-20 card p-10">
        <HeroGauge />
      </div>

      <p className="text-xs text-muted mt-10 text-center max-w-md mx-auto">
        Not a diagnosis. Suggestions are generated automatically and should be
        confirmed with a licensed physician.
      </p>
    </div>
  );
}
