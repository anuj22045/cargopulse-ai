// useDashboardWebSocket.ts
// Connects to ws://127.0.0.1:8000/ws/dashboard
// Receives live dashboard stat updates from the simulation scheduler.

import { useEffect, useRef, useState } from "react";

const WS_BASE_URL = "ws://127.0.0.1:8000";

export interface DashboardUpdate {
  type: string;
  total_shipments: number;
  in_transit: number;
  delayed: number;
  delivered: number;
  status_breakdown: { status: string; count: number }[];
  avg_delay_risk: number;
}

export type DashboardWsState =
  | "connecting"
  | "connected"
  | "disconnected"
  | "reconnecting";

export function useDashboardWebSocket() {
  const [latestStats, setLatestStats] =
    useState<DashboardUpdate | null>(null);

  const [wsState, setWsState] =
    useState<DashboardWsState>("connecting");

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);

  useEffect(() => {
    let shouldReconnect = true;

    const connect = () => {
      setWsState("connecting");

      const socket = new WebSocket(
        `${WS_BASE_URL}/ws/dashboard`
      );

      socketRef.current = socket;

      socket.onopen = () => {
        console.log("Dashboard WebSocket connected");
        setWsState("connected");
      };

      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          const update: DashboardUpdate =
            message.data ?? message;

          console.log("Dashboard live update received:", update);
          setLatestStats(update);
        } catch (error) {
          console.error(
            "Invalid dashboard WebSocket message:", error
          );
        }
      };

      socket.onerror = (error) => {
        console.error("Dashboard WebSocket error:", error);
      };

      socket.onclose = () => {
        setWsState(shouldReconnect ? "reconnecting" : "disconnected");

        if (!shouldReconnect) {
          return;
        }

        reconnectTimerRef.current = window.setTimeout(() => {
          connect();
        }, 3000);
      };
    };

    connect();

    return () => {
      shouldReconnect = false;
      setWsState("disconnected");

      if (reconnectTimerRef.current !== null) {
        window.clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }

      socketRef.current?.close();
      socketRef.current = null;
    };
  }, []);

  return {
    latestStats,
    wsState,
    isConnected: wsState === "connected",
  };
}
