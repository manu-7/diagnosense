import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";

import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import SymptomChecker from "./pages/SymptomChecker";
import Centers from "./pages/Centers";
import CenterDetail from "./pages/CenterDetail";
import MyBookings from "./pages/MyBookings";
import ReportDetail from "./pages/ReportDetail";
import CenterDashboard from "./pages/CenterDashboard";
import CenterBookings from "./pages/CenterBookings";

export default function App() {
  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/centers" element={<Centers />} />
          <Route path="/centers/:centerId" element={<CenterDetail />} />

          <Route
            path="/symptom-check"
            element={
              <ProtectedRoute allow={["patient"]}>
                <SymptomChecker />
              </ProtectedRoute>
            }
          />
          <Route
            path="/bookings"
            element={
              <ProtectedRoute allow={["patient"]}>
                <MyBookings />
              </ProtectedRoute>
            }
          />
          <Route
            path="/bookings/:bookingId/report"
            element={
              <ProtectedRoute allow={["patient", "center", "admin"]}>
                <ReportDetail />
              </ProtectedRoute>
            }
          />

          <Route
            path="/center/dashboard"
            element={
              <ProtectedRoute allow={["center"]}>
                <CenterDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/center/bookings"
            element={
              <ProtectedRoute allow={["center"]}>
                <CenterBookings />
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<Home />} />
        </Routes>
      </main>
    </div>
  );
}
