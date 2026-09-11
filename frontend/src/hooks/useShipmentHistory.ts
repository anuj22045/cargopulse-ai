import { useEffect, useState } from "react";

import { apiClient } from "../api/client";
import { useWebSocket } from "./useWebSocket";

export interface RiskHistoryPoint {
  timestamp: string;
  delay_probability: number;
}

export interface EtaHistoryPoint {
  timestamp: string;
  predicted_eta: string;
}

export interface SpeedHistoryPoint {
  timestamp: string;
  speed: number | null;
  distance_remaining: number | null;
}

export interface EventHistoryPoint {
  timestamp: string;
  event_type: string;
  description: string | null;
  severity?: string | null;
}

export function useShipmentHistory(
  shipmentId: number | null
) {
  const [riskHistory, setRiskHistory] =
    useState<RiskHistoryPoint[]>([]);

  const [etaHistory, setEtaHistory] =
    useState<EtaHistoryPoint[]>([]);

  const [speedHistory, setSpeedHistory] =
    useState<SpeedHistoryPoint[]>([]);

  const [eventHistory, setEventHistory] =
    useState<EventHistoryPoint[]>([]);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const {
    latestUpdate,
    isConnected,
  } = useWebSocket(shipmentId);

  useEffect(() => {
    if (!shipmentId) {
      return;
    }

    async function fetchHistory() {
      try {
        setLoading(true);
        setError(null);

        const [
          risk,
          eta,
          speed,
          events,
        ] = await Promise.all([
          apiClient(
            `/api/shipments/${shipmentId}/risk-history`
          ),
          apiClient(
            `/api/shipments/${shipmentId}/eta-history`
          ),
          apiClient(
            `/api/shipments/${shipmentId}/speed-history`
          ),
          apiClient(
            `/api/shipments/${shipmentId}/events`
          ),
        ]);

        setRiskHistory(risk);
        setEtaHistory(eta);
        setSpeedHistory(speed);
        setEventHistory(events);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to fetch shipment history"
        );
      } finally {
        setLoading(false);
      }
    }

    fetchHistory();
  }, [shipmentId]);

  useEffect(() => {
    if (!latestUpdate) {
      return;
    }

    const timestamp = new Date().toISOString();

    const speed = latestUpdate.effective_speed_kmh;
    const distanceRemaining =
      latestUpdate.distance_remaining_km;

    if (
      speed !== undefined &&
      distanceRemaining !== undefined
    ) {
      setSpeedHistory((previous) => [
        ...previous,
        {
          timestamp,
          speed: speed ?? null,
          distance_remaining: distanceRemaining ?? null,
        },
      ]);
    }

    // Deduplication guard: only add a SIMULATION_UPDATE event
    // if the last event in history is not within the last 5 seconds.
    // This prevents the list from growing unbounded when the same
    // condition persists across multiple ticks.
    if (
      latestUpdate.weather ||
      latestUpdate.congestion
    ) {
      setEventHistory((previous) => {
        const now = Date.now();
        const last = previous[previous.length - 1];

        if (last) {
          const lastTime = new Date(last.timestamp).getTime();
          // Skip if less than 5 seconds since last event of same type
          if (
            last.event_type === "SIMULATION_UPDATE" &&
            now - lastTime < 5000
          ) {
            return previous;
          }
        }

        return [
          ...previous,
          {
            timestamp,
            event_type: "SIMULATION_UPDATE",
            description:
              `Weather: ${latestUpdate.weather ?? "—"}, ` +
              `Congestion: ${latestUpdate.congestion ?? "—"}, ` +
              `Speed: ${latestUpdate.effective_speed_kmh ?? "—"} km/h`,
            severity: latestUpdate.severity ?? null,
          },
        ];
      });
    }
  }, [latestUpdate]);

  return {
    riskHistory,
    etaHistory,
    speedHistory,
    eventHistory,
    latestUpdate,
    isConnected,
    loading,
    error,
  };
}