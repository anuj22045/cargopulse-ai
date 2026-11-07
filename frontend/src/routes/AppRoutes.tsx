import { BrowserRouter, Routes, Route } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import Dashboard from "../pages/Dashboard";
import Shipments from "../pages/Shipments";
import ShipmentDetails from "../pages/ShipmentDetails";
import Analytics from "../pages/Analytics";
import Login from "../pages/Login";
import Simulation from "../pages/Simulation";
import Optimizer from "../pages/Optimizer";
import DependencyGraph from "../pages/DependencyGraph";

function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<Login />} />

        {/* App (inside MainLayout) */}
        <Route element={<MainLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/shipments" element={<Shipments />} />
          <Route path="/shipments/:shipmentId" element={<ShipmentDetails />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/simulator" element={<Simulation />} />
          {/* Day 17 — Multi-Objective Optimizer */}
          <Route path="/optimizer" element={<Optimizer />} />
          {/* Day 17 — Supply Chain Dependency Graph */}
          <Route path="/dependency-graph" element={<DependencyGraph />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default AppRoutes;