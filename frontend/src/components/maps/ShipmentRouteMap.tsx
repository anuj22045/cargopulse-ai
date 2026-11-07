import { useEffect, useMemo, useRef } from "react";
import {
  MapContainer,
  Marker,
  Polyline,
  Popup,
  TileLayer,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import { seaRoute } from "searoute-ts";

interface ShipmentRouteMapProps {
  /** Current live/stored shipment position */
  latitude: number | null;
  longitude: number | null;
  /** Route origin port coordinates */
  originLatitude?: number | null;
  originLongitude?: number | null;
  /** Route destination port coordinates */
  destinationLatitude?: number | null;
  destinationLongitude?: number | null;
}

const shipmentIcon = L.divIcon({
  className: "",
  html: `
    <div style="
      width: 18px;
      height: 18px;
      background: #2563eb;
      border: 3px solid white;
      border-radius: 50%;
      box-shadow: 0 1px 6px #64748b;
    "></div>
  `,
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

/**
 * Fits the map to the given positions only when the route itself changes,
 * not on every live coordinate update that re-renders the parent.
 */
function MapFitter({ positions }: { positions: [number, number][] }) {
  const map = useMap();
  const routeKey = useMemo(
    () =>
      positions.length > 0
        ? `${positions[0]?.join(",")}_${positions[positions.length - 1]?.join(",")}_${positions.length}`
        : "",
    [positions],
  );
  const fittedRouteKey = useRef<string>("");

  useEffect(() => {
    if (positions.length > 0 && routeKey !== fittedRouteKey.current) {
      map.fitBounds(positions, { padding: [25, 25] });
      fittedRouteKey.current = routeKey;
    }
  }, [positions, routeKey, map]);

  return null;
}

export default function ShipmentRouteMap({
  latitude,
  longitude,
  originLatitude,
  originLongitude,
  destinationLatitude,
  destinationLongitude,
}: ShipmentRouteMapProps) {
  // ── Validate current shipment position ──────────────────────────────────
  const hasPosition =
    latitude != null &&
    longitude != null &&
    Number.isFinite(latitude) &&
    Number.isFinite(longitude) &&
    latitude >= -90 &&
    latitude <= 90 &&
    longitude >= -180 &&
    longitude <= 180;

  const hasOrigin =
    originLatitude != null &&
    originLongitude != null &&
    Number.isFinite(originLatitude) &&
    Number.isFinite(originLongitude) &&
    originLatitude >= -90 &&
    originLatitude <= 90 &&
    originLongitude >= -180 &&
    originLongitude <= 180;

  const hasDestination =
    destinationLatitude != null &&
    destinationLongitude != null &&
    Number.isFinite(destinationLatitude) &&
    Number.isFinite(destinationLongitude) &&
    destinationLatitude >= -90 &&
    destinationLatitude <= 90 &&
    destinationLongitude >= -180 &&
    destinationLongitude <= 180;

  // ── Compute maritime route geometry ─────────────────────────────────────
  // seaRoute input: [longitude, latitude]; GeoJSON output: [longitude, latitude]
  // Leaflet Polyline input: [latitude, longitude]
  const seaRouteCoordinates = useMemo<[number, number][]>(() => {
    if (!hasOrigin || !hasDestination) return [];

    try {
      const result = seaRoute(
        [originLongitude!, originLatitude!],           // [lng, lat]
        [destinationLongitude!, destinationLatitude!], // [lng, lat]
      );

      if (
        !result?.geometry?.coordinates ||
        result.geometry.coordinates.length === 0
      ) {
        return [];
      }

      // Convert GeoJSON [lng, lat] → Leaflet [lat, lng]
      return result.geometry.coordinates.map(([lng, lat]) => [lat, lng]);
    } catch {
      return [];
    }
  }, [
    hasOrigin,
    hasDestination,
    originLatitude,
    originLongitude,
    destinationLatitude,
    destinationLongitude,
  ]);

  // ── Positions used for fitting map bounds ────────────────────────────────
  const fitPositions = useMemo<[number, number][]>(() => {
    if (seaRouteCoordinates.length > 0) return seaRouteCoordinates;
    // Fallback: fit to available markers when no route geometry
    const pts: [number, number][] = [];
    if (hasPosition) pts.push([latitude!, longitude!]);
    if (hasOrigin) pts.push([originLatitude!, originLongitude!]);
    if (hasDestination) pts.push([destinationLatitude!, destinationLongitude!]);
    return pts;
  }, [
    seaRouteCoordinates,
    hasPosition,
    latitude,
    longitude,
    hasOrigin,
    originLatitude,
    originLongitude,
    hasDestination,
    destinationLatitude,
    destinationLongitude,
  ]);

  // ── Guard: no usable data at all ─────────────────────────────────────────
  if (!hasPosition && !hasOrigin && !hasDestination) {
    return (
      <div className="flex h-80 items-center justify-center rounded-lg bg-slate-50 text-sm text-slate-500">
        Shipment coordinates are not available.
      </div>
    );
  }

  const currentPosition: [number, number] | null = hasPosition
    ? [latitude!, longitude!]
    : null;

  const originPosition: [number, number] | null = hasOrigin
    ? [originLatitude!, originLongitude!]
    : null;

  const destinationPosition: [number, number] | null = hasDestination
    ? [destinationLatitude!, destinationLongitude!]
    : null;

  // Default map centre: first available point
  const defaultCenter: [number, number] =
    currentPosition ?? originPosition ?? destinationPosition ?? [0, 0];

  return (
    <div className="h-80 overflow-hidden rounded-lg">
      <MapContainer
        center={defaultCenter}
        zoom={2}
        scrollWheelZoom
        className="h-full w-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Fit map to route/markers only when the route key changes */}
        {fitPositions.length > 0 && <MapFitter positions={fitPositions} />}

        {/* Maritime route line */}
        {seaRouteCoordinates.length > 0 && (
          <Polyline
            positions={seaRouteCoordinates}
            pathOptions={{
              color: "#f59e0b",
              weight: 4,
              opacity: 0.9,
            }}
          />
        )}

        {/* Origin marker */}
        {originPosition && (
          <Marker position={originPosition}>
            <Popup>Origin</Popup>
          </Marker>
        )}

        {/* Current shipment position marker */}
        {currentPosition && (
          <Marker position={currentPosition} icon={shipmentIcon}>
            <Popup>
              Current shipment position
              <br />
              {latitude!.toFixed(4)}, {longitude!.toFixed(4)}
            </Popup>
          </Marker>
        )}

        {/* Destination marker */}
        {destinationPosition && (
          <Marker position={destinationPosition}>
            <Popup>Destination</Popup>
          </Marker>
        )}
      </MapContainer>
    </div>
  );
}
