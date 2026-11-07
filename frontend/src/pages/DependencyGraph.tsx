import { useEffect, useState } from "react";
import {
  GitBranch,
  AlertTriangle,
  HelpCircle,
  Loader2,
  RefreshCw,
  Info,
} from "lucide-react";
import { getShipments } from "../services/shipmentService";
import {
  getDependencyGraph,
  type DependencyGraph,
  type GraphNode,
  type GraphEdge,
} from "../services/optimizerService";

// ── Severity colour map ───────────────────────────────────────────────────────

const SEVERITY_COLORS: Record<string, { fill: string; stroke: string; text: string; badge: string }> = {
  HIGH:    { fill: "#fef2f2", stroke: "#ef4444", text: "#b91c1c", badge: "bg-red-100 text-red-700" },
  MEDIUM:  { fill: "#fffbeb", stroke: "#f59e0b", text: "#b45309", badge: "bg-amber-100 text-amber-700" },
  LOW:     { fill: "#f0fdf4", stroke: "#22c55e", text: "#15803d", badge: "bg-green-100 text-green-700" },
  NONE:    { fill: "#f8fafc", stroke: "#94a3b8", text: "#475569", badge: "bg-slate-100 text-slate-600" },
  UNKNOWN: { fill: "#f8fafc", stroke: "#94a3b8", text: "#94a3b8", badge: "bg-slate-100 text-slate-400" },
};

const NODE_TYPE_ICONS: Record<string, string> = {
  shipment: "📦",
  route:    "🗺",
  carrier:  "🚚",
  order:    "🛒",
};

// ── SVG node-link diagram ─────────────────────────────────────────────────────

// Layout: left-to-right linear arrangement
// shipment (center) → route, carrier, order (right column)

const NODE_W = 140;
const NODE_H = 72;
const GAP_X = 180;
const GAP_Y = 96;

interface LayoutNode extends GraphNode {
  x: number;
  y: number;
}

function layoutNodes(nodes: GraphNode[]): LayoutNode[] {
  const shipment = nodes.find((n) => n.type === "shipment");
  const others = nodes.filter((n) => n.type !== "shipment");

  const totalHeight = others.length * (NODE_H + GAP_Y) - GAP_Y;
  const centerY = totalHeight / 2;

  const laidOut: LayoutNode[] = [];

  if (shipment) {
    laidOut.push({ ...shipment, x: 40, y: centerY });
  }

  others.forEach((n, i) => {
    laidOut.push({
      ...n,
      x: 40 + GAP_X + NODE_W + 40,
      y: i * (NODE_H + GAP_Y),
    });
  });

  return laidOut;
}

function svgColors(node: LayoutNode) {
  const sev = node.data_source === "missing" ? "UNKNOWN" : node.severity;
  return SEVERITY_COLORS[sev] ?? SEVERITY_COLORS.UNKNOWN;
}

interface DiagramProps {
  graph: DependencyGraph;
  onSelectNode: (node: GraphNode | null) => void;
  selectedId: string | null;
}

function GraphDiagram({ graph, onSelectNode, selectedId }: DiagramProps) {
  const laidOut = layoutNodes(graph.nodes);
  const byId: Record<string, LayoutNode> = {};
  for (const n of laidOut) byId[n.id] = n;

  // Determine SVG viewport
  const allX = laidOut.map((n) => n.x + NODE_W);
  const allY = laidOut.map((n) => n.y + NODE_H);
  const svgW = Math.max(...allX) + 40;
  const svgH = Math.max(...allY) + 40;

  function edgePath(e: GraphEdge) {
    const src = byId[e.source];
    const tgt = byId[e.target];
    if (!src || !tgt) return null;
    const x1 = src.x + NODE_W;
    const y1 = src.y + NODE_H / 2;
    const x2 = tgt.x;
    const y2 = tgt.y + NODE_H / 2;
    const mx = (x1 + x2) / 2;
    return `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`;
  }

  return (
    <svg
      width="100%"
      viewBox={`0 0 ${svgW} ${svgH}`}
      className="overflow-visible"
    >
      <defs>
        <marker
          id="arrow"
          markerWidth="8"
          markerHeight="8"
          refX="6"
          refY="3"
          orient="auto"
        >
          <path d="M0,0 L0,6 L8,3 z" fill="#94a3b8" />
        </marker>
      </defs>

      {/* Edges */}
      {graph.edges.map((e, i) => {
        const d = edgePath(e);
        if (!d) return null;
        return (
          <g key={i}>
            <path
              d={d}
              fill="none"
              stroke="#cbd5e1"
              strokeWidth={1.5}
              markerEnd="url(#arrow)"
            />
            {/* Edge label */}
            <text
              x={
                ((byId[e.source]?.x ?? 0) + NODE_W +
                  (byId[e.target]?.x ?? 0)) /
                  2
              }
              y={
                ((byId[e.source]?.y ?? 0) +
                  (byId[e.target]?.y ?? 0)) /
                  2 +
                NODE_H / 2 -
                6
              }
              fontSize={9}
              fill="#94a3b8"
              textAnchor="middle"
            >
              {e.relationship_type.replace(/_/g, " ")}
            </text>
          </g>
        );
      })}

      {/* Nodes */}
      {laidOut.map((node) => {
        const colors = svgColors(node);
        const isSelected = node.id === selectedId;
        const isMissing = node.data_source === "missing";
        return (
          <g
            key={node.id}
            transform={`translate(${node.x}, ${node.y})`}
            className="cursor-pointer"
            onClick={() =>
              onSelectNode(isSelected ? null : node)
            }
          >
            <rect
              width={NODE_W}
              height={NODE_H}
              rx={10}
              fill={colors.fill}
              stroke={isSelected ? "#f59e0b" : colors.stroke}
              strokeWidth={isSelected ? 2.5 : isMissing ? 1 : 1.5}
              strokeDasharray={isMissing ? "4 3" : undefined}
            />
            {/* Icon */}
            <text x={12} y={26} fontSize={16}>
              {NODE_TYPE_ICONS[node.type] ?? "◆"}
            </text>
            {/* Label */}
            <text
              x={34}
              y={24}
              fontSize={11}
              fontWeight="600"
              fill={colors.text}
            >
              {node.label.length > 16
                ? node.label.slice(0, 15) + "…"
                : node.label}
            </text>
            {/* Type badge */}
            <text x={34} y={37} fontSize={9} fill="#94a3b8">
              {node.type.toUpperCase()}
            </text>
            {/* Severity badge */}
            <rect
              x={8}
              y={46}
              width={NODE_W - 16}
              height={16}
              rx={4}
              fill={colors.stroke}
              opacity={isMissing ? 0.2 : 0.15}
            />
            <text
              x={NODE_W / 2}
              y={57}
              fontSize={9}
              fontWeight="600"
              fill={colors.text}
              textAnchor="middle"
            >
              {isMissing
                ? "DATA UNAVAILABLE"
                : `${node.impact_status} · ${node.severity}`}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

// ── Node detail panel ─────────────────────────────────────────────────────────

function NodeDetail({ node }: { node: GraphNode }) {
  const colors = SEVERITY_COLORS[node.severity] ?? SEVERITY_COLORS.UNKNOWN;
  const isMissing = node.data_source === "missing";

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            {node.type}
          </p>
          <p className="mt-0.5 text-base font-bold text-slate-800">
            {node.label}
          </p>
        </div>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-semibold ${colors.badge}`}
        >
          {isMissing ? "No Data" : node.severity}
        </span>
      </div>

      {isMissing ? (
        <div className="flex items-start gap-2 rounded-lg bg-slate-50 p-3 text-xs text-slate-500">
          <HelpCircle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />
          <span>
            This entity is not present in the database. The relationship is
            acknowledged but impact cannot be calculated.
          </span>
        </div>
      ) : (
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
          <div>
            <dt className="text-slate-400">Impact Status</dt>
            <dd className="font-semibold text-slate-700">{node.impact_status}</dd>
          </div>
          <div>
            <dt className="text-slate-400">Delay Probability</dt>
            <dd className="font-semibold text-slate-700">
              {node.delay_probability != null
                ? `${(node.delay_probability * 100).toFixed(1)}%`
                : "—"}
            </dd>
          </div>
          <div>
            <dt className="text-slate-400">Cost Impact</dt>
            <dd className="font-semibold text-slate-500 italic">
              unavailable
            </dd>
          </div>
          <div>
            <dt className="text-slate-400">Data Source</dt>
            <dd className="font-semibold text-slate-700">{node.data_source}</dd>
          </div>
        </dl>
      )}

      {Object.keys(node.attributes).length > 0 && !isMissing && (
        <div className="border-t border-slate-100 pt-3">
          <p className="mb-2 text-xs font-semibold text-slate-500">
            Attributes
          </p>
          <dl className="space-y-1 text-xs">
            {Object.entries(node.attributes).map(([k, v]) =>
              v != null ? (
                <div key={k} className="flex gap-2">
                  <dt className="w-28 flex-shrink-0 text-slate-400">{k}</dt>
                  <dd className="text-slate-700 truncate">{String(v)}</dd>
                </div>
              ) : null
            )}
          </dl>
        </div>
      )}
    </div>
  );
}

// ── Impact summary strip ──────────────────────────────────────────────────────

function ImpactStrip({ graph }: { graph: DependencyGraph }) {
  const s = graph.impact_summary;
  const colors = SEVERITY_COLORS[s.severity] ?? SEVERITY_COLORS.UNKNOWN;

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {[
        {
          label: "Delay Risk",
          value: s.delay_probability != null
            ? `${(s.delay_probability * 100).toFixed(1)}%`
            : "—",
          sub: s.severity,
          color: colors.text,
        },
        {
          label: "Impacted Downstream",
          value: s.impacted_downstream_count,
          sub: s.impacted_downstream_labels.join(", ") || "none",
          color: s.impacted_downstream_count > 0 ? "#b91c1c" : "#15803d",
        },
        {
          label: "Data Unavailable",
          value: s.unavailable_count,
          sub: s.unavailable_labels.join(", ") || "none",
          color: "#94a3b8",
        },
        {
          label: "Cost Impact",
          value: "—",
          sub: "no cost model",
          color: "#94a3b8",
        },
      ].map(({ label, value, sub, color }) => (
        <div
          key={label}
          className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm"
        >
          <p className="text-xs text-slate-400">{label}</p>
          <p
            className="mt-0.5 text-xl font-bold"
            style={{ color }}
          >
            {value}
          </p>
          <p className="mt-0.5 truncate text-xs text-slate-400">{sub}</p>
        </div>
      ))}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

function DependencyGraphPage() {
  const [shipments, setShipments] = useState<{ id: number; label: string }[]>([]);
  const [shipLoading, setShipLoading] = useState(true);

  const [selectedShipId, setSelectedShipId] = useState<number | "">("");
  const [graph, setGraph] = useState<DependencyGraph | null>(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [graphError, setGraphError] = useState<string | null>(null);

  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  // Load simulation-enabled shipments for the selector
  useEffect(() => {
    getShipments(0, 100, undefined, undefined, undefined, true)
      .then((data) => {
        setShipments(
          data.map((s) => ({
            id: s.id,
            label: `${s.shipment_reference} (${s.shipment_status ?? "?"})`,
          }))
        );
        if (data.length > 0) setSelectedShipId(data[0].id);
      })
      .catch(() => {})
      .finally(() => setShipLoading(false));
  }, []);

  function loadGraph(shipId: number) {
    setGraphLoading(true);
    setGraphError(null);
    setGraph(null);
    setSelectedNode(null);
    getDependencyGraph(shipId)
      .then(setGraph)
      .catch((err: Error) => setGraphError(err.message))
      .finally(() => setGraphLoading(false));
  }

  function handleShipmentSelect(e: React.ChangeEvent<HTMLSelectElement>) {
    const id = Number(e.target.value);
    setSelectedShipId(id);
    if (id) loadGraph(id);
  }

  function handleRefresh() {
    if (selectedShipId === "") return;
    loadGraph(Number(selectedShipId));
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100">
          <GitBranch className="h-5 w-5 text-blue-600" />
        </div>
        <div>
          <h2 className="text-base font-semibold text-slate-800">
            Supply Chain Dependency Graph
          </h2>
          <p className="text-sm text-slate-500">
            Verified relationships and downstream delay impact for a shipment.
          </p>
        </div>
      </div>

      {/* Shipment selector */}
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-[220px]">
          <label
            htmlFor="dep-ship-select"
            className="mb-1.5 block text-xs font-medium text-slate-600"
          >
            Shipment (simulation-enabled)
          </label>
          {shipLoading ? (
            <div className="h-10 animate-pulse rounded-lg bg-slate-100" />
          ) : (
            <select
              id="dep-ship-select"
              value={selectedShipId}
              onChange={handleShipmentSelect}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            >
              {shipments.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label}
                </option>
              ))}
            </select>
          )}
        </div>
        <button
          id="dep-refresh-btn"
          onClick={handleRefresh}
          disabled={graphLoading || selectedShipId === ""}
          className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${graphLoading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Error */}
      {graphError && (
        <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <span>{graphError}</span>
        </div>
      )}

      {/* Loading */}
      {graphLoading && (
        <div className="flex items-center justify-center rounded-xl border border-slate-200 bg-white py-16">
          <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
          <span className="ml-3 text-sm text-slate-500">
            Building dependency graph…
          </span>
        </div>
      )}

      {/* Graph content */}
      {graph && !graphLoading && (
        <>
          {/* Impact summary strip */}
          <ImpactStrip graph={graph} />

          {/* Main diagram + detail panel */}
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            {/* SVG diagram */}
            <div className="lg:col-span-2 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="mb-4 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Dependency Graph
              </p>
              <GraphDiagram
                graph={graph}
                onSelectNode={setSelectedNode}
                selectedId={selectedNode?.id ?? null}
              />
              <p className="mt-3 text-xs text-slate-400">
                Click a node to inspect its details.{" "}
                <span className="font-medium text-slate-500">Dashed border</span> = data unavailable.
              </p>
            </div>

            {/* Detail / info panel */}
            <div className="space-y-4">
              {selectedNode ? (
                <NodeDetail node={selectedNode} />
              ) : (
                <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 py-10 text-center">
                  <GitBranch className="mx-auto h-7 w-7 text-slate-300" />
                  <p className="mt-3 text-sm text-slate-400">
                    Select a node to view details
                  </p>
                </div>
              )}

              {/* Data notes */}
              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <div className="mb-2 flex items-center gap-2">
                  <Info className="h-3.5 w-3.5 text-slate-400" />
                  <p className="text-xs font-semibold text-slate-500">
                    Data Notes
                  </p>
                </div>
                <ul className="space-y-1.5">
                  {graph.data_notes.map((note, i) => (
                    <li key={i} className="text-xs text-slate-500 leading-relaxed">
                      • {note}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Severity legend */}
          <div className="flex flex-wrap gap-3 text-xs">
            {Object.entries(SEVERITY_COLORS).map(([sev, c]) => (
              <span
                key={sev}
                className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 font-medium ${c.badge}`}
              >
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ background: c.stroke }}
                />
                {sev}
              </span>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default DependencyGraphPage;
