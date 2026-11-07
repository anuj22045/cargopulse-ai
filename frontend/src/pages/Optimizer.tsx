/**
 * Multi-Objective Optimizer Page — Day 17 Phase 3
 * =================================================
 * Lets users adjust objective weights via sliders and see ranked
 * shipping-mode options with per-objective scores, composite scores,
 * and Pareto-optimal highlighting.
 *
 * Connects to: POST /optimizer/shipment/{id}
 * Service:     optimizerService.ts → runOptimizer()
 *
 * Design rules (matching existing app style):
 * - Tailwind utility classes, matching Simulation.tsx / ShipmentDetails.tsx
 * - lucide-react icons only (already a dep)
 * - No new packages
 * - Unavailable metrics (cost, impact) shown explicitly as "—  unavailable"
 *   — never as zero
 */

import { useEffect, useState } from "react";
import {
  Target,
  Trophy,
  AlertCircle,
  Loader2,
  RefreshCw,
  Info,
  Star,
} from "lucide-react";
import { getShipments } from "../services/shipmentService";
import {
  runOptimizer,
  type ObjectiveWeights,
  type ScoredOption,
  type OptimizerResponse,
} from "../services/optimizerService";

// ── Constants ─────────────────────────────────────────────────────────────────

/** Objectives that will always be unavailable in the current project */
const ALWAYS_UNAVAILABLE = new Set(["cost", "impact"]);

const SHIPPING_MODE_ICONS: Record<string, string> = {
  "Same Day":      "⚡",
  "First Class":   "✈️",
  "Second Class":  "🚢",
  "Standard Class":"📦",
};

// ── Weight slider ─────────────────────────────────────────────────────────────

interface SliderProps {
  label: string;
  value: number;
  onChange: (v: number) => void;
  unavailable?: boolean;
  tooltip: string;
}

function WeightSlider({
  label,
  value,
  onChange,
  unavailable = false,
  tooltip,
}: SliderProps) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <span className="text-sm font-medium text-slate-700">{label}</span>
          {unavailable && (
            <span className="rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-400">
              UNAVAILABLE
            </span>
          )}
        </div>
        <span className="text-sm font-semibold text-slate-800 tabular-nums">
          {value}
        </span>
      </div>
      <input
        type="range"
        min={0}
        max={10}
        step={1}
        value={value}
        disabled={unavailable}
        onChange={(e) => onChange(Number(e.target.value))}
        className={`h-1.5 w-full cursor-pointer appearance-none rounded-full bg-slate-200 accent-amber-500 ${
          unavailable ? "cursor-not-allowed opacity-40" : ""
        }`}
        title={tooltip}
      />
      <p className="text-[11px] text-slate-400">{tooltip}</p>
    </div>
  );
}

// ── Score bar ─────────────────────────────────────────────────────────────────

function ScoreBar({ value, color }: { value: number | null; color: string }) {
  if (value === null) {
    return (
      <span className="text-xs italic text-slate-400">— unavailable</span>
    );
  }
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${(value * 100).toFixed(1)}%`, background: color }}
        />
      </div>
      <span className="w-10 text-right text-xs font-semibold text-slate-700 tabular-nums">
        {(value * 100).toFixed(0)}
      </span>
    </div>
  );
}

// ── Ranked option card ────────────────────────────────────────────────────────

interface RankedCardProps {
  option: ScoredOption;
  rank: number;
  effectiveWeights: Record<string, number>;
}

function RankedCard({ option, rank, effectiveWeights }: RankedCardProps) {
  const isPareto = option.is_pareto_optimal;
  const isFirst = rank === 1;

  return (
    <div
      className={`relative rounded-xl border bg-white p-4 shadow-sm transition-all ${
        isFirst
          ? "border-amber-400 ring-1 ring-amber-200"
          : isPareto
          ? "border-blue-200"
          : "border-slate-200"
      }`}
    >
      {/* Rank + Pareto badges */}
      <div className="mb-3 flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span
            className={`flex h-7 w-7 items-center justify-center rounded-full text-sm font-bold ${
              isFirst
                ? "bg-amber-500 text-white"
                : "bg-slate-100 text-slate-600"
            }`}
          >
            {isFirst ? <Trophy className="h-3.5 w-3.5" /> : rank}
          </span>
          <div>
            <p className="text-sm font-semibold text-slate-800">
              {SHIPPING_MODE_ICONS[option.shipping_mode] ?? "◆"}{" "}
              {option.shipping_mode}
            </p>
          </div>
        </div>
        <div className="flex gap-1.5">
          {isPareto && (
            <span className="flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-semibold text-blue-700">
              <Star className="h-2.5 w-2.5" />
              Pareto-optimal
            </span>
          )}
        </div>
      </div>

      {/* Composite score */}
      <div className="mb-3 flex items-baseline gap-2">
        <span className="text-2xl font-bold text-slate-800 tabular-nums">
          {((option.composite_score ?? 0) * 100).toFixed(1)}
        </span>
        <span className="text-xs text-slate-400">composite score</span>
      </div>

      {/* Per-objective scores */}
      <div className="space-y-2 border-t border-slate-100 pt-3 text-xs">
        {/* Delay score */}
        <div className="flex items-center gap-2">
          <span className="w-24 flex-shrink-0 text-slate-500">
            Delay Risk
            {effectiveWeights.delay != null && (
              <span className="ml-1 text-slate-300">
                ×{(effectiveWeights.delay * 100).toFixed(0)}%
              </span>
            )}
          </span>
          <ScoreBar value={option.delay_score} color="#22c55e" />
        </div>

        {/* ETA score */}
        <div className="flex items-center gap-2">
          <span className="w-24 flex-shrink-0 text-slate-500">
            ETA Speed
            {effectiveWeights.eta != null && (
              <span className="ml-1 text-slate-300">
                ×{(effectiveWeights.eta * 100).toFixed(0)}%
              </span>
            )}
          </span>
          <ScoreBar value={option.eta_score} color="#3b82f6" />
        </div>

        {/* Cost score — always unavailable */}
        <div className="flex items-center gap-2">
          <span className="w-24 flex-shrink-0 text-slate-400 line-through">
            Cost
          </span>
          <ScoreBar value={option.cost_score} color="#f59e0b" />
        </div>

        {/* Impact score — always unavailable */}
        <div className="flex items-center gap-2">
          <span className="w-24 flex-shrink-0 text-slate-400 line-through">
            Supply Impact
          </span>
          <ScoreBar value={option.impact_score} color="#8b5cf6" />
        </div>
      </div>

      {/* Raw metrics */}
      <div className="mt-3 flex gap-4 border-t border-slate-100 pt-3 text-xs text-slate-500">
        <span>
          Delay prob:{" "}
          <strong className="text-slate-700">
            {(option.delay_probability * 100).toFixed(1)}%
          </strong>
        </span>
        <span>
          ETA:{" "}
          <strong className="text-slate-700">
            {option.eta_days.toFixed(1)} days
          </strong>
        </span>
      </div>

      {/* Explanation */}
      {isFirst && (
        <div className="mt-3 rounded-lg bg-amber-50 p-2.5 text-xs text-amber-800">
          <strong>Why this option?</strong> Lowest delay risk (
          {(option.delay_probability * 100).toFixed(1)}%) combined with fastest
          ETA ({option.eta_days.toFixed(1)}d) gives the highest weighted composite
          score under your current weight settings.
        </div>
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

function OptimizerPage() {
  // Shipment selector
  const [shipments, setShipments] = useState<{ id: number; label: string }[]>([]);
  const [shipLoading, setShipLoading] = useState(true);
  const [selectedShipId, setSelectedShipId] = useState<number | "">("");

  // Weight sliders (0-10 int scale, normalised before sending)
  const [wDelay, setWDelay] = useState(7);
  const [wEta, setWEta] = useState(3);
  // cost and impact remain 0 — they are always unavailable in the current project

  // Results
  const [result, setResult] = useState<OptimizerResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Weight validation: at least one available weight must be > 0
  const validWeights = wDelay > 0 || wEta > 0;

  // Load shipments on mount
  useEffect(() => {
    getShipments(0, 100, undefined, undefined, undefined, true)
      .then((data) => {
        const items = data.map((s) => ({
          id: s.id,
          label: `${s.shipment_reference} (${s.shipment_status ?? "?"})`,
        }));
        setShipments(items);
        if (items.length > 0) setSelectedShipId(items[0].id);
      })
      .catch(() => {})
      .finally(() => setShipLoading(false));
  }, []);

  // Explicit run — called by button and by shipment selector onChange
  function handleRun(shipId?: number) {
    const id = shipId ?? (selectedShipId === "" ? null : Number(selectedShipId));
    if (id === null || !validWeights) return;
    setLoading(true);
    setError(null);
    setResult(null);
    const weights: Partial<ObjectiveWeights> = {
      w_delay: wDelay,
      w_eta: wEta,
      w_cost: 0,
      w_impact: 0,
    };
    runOptimizer(id, weights)
      .then(setResult)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }

  function handleShipmentChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const id = Number(e.target.value);
    setSelectedShipId(id);
    setResult(null);
    setError(null);
    // Auto-run for newly selected shipment
    if (id && validWeights) {
      setLoading(true);
      const weights: Partial<ObjectiveWeights> = {
        w_delay: wDelay,
        w_eta: wEta,
        w_cost: 0,
        w_impact: 0,
      };
      runOptimizer(id, weights)
        .then(setResult)
        .catch((err: Error) => setError(err.message))
        .finally(() => setLoading(false));
    }
  }

  const effectiveWeights = result?.ranked_options?.[0]?.effective_weights ?? {};
  const paretoOptions = result?.ranked_options?.filter((o) => o.is_pareto_optimal) ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-100">
          <Target className="h-5 w-5 text-amber-600" />
        </div>
        <div>
          <h2 className="text-base font-semibold text-slate-800">
            Multi-Objective Optimizer
          </h2>
          <p className="text-sm text-slate-500">
            Rank shipping modes by weighted delay risk and ETA speed.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* ── Left column: controls ── */}
        <div className="space-y-5">
          {/* Shipment selector */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
              Shipment
            </p>
            {shipLoading ? (
              <div className="h-9 animate-pulse rounded-lg bg-slate-100" />
            ) : (
              <select
                value={selectedShipId}
                onChange={handleShipmentChange}
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 outline-none transition focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
              >
                {shipments.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Weight sliders */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="mb-4 text-xs font-semibold uppercase tracking-wide text-slate-500">
              Objective Weights
            </p>
            <div className="space-y-5">
              <WeightSlider
                label="Delay Risk"
                value={wDelay}
                onChange={setWDelay}
                tooltip="Higher → penalise delay probability more heavily"
              />
              <WeightSlider
                label="ETA Speed"
                value={wEta}
                onChange={setWEta}
                tooltip="Higher → favour faster estimated arrival"
              />
              <WeightSlider
                label="Cost"
                value={0}
                onChange={() => {}}
                unavailable
                tooltip="No shipping-cost model available in this project"
              />
              <WeightSlider
                label="Supply Impact"
                value={0}
                onChange={() => {}}
                unavailable
                tooltip="No supply-chain impact model available in this project"
              />
            </div>

            {/* Weight normalisation note */}
            <div className="mt-4 flex items-start gap-2 rounded-lg bg-slate-50 p-3 text-xs text-slate-500">
              <Info className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-slate-400" />
              <span>
                Weights are normalised to sum to 1 before scoring. Sliders set
                relative importance — absolute values don't matter, only ratios.
              </span>
            </div>

            {!validWeights && (
              <div className="mt-3 flex items-start gap-2 rounded-lg bg-red-50 p-3 text-xs text-red-700">
                <AlertCircle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />
                <span>
                  At least one available weight (Delay Risk or ETA Speed) must
                  be &gt; 0.
                </span>
              </div>
            )}

            <button
              onClick={() => handleRun()}
              disabled={loading || selectedShipId === "" || !validWeights}
              className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-amber-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-amber-600 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              {loading ? "Scoring…" : "Run Optimizer"}
            </button>
          </div>

          {/* Unavailable objectives note */}
          {result && (
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Objective Availability
              </p>
              <div className="space-y-1.5 text-xs">
                {result.available_objectives.map((obj) => (
                  <div key={obj} className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
                    <span className="capitalize text-slate-700">{obj}</span>
                    <span className="text-slate-400">— active</span>
                  </div>
                ))}
                {result.unavailable_objectives.map((obj) => (
                  <div key={obj} className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-slate-300" />
                    <span
                      className={`capitalize text-slate-400 ${
                        ALWAYS_UNAVAILABLE.has(obj) ? "line-through" : ""
                      }`}
                    >
                      {obj}
                    </span>
                    <span className="text-slate-300">— no model</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ── Right columns: results ── */}
        <div className="lg:col-span-2 space-y-4">
          {/* Error */}
          {error && (
            <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Loading */}
          {loading && (
            <div className="flex items-center justify-center rounded-xl border border-slate-200 bg-white py-16">
              <Loader2 className="h-6 w-6 animate-spin text-amber-500" />
              <span className="ml-3 text-sm text-slate-500">
                Running optimizer…
              </span>
            </div>
          )}

          {/* Results */}
          {result && !loading && (
            <>
              {/* Summary bar */}
              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
                  <p className="text-xs text-slate-400">Modes Evaluated</p>
                  <p className="mt-0.5 text-xl font-bold text-slate-800">
                    {result.ranked_options.length}
                  </p>
                </div>
                <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
                  <p className="text-xs text-slate-400">Pareto-Optimal</p>
                  <p className="mt-0.5 text-xl font-bold text-blue-700">
                    {paretoOptions.length}
                  </p>
                  <p className="text-xs text-slate-400 truncate">
                    {paretoOptions.map((o) => o.shipping_mode).join(", ")}
                  </p>
                </div>
                <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
                  <p className="text-xs text-slate-400">Active Objectives</p>
                  <p className="mt-0.5 text-xl font-bold text-green-700">
                    {result.available_objectives.length}
                  </p>
                  <p className="text-xs text-slate-400">
                    of {result.available_objectives.length +
                      result.unavailable_objectives.length} total
                  </p>
                </div>
              </div>

              {/* Pareto highlight box (if any non-winner Pareto options) */}
              {paretoOptions.length > 1 && (
                <div className="flex items-start gap-3 rounded-xl border border-blue-200 bg-blue-50 p-4 text-sm text-blue-800">
                  <Star className="mt-0.5 h-4 w-4 flex-shrink-0 text-blue-500" />
                  <div>
                    <strong>Pareto-optimal options</strong> — these modes are
                    not dominated: no other option is strictly better on{" "}
                    <em>every</em> objective simultaneously.{" "}
                    {paretoOptions.map((o) => o.shipping_mode).join(", ")}.
                  </div>
                </div>
              )}

              {/* Ranked cards */}
              <div className="space-y-3">
                {result.ranked_options.map((opt, i) => (
                  <RankedCard
                    key={opt.shipping_mode}
                    option={opt}
                    rank={i + 1}
                    effectiveWeights={effectiveWeights}
                  />
                ))}
              </div>

              {/* Generated-at footer */}
              <p className="text-right text-xs text-slate-400">
                Scored at{" "}
                {new Date(result.generated_at).toLocaleTimeString()}
              </p>
            </>
          )}

          {/* Empty state */}
          {!result && !loading && !error && (
            <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 py-20 text-center">
              <Target className="h-8 w-8 text-slate-300" />
              <p className="mt-3 text-sm text-slate-400">
                Select a shipment and click{" "}
                <span className="font-semibold">Run Optimizer</span>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default OptimizerPage;
