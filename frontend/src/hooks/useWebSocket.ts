// React component
//       ↓
// useWebSocket(2)
//       ↓
// ws://127.0.0.1:8000/ws/shipments/2
//       ↓
// Receives simulation update
//       ↓
// latestUpdate

import { useEffect, useRef, useState } from "react";

const WS_BASE_URL = "ws://127.0.0.1:8000";

export interface ShipmentUpdate {
    type: string;
    weather?: string;
    shipment_id: number;
    congestion?: string;
    mechanical_event?: string;
    customs_delay?: string;
    effective_speed_kmh?: number;
    speed_modifier?: number;
    port_wait_hours?: number;
    distance_remaining_km?: number;
    simulation_elapsed_minutes?: number;
    latitude?: number;
    longitude?: number;
    severity?: string;
}

export function useWebSocket(shipmentId: number | null) {
    const [latestUpdate, setLatestUpdate] =
    useState<ShipmentUpdate | null>(null);

    const [isConnected, setIsConnected] =
    useState(false);

    const socketRef = useRef<WebSocket | null>(null);
    const reconnectTimerRef = useRef<number | null>(null);

    useEffect(() => {
    if (!shipmentId) {
        return;
    }

    let shouldReconnect = true;

    const connect = () => {
    const socket = new WebSocket(
        `${WS_BASE_URL}/ws/shipments/${shipmentId}`
    );

    socketRef.current = socket;

    socket.onopen = () => {
        console.log(
        `WebSocket connected for shipment ${shipmentId}`
        );

        setIsConnected(true);
    };

    socket.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);

            const update: ShipmentUpdate =
            message.data ?? message;

            console.log(
                "Live shipment update received:",update);

            setLatestUpdate(update);
        } catch (error) {
            console.error(
            "Invalid WebSocket message:",error);
        }
    };

    socket.onerror = (error) => {
        console.error(
        "WebSocket error:",
        error
        );
    };

    socket.onclose = () => {
        setIsConnected(false);

    if (!shouldReconnect) {
        return;
    }

    reconnectTimerRef.current = window.setTimeout(
        connect,
        3000
        );
    };
    };

    connect();

    return () => {
        shouldReconnect = false;

    if (reconnectTimerRef.current !== null) {
    window.clearTimeout(
        reconnectTimerRef.current
        );
    }

    socketRef.current?.close();
    socketRef.current = null;
    };
    }, [shipmentId]);

    return {
    latestUpdate,
    isConnected,
    };
}   