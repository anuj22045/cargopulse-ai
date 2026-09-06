import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Search, X, ChevronLeft, ChevronRight, Filter } from "lucide-react";
import { getShipments, type Shipment } from "../services/shipmentService";

function StatusBadge({ status }: { status: string | null }) {
  const map: Record<string, string> = {
    Shipping: "bg-blue-100 text-blue-700",
    Shipped: "bg-purple-100 text-purple-700",
    Delivered: "bg-green-100 text-green-700",
    "Late delivery": "bg-red-100 text-red-700",
    Cancelled: "bg-slate-100 text-slate-600",
    "Suspected Fraud": "bg-orange-100 text-orange-700",
  };
  const cls = status
    ? (map[status] ?? "bg-slate-100 text-slate-600")
    : "bg-slate-100 text-slate-600";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${cls}`}
    >
      {status ?? "Unknown"}
    </span>
  );
}

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
          err instanceof Error ? err.message : "Failed to load shipments"
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

  function handleShippingModeChange(event: React.ChangeEvent<HTMLSelectElement>) {
    setShippingMode(event.target.value);
    setCurrentPage(1);
  }

  function handleShipmentStatusChange(event: React.ChangeEvent<HTMLSelectElement>) {
    setShipmentStatus(event.target.value);
    setCurrentPage(1);
  }

  function handlePrevious() {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  }

  function handleNext() {
    if (shipments.length === pageSize) setCurrentPage(currentPage + 1);
  }

  return (
    <div className="space-y-5">
      {/* Filters row */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Search */}
        <div className="relative flex-1 min-w-[220px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            id="shipments-search-input"
            type="text"
            placeholder="Search by reference or order ID…"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") handleSearch();
            }}
            className="w-full rounded-lg border border-slate-300 bg-white py-2 pl-9 pr-10 text-sm text-slate-900 placeholder-slate-400 outline-none transition focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
          {searchInput && (
            <button
              onClick={handleClearSearch}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        <button
          id="shipments-search-btn"
          onClick={handleSearch}
          className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-amber-600"
        >
          Search
        </button>

        {/* Divider */}
        <div className="h-6 w-px bg-slate-200" />

        {/* Filters */}
        <div className="flex items-center gap-2">
          <Filter className="h-3.5 w-3.5 text-slate-400" />
          <span className="text-xs text-slate-500">Filters:</span>
        </div>

        <select
          id="shipments-mode-filter"
          value={shippingMode}
          onChange={handleShippingModeChange}
          className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        >
          <option value="">All Modes</option>
          <option value="First Class">First Class</option>
          <option value="Second Class">Second Class</option>
          <option value="Same Day">Same Day</option>
          <option value="Standard Class">Standard Class</option>
        </select>

        <select
          id="shipments-status-filter"
          value={shipmentStatus}
          onChange={handleShipmentStatusChange}
          className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        >
          <option value="">All Statuses</option>
          <option value="Shipping">Shipping</option>
          <option value="Shipped">Shipped</option>
          <option value="Delivered">Delivered</option>
          <option value="Late delivery">Late delivery</option>
          <option value="Cancelled">Cancelled</option>
          <option value="Suspected Fraud">Suspected Fraud</option>
        </select>
      </div>

      {/* Table card */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        {loading ? (
          <div className="space-y-3 p-6">
            {[...Array(pageSize)].map((_, i) => (
              <div key={i} className="h-8 animate-pulse rounded bg-slate-100" />
            ))}
          </div>
        ) : error ? (
          <div className="px-6 py-8 text-center text-sm text-red-500">
            Error: {error}
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <th className="px-5 py-3">Reference</th>
                    <th className="px-5 py-3">Order ID</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3">Shipping Mode</th>
                    <th className="px-5 py-3">Region</th>
                    <th className="px-5 py-3">Market</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {shipments.map((shipment) => (
                    <tr
                      key={shipment.id}
                      className="transition-colors hover:bg-slate-50"
                    >
                      <td className="px-5 py-3">
                        <Link
                          to={`/shipments/${shipment.id}`}
                          className="font-medium text-amber-600 hover:text-amber-700 hover:underline"
                        >
                          {shipment.shipment_reference}
                        </Link>
                      </td>
                      <td className="px-5 py-3 text-slate-600">
                        {shipment.order_id ?? "—"}
                      </td>
                      <td className="px-5 py-3">
                        <StatusBadge status={shipment.shipment_status} />
                      </td>
                      <td className="px-5 py-3 text-slate-600">
                        {shipment.shipping_mode ?? "—"}
                      </td>
                      <td className="px-5 py-3 text-slate-600">
                        {shipment.order_region ?? "—"}
                      </td>
                      <td className="px-5 py-3 text-slate-600">
                        {shipment.market ?? "—"}
                      </td>
                    </tr>
                  ))}
                  {shipments.length === 0 && (
                    <tr>
                      <td
                        colSpan={6}
                        className="px-5 py-10 text-center text-slate-400"
                      >
                        No shipments found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between border-t border-slate-100 px-5 py-3">
              <p className="text-xs text-slate-500">
                Page <span className="font-medium text-slate-700">{currentPage}</span>
                {" "}· {shipments.length} records
              </p>
              <div className="flex items-center gap-2">
                <button
                  id="shipments-prev-btn"
                  onClick={handlePrevious}
                  disabled={currentPage === 1}
                  className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                  Previous
                </button>
                <button
                  id="shipments-next-btn"
                  onClick={handleNext}
                  disabled={shipments.length < pageSize}
                  className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Next
                  <ChevronRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default Shipments;