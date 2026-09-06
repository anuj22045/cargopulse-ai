import { BrowserRouter, Routes, Route } from "react-router-dom";
import Shipments from "../pages/Shipments";
import ShipmentDetails from "../pages/ShipmentDetails";

function AppRoutes() {
    return (
    <BrowserRouter>
        <Routes>
        <Route path="/" element={<h1>CargoPulse AI</h1>} />
        <Route path="/shipments" element={<Shipments />} />
        <Route
        path="/shipments/:shipmentId"
        element={<ShipmentDetails />}
        />
        </Routes>
    </BrowserRouter>
    );
}

export default AppRoutes;