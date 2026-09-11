// SpeedDistanceChart.tsx
// Dual-axis chart showing speed (km/h, left axis) and distance remaining (km, right axis).
// Data comes from GET /api/shipments/{id}/speed-history + live WebSocket updates.

import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { SpeedHistoryPoint } from "../../hooks/useShipmentHistory";

interface Props {
  data: SpeedHistoryPoint[];
  loading?: boolean;
}

function formatTime(timestamp: string): string {
  try {
    return new Date(timestamp).toLocaleTimeString("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  } catch {
    return timestamp;
  }
}

function SpeedDistanceTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { name: string; value: number; color: string }[];
  label?: string;
}) {
  if (!active || !payload || payload.length === 0) return null;

  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-lg text-xs">
      <p className="mb-2 text-slate-500">
        {label
          ? (() => {
              try {
                return new Date(label).toLocaleString("en-IN", {
                  dateStyle: "medium",
                  timeStyle: "short",
                });
              } catch {
                return label;
              }
            })()
          : ""}
      </p>
      {payload.map((entry) => (
        <p
          key={entry.name}
          className="font-semibold"
          style={{ color: entry.color }}
        >
          {entry.name}:{" "}
          {entry.value != null
            ? entry.name.includes("Speed")
              ? `${entry.value} km/h`
              : `${entry.value} km`
            : "—"}
        </p>
      ))}
    </div>
  );
}

export function SpeedDistanceChart({ data, loading }: Props) {
  // Sort chronologically; filter completely null rows
  const chartData = [...data]
    .filter(
      (p) =>
        (p.speed != null && isFinite(p.speed)) ||
        (p.distance_remaining != null &&
          isFinite(p.distance_remaining))
    )
    .sort(
      (a, b) =>
        new Date(a.timestamp).getTime() -
        new Date(b.timestamp).getTime()
    );

  if (loading) {
    return (
      <div className="flex h-56 items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
      </div>
    );
  }

  if (chartData.length === 0) {
    return (
      <div className="flex h-56 flex-col items-center justify-center gap-2 text-center">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-50">
          <span className="text-lg">🚛</span>
        </div>
        <p className="text-sm font-medium text-slate-500">
          No speed data available yet
        </p>
        <p className="text-xs text-slate-400">
          Speed and distance data will appear as the simulation runs
        </p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <ComposedChart
        data={chartData}
        margin={{ top: 8, right: 48, left: 0, bottom: 4 }}
      >
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="#f1f5f9"
          vertical={false}
        />
        <XAxis
          dataKey="timestamp"
          tickFormatter={formatTime}
          tick={{ fontSize: 10, fill: "#94a3b8" }}
          tickLine={false}
          axisLine={false}
          minTickGap={40}
        />
        {/* Left Y-axis — Speed */}
        <YAxis
          yAxisId="speed"
          orientation="left"
          tickFormatter={(v) => `${v}`}
          tick={{ fontSize: 10, fill: "#3b82f6" }}
          tickLine={false}
          axisLine={false}
          width={40}
          label={{
            value: "Speed (km/h)",
            angle: -90,
            position: "insideLeft",
            offset: 10,
            style: { fontSize: 9, fill: "#3b82f6" },
          }}
        />
        {/* Right Y-axis — Distance Remaining */}
        <YAxis
          yAxisId="distance"
          orientation="right"
          tickFormatter={(v) => `${v}`}
          tick={{ fontSize: 10, fill: "#10b981" }}
          tickLine={false}
          axisLine={false}
          width={48}
          label={{
            value: "Distance (km)",
            angle: 90,
            position: "insideRight",
            offset: 10,
            style: { fontSize: 9, fill: "#10b981" },
          }}
        />
        <Tooltip content={<SpeedDistanceTooltip />} />
        <Legend
          iconType="plainline"
          iconSize={12}
          wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }}
          formatter={(value) => (
            <span style={{ color: "#475569" }}>{value}</span>
          )}
        />
        <Line
          yAxisId="speed"
          type="monotone"
          dataKey="speed"
          name="Speed (km/h)"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: "#3b82f6", strokeWidth: 0 }}
          isAnimationActive={false}
          connectNulls={false}
        />
        <Line
          yAxisId="distance"
          type="monotone"
          dataKey="distance_remaining"
          name="Distance Remaining (km)"
          stroke="#10b981"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: "#10b981", strokeWidth: 0 }}
          isAnimationActive={false}
          connectNulls={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
