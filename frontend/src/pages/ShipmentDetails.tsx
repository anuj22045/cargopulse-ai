import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  ArrowLeft,
  MapPin,
  Truck,
  Calendar,
  Activity,
  Brain,
  Lightbulb,
  ClipboardList,
  AlertTriangle,
  CheckCircle,
  Clock,
  Info,
  Navigation,
  TrendingDown,
  BarChart2,
  Gauge,
  ListOrdered,
} from "lucide-react";
import { getShipment, type Shipment } from "../services/shipmentService";
import {
  getShipmentPredictions,
  type AIPrediction,
} from "../services/aiPredictionService";
import {
  getShipmentSimulationEvents,
  type SimulationEvent,
} from "../services/simulationService";
import {
  getShipmentRecommendations,
  type AIRecommendation,
} from "../services/aiRecommendationService";
import {
  getShipmentDecisions,
  type DecisionHistory,
} from "../services/decisionService";
import {
  getShipmentEvents,
  type ShipmentEvent,
} from "../services/shipmentEventService";
import { useShipmentHistory } from "../hooks/useShipmentHistory";
import { RiskHistoryChart } from "../components/charts/RiskHistoryChart";
import { ETAHistoryChart } from "../components/charts/ETAHistoryChart";
import { SpeedDistanceChart } from "../components/charts/SpeedDistanceChart";
import { EventTimeline } from "../components/charts/EventTimeline";

// ─── Helpers ────────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string | null }) {
  const map: Record<string, string> = {
    Shipping: "bg-blue-100 text-blue-700 border-blue-200",
    Shipped: "bg-purple-100 text-purple-700 border-purple-200",
    Delivered: "bg-green-100 text-green-700 border-green-200",
    "Late delivery": "bg-red-100 text-red-700 border-red-200",
    Cancelled: "bg-slate-100 text-slate-600 border-slate-200",
    "Suspected Fraud": "bg-orange-100 text-orange-700 border-orange-200",
  };
  const cls = status
    ? (map[status] ?? "bg-slate-100 text-slate-600 border-slate-200")
    : "bg-slate-100 text-slate-600 border-slate-200";
  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-sm font-medium ${cls}`}
    >
      {status ?? "Unknown"}
    </span>
  );
}

function InfoCard({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-amber-50">
        <Icon className="h-4 w-4 text-amber-500" />
      </div>
      <div>
        <p className="text-xs text-slate-500">{label}</p>
        <p className="mt-0.5 text-sm font-semibold text-slate-800">
          {value ?? "—"}
        </p>
      </div>
    </div>
  );
}

function SectionCard({
  title,
  icon: Icon,
  subtitle,
  children,
}: {
  title: string;
  icon: React.ElementType;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center gap-2 border-b border-slate-100 px-5 py-4">
        <Icon className="h-4 w-4 text-amber-500" />
        <div>
          <h2 className="text-sm font-semibold text-slate-800">{title}</h2>
          {subtitle && (
            <p className="text-[10px] text-slate-400">{subtitle}</p>
          )}
        </div>
      </div>
      <div className="px-5 py-4">{children}</div>
    </div>
  );
}

// ─── Risk Gauge ───────────────────────────────────────────────────────────────

function RiskGauge({ probability }: { probability: number }) {
  const pct = Math.min(Math.max(probability, 0), 1);
  const radius = 34;
  const circ = 2 * Math.PI * radius;
  // Only fill the top 75% of the circle (like a speedometer arc)
  const arcFraction = 0.75;
  const dashArray = circ * arcFraction;
  const dashOffset = dashArray * (1 - pct);
  const rotate = -225; // start from bottom-left

  const color =
    pct >= 0.7 ? "#ef4444" : pct >= 0.4 ? "#f59e0b" : "#22c55e";
  const label =
    pct >= 0.7 ? "High Risk" : pct >= 0.4 ? "Med Risk" : "Low Risk";

  return (
    <div className="flex flex-col items-center">
      <svg width="88" height="72" viewBox="0 0 88 72">
        {/* Track */}
        <circle
          cx="44" cy="52" r={radius}
          fill="none"
          stroke="#e2e8f0"
          strokeWidth="8"
          strokeDasharray={`${dashArray} ${circ}`}
          strokeDashoffset={0}
          strokeLinecap="round"
          transform={`rotate(${rotate} 44 52)`}
        />
        {/* Fill */}
        <circle
          cx="44" cy="52" r={radius}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeDasharray={`${dashArray} ${circ}`}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          transform={`rotate(${rotate} 44 52)`}
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
        {/* Center text */}
        <text x="44" y="56" textAnchor="middle" fontSize="13" fontWeight="700" fill={color}>
          {(pct * 100).toFixed(0)}%
        </text>
      </svg>
      <span
        className="-mt-1 text-[10px] font-semibold uppercase tracking-wide"
        style={{ color }}
      >
        {label}
      </span>
    </div>
  );
}

function EventTypeIcon({ type }: { type: string }) {
  const t = type.toLowerCase();
  if (t.includes("delay") || t.includes("late") || t.includes("risk"))
    return <AlertTriangle className="h-3.5 w-3.5 text-red-500" />;
  if (t.includes("deliver") || t.includes("complete") || t.includes("arrive"))
    return <CheckCircle className="h-3.5 w-3.5 text-green-500" />;
  if (t.includes("depart") || t.includes("ship") || t.includes("transit"))
    return <Truck className="h-3.5 w-3.5 text-blue-500" />;
  return <Info className="h-3.5 w-3.5 text-slate-400" />;
}

function formatDateTime(dt: string) {
  try {
    return new Date(dt).toLocaleString("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return dt;
  }
}

// ─── Main Component ──────────────────────────────────────────────────────────

function ShipmentDetails() {
  const { shipmentId } = useParams<{ shipmentId: string }>();
  const [shipment, setShipment] = useState<Shipment | null>(null);
  const [events, setEvents] = useState<ShipmentEvent[]>([]);
  const [predictions, setPredictions] = useState<AIPrediction[]>([]);
  const [simulationEvents, setSimulationEvents] = useState<SimulationEvent[]>([]);
  const [recommendations, setRecommendations] = useState<AIRecommendation[]>([]);
  const [decisions, setDecisions] = useState<DecisionHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const numericShipmentId = shipmentId ? Number(shipmentId) : null;

  const {
    riskHistory,
    etaHistory,
    speedHistory,
    eventHistory,
    latestUpdate,
    isConnected,
    loading: historyLoading,
    error: historyError,
  } = useShipmentHistory(numericShipmentId);

  useEffect(() => {
    async function loadShipment() {
      if (!shipmentId) {
        setError("Shipment ID is missing");
        setLoading(false);
        return;
      }
      const id = Number(shipmentId);

      if (Number.isNaN(id)) {
        setError("Invalid shipment ID");
        setLoading(false);
        return;
      }

      try {
        const id = Number(shipmentId);
        const shipmentData = await getShipment(id);
        const eventData = await getShipmentEvents(id);
        const predictionData = await getShipmentPredictions(id);
        const simulationData = await getShipmentSimulationEvents(id);
        const recommendationData = await getShipmentRecommendations(id);
        const decisionData = await getShipmentDecisions(id);

        setShipment(shipmentData);
        setEvents(eventData);
        setPredictions(predictionData);
        setSimulationEvents(simulationData);
        setRecommendations(recommendationData);
        setDecisions(decisionData);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load shipment"
        );
      } finally {
        setLoading(false);
      }
    }

    loadShipment();
  }, [shipmentId]);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-10 w-48 animate-pulse rounded-lg bg-slate-200" />
        <div className="h-24 animate-pulse rounded-xl bg-slate-200" />
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-20 animate-pulse rounded-xl bg-slate-200" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {error}
      </div>
    );
  }

  if (!shipment) {
    return (
      <p className="text-sm text-slate-500">Shipment not found.</p>
    );
  }

  const latestPrediction = predictions[predictions.length - 1] ?? null;

  return (
    <div className="space-y-5">
      {/* Back link */}
      <Link
        to="/shipments"
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 transition hover:text-slate-700"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Shipments
      </Link>

      {/* Header card */}
      <div className="flex flex-wrap items-start justify-between gap-4 rounded-xl border border-slate-200 bg-white px-6 py-5 shadow-sm">
        <div>
          <p className="mb-1 text-xs text-slate-500">Shipment Reference</p>
          <h1 className="text-xl font-bold text-slate-900">
            {shipment.shipment_reference}
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            ID: {shipment.id} · Order: {shipment.order_id ?? "—"}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <StatusBadge status={shipment.shipment_status} />
          {latestPrediction && (
            <RiskGauge probability={latestPrediction.delay_probability} />
          )}
        </div>
      </div>

      {/* Live Simulation Status */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-800">
              Live Simulation
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              Real-time shipment updates from WebSocket
            </p>
          </div>

          <span
            className={`rounded-full px-3 py-1 text-xs font-medium ${
              isConnected
                ? "bg-green-100 text-green-700"
                : "bg-red-100 text-red-700"
            }`}
          >
            {isConnected ? "● Connected" : "○ Disconnected"}
          </span>
        </div>

        {latestUpdate && (
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <InfoCard
              icon={Activity}
              label="Speed"
              value={
                latestUpdate.effective_speed_kmh != null
                  ? `${latestUpdate.effective_speed_kmh} km/h`
                  : "—"
              }
            />

            <InfoCard
              icon={Navigation}
              label="Distance Remaining"
              value={
                latestUpdate.distance_remaining_km != null
                  ? `${latestUpdate.distance_remaining_km} km`
                  : "—"
              }
            />

            <InfoCard
              icon={Activity}
              label="Weather"
              value={latestUpdate.weather ?? "—"}
            />

            <InfoCard
              icon={Activity}
              label="Congestion"
              value={latestUpdate.congestion ?? "—"}
            />
          </div>
        )}

        {!latestUpdate && (
          <p className="mt-4 text-xs text-slate-400">
            Waiting for live simulation update...
          </p>
        )}
      </div>

      {/* Info cards grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <InfoCard
          icon={Truck}
          label="Shipping Mode"
          value={shipment.shipping_mode}
        />
        <InfoCard
          icon={MapPin}
          label="Region / Market"
          value={
            shipment.order_region && shipment.market
              ? `${shipment.order_region} · ${shipment.market}`
              : shipment.order_region ?? shipment.market
          }
        />
        <InfoCard
          icon={Calendar}
          label="Scheduled Days"
          value={
            shipment.scheduled_shipping_days
              ? `${shipment.scheduled_shipping_days} days`
              : null
          }
        />
        <InfoCard
          icon={MapPin}
          label="Last Known Position"
          value={
            shipment.current_latitude && shipment.current_longitude
              ? `${shipment.current_latitude.toFixed(4)}, ${shipment.current_longitude.toFixed(4)}`
              : "Not available"
          }
        />
      </div>

      {/* Financials */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <InfoCard icon={Activity} label="Customer Segment" value={shipment.customer_segment} />
        <InfoCard icon={Activity} label="Sales" value={shipment.sales ? `$${shipment.sales}` : null} />
        <InfoCard icon={Activity} label="Profit / Order" value={shipment.profit_per_order ? `$${shipment.profit_per_order}` : null} />
      </div>

      {/* Map placeholder */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <div className="flex items-center gap-2 border-b border-slate-100 px-5 py-4">
          <Navigation className="h-4 w-4 text-amber-500" />
          <h2 className="text-sm font-semibold text-slate-800">Route Map</h2>
          <span className="ml-auto rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-600">
            Phase 7 — Live tracking
          </span>
        </div>
        <div className="relative flex h-52 items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
          {/* Grid pattern */}
          <svg className="absolute inset-0 h-full w-full opacity-30" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">
                <path d="M 24 0 L 0 0 0 24" fill="none" stroke="#94a3b8" strokeWidth="0.5" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
          {/* Route line placeholder */}
          <svg className="absolute inset-0 h-full w-full" xmlns="http://www.w3.org/2000/svg">
            <line x1="15%" y1="50%" x2="85%" y2="50%" stroke="#f59e0b" strokeWidth="2" strokeDasharray="6 4" opacity="0.6" />
            <circle cx="15%" cy="50%" r="6" fill="#22c55e" opacity="0.8" />
            <circle cx="85%" cy="50%" r="6" fill="#ef4444" opacity="0.8" />
          </svg>
          <div className="z-10 flex flex-col items-center gap-2 text-center">
            <MapPin className="h-8 w-8 text-slate-300" />
            <p className="text-sm font-medium text-slate-500">Interactive map coming in Phase 7</p>
            {shipment.current_latitude && shipment.current_longitude && (
              <p className="text-xs text-slate-400">
                Current position: {shipment.current_latitude.toFixed(4)}, {shipment.current_longitude.toFixed(4)}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* ─── Day 13 Charts ──────────────────────────────────────────────────── */}

      {/* Risk Over Time + ETA Trend */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {/* Risk Over Time */}
        <SectionCard
          title="Delay Risk Over Time"
          icon={TrendingDown}
          subtitle="Delay probability from AI predictions"
        >
          {historyError ? (
            <p className="text-xs text-red-500 py-4">{historyError}</p>
          ) : (
            <RiskHistoryChart data={riskHistory} loading={historyLoading} />
          )}
        </SectionCard>

        {/* ETA Trend */}
        <SectionCard
          title="ETA Trend"
          icon={Clock}
          subtitle="Predicted arrival time trend"
        >
          {historyError ? (
            <p className="text-xs text-red-500 py-4">{historyError}</p>
          ) : (
            <ETAHistoryChart data={etaHistory} loading={historyLoading} />
          )}
        </SectionCard>
      </div>

      {/* Speed & Distance chart */}
      <SectionCard
        title="Speed & Distance Remaining"
        icon={Gauge}
        subtitle="Live simulation speed and remaining distance"
      >
        {historyError ? (
          <p className="text-xs text-red-500 py-4">{historyError}</p>
        ) : (
          <SpeedDistanceChart data={speedHistory} loading={historyLoading} />
        )}
      </SectionCard>

      {/* Event / Condition Timeline */}
      <SectionCard
        title="Event & Condition Timeline"
        icon={ListOrdered}
        subtitle="Shipment events from REST API + live simulation updates"
      >
        <EventTimeline events={eventHistory} />
      </SectionCard>

      {/* ─── Existing sections (preserved) ─────────────────────────────────── */}

      {/* Event timeline (original REST-based from shipmentEventService) */}
      <SectionCard title="Shipment Events (Log)" icon={Clock}>
        {events.length === 0 ? (
          <p className="text-sm text-slate-400">No events recorded yet.</p>
        ) : (
          <ol className="relative border-l border-slate-200 pl-6 space-y-5">
            {events.map((event) => (
              <li key={event.id} className="relative">
                {/* Dot */}
                <span className="absolute -left-[22px] flex h-5 w-5 items-center justify-center rounded-full bg-white ring-2 ring-slate-200">
                  <EventTypeIcon type={event.event_type} />
                </span>
                <div>
                  <p className="text-xs text-slate-400">
                    {formatDateTime(event.event_time)}
                  </p>
                  <p className="mt-0.5 text-sm font-semibold text-slate-800">
                    {event.event_type}
                  </p>
                  {event.description && (
                    <p className="mt-0.5 text-xs text-slate-500">
                      {event.description}
                    </p>
                  )}
                  {(event.latitude || event.longitude) && (
                    <p className="mt-0.5 text-xs text-slate-400">
                      📍 {event.latitude?.toFixed(4)}, {event.longitude?.toFixed(4)}
                    </p>
                  )}
                </div>
              </li>
            ))}
          </ol>
        )}
      </SectionCard>

      {/* AI Predictions */}
      <SectionCard title="AI Prediction History" icon={Brain}>
        {predictions.length === 0 ? (
          <p className="text-sm text-slate-400">No predictions available yet.</p>
        ) : (
          <div className="space-y-3">
            {predictions.map((p) => (
              <div
                key={p.id}
                className="flex flex-wrap items-center gap-4 rounded-lg border border-slate-100 bg-slate-50 px-4 py-3"
              >
                <div className="flex-1 min-w-[120px]">
                  <p className="text-xs text-slate-500">Delay Probability</p>
                  <div className="mt-1 flex items-center gap-2">
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-200">
                      <div
                        className={`h-full rounded-full ${
                          p.delay_probability >= 0.7
                            ? "bg-red-500"
                            : p.delay_probability >= 0.4
                            ? "bg-amber-500"
                            : "bg-green-500"
                        }`}
                        style={{ width: `${p.delay_probability * 100}%` }}
                      />
                    </div>
                    <span className="text-xs font-semibold text-slate-700">
                      {(p.delay_probability * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Predicted ETA</p>
                  <p className="text-xs font-medium text-slate-700">
                    {p.predicted_eta ?? "—"}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Confidence</p>
                  <p className="text-xs font-medium text-slate-700">
                    {p.confidence_score != null
                      ? `${(p.confidence_score * 100).toFixed(0)}%`
                      : "—"}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Model</p>
                  <p className="text-xs font-medium text-slate-700">
                    {p.model_version}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Time</p>
                  <p className="text-xs text-slate-400">
                    {formatDateTime(p.prediction_time)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </SectionCard>

      {/* Simulation History */}
      <SectionCard title="Simulation History" icon={BarChart2}>
        {simulationEvents.length === 0 ? (
          <p className="text-sm text-slate-400">No simulation events yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  <th className="px-3 py-2">Time</th>
                  <th className="px-3 py-2">Traffic</th>
                  <th className="px-3 py-2">Temp (°C)</th>
                  <th className="px-3 py-2">Humidity</th>
                  <th className="px-3 py-2">Wait (h)</th>
                  <th className="px-3 py-2">Asset Util.</th>
                  <th className="px-3 py-2">Position</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {simulationEvents.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 text-slate-500">
                      {formatDateTime(s.simulation_time)}
                    </td>
                    <td className="px-3 py-2 text-slate-700">
                      {s.traffic_status ?? "—"}
                    </td>
                    <td className="px-3 py-2 text-slate-700">
                      {s.temperature ?? "—"}
                    </td>
                    <td className="px-3 py-2 text-slate-700">
                      {s.humidity ?? "—"}
                    </td>
                    <td className="px-3 py-2 text-slate-700">
                      {s.waiting_time ?? "—"}
                    </td>
                    <td className="px-3 py-2 text-slate-700">
                      {s.asset_utilization ?? "—"}
                    </td>
                    <td className="px-3 py-2 text-slate-500">
                      {s.latitude && s.longitude
                        ? `${s.latitude.toFixed(3)}, ${s.longitude.toFixed(3)}`
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>

      {/* AI Recommendations */}
      <SectionCard title="AI Recommendations" icon={Lightbulb}>
        {recommendations.length === 0 ? (
          <p className="text-sm text-slate-400">No recommendations available yet.</p>
        ) : (
          <div className="space-y-3">
            {recommendations.map((r) => (
              <div
                key={r.id}
                className="rounded-lg border border-amber-100 bg-amber-50 px-4 py-3"
              >
                <p className="text-sm font-semibold text-slate-800">
                  {r.recommended_action}
                </p>
                {r.reason && (
                  <p className="mt-1 text-xs text-slate-600">{r.reason}</p>
                )}
                <div className="mt-2 flex flex-wrap gap-4">
                  {r.expected_delay_reduction != null && (
                    <span className="text-xs text-slate-500">
                      Delay reduction:{" "}
                      <strong className="text-green-600">
                        {r.expected_delay_reduction}h
                      </strong>
                    </span>
                  )}
                  {r.expected_cost && (
                    <span className="text-xs text-slate-500">
                      Est. cost: <strong>${r.expected_cost}</strong>
                    </span>
                  )}
                  {r.confidence_score != null && (
                    <span className="text-xs text-slate-500">
                      Confidence:{" "}
                      <strong>
                        {(r.confidence_score * 100).toFixed(0)}%
                      </strong>
                    </span>
                  )}
                  <span className="text-xs text-slate-400">
                    {formatDateTime(r.created_at)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </SectionCard>

      {/* Decision History */}
      <SectionCard title="Decision History" icon={ClipboardList}>
        {decisions.length === 0 ? (
          <p className="text-sm text-slate-400">No decisions recorded yet.</p>
        ) : (
          <div className="space-y-3">
            {decisions.map((d) => (
              <div
                key={d.id}
                className="flex flex-wrap items-start gap-4 rounded-lg border border-slate-100 bg-slate-50 px-4 py-3"
              >
                <div className="flex-1 min-w-[160px]">
                  <p className="text-xs text-slate-500">Decision</p>
                  <p className="text-sm font-semibold text-slate-800">
                    {d.decision}
                  </p>
                </div>
                {d.decision_reason && (
                  <div className="flex-1 min-w-[160px]">
                    <p className="text-xs text-slate-500">Reason</p>
                    <p className="text-xs text-slate-700">{d.decision_reason}</p>
                  </div>
                )}
                {d.actual_outcome && (
                  <div>
                    <p className="text-xs text-slate-500">Outcome</p>
                    <p className="text-xs font-medium text-slate-700">
                      {d.actual_outcome}
                    </p>
                  </div>
                )}
                <div>
                  <p className="text-xs text-slate-500">Recorded</p>
                  <p className="text-xs text-slate-400">
                    {formatDateTime(d.created_at)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}

export default ShipmentDetails;