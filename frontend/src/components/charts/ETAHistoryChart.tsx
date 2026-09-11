// ETAHistoryChart.tsx
// Renders predicted ETA over time as a line chart.
// Data comes from GET /api/shipments/{id}/eta-history.
// If no data exists (ML predictions not yet available), shows a graceful empty state.

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { EtaHistoryPoint } from "../../hooks/useShipmentHistory";

interface Props {
  data: EtaHistoryPoint[];
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

function formatETA(eta: string): string {
  try {
    return new Date(eta).toLocaleDateString("en-IN", {
      month: "short",
      day: "numeric",
    });
  } catch {
    return eta;
  }
}

// Convert ETA string to a numeric value (days from now) for the Y-axis
function etaToNumeric(eta: string): number {
  try {
    const ms = new Date(eta).getTime() - Date.now();
    return Math.round(ms / (1000 * 60 * 60)); // hours from now
  } catch {
    return 0;
  }
}

function ETATooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: EtaHistoryPoint }[];
}) {
  if (!active || !payload || payload.length === 0) return null;

  const point = payload[0].payload;

  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-lg text-xs">
      <p className="mb-1 text-slate-500">
        Predicted at: {new Date(point.timestamp).toLocaleString("en-IN", {
          dateStyle: "medium",
          timeStyle: "short",
        })}
      </p>
      <p className="font-semibold text-violet-600">
        ETA: {new Date(point.predicted_eta).toLocaleString("en-IN", {
          dateStyle: "medium",
          timeStyle: "short",
        })}
      </p>
    </div>
  );
}

export function ETAHistoryChart({ data, loading }: Props) {
  // Sort chronologically and filter out null/invalid ETAs
  const chartData = [...data]
    .filter((p) => {
      if (!p.predicted_eta) return false;
      const d = new Date(p.predicted_eta);
      return !isNaN(d.getTime());
    })
    .sort(
      (a, b) =>
        new Date(a.timestamp).getTime() -
        new Date(b.timestamp).getTime()
    )
    .map((p) => ({
      ...p,
      eta_numeric: etaToNumeric(p.predicted_eta),
    }));

  if (loading) {
    return (
      <div className="flex h-48 items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-violet-500 border-t-transparent" />
      </div>
    );
  }

  if (chartData.length === 0) {
    return (
      <div className="flex h-48 flex-col items-center justify-center gap-2 text-center">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-violet-50">
          <span className="text-lg">🕐</span>
        </div>
        <p className="text-sm font-medium text-slate-500">
          No ETA predictions available yet
        </p>
        <p className="text-xs text-slate-400">
          ETA predictions will be available after ML Phase 8/9
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
          tickFormatter={(v) => `${v}h`}
          tick={{ fontSize: 10, fill: "#94a3b8" }}
          tickLine={false}
          axisLine={false}
          width={40}
          label={{
            value: "Hours to ETA",
            angle: -90,
            position: "insideLeft",
            offset: 10,
            style: { fontSize: 9, fill: "#94a3b8" },
          }}
        />
        <Tooltip
          content={<ETATooltip />}
        />
        <Line
          type="monotone"
          dataKey="eta_numeric"
          name="Predicted ETA"
          stroke="#8b5cf6"
          strokeWidth={2}
          dot={chartData.length <= 20}
          activeDot={{ r: 4, fill: "#8b5cf6", strokeWidth: 0 }}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
