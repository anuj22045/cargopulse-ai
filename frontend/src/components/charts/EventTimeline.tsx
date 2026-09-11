// EventTimeline.tsx
// Vertical timeline showing shipment events from the events API + live WebSocket updates.
// Icons are assigned per event_type using lucide-react.
// Colors are derived from severity (INFO / WARNING / CRITICAL) when available,
// or from event_type as a UI-only fallback.

import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Cloud,
  Package,
  Truck,
  Clock,
  Wrench,
  FileText,
  Zap,
} from "lucide-react";
import type { EventHistoryPoint } from "../../hooks/useShipmentHistory";

interface Props {
  events: EventHistoryPoint[];
}

// ── Icon and color logic ─────────────────────────────────────────────────────

interface EventStyle {
  icon: React.ElementType;
  dotColor: string;        // Tailwind bg class for the dot
  iconColor: string;       // Tailwind text class for the icon
  badgeColor: string;      // Tailwind bg+text class for the badge
}

function getEventStyle(
  eventType: string,
  severity?: string | null
): EventStyle {
  const type = eventType.toUpperCase();

  // Severity-based colors (authoritative when present)
  if (severity === "CRITICAL") {
    return {
      icon: AlertTriangle,
      dotColor: "bg-red-500",
      iconColor: "text-white",
      badgeColor: "bg-red-100 text-red-700",
    };
  }
  if (severity === "WARNING") {
    return {
      icon: AlertTriangle,
      dotColor: "bg-amber-500",
      iconColor: "text-white",
      badgeColor: "bg-amber-100 text-amber-700",
    };
  }

  // Event-type-based icons (UI categorization only, not a backend prediction)
  if (type.includes("DELIVER") || type.includes("ARRIVE")) {
    return {
      icon: CheckCircle,
      dotColor: "bg-green-500",
      iconColor: "text-white",
      badgeColor: "bg-green-100 text-green-700",
    };
  }
  if (type.includes("PICKED") || type.includes("PICKUP")) {
    return {
      icon: Package,
      dotColor: "bg-blue-500",
      iconColor: "text-white",
      badgeColor: "bg-blue-100 text-blue-700",
    };
  }
  if (type.includes("DELAY") || type.includes("LATE")) {
    return {
      icon: AlertTriangle,
      dotColor: "bg-red-400",
      iconColor: "text-white",
      badgeColor: "bg-red-100 text-red-700",
    };
  }
  if (type.includes("WEATHER") || type.includes("STORM") || type.includes("FOG")) {
    return {
      icon: Cloud,
      dotColor: "bg-sky-500",
      iconColor: "text-white",
      badgeColor: "bg-sky-100 text-sky-700",
    };
  }
  if (type.includes("CONGESTION") || type.includes("TRAFFIC")) {
    return {
      icon: Zap,
      dotColor: "bg-orange-500",
      iconColor: "text-white",
      badgeColor: "bg-orange-100 text-orange-700",
    };
  }
  if (type.includes("MECHANICAL") || type.includes("BREAKDOWN")) {
    return {
      icon: Wrench,
      dotColor: "bg-red-500",
      iconColor: "text-white",
      badgeColor: "bg-red-100 text-red-700",
    };
  }
  if (type.includes("TRANSIT") || type.includes("SHIP") || type.includes("DEPART")) {
    return {
      icon: Truck,
      dotColor: "bg-blue-500",
      iconColor: "text-white",
      badgeColor: "bg-blue-100 text-blue-700",
    };
  }
  if (type.includes("CUSTOMS")) {
    return {
      icon: FileText,
      dotColor: "bg-purple-500",
      iconColor: "text-white",
      badgeColor: "bg-purple-100 text-purple-700",
    };
  }
  if (type.includes("SIMULATION_UPDATE")) {
    return {
      icon: Activity,
      dotColor: "bg-slate-400",
      iconColor: "text-white",
      badgeColor: "bg-slate-100 text-slate-600",
    };
  }

  // Default
  return {
    icon: Clock,
    dotColor: "bg-slate-400",
    iconColor: "text-white",
    badgeColor: "bg-slate-100 text-slate-600",
  };
}

function formatDateTime(dt: string): string {
  try {
    return new Date(dt).toLocaleString("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return dt;
  }
}

// ── Component ────────────────────────────────────────────────────────────────

export function EventTimeline({ events }: Props) {
  if (events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 py-8 text-center">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100">
          <Clock className="h-5 w-5 text-slate-400" />
        </div>
        <p className="text-sm font-medium text-slate-500">
          No events recorded yet
        </p>
        <p className="text-xs text-slate-400">
          Events will appear here as the shipment progresses
        </p>
      </div>
    );
  }

  // Show newest events first
  const sorted = [...events].sort(
    (a, b) =>
      new Date(b.timestamp).getTime() -
      new Date(a.timestamp).getTime()
  );

  return (
    <ol className="relative space-y-0 border-l border-slate-200 pl-6">
      {sorted.map((event, index) => {
        const style = getEventStyle(event.event_type, event.severity);
        const Icon = style.icon;

        return (
          <li
            key={`${event.timestamp}-${index}`}
            className="relative pb-5 last:pb-0"
          >
            {/* Timeline dot */}
            <span
              className={`absolute -left-[22px] flex h-5 w-5 items-center justify-center rounded-full ring-2 ring-white ${style.dotColor}`}
            >
              <Icon className={`h-2.5 w-2.5 ${style.iconColor}`} />
            </span>

            <div className="rounded-lg border border-slate-100 bg-slate-50 px-4 py-3 hover:bg-white transition-colors">
              {/* Header row */}
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${style.badgeColor}`}
                >
                  {event.event_type.replace(/_/g, " ")}
                </span>
                {event.severity && (
                  <span className="text-[10px] text-slate-400">
                    {event.severity}
                  </span>
                )}
                <time className="ml-auto text-[10px] text-slate-400 whitespace-nowrap">
                  {formatDateTime(event.timestamp)}
                </time>
              </div>

              {/* Description */}
              {event.description && (
                <p className="mt-1.5 text-xs leading-relaxed text-slate-600 break-words">
                  {event.description}
                </p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
