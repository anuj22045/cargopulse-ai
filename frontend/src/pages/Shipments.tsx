import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getShipments, type Shipment } from "../services/shipmentService";

function Shipments() {
    const [shipments, setShipments] = useState<Shipment[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [shippingMode, setShippingMode] = useState("");
    const [shipmentStatus, setShipmentStatus] = useState("");
    const [search, setSearch] = useState("");
    const [searchInput, setSearchInput] = useState("");

    const pageSize = 10;

    useEffect(() => {
    async function loadShipments() {    
        setLoading(true);
        setError(null);

        try {
        const skip = (currentPage - 1) * pageSize;

        const data = await getShipments(
            skip,
            pageSize,
            shippingMode,
            shipmentStatus,
            search
        );

        setShipments(data);
        } catch (err) {
        setError(
            err instanceof Error
            ? err.message
            : "Failed to load shipments"
        );
        } finally {
        setLoading(false);
        }
    }

    loadShipments();
    }, [currentPage, shippingMode, shipmentStatus, search]);

    function handleSearch() {
    setSearch(searchInput.trim());
    setCurrentPage(1);
    }

    function handleClearSearch() {
    setSearchInput("");
    setSearch("");
    setCurrentPage(1);
    }

    function handleShippingModeChange(
    event: React.ChangeEvent<HTMLSelectElement>
    ) {
    setShippingMode(event.target.value);
    setCurrentPage(1);
    }

    function handleShipmentStatusChange(
    event: React.ChangeEvent<HTMLSelectElement>
    ) {
    setShipmentStatus(event.target.value);
    setCurrentPage(1);
    }

    function handlePrevious() {
    if (currentPage > 1) {
        setCurrentPage(currentPage - 1);
    }
    }

    function handleNext() {
    if (shipments.length === pageSize) {
        setCurrentPage(currentPage + 1);
    }
    }

    if (loading) {
    return <p>Loading shipments...</p>;
    }

    if (error) {
    return <p>Error: {error}</p>;
    }

    return (
    <div>
        <h1>Shipments</h1>

        <div>
        <input
            type="text"
            placeholder="Search shipment reference or order ID"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            onKeyDown={(event) => {
            if (event.key === "Enter") {
                handleSearch();
            }
            }}
        />

        <button onClick={handleSearch}>
            Search
        </button>   

        <button onClick={handleClearSearch}>
            Clear
        </button>
        </div>

        <div>
        <label>
            Shipping Mode:
            <select
            value={shippingMode}
            onChange={handleShippingModeChange}
            >
            <option value="">All</option>
            <option value="First Class">First Class</option>
            <option value="Second Class">Second Class</option>
            <option value="Same Day">Same Day</option>
            <option value="Standard Class">Standard Class</option>
            </select>
        </label>

        <label>
            Shipment Status:
            <select
            value={shipmentStatus}
            onChange={handleShipmentStatusChange}
            >
            <option value="">All</option>
            <option value="Shipping">Shipping</option>
            <option value="Shipped">Shipped</option>
            <option value="Delivered">Delivered</option>
            <option value="Late delivery">Late delivery</option>
            <option value="Cancelled">Cancelled</option>
            <option value="Suspected Fraud">Suspected Fraud</option>
            </select>
        </label>
        </div>

        <table>
        <thead>
            <tr>
            <th>Reference</th>
            <th>Order ID</th>
            <th>Status</th>
            <th>Shipping Mode</th>
            <th>Region</th>
            <th>Market</th>
            </tr>
        </thead>

        <tbody>
            {shipments.map((shipment) => (
            <tr key={shipment.id}>
            <td>
                <Link to={`/shipments/${shipment.id}`}>
                {shipment.shipment_reference}
                </Link>
            </td>
            <td>{shipment.order_id}</td>
            <td>{shipment.shipment_status}</td>
            <td>{shipment.shipping_mode}</td>
            <td>{shipment.order_region}</td>
            <td>{shipment.market}</td>
            </tr>
            ))}
        </tbody>
        </table>

        {shipments.length === 0 && (
        <p>No shipments found.</p>
        )}

        <div>
        <button
            onClick={handlePrevious}
            disabled={currentPage === 1}
        >
            Previous
        </button>

        <span>
            Page {currentPage}
        </span>

        <button
            onClick={handleNext}
            disabled={shipments.length < pageSize}
        >
            Next
        </button>
        </div>
    </div>
    );
}

export default Shipments;