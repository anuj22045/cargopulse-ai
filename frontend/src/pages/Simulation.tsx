import { useEffect, useState } from "react";
import {
  FlaskConical,
  ArrowRight,
  TrendingDown,
  TrendingUp,
  Minus,
  AlertCircle,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import { getShipments, type Shipment } from "../services/shipmentService";
import { apiClient } from "../api/client";
import {
  simulateWhatIf,
  SUPPORTED_SHIPPING_MODES,
  type WhatIfResult,
} from "../services/whatIfService";

// ── Small helpers ─────────────────────────────────────────────────────────────

function pct(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

function DeltaIcon({ value }: { value: number }) {
  if (Math.abs(value) < 0.001)
    return <Minus className="h-3.5 w-3.5 text-slate-400" />;
  if (value < 0)
    return <TrendingDown className="h-3.5 w-3.5 text-green-600" />;
  return <TrendingUp className="h-3.5 w-3.5 text-red-500" />;
}

// Positive delta = worse (more days / more risk). colour accordingly.
function deltaClass(value: number, positiveIsBad = true) {
  if (Math.abs(value) < 0.001) return "text-slate-500";
  const bad = positiveIsBad ? value > 0 : value < 0;
  return bad ? "text-red-600 font-semibold" : "text-green-600 font-semibold";
}

// ── Metric card ───────────────────────────────────────────────────────────────

interface MetricCardProps {
  label: string;
  current: string;
  alternative: string;
  delta: string;
  deltaValue: number;
  positiveIsBad?: boolean;
}

function MetricCard({
  label,
  current,
  alternative,
  delta,
  deltaValue,
  positiveIsBad = true,
}: MetricCardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </p>
      <div className="flex items-center gap-4">
        {/* Current */}
        <div className="flex-1 text-center">
          <p className="text-xs text-slate-400">Current</p>
          <p className="mt-1 text-xl font-bold text-slate-800">{current}</p>
        </div>

        <ArrowRight className="h-4 w-4 flex-shrink-0 text-slate-300" />

        {/* Alternative */}
        <div className="flex-1 text-center">
          <p className="text-xs text-slate-400">Alternative</p>
          <p className="mt-1 text-xl font-bold text-slate-800">{alternative}</p>
        </div>

        {/* Delta */}
        <div className="flex-shrink-0 rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-center">
          <p className="text-xs text-slate-400">Change</p>
          <p className={`mt-1 flex items-center gap-1 text-sm ${deltaClass(deltaValue, positiveIsBad)}`}>
            <DeltaIcon value={deltaValue} />
            {delta}
          </p>
        </div>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

function Simulation() {
  // Shipment list state
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [shipmentsLoading, setShipmentsLoading] = useState(true);
  const [shipmentsError, setShipmentsError] = useState<string | null>(null);

  // Selections
  const [selectedShipmentId, setSelectedShipmentId] = useState<number | "">("");
  const [alternativeMode, setAlternativeMode] = useState<string>("");

  // Simulation state
  const [simulating, setSimulating] = useState(false);
  const [result, setResult] = useState<WhatIfResult | null>(null);
  const [simError, setSimError] = useState<string | null>(null);

  // Apply state
  const [applying, setApplying] = useState(false);
  const [applySuccess, setApplySuccess] = useState(false);
  const [applyError, setApplyError] = useState<string | null>(null);

  // Load shipment list on mount
  useEffect(() => {
    async function load() {
      setShipmentsLoading(true);
      setShipmentsError(null);
      try {
        const data = await getShipments(0, 100, undefined, undefined, undefined, true);
        setShipments(data);
      } catch (err) {
        setShipmentsError(
          err instanceof Error ? err.message : "Failed to load shipments"
        );
      } finally {
        setShipmentsLoading(false);
      }
    }
    load();
  }, []);

  // Derive currently selected shipment object
  const selectedShipment =
    selectedShipmentId !== ""
      ? shipments.find((s) => s.id === selectedShipmentId) ?? null
      : null;

  // Available alternative modes (exclude the shipment's current mode)
  const availableModes = SUPPORTED_SHIPPING_MODES.filter(
    (m) => m !== (selectedShipment?.shipping_mode ?? "")
  );

  // Reset result when selection changes
  function handleShipmentChange(event: React.ChangeEvent<HTMLSelectElement>) {
    const id = event.target.value ? Number(event.target.value) : "";
    setSelectedShipmentId(id);
    setAlternativeMode("");
    setResult(null);
    setSimError(null);
    setApplySuccess(false);
    setApplyError(null);
  }

  function handleModeChange(event: React.ChangeEvent<HTMLSelectElement>) {
    setAlternativeMode(event.target.value);
    setResult(null);
    setSimError(null);
    setApplySuccess(false);
    setApplyError(null);
  }

  // Simulate
  async function handleSimulate() {
    if (selectedShipmentId === "" || !alternativeMode) return;
    setSimulating(true);
    setResult(null);
    setSimError(null);
    setApplySuccess(false);
    setApplyError(null);

    try {
      const data = await simulateWhatIf(
        Number(selectedShipmentId),
        alternativeMode
      );
      setResult(data);
    } catch (err) {
      setSimError(
        err instanceof Error ? err.message : "Simulation failed"
      );
    } finally {
      setSimulating(false);
    }
  }

  // Apply — PATCH shipping_mode via existing PUT /shipments/{id}
  async function handleApply() {
    if (!result || selectedShipmentId === "") return;
    setApplying(true);
    setApplyError(null);
    setApplySuccess(false);

    try {
      await apiClient(`/shipments/${selectedShipmentId}`, {
        method: "PUT",
        body: JSON.stringify({ shipping_mode: result.alternative.shipping_mode }),
      });
      setApplySuccess(true);
      // Refresh shipment list so the selector reflects the new mode
      const data = await getShipments(0, 100, undefined, undefined, undefined, true);
      setShipments(data);
    } catch (err) {
      setApplyError(
        err instanceof Error ? err.message : "Failed to apply change"
      );
    } finally {
      setApplying(false);
    }
  }

  const canSimulate =
    selectedShipmentId !== "" && alternativeMode !== "" && !simulating;

  const canApply =
    result !== null &&
    !applySuccess &&
    !applying &&
    selectedShipmentId !== "" &&
    alternativeMode !== "";

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-100">
          <FlaskConical className="h-5 w-5 text-amber-600" />
        </div>
        <div>
          <h2 className="text-base font-semibold text-slate-800">
            What-If Simulator
          </h2>
          <p className="text-sm text-slate-500">
            Compare predicted ETA and delay risk for an alternative shipping
            mode — without changing the real shipment.
          </p>
        </div>
      </div>

      {/* Controls card */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="mb-4 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Scenario Setup
        </p>

        <div className="flex flex-wrap gap-4">
          {/* Shipment selector */}
          <div className="flex-1 min-w-[240px]">
            <label
              htmlFor="sim-shipment-select"
              className="mb-1.5 block text-xs font-medium text-slate-600"
            >
              Shipment
            </label>
            {shipmentsLoading ? (
              <div className="h-10 animate-pulse rounded-lg bg-slate-100" />
            ) : shipmentsError ? (
              <p className="text-xs text-red-500">{shipmentsError}</p>
            ) : (
              <select
                id="sim-shipment-select"
                value={selectedShipmentId}
                onChange={handleShipmentChange}
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 outline-none transition focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
              >
                <option value="">Select a shipment…</option>
                {shipments.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.shipment_reference} — {s.shipping_mode ?? "Unknown"} (
                    {s.shipment_status ?? "Unknown"})
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Current mode (read-only) */}
          <div className="min-w-[160px]">
            <p className="mb-1.5 text-xs font-medium text-slate-600">
              Current Mode
            </p>
            <div className="flex h-10 items-center rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-700">
              {selectedShipment?.shipping_mode ?? (
                <span className="text-slate-400">—</span>
              )}
            </div>
          </div>

          {/* Alternative mode selector */}
          <div className="min-w-[200px]">
            <label
              htmlFor="sim-alt-mode-select"
              className="mb-1.5 block text-xs font-medium text-slate-600"
            >
              Alternative Mode
            </label>
            <select
              id="sim-alt-mode-select"
              value={alternativeMode}
              onChange={handleModeChange}
              disabled={!selectedShipment}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 outline-none transition focus:border-amber-400 focus:ring-2 focus:ring-amber-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="">Select alternative…</option>
              {availableModes.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>

          {/* Simulate button */}
          <div className="flex items-end">
            <button
              id="sim-run-btn"
              onClick={handleSimulate}
              disabled={!canSimulate}
              className="flex items-center gap-2 rounded-lg bg-amber-500 px-5 py-2 text-sm font-medium text-white transition hover:bg-amber-600 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {simulating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Simulating…
                </>
              ) : (
                <>
                  <FlaskConical className="h-4 w-4" />
                  Simulate
                </>
              )}
            </button>
          </div>
        </div>

        {/* Unsupported parameters note */}
        <p className="mt-4 text-xs text-slate-400">
          Only <strong>shipping mode</strong> is supported as a scenario
          parameter. Carrier, route, weather, and departure time are not model
          features and are not available as simulation inputs.
        </p>
      </div>

      {/* Simulation error */}
      {simError && (
        <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <span>{simError}</span>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Simulation Results
          </p>

          {/* Metric cards */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <MetricCard
              label="Predicted ETA (days)"
              current={`${result.current.eta_days} days`}
              alternative={`${result.alternative.eta_days} days`}
              delta={`${result.delta.eta_days > 0 ? "+" : ""}${result.delta.eta_days} days`}
              deltaValue={result.delta.eta_days}
              positiveIsBad={true}
            />
            <MetricCard
              label="Delay Risk (probability)"
              current={pct(result.current.delay_probability)}
              alternative={pct(result.alternative.delay_probability)}
              delta={`${result.delta.risk_percentage_points > 0 ? "+" : ""}${result.delta.risk_percentage_points} pp`}
              deltaValue={result.delta.risk_percentage_points}
              positiveIsBad={true}
            />
          </div>

          {/* Cost */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
              Cost
            </p>
            <p className="text-sm text-slate-500">
              N/A — no shipping cost model is available in this version.
            </p>
          </div>

          {/* Trade-off callout when risk increases */}
          {result.delta.risk_percentage_points > 0 &&
            result.delta.eta_days < 0 && (
              <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
                <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-600" />
                <span>
                  <strong>Trade-off:</strong> The alternative arrives faster but
                  carries a{" "}
                  <strong>
                    +{result.delta.risk_percentage_points} pp higher delay risk
                  </strong>
                  . Review both metrics before applying.
                </span>
              </div>
            )}

          {/* Apply section */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="mb-1 text-sm font-semibold text-slate-700">
              Apply Alternative
            </p>
            <p className="mb-4 text-xs text-slate-500">
              This will update the shipment's{" "}
              <strong>shipping_mode</strong> to{" "}
              <strong>{result.alternative.shipping_mode}</strong> in the
              database. Only the shipping mode field is changed. Simulation
              results are not persisted.
            </p>

            {applySuccess ? (
              <div className="flex items-center gap-2 text-sm font-medium text-green-700">
                <CheckCircle2 className="h-4 w-4" />
                Shipping mode updated to{" "}
                <strong>{result.alternative.shipping_mode}</strong>
              </div>
            ) : (
              <div className="flex flex-wrap items-center gap-3">
                <button
                  id="sim-apply-btn"
                  onClick={handleApply}
                  disabled={!canApply}
                  className="flex items-center gap-2 rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {applying ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Applying…
                    </>
                  ) : (
                    "Apply Alternative"
                  )}
                </button>
                {applyError && (
                  <p className="text-xs text-red-600">{applyError}</p>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!result && !simulating && !simError && (
        <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 py-14 text-center">
          <FlaskConical className="mx-auto h-8 w-8 text-slate-300" />
          <p className="mt-3 text-sm text-slate-400">
            Select a shipment and an alternative shipping mode, then click{" "}
            <strong className="text-slate-500">Simulate</strong>.
          </p>
        </div>
      )}
    </div>
  );
}

export default Simulation;
