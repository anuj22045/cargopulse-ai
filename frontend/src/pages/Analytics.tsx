import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
  Legend,
} from "recharts";
import { BarChart2, PieChart as PieIcon, TrendingUp } from "lucide-react";
import { getShipments, type Shipment } from "../services/shipmentService";

const STATUS_COLORS: Record<string, string> = {
  Shipping: "#3b82f6",
  Shipped: "#8b5cf6",
  Delivered: "#22c55e",
  "Late delivery": "#ef4444",
  Cancelled: "#64748b",
  "Suspected Fraud": "#f97316",
};

const MODE_COLORS = ["#f59e0b", "#3b82f6", "#22c55e", "#8b5cf6"];
const FALLBACK_COLORS = ["#3b82f6", "#22c55e", "#ef4444", "#f59e0b", "#8b5cf6", "#f97316"];

function aggregateBy(
  shipments: Shipment[],
  key: keyof Shipment
): { name: string; count: number }[] {
  const map: Record<string, number> = {};
  for (const s of shipments) {
    const val = String(s[key] ?? "Unknown");
    map[val] = (map[val] ?? 0) + 1;
  }
  return Object.entries(map)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count);
}

function ChartCard({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: React.ElementType;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center gap-2">
        <Icon className="h-4 w-4 text-amber-500" />
        <h2 className="text-sm font-semibold text-slate-800">{title}</h2>
      </div>
      {children}
    </div>
  );
}

function Analytics() {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch up to 100 records for aggregation (backend max limit)
    getShipments(0, 100)
      .then(setShipments)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const statusData = aggregateBy(shipments, "shipment_status");
  const modeData = aggregateBy(shipments, "shipping_mode");
  const marketData = aggregateBy(shipments, "market").slice(0, 8);

  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-80 animate-pulse rounded-xl bg-slate-200" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        Could not load analytics data: {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary strip */}
      <div className="flex flex-wrap gap-4">
        {[
          { label: "Records loaded", value: shipments.length.toLocaleString() },
          { label: "Distinct statuses", value: statusData.length },
          { label: "Shipping modes", value: modeData.length },
          { label: "Markets", value: marketData.length },
        ].map(({ label, value }) => (
          <div
            key={label}
            className="flex-1 min-w-[140px] rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm"
          >
            <p className="text-xs text-slate-500">{label}</p>
            <p className="mt-0.5 text-xl font-bold text-slate-900">{value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Status bar chart */}
        <ChartCard title="Shipments by Status" icon={BarChart2}>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={statusData} margin={{ left: -10 }}>
              <XAxis
                dataKey="name"
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
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {statusData.map((entry, i) => (
                  <Cell
                    key={entry.name}
                    fill={STATUS_COLORS[entry.name] ?? FALLBACK_COLORS[i % FALLBACK_COLORS.length]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Shipping mode pie */}
        <ChartCard title="Shipping Mode Distribution" icon={PieIcon}>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={modeData}
                dataKey="count"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={85}
                label={({ name, percent }) =>
                  `${name} ${((percent ?? 0) * 100).toFixed(0)}%`
                }
                labelLine={false}
              >
                {modeData.map((_, i) => (
                  <Cell
                    key={i}
                    fill={MODE_COLORS[i % MODE_COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip
              formatter={(val) => [Number(val).toLocaleString(), "Shipments"]}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Market bar chart */}
        <ChartCard title="Shipments by Market" icon={TrendingUp}>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={marketData} layout="vertical" margin={{ left: 10 }}>
              <XAxis
                type="number"
                tick={{ fontSize: 11, fill: "#64748b" }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                type="category"
                dataKey="name"
                width={90}
                tick={{ fontSize: 11, fill: "#64748b" }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                cursor={{ fill: "#f1f5f9" }}
              formatter={(val) => [Number(val).toLocaleString(), "Shipments"]}
              />
              <Bar dataKey="count" fill="#f59e0b" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}

export default Analytics;
