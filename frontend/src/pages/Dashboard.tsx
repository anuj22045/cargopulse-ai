import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  Package,
  Truck,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Wifi,
  WifiOff,
} from "lucide-react";
import { getDashboardStats, type DashboardStats } from "../services/dashboardService";
import { getShipments, type Shipment } from "../services/shipmentService";
import { useDashboardWebSocket } from "../hooks/useDashboardWebSocket";

const STATUS_COLORS: Record<string, string> = {
  Shipping: "#3b82f6",
  Shipped: "#8b5cf6",
  Delivered: "#22c55e",
  "Late delivery": "#ef4444",
  Cancelled: "#64748b",
  "Suspected Fraud": "#f97316",
};

const FALLBACK_PIE_COLORS = [
  "#3b82f6", "#22c55e", "#ef4444", "#f59e0b", "#8b5cf6", "#f97316",
];

function StatCard({
  label,
  value,
  icon: Icon,
  color,
  sub,
  live,
}: {
  label: string;
  value: number | string;
  icon: React.ElementType;
  color: string;
  sub?: string;
  live?: boolean;
}) {
  return (
    <div className="flex items-start gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className={`flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-lg ${color}`}>
        <Icon className="h-5 w-5 text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <p className="text-sm text-slate-500">{label}</p>
          {live && (
            <span className="inline-flex h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
          )}
        </div>
        <p className="mt-0.5 text-2xl font-bold text-slate-900">{value}</p>
        {sub && <p className="mt-0.5 text-xs text-slate-400">{sub}</p>}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string | null }) {
  const map: Record<string, string> = {
    Shipping: "bg-blue-100 text-blue-700",
    Shipped: "bg-purple-100 text-purple-700",
    Delivered: "bg-green-100 text-green-700",
    "Late delivery": "bg-red-100 text-red-700",
    Cancelled: "bg-slate-100 text-slate-600",
    "Suspected Fraud": "bg-orange-100 text-orange-700",
  };
  const cls = status ? (map[status] ?? "bg-slate-100 text-slate-600") : "bg-slate-100 text-slate-600";
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${cls}`}>
      {status ?? "Unknown"}
    </span>
  );
}

function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentShipments, setRecentShipments] = useState<Shipment[]>([]);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [shipmentsError, setShipmentsError] = useState<string | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [shipmentsLoading, setShipmentsLoading] = useState(true);

  // Dashboard WebSocket — live stat updates from simulation scheduler
  const { latestStats, wsState, isConnected: wsConnected } = useDashboardWebSocket();

  // Merge live WebSocket stats into the displayed stats
  const displayStats: DashboardStats | null = latestStats
    ? {
        total_shipments: latestStats.total_shipments,
        in_transit: latestStats.in_transit,
        delayed: latestStats.delayed,
        delivered: latestStats.delivered,
        status_breakdown: latestStats.status_breakdown,
        avg_delay_risk: latestStats.avg_delay_risk,
      }
    : stats;

  useEffect(() => {
    getDashboardStats()
      .then(setStats)
      .catch((err: Error) => setStatsError(err.message))
      .finally(() => setStatsLoading(false));

    getShipments(0, 5)
      .then(setRecentShipments)
      .catch((err: Error) => setShipmentsError(err.message))
      .finally(() => setShipmentsLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      {/* Live connection badge */}
      <div className="flex items-center justify-end gap-2">
        {wsConnected ? (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-green-50 px-3 py-1 text-xs font-medium text-green-700 border border-green-200">
            <Wifi className="h-3 w-3" />
            Live updates active
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-500 border border-slate-200">
            <WifiOff className="h-3 w-3" />
            {wsState === "reconnecting" ? "Reconnecting..." : "Disconnected"}
          </span>
        )}
      </div>

      {/* Stat cards */}
      {statsLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 animate-pulse rounded-xl bg-slate-200" />
          ))}
        </div>
      ) : statsError ? (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          Could not load dashboard stats: {statsError}
        </div>
      ) : displayStats ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            label="Total Shipments"
            value={displayStats.total_shipments.toLocaleString()}
            icon={Package}
            color="bg-slate-700"
            live={wsConnected}
          />
          <StatCard
            label="In Transit"
            value={displayStats.in_transit.toLocaleString()}
            icon={Truck}
            color="bg-blue-500"
            sub="Currently active"
            live={wsConnected}
          />
          <StatCard
            label="Delayed"
            value={displayStats.delayed.toLocaleString()}
            icon={AlertTriangle}
            color="bg-red-500"
            sub="Require attention"
            live={wsConnected}
          />
          <StatCard
            label="Delivered"
            value={displayStats.delivered.toLocaleString()}
            icon={CheckCircle}
            color="bg-green-500"
            sub="Successfully completed"
            live={wsConnected}
          />
        </div>
      ) : null}

      {/* Charts row */}
      {displayStats && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Pie chart — status breakdown */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-amber-500" />
              <h2 className="text-sm font-semibold text-slate-800">
                Shipment Status Breakdown
              </h2>
              {wsConnected && (
                <span className="ml-auto text-[10px] text-green-600 font-medium">● Live</span>
              )}
            </div>
            {displayStats.status_breakdown.length === 0 ? (
              <p className="py-8 text-center text-sm text-slate-400">No data available</p>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={displayStats.status_breakdown}
                    dataKey="count"
                    nameKey="status"
                    cx="50%"
                    cy="45%"
                    outerRadius={95}
                    innerRadius={40}
                    isAnimationActive={false}
                  >
                    {displayStats.status_breakdown.map((entry, index) => (
                      <Cell
                        key={entry.status}
                        fill={STATUS_COLORS[entry.status] ?? FALLBACK_PIE_COLORS[index % FALLBACK_PIE_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(val, name) => [
                      `${Number(val).toLocaleString()} shipments`,
                      String(name),
                    ]}
                  />
                  <Legend
                    iconType="circle"
                    iconSize={8}
                    wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }}
                    formatter={(value) => (
                      <span style={{ color: "#475569" }}>{value}</span>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Bar chart — risk distribution */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              <h2 className="text-sm font-semibold text-slate-800">
                Risk Distribution by Status
              </h2>
              {wsConnected && (
                <span className="ml-auto text-[10px] text-green-600 font-medium">● Live</span>
              )}
            </div>
            {displayStats.status_breakdown.length === 0 ? (
              <p className="py-8 text-center text-sm text-slate-400">No data available</p>
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={displayStats.status_breakdown} margin={{ left: -10 }}>
                  <XAxis
                    dataKey="status"
                    tick={{ fontSize: 11, fill: "#64748b" }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: "#64748b" }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip
                    cursor={{ fill: "#f1f5f9" }}
                    formatter={(val) => [Number(val).toLocaleString(), "Shipments"]}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]} isAnimationActive={false}>
                    {displayStats.status_breakdown.map((entry, index) => (
                      <Cell
                        key={entry.status}
                        fill={STATUS_COLORS[entry.status] ?? FALLBACK_PIE_COLORS[index % FALLBACK_PIE_COLORS.length]}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      )}

      {/* Recent shipments */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <h2 className="text-sm font-semibold text-slate-800">Recent Shipments</h2>
          <Link
            to="/shipments"
            className="text-xs font-medium text-amber-600 hover:text-amber-700"
          >
            View all →
          </Link>
        </div>

        {shipmentsLoading ? (
          <div className="space-y-3 p-5">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-8 animate-pulse rounded bg-slate-100" />
            ))}
          </div>
        ) : shipmentsError ? (
          <p className="px-5 py-4 text-sm text-red-500">
            Could not load recent shipments: {shipmentsError}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  <th className="px-5 py-3">Reference</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Shipping Mode</th>
                  <th className="px-5 py-3">Market</th>
                  <th className="px-5 py-3">Region</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {recentShipments.map((s) => (
                  <tr
                    key={s.id}
                    className="transition-colors hover:bg-slate-50"
                  >
                    <td className="px-5 py-3">
                      <Link
                        to={`/shipments/${s.id}`}
                        className="font-medium text-amber-600 hover:text-amber-700 hover:underline"
                      >
                        {s.shipment_reference}
                      </Link>
                    </td>
                    <td className="px-5 py-3">
                      <StatusBadge status={s.shipment_status} />
                    </td>
                    <td className="px-5 py-3 text-slate-600">{s.shipping_mode ?? "—"}</td>
                    <td className="px-5 py-3 text-slate-600">{s.market ?? "—"}</td>
                    <td className="px-5 py-3 text-slate-600">{s.order_region ?? "—"}</td>
                  </tr>
                ))}
                {recentShipments.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-5 py-8 text-center text-slate-400">
                      No shipments found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
