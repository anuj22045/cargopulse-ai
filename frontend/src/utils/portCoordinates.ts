
export interface PortCoordinates {
  latitude: number;
  longitude: number;
}

const PORT_COORDINATES: Record<string, PortCoordinates> = {
  "port of shanghai, china": {
    latitude: 31.24,
    longitude: 121.485,
  },
  "port of los angeles, usa": {
    latitude: 33.643672,
    longitude: -118.330938,
  },
};

export function getPortCoordinates(
  portName: string | null | undefined,
): PortCoordinates | null {
  if (!portName) {
    return null;
  }

  return PORT_COORDINATES[portName.trim().toLowerCase()] ?? null;
}
