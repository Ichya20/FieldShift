import { useEffect, useState } from "react";
import type { Place } from "../../lib/scenario";

const OPTIONS = [
  { id: "klaten_cropland_primary", label: "Contoh Klaten utama" },
  { id: "klaten_cropland_candidate", label: "Contoh Klaten pembanding" },
  { id: "custom", label: "Pilih titik sendiri" },
] as const;

export const PLACE_LABEL: Record<string, string> = {
  klaten_cropland_primary: "Contoh Klaten utama",
  klaten_cropland_candidate: "Contoh Klaten pembanding",
  custom: "Titik pilihan",
};

export function placeLabel(place: Place) {
  return place.kind === "example" ? PLACE_LABEL[place.exampleId] : "Titik pilihan";
}

function parseCoordinate(text: string, min: number, max: number): number | null {
  const normalized = text.trim().replace(",", ".").replace("\u2212", "-");
  if (!/^-?\d+(\.\d+)?$/.test(normalized)) return null;
  const value = Number(normalized);
  return value >= min && value <= max ? value : null;
}

interface Props {
  name: string;
  place: Place;
  onChange: (place: Place) => void;
  compact?: boolean;
}

export function PlacePicker({ name, place, onChange, compact = false }: Props) {
  const current = place.kind === "example" ? place.exampleId : "custom";
  const [lat, setLat] = useState(place.kind === "custom" && place.lat !== null ? String(place.lat) : "");
  const [lng, setLng] = useState(place.kind === "custom" && place.lng !== null ? String(place.lng) : "");

  useEffect(() => {
    if (place.kind === "custom") {
      setLat(place.lat !== null ? String(Number(place.lat.toFixed(6))) : "");
      setLng(place.lng !== null ? String(Number(place.lng.toFixed(6))) : "");
    }
  }, [place]);

  const latValue = parseCoordinate(lat, -90, 90);
  const lngValue = parseCoordinate(lng, -180, 180);

  const commit = (nextLat: string, nextLng: string, regional: boolean) => {
    onChange({ kind: "custom", lat: parseCoordinate(nextLat, -90, 90), lng: parseCoordinate(nextLng, -180, 180), regionalClimate: regional });
  };

  return (
    <div className={`place-picker${compact ? " place-picker--compact" : ""}`}>
      <fieldset className="choice-row">
        <legend className="field__label">Lokasi</legend>
        <div className="choice-row__options">
          {OPTIONS.map((option) => (
            <label key={option.id} className="choice">
              <input
                type="radio"
                name={name}
                value={option.id}
                checked={current === option.id}
                onChange={() => {
                  if (option.id === "custom") onChange({ kind: "custom", lat: latValue, lng: lngValue, regionalClimate: place.kind === "custom" ? place.regionalClimate : false });
                  else onChange({ kind: "example", exampleId: option.id });
                }}
              />
              <span>{option.label}</span>
            </label>
          ))}
        </div>
      </fieldset>
      {place.kind === "custom" && (
        <div className="custom-point" id={`${name}-custom`}>
          <div className="field-pair">
            <label className="field">
              <span className="field__label">Lintang (desimal)</span>
              <input
                className="input"
                inputMode="decimal"
                placeholder="−7,7219"
                value={lat}
                aria-invalid={lat !== "" && latValue === null}
                onChange={(event) => setLat(event.target.value)}
                onBlur={() => commit(lat, lng, place.regionalClimate)}
              />
            </label>
            <label className="field">
              <span className="field__label">Bujur (desimal)</span>
              <input
                className="input"
                inputMode="decimal"
                placeholder="110,5535"
                value={lng}
                aria-invalid={lng !== "" && lngValue === null}
                onChange={(event) => setLng(event.target.value)}
                onBlur={() => commit(lat, lng, place.regionalClimate)}
              />
            </label>
          </div>
          <p className="field__hint">Contoh format: lintang −7,7219 dan bujur 110,5535. Lintang selatan bernilai negatif.</p>
          <label className="check">
            <input
              type="checkbox"
              checked={place.regionalClimate}
              onChange={(event) => onChange({ ...place, regionalClimate: event.target.checked })}
            />
            <span>
              Gunakan konteks iklim regional Yogyakarta
              <small>Titik NASA POWER mewakili grid puluhan kilometer; bukan cuaca petak di titik ini.</small>
            </span>
          </label>
        </div>
      )}
    </div>
  );
}
