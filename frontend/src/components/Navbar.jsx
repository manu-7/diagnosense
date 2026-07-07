import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function NavItem({ to, children }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `px-3.5 py-2 text-sm font-medium rounded-lg transition-colors ${
          isActive ? "bg-pine-light text-pine-dark" : "text-muted hover:text-ink hover:bg-line/50"
        }`
      }
    >
      {children}
    </NavLink>
  );
}

function LogoMark() {
  return (
    <svg width="34" height="34" viewBox="0 0 34 34" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="34" height="34" rx="9" fill="#0D4F45" />
      <path
        d="M8 18h3.2l2-6.5 3 12 2.4-9 1.8 3.5H26"
        stroke="#F7EEDD"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </svg>
  );
}

export default function Navbar() {
  const { isAuthenticated, role, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="border-b border-line bg-surface/90 backdrop-blur-md sticky top-0 z-30">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-[68px] flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2.5">
          <LogoMark />
          <span className="font-display font-semibold text-lg tracking-tight text-ink">
            Diagno<span className="text-pine">Sense</span>
          </span>
        </Link>

        <nav className="flex items-center gap-1">
          {!isAuthenticated && (
            <>
              <NavItem to="/centers">Find centers</NavItem>
              <NavItem to="/login">Log in</NavItem>
              <Link to="/register" className="btn-primary ml-2 !py-2 !px-4">
                Get started
              </Link>
            </>
          )}

          {isAuthenticated && role === "patient" && (
            <>
              <NavItem to="/symptom-check">Symptom check</NavItem>
              <NavItem to="/centers">Find centers</NavItem>
              <NavItem to="/bookings">My bookings</NavItem>
            </>
          )}

          {isAuthenticated && role === "center" && (
            <>
              <NavItem to="/center/dashboard">Dashboard</NavItem>
              <NavItem to="/center/bookings">Bookings</NavItem>
            </>
          )}

          {isAuthenticated && (
            <button
              onClick={() => {
                logout();
                navigate("/login");
              }}
              className="ml-2 px-3.5 py-2 text-sm font-medium text-muted hover:text-status-danger transition-colors"
            >
              Log out
            </button>
          )}
        </nav>
      </div>
    </header>
  );
}
