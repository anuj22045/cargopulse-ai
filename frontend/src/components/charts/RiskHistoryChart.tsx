// RiskHistoryChart.tsx
// Renders delay probability over time as a line chart.
// Data comes from GET /api/shipments/{id}/risk-history
// and is updated live via WebSocket through useShipmentHistory.

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { RiskHistoryPoint } from "../../hooks/useShipmentHistory";

interface Props {
  data: RiskHistoryPoint[];
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

function formatTooltipTime(timestamp: string): string {
  try {
    return new Date(timestamp).toLocaleString("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return timestamp;
  }
}

function RiskTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { value: number; payload: RiskHistoryPoint }[];
  label?: string;
}) {
  if (!active || !payload || payload.length === 0) return null;

  const point = payload[0].payload;
  const pct = (payload[0].value * 100).toFixed(1);
  const color =
    payload[0].value >= 0.7
      ? "#ef4444"
      : payload[0].value >= 0.4
      ? "#f59e0b"
      : "#22c55e";

  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-lg text-xs">
      <p className="mb-1 text-slate-500">{formatTooltipTime(point.timestamp)}</p>
      <p className="font-semibold" style={{ color }}>
        Delay Risk: {pct}%
      </p>
      {label && (
        <p className="text-slate-400 text-[10px]">{label}</p>
      )}
    </div>
  );
}

export function RiskHistoryChart({ data, loading }: Props) {
  // Sort chronologically and filter out null/invalid values
  const chartData = [...data]
    .filter(
      (p) =>
        p.delay_probability != null &&
        isFinite(p.delay_probability)
    )
    .sort(
      (a, b) =>
        new Date(a.timestamp).getTime() -
        new Date(b.timestamp).getTime()
    );

  if (loading) {
    return (
      <div className="flex h-48 items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-amber-500 border-t-transparent" />
      </div>
    );
  }

  if (chartData.length === 0) {
    return (
      <div className="flex h-48 flex-col items-center justify-center gap-2 text-center">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100">
          <span className="text-lg">📊</span>
        </div>
        <p className="text-sm font-medium text-slate-500">
          No risk history available yet
        </p>
        <p className="text-xs text-slate-400">
          Risk data will appear as the simulation runs
        </p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart
        data={chartData}
        margin={{ top: 8, right: 16, left: 0, bottom: 4 }}
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
        <YAxis
          tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
          domain={[0, 1]}
          tick={{ fontSize: 10, fill: "#94a3b8" }}
          tickLine={false}
          axisLine={false}
          width={40}
        />
        <Tooltip content={<RiskTooltip />} />
        {/* Reference lines at key thresholds */}
        <ReferenceLine
          y={0.7}
          stroke="#ef4444"
          strokeDasharray="4 2"
          strokeOpacity={0.4}
          label={{ value: "High", position: "right", fontSize: 9, fill: "#ef4444" }}
        />
        <ReferenceLine
          y={0.4}
          stroke="#f59e0b"
          strokeDasharray="4 2"
          strokeOpacity={0.4}
          label={{ value: "Med", position: "right", fontSize: 9, fill: "#f59e0b" }}
        />
        <Line
          type="monotone"
          dataKey="delay_probability"
          stroke="#f59e0b"
          strokeWidth={2}
          dot={chartData.length <= 20}
          activeDot={{ r: 4, fill: "#f59e0b", strokeWidth: 0 }}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
