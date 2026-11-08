import type { VegetationSeries } from "./types";

const MODIS_RADIUS = 6371007.181;

/** Inverse MODIS sinusoidal projection (sphere R = 6 371 007,181 m). */
export function sinusoidalToLatLng(x: number, y: number): [number, number] {
  const lat = y / MODIS_RADIUS;
  const lon = x / (MODIS_RADIUS * Math.cos(lat));
  return [(lat * 180) / Math.PI, (lon * 180) / Math.PI];
}

/** Corners of the exact MODIS product footprint returned by the backend, as [lat, lng] pairs. */
export function footprintPolygon(series: VegetationSeries): [number, number][] {
  const { xllcorner, yllcorner, cellsize, nrows, ncols } = series.support;
  const x1 = xllcorner + cellsize * ncols;
  const y1 = yllcorner + cellsize * nrows;
  return [
    sinusoidalToLatLng(xllcorner, yllcorner),
    sinusoidalToLatLng(x1, yllcorner),
    sinusoidalToLatLng(x1, y1),
    sinusoidalToLatLng(xllcorner, y1),
  ];
}

// Extraction extent of the SoilGrids/Copernicus/WorldCover subset
// (data/prepared/soil-terrain/summary.json · bbox_soil_terrain_wgs84).
export const SOIL_TERRAIN_BBOX = { west: 110.54, south: -7.73, east: 110.56, north: -7.71 };

export const EXAMPLE_CENTER: [number, number] = [-7.7225, 110.5505];

export function insideBox(lat: number, lng: number, box: { west: number; east: number; south: number; north: number }) {
  return lng >= box.west && lng <= box.east && lat >= box.south && lat <= box.north;
}
