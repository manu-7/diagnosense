import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api, apiErrorMessage, clearTokens, setTokens } from "../api/client";

const AuthContext = createContext(null);

function decodeRole(accessToken) {
  try {
    const payload = JSON.parse(atob(accessToken.split(".")[1]));
    return payload.role;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [role, setRole] = useState(() => localStorage.getItem("user_role"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const access = localStorage.getItem("access_token");
    if (!access) {
      setLoading(false);
      return;
    }
    // We don't have a /users/me endpoint, so we rely on the JWT role claim
    // for gating routes and re-fetch specific profile data per page as needed.
    setRole(decodeRole(access));
    setLoading(false);
  }, []);

  async function login(email, password) {
    const { data } = await api.post("/auth/login", { email, password });
    setTokens(data.access_token, data.refresh_token);
    const decodedRole = decodeRole(data.access_token);
    localStorage.setItem("user_role", decodedRole);
    setRole(decodedRole);
    return decodedRole;
  }

  async function register(payload) {
    await api.post("/auth/register", payload);
  }

  function logout() {
    clearTokens();
    setUser(null);
    setRole(null);
  }

  const value = useMemo(
    () => ({ user, role, loading, login, register, logout, isAuthenticated: !!role }),
    [user, role, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export { apiErrorMessage };
