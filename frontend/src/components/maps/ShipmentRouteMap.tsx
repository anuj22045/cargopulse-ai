
import { useEffect } from "react";
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

interface ShipmentRouteMapProps {
  latitude: number | null;
  longitude: number | null;
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

function MapUpdater({
  latitude,
  longitude,
}: {
  latitude: number;
  longitude: number;
}) {
  const map = useMap();

  useEffect(() => {
    map.flyTo([latitude, longitude], map.getZoom(), {
      duration: 0.8,
    });
  }, [latitude, longitude, map]);

  return null;
}

export default function ShipmentRouteMap({
  latitude,
  longitude,
  destinationLatitude,
  destinationLongitude,
}: ShipmentRouteMapProps) {
  const hasPosition =
    latitude != null &&
    longitude != null &&
    Number.isFinite(latitude) &&
    Number.isFinite(longitude) &&
    latitude >= -90 &&
    latitude <= 90 &&
    longitude >= -180 &&
    longitude <= 180;

  if (!hasPosition) {
    return (
      <div className="flex h-80 items-center justify-center rounded-lg bg-slate-50 text-sm text-slate-500">
        Shipment coordinates are not available.
      </div>
    );
  }

  const currentPosition: [number, number] = [
    latitude,
    longitude,
  ];

  const hasDestination =
    destinationLatitude != null &&
    destinationLongitude != null &&
    Number.isFinite(destinationLatitude) &&
    Number.isFinite(destinationLongitude) &&
    destinationLatitude >= -90 &&
    destinationLatitude <= 90 &&
    destinationLongitude >= -180 &&
    destinationLongitude <= 180;

  const destinationPosition: [number, number] | null =
    hasDestination
      ? [destinationLatitude, destinationLongitude]
      : null;

  return (
    <div className="h-80 overflow-hidden rounded-lg">
      <MapContainer
        center={currentPosition}
        zoom={6}
        scrollWheelZoom
        className="h-full w-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MapUpdater
          latitude={latitude}
          longitude={longitude}
        />

        {destinationPosition && (
          <Polyline
            positions={[
              currentPosition,
              destinationPosition,
            ]}
            pathOptions={{
              color: "#f59e0b",
              weight: 4,
              dashArray: "8 8",
            }}
          />
        )}

        <Marker
          position={currentPosition}
          icon={shipmentIcon}
        >
          <Popup>
            Current shipment position
            <br />
            {latitude.toFixed(4)}, {longitude.toFixed(4)}
          </Popup>
        </Marker>

        {destinationPosition && (
          <Marker position={destinationPosition}>
            <Popup>Destination</Popup>
          </Marker>
        )}
      </MapContainer>
    </div>
  );
}
