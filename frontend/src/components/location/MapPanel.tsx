import { LocateFixed } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type * as Leaflet from "leaflet";
import { EXAMPLE_CENTER, SOIL_TERRAIN_BBOX, footprintPolygon } from "../../lib/geo";
import type { ContextResponse, ResolvedLocation } from "../../lib/types";
import type { Place } from "../../lib/scenario";

type LayerKey = "coverage" | "pixel" | "soil";

const LAYER_LABEL: Record<LayerKey, string> = {
  coverage: "Cakupan data",
  pixel: "Piksel vegetasi",
  soil: "Tanah & medan",
};

const EXAMPLE_NAME: Record<string, string> = {
  klaten_cropland_primary: "Contoh Klaten utama",
  klaten_cropland_candidate: "Contoh Klaten pembanding",
};

interface Props {
  examples: ResolvedLocation[];
  place: Place;
  context: ContextResponse | null;
  onPick: (lat: number, lng: number) => void;
  onSelectExample: (id: "klaten_cropland_primary" | "klaten_cropland_candidate") => void;
}

export function MapPanel({ examples, place, context, onPick, onSelectExample }: Props) {
  const host = useRef<HTMLDivElement>(null);
  const map = useRef<Leaflet.Map | null>(null);
  const L = useRef<typeof Leaflet | null>(null);
  const groups = useRef<Partial<Record<LayerKey | "markers" | "custom", Leaflet.LayerGroup>>>({});
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState<"none" | "tiles" | "library">("none");
  const [layers, setLayers] = useState<Record<LayerKey, boolean>>({ coverage: true, pixel: true, soil: true });
  const latest = useRef({ place, onPick, onSelectExample });
  latest.current = { place, onPick, onSelectExample };

  // Create the map once.
  useEffect(() => {
    let cancelled = false;
    Promise.all([import("leaflet"), import("leaflet/dist/leaflet.css")])
      .then(([module]) => {
        if (cancelled || !host.current) return;
        const leaflet = (module as unknown as { default?: typeof Leaflet }).default ?? (module as unknown as typeof Leaflet);
        L.current = leaflet;
        const instance = leaflet.map(host.current, { center: EXAMPLE_CENTER, zoom: 14, scrollWheelZoom: false, zoomControl: true, attributionControl: true });
        let loaded = 0;
        let errors = 0;
        const tiles = leaflet
          .tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">kontributor OpenStreetMap</a>',
          })
          .addTo(instance);
        tiles.on("tileload", () => {
          loaded += 1;
          if (loaded > 0) setFailed((value) => (value === "tiles" ? "none" : value));
        });
        tiles.on("tileerror", () => {
          errors += 1;
          if (errors >= 4 && loaded === 0) setFailed("tiles");
        });
        leaflet.control.scale({ metric: true, imperial: false, position: "bottomleft" }).addTo(instance);
        instance.attributionControl.setPrefix(false);
        instance.on("click", (event: Leaflet.LeafletMouseEvent) => {
          if (latest.current.place.kind === "custom") latest.current.onPick(event.latlng.lat, event.latlng.lng);
        });
        for (const key of ["coverage", "pixel", "soil", "markers", "custom"] as const) {
          groups.current[key] = leaflet.layerGroup().addTo(instance);
        }
        map.current = instance;
        setReady(true);
      })
      .catch(() => setFailed("library"));
    return () => {
      cancelled = true;
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // Example markers.
  useEffect(() => {
    const leaflet = L.current;
    const group = groups.current.markers;
    if (!ready || !leaflet || !group) return;
    group.clearLayers();
    for (const example of examples) {
      const { latitude, longitude } = example.coordinate;
      if (latitude === null || longitude === null || !example.example_id) continue;
      const selected = place.kind === "example" && place.exampleId === example.example_id;
      const marker = leaflet
        .marker([latitude, longitude], {
          icon: leaflet.divIcon({ className: `map-pin${selected ? " map-pin--selected" : ""}`, iconSize: [18, 18], iconAnchor: [9, 9] }),
          keyboard: true,
          title: EXAMPLE_NAME[example.example_id],
          alt: EXAMPLE_NAME[example.example_id],
        })
        .bindTooltip(EXAMPLE_NAME[example.example_id], {
          permanent: true,
          direction: example.example_id === "klaten_cropland_primary" ? "right" : "left",
          offset: example.example_id === "klaten_cropland_primary" ? [10, 0] : [-10, 0],
          className: "map-label",
        })
        .on("click", () => example.example_id && latest.current.onSelectExample(example.example_id));
      group.addLayer(marker);
    }
  }, [ready, examples, place]);

  // Custom point.
  useEffect(() => {
    const leaflet = L.current;
    const group = groups.current.custom;
    if (!ready || !leaflet || !group) return;
    group.clearLayers();
    if (place.kind === "custom" && place.lat !== null && place.lng !== null) {
      group.addLayer(
        leaflet
          .marker([place.lat, place.lng], { icon: leaflet.divIcon({ className: "map-pin map-pin--custom", iconSize: [18, 18], iconAnchor: [9, 9] }), title: "Titik pilihan" })
          .bindTooltip("Titik pilihan", { permanent: true, direction: "top", offset: [0, -10], className: "map-label" }),
      );
    }
  }, [ready, place]);

  // Coverage layers drawn from the real support of each source.
  useEffect(() => {
    const leaflet = L.current;
    if (!ready || !leaflet) return;
    const { coverage, pixel, soil } = groups.current;
    coverage?.clearLayers();
    pixel?.clearLayers();
    soil?.clearLayers();
    if (layers.soil && soil) {
      soil.addLayer(
        leaflet
          .rectangle(
            [
              [SOIL_TERRAIN_BBOX.south, SOIL_TERRAIN_BBOX.west],
              [SOIL_TERRAIN_BBOX.north, SOIL_TERRAIN_BBOX.east],
            ],
            { color: "#6f5a45", weight: 1.5, dashArray: "6 5", fill: true, fillOpacity: 0.04, interactive: false },
          )
          .bindTooltip("Subset tanah & medan", { sticky: true }),
      );
    }
    const series = context?.layers.vegetation.series ?? [];
    if (layers.pixel && pixel) {
      const seen = new Set<string>();
      for (const s of series) {
        const key = `${s.support.xllcorner}:${s.support.yllcorner}`;
        if (seen.has(key)) continue;
        seen.add(key);
        pixel.addLayer(
          leaflet.polygon(footprintPolygon(s), { color: "#3f5636", weight: 2, fillColor: "#647347", fillOpacity: 0.16, interactive: false }),
        );
      }
    }
    if (layers.coverage && coverage) {
      const cell = context?.layers.gaez.rows[0]?.pixel_bounds;
      if (cell) {
        coverage.addLayer(
          leaflet.rectangle(
            [
              [cell.south, cell.west],
              [cell.north, cell.east],
            ],
            { color: "#526477", weight: 1.5, dashArray: "2 5", fill: false, interactive: false },
          ),
        );
      }
      const power = context?.layers.climate.support.coordinate;
      if (power && power.latitude !== null && power.longitude !== null && context?.location.climate_context_id) {
        coverage.addLayer(
          leaflet
            .marker([power.latitude, power.longitude], { icon: leaflet.divIcon({ className: "map-square", iconSize: [12, 12], iconAnchor: [6, 6] }), interactive: true, title: "Titik konteks iklim POWER" })
            .bindTooltip("Titik konteks iklim regional POWER", { direction: "top" }),
        );
      }
    }
  }, [ready, layers, context]);

  // Follow the selected place.
  useEffect(() => {
    if (!ready || !map.current) return;
    if (place.kind === "example") {
      const example = examples.find((item) => item.example_id === place.exampleId);
      const { latitude, longitude } = example?.coordinate ?? { latitude: null, longitude: null };
      if (latitude !== null && longitude !== null) map.current.panTo([latitude, longitude], { animate: true });
    } else if (place.lat !== null && place.lng !== null) {
      map.current.panTo([place.lat, place.lng]);
    }
  }, [ready, place, examples]);

  if (failed === "library") {
    return (
      <div className="map map--failed" role="status">
        <p>Peta gagal dimuat. Pemilih contoh dan isian koordinat di samping tetap dapat dipakai.</p>
      </div>
    );
  }

  return (
    <div className="map-wrap">
      <div className="map" ref={host} aria-label="Peta lokasi contoh Klaten" role="region" />
      {failed === "tiles" && (
        <p className="map__overlay" role="status">
          Peta dasar gagal dimuat. Titik contoh, cakupan data, dan isian koordinat tetap dapat dipakai.
        </p>
      )}
      {place.kind === "custom" && (
        <p className="map__hint">Klik peta untuk memilih titik, atau isi koordinat.</p>
      )}
      <div className="map__tools">
        <fieldset className="layer-toggles">
          <legend className="visually-hidden">Lapisan peta</legend>
          {(Object.keys(LAYER_LABEL) as LayerKey[]).map((key) => (
            <label key={key} className={`layer-toggle layer-toggle--${key}`}>
              <input type="checkbox" checked={layers[key]} onChange={(event) => setLayers((value) => ({ ...value, [key]: event.target.checked }))} />
              <span className="layer-toggle__swatch" aria-hidden="true" />
              {LAYER_LABEL[key]}
            </label>
          ))}
        </fieldset>
        <button
          type="button"
          className="button button--quiet button--small"
          onClick={() => map.current?.setView(EXAMPLE_CENTER, 14)}
        >
          <LocateFixed aria-hidden="true" size={16} />
          Kembali ke area contoh
        </button>
      </div>
      <dl className="map-legend">
        <div>
          <dt>
            <span className="map-legend__pin" aria-hidden="true" /> Titik contoh
          </dt>
          <dd>Piksel MODIS terpilih, belum terverifikasi sebagai lahan.</dd>
        </div>
        <div>
          <dt>
            <span className="map-legend__pixel" aria-hidden="true" /> Piksel vegetasi
          </dt>
          <dd>Footprint MODIS ±232 m dari respons API; bukan batas petak.</dd>
        </div>
        <div>
          <dt>
            <span className="map-legend__soil" aria-hidden="true" /> Tanah &amp; medan
          </dt>
          <dd>Subset SoilGrids, Copernicus DEM, dan WorldCover (±2 × 2 km).</dd>
        </div>
        <div>
          <dt>
            <span className="map-legend__cell" aria-hidden="true" /> Cakupan data
          </dt>
          <dd>Sel GAEZ 5 arc-menit (±9 km) dan titik iklim regional POWER (110,37; −7,80).</dd>
        </div>
      </dl>
    </div>
  );
}
