import { ArrowRight, RefreshCw } from "lucide-react";
import { useState } from "react";
import type { ApiError } from "../../lib/api";
import { coord, fmtDate, fmtDateShort, fmtWindow, num, percent, signed } from "../../lib/format";
import { CROPS, GAEZ_CROP, GAEZ_REGIME, LANDCOVER_CLASS, TIME_MODES, timeModeLabel } from "../../lib/labels";
import type { LocationEvidence, Load, ReferenceData } from "../../lib/hooks";
import { PERIODS, type Period } from "../../lib/periods";
import type { Place } from "../../lib/scenario";
import type {
  AnalogueSummary,
  AnyClimateSummary,
  ClimateLayer,
  ClimateMetric,
  ContextResponse,
  CropReference,
  MonthlyClimateResponse,
  Status,
  TimeMode,
} from "../../lib/types";
import { MonthlyBars, PhRange, VegetationPanels, type MonthValue } from "../charts";
import { Disclosure } from "../Disclosure";
import { SourceButton, type EvidenceItem } from "../Evidence";
import { StatusBadge } from "../StatusBadge";
import { MapPanel } from "./MapPanel";
import { PlacePicker, placeLabel } from "./PlacePicker";

interface Props {
  reference: (Load<ReferenceData> & { retry: () => void });
  place: Place;
  onPlace: (place: Place) => void;
  period: Period;
  onPeriod: (period: Period) => void;
  timeMode: TimeMode;
  onTimeMode: (mode: TimeMode) => void;
  evidence: { load: Load<LocationEvidence> | { state: "idle" }; retry: () => void };
  onCompose: () => void;
  onDemo: () => void;
}

const isAnalogue = (summary: AnyClimateSummary | null | undefined): summary is AnalogueSummary =>
  Boolean(summary && summary.mode === "historical_analogue_not_forecast");

function metricValue(summary: AnyClimateSummary | null | undefined, metric: ClimateMetric) {
  if (!summary) return { value: null, low: null, high: null, valid: 0, expected: 0 };
  if (isAnalogue(summary)) {
    const stats = summary.statistics[metric];
    return { value: stats.mean, low: stats.p10, high: stats.p90, valid: stats.count, expected: summary.baseline_end_year - summary.baseline_start_year + 1 };
  }
  return { value: summary[metric], low: undefined, high: undefined, valid: summary.valid_days[metric], expected: summary.days_expected };
}

function ErrorNotice({ error, onRetry }: { error: ApiError; onRetry: () => void }) {
  const unavailable = error.status === 503;
  return (
    <div className="notice notice--conflict" role="alert">
      <div>
        <p>
          <strong>{unavailable ? "Paket data lokal belum tersedia." : "Data belum dapat dimuat. Coba lagi."}</strong>{" "}
          {unavailable
            ? "Layanan berjalan, tetapi paket data tidak lolos pemeriksaan integritas."
            : error.status === 0
              ? "Layanan FieldShift di 127.0.0.1:8000 tidak menjawab."
              : error.message}
        </p>
        <div className="notice__actions">
          <button type="button" className="button button--secondary button--small" onClick={onRetry}>
            <RefreshCw aria-hidden="true" size={16} /> Coba lagi
          </button>
        </div>
      </div>
    </div>
  );
}

export function LocationSection(props: Props) {
  const { reference, place, onPlace, period, onPeriod, timeMode, onTimeMode, evidence, onCompose, onDemo } = props;
  const load = evidence.load;
  const ready = load.state === "ready" ? load.data : null;
  const examples = reference.state === "ready" ? reference.data.locations : [];

  return (
    <section id="kondisi" className="section" aria-labelledby="kondisi-title">
      <div className="container">
        <header className="section-head">
          <h2 id="kondisi-title">Kondisi lokasi</h2>
          <p>Konteks lingkungan untuk meninjau pilihan rotasi. Setiap angka membawa sumber, periode, dan dukungan ruangnya.</p>
        </header>

        <div className="toolbar panel">
          <PlacePicker name="place-main" place={place} onChange={onPlace} />
          <div className="toolbar__group">
            <label className="field">
              <span className="field__label">Periode</span>
              <select
                className="input select"
                value={period.id}
                onChange={(event) => onPeriod(PERIODS.find((item) => item.id === event.target.value) ?? PERIODS[0])}
              >
                {PERIODS.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span className="field__label">Mode waktu</span>
              <select className="input select" value={timeMode} onChange={(event) => onTimeMode(event.target.value as TimeMode)}>
                {TIME_MODES.map((mode) => (
                  <option key={mode.id} value={mode.id}>
                    {mode.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <p className="toolbar__note meta">
            {TIME_MODES.find((mode) => mode.id === timeMode)?.help} Periode {fmtWindow(period.start, period.endExclusive)}.
          </p>
          {period.partial && timeMode === "historical_replay" && (
            <div className="notice notice--review toolbar__wide">
              <div>
                Periode 2026 belum lengkap. Mode “Data terbaru parsial” menampilkan tanggal valid per metrik.
                <div className="notice__actions">
                  <button type="button" className="button button--secondary button--small" onClick={() => onTimeMode("recent_partial")}>
                    Gunakan mode parsial
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {reference.state === "error" && <ErrorNotice error={reference.error} onRetry={reference.retry} />}

        <div className="location-grid">
          <MapPanel
            examples={examples}
            place={place}
            context={ready?.context ?? null}
            onPick={(lat, lng) => onPlace({ kind: "custom", lat, lng, regionalClimate: place.kind === "custom" ? place.regionalClimate : false })}
            onSelectExample={(exampleId) => onPlace({ kind: "example", exampleId })}
          />
          <LocationSummary place={place} load={load} onRetry={evidence.retry} onPlace={onPlace} />
        </div>

        {load.state === "ready" && (
          <>
            <ClimatePanel monthly={load.data.monthly} layer={load.data.context.layers.climate} period={period} timeMode={timeMode} onPlace={onPlace} place={place} />
            <div className="evidence-grid">
              <SoilPanel context={load.data.context} crops={reference.state === "ready" ? reference.data.crops : []} onPlace={onPlace} />
              <VegetationPanel context={load.data.context} period={period} onPlace={onPlace} />
            </div>
            <OtherContext context={load.data.context} onPlace={onPlace} />
          </>
        )}
        {load.state === "loading" && <EvidenceSkeleton />}

        <div className="section-actions">
          <button type="button" className="button button--primary button--large" onClick={onCompose}>
            Susun skenario <ArrowRight aria-hidden="true" size={18} />
          </button>
          <button type="button" className="button button--secondary button--large" onClick={onDemo}>
            Lihat demo perbandingan
          </button>
        </div>
      </div>
    </section>
  );
}

function EvidenceSkeleton() {
  return (
    <div className="evidence-skeleton" aria-busy="true" aria-live="polite">
      <div className="panel">
        <p className="meta">Memuat iklim, tanah, dan vegetasi…</p>
        <div className="skeleton-row">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="skeleton" style={{ height: 64 }} />
          ))}
        </div>
      </div>
    </div>
  );
}

const LAYERS: { key: keyof ContextResponse["layers"]; name: string; source: string }[] = [
  { key: "climate", name: "Iklim regional", source: "NASA POWER" },
  { key: "vegetation", name: "Vegetasi", source: "MODIS Terra & Aqua" },
  { key: "soil", name: "Tanah", source: "SoilGrids" },
  { key: "terrain", name: "Elevasi & lereng", source: "Copernicus DEM" },
  { key: "landcover", name: "Tutupan lahan 2021", source: "ESA WorldCover" },
  { key: "gaez", name: "Kategori GAEZ", source: "FAO GAEZ v5" },
];

function layerSupport(context: ContextResponse, key: keyof ContextResponse["layers"]): string {
  const layers = context.layers;
  switch (key) {
    case "climate":
      return "Grid regional puluhan km, bukan cuaca petak";
    case "vegetation":
      return layers.vegetation.series.length ? "Piksel 250 m campuran, Terra dan Aqua terpisah" : "Tidak ada piksel MODIS yang memuat titik";
    case "soil":
      return "Sel 250 m, prediksi model, bukan uji laboratorium";
    case "terrain":
      return "Sel 30 m, model permukaan (DSM)";
    case "landcover":
      return layers.landcover.footprints.length ? "Di dalam footprint MODIS, kondisi 2021" : "Hanya untuk footprint MODIS contoh";
    case "gaez":
      return "Sel 5 arc-menit (±9 km), model 2001–2020";
  }
}

function LocationSummary({ place, load, onRetry, onPlace }: { place: Place; load: Props["evidence"]["load"]; onRetry: () => void; onPlace: (place: Place) => void }) {
  if (load.state === "idle") {
    return (
      <aside className="panel location-summary">
        <h3>Titik pilihan</h3>
        <p className="meta">Klik peta atau isi lintang dan bujur. Setiap layer diperiksa terpisah; titik di luar cakupan tidak menerima angka titik terdekat.</p>
      </aside>
    );
  }
  if (load.state === "loading") {
    return (
      <aside className="panel location-summary" aria-busy="true">
        <h3>{placeLabel(place)}</h3>
        <p className="meta">Memeriksa ketersediaan layer…</p>
        <ul className="layer-list">
          {LAYERS.map((layer) => (
            <li key={layer.key}>
              <span className="layer-list__name">{layer.name}</span>
              <span className="skeleton" style={{ width: 120, height: 24 }} />
            </li>
          ))}
        </ul>
      </aside>
    );
  }
  if (load.state === "error") {
    return (
      <aside className="panel location-summary">
        <h3>{placeLabel(place)}</h3>
        <ErrorNotice error={load.error} onRetry={onRetry} />
      </aside>
    );
  }
  const context = load.data.context;
  const { latitude, longitude } = context.location.coordinate;
  const footprint = context.layers.landcover.footprints[0];
  return (
    <aside className="panel location-summary" aria-live="polite">
      <div className="location-summary__head">
        <h3>{placeLabel(place)}</h3>
        <p className="num location-summary__coord">
          {coord(latitude)}; {coord(longitude)}
        </p>
        <p className="meta">Presisi grid, bukan GPS petak.</p>
        <span className="tag">{context.location.example_id ? "Lokasi contoh · belum terverifikasi sebagai lahan" : "Titik pengguna · belum terverifikasi sebagai lahan"}</span>
        {footprint && (
          <p className="meta">
            Tutupan lahan 2021 di dalam piksel MODIS: {percent(footprint.stats.cropland_fraction_valid_cells)} lahan pertanian, piksel campuran.
          </p>
        )}
      </div>
      <ul className="layer-list">
        {LAYERS.map((layer) => {
          const value = context.layers[layer.key];
          return (
            <li key={layer.key}>
              <div className="layer-list__text">
                <span className="layer-list__name">
                  {layer.name} <span className="layer-list__source">· {layer.source}</span>
                </span>
                <span className="meta">{layerSupport(context, layer.key)}</span>
              </div>
              <div className="layer-list__state">
                <StatusBadge status={value.status} compact />
                <SourceButton
                  item={{
                    title: `${layer.name} · ${layer.source}`,
                    kind: layer.key === "soil" || layer.key === "gaez" ? "model_prediction" : "public_data",
                    sourceRefs: value.source_refs,
                    period: layer.key === "climate" ? fmtWindow(context.window?.start_date ?? "", context.window?.end_exclusive ?? "") : undefined,
                    support: layerSupport(context, layer.key),
                    limitations: "warnings" in value ? (value.warnings as string[]) : undefined,
                  }}
                />
              </div>
            </li>
          );
        })}
      </ul>
      {context.location.example_id === null && Object.values(context.layers).some((layer) => layer.status === "outside_coverage") && (
        <div className="notice">
          <div>
            Sebagian layer di luar cakupan titik ini. Angka dari titik lain tidak dipakai sebagai pengganti.
            <div className="notice__actions">
              <button type="button" className="button button--secondary button--small" onClick={() => onPlace({ kind: "example", exampleId: "klaten_cropland_primary" })}>
                Buka contoh Klaten
              </button>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}

function OutsideCoverage({ text, onPlace }: { text: string; onPlace: (place: Place) => void }) {
  return (
    <div className="empty-state">
      <p>{text}</p>
      <button type="button" className="button button--secondary button--small" onClick={() => onPlace({ kind: "example", exampleId: "klaten_cropland_primary" })}>
        Buka contoh Klaten
      </button>
    </div>
  );
}

function ClimatePanel({
  monthly,
  layer,
  period,
  timeMode,
  place,
  onPlace,
}: {
  monthly: MonthlyClimateResponse;
  layer: ClimateLayer;
  period: Period;
  timeMode: TimeMode;
  place: Place;
  onPlace: (place: Place) => void;
}) {
  const summary = layer.summary;
  const analogue = isAnalogue(summary);
  const periodText = fmtWindow(period.start, period.endExclusive);
  const base: Omit<EvidenceItem, "title"> = {
    kind: "public_data",
    sourceRefs: layer.source_refs,
    period: analogue ? `${periodText}, dipetakan ke 1991–2020` : periodText,
    support: "Satu titik grid POWER (110,37; −7,80) mewakili wilayah puluhan km",
    limitations: layer.warnings,
  };
  const metrics: { key: ClimateMetric; label: string; unit: string; help?: string; signed?: boolean; method?: string }[] = [
    { key: "rainfall_total_mm", label: "Hujan regional", unit: "mm" },
    { key: "reference_eto_total_mm", label: "ETo referensi", unit: "mm", method: "FAO-56 Penman–Monteith dari variabel POWER harian" },
    {
      key: "rain_minus_reference_eto_total_mm",
      label: "Selisih P−ETo",
      unit: "mm",
      signed: true,
      help: "Selisih hujan dan ETo referensi; bukan kebutuhan irigasi.",
      method: "Hujan dikurangi ETo referensi pada hari yang sama-sama valid",
    },
    { key: "temperature_mean_c", label: "Suhu rerata", unit: "°C" },
  ];

  const series = (metric: ClimateMetric): MonthValue[] =>
    monthly.months.map((month) => {
      const value = metricValue(month.summary, metric);
      return { month: `${month.month}-01`, value: value.value, low: value.low, high: value.high, valid: value.valid, expected: value.expected };
    });

  const latest = monthly.latest_valid_dates;
  return (
    <Disclosure
      className="climate-panel"
      defaultOpen
      title={
        <>
          Iklim regional <span className="disclosure__source">· NASA POWER</span>
        </>
      }
      status={<StatusBadge status={layer.status} compact />}
      meta={
        <p className="meta">
          {timeModeLabel(timeMode)} · {analogue ? `statistik tanggal yang sama 1991–2020, ${summary.counts_by_metric.rainfall_total_mm} tahun lengkap` : periodText} · konteks regional, bukan cuaca petak.
        </p>
      }
    >
      {layer.status === "needs_input" ? (
        <div className="empty-state">
          <p>Titik pilihan belum memakai konteks iklim. Konteks POWER hanya dipakai bila dipilih secara eksplisit.</p>
          {place.kind === "custom" && (
            <button type="button" className="button button--secondary button--small" onClick={() => onPlace({ ...place, regionalClimate: true })}>
              Gunakan konteks iklim regional Yogyakarta
            </button>
          )}
        </div>
      ) : (
        <>
          <dl className="metric-strip">
            {metrics.map((metric) => {
              const value = metricValue(summary, metric.key);
              const text = metric.signed ? signed(value.value, 2) : num(value.value, metric.key === "temperature_mean_c" ? 2 : 2);
              const complete = value.value !== null;
              return (
                <div key={metric.key} className="metric">
                  <dt>{metric.label}</dt>
                  <dd>
                    <span className="metric__value num">
                      {complete ? text : "Belum lengkap"}
                      {complete && <span className="metric__unit"> {metric.unit}</span>}
                    </span>
                    <span className="meta num">
                      {analogue
                        ? `Rerata ${value.valid} tahun · P10–P90 ${num(value.low, 1)}–${num(value.high, 1)}`
                        : `${value.valid}/${value.expected} hari valid`}
                    </span>
                    {latest && !complete && latest[metric.key] && <span className="meta">Valid sampai {fmtDate(latest[metric.key])}</span>}
                    {metric.help && <span className="metric__help">{metric.help}</span>}
                    <SourceButton
                      item={{
                        ...base,
                        title: metric.label,
                        value: complete ? `${text} ${metric.unit}` : "Belum lengkap",
                        kind: metric.method ? "app_calculation" : "public_data",
                        method: metric.method,
                        validity: analogue ? `${value.valid} tahun analog lengkap` : `${value.valid}/${value.expected} hari valid`,
                      }}
                    />
                  </dd>
                </div>
              );
            })}
          </dl>
          <div className="chart-pair">
            <MonthlyBars
              title={analogue ? "Hujan bulanan, rerata analog (mm)" : "Hujan bulanan (mm)"}
              unit="mm"
              tone="rain"
              values={series("rainfall_total_mm")}
              rangeLabel={analogue ? "Garis: rentang P10–P90 antar tahun analog. Bukan prakiraan." : undefined}
            />
            <MonthlyBars
              title={analogue ? "ETo referensi bulanan, rerata analog (mm)" : "ETo referensi bulanan (mm)"}
              unit="mm"
              tone="eto"
              values={series("reference_eto_total_mm")}
              rangeLabel={analogue ? "Garis: rentang P10–P90 antar tahun analog. Bukan prakiraan." : undefined}
            />
          </div>
          {latest && Object.values(latest).some(Boolean) && timeMode === "recent_partial" && (
            <p className="meta">
              Tanggal valid terakhir: hujan {fmtDateShort(latest.rainfall_total_mm)}, ETo {fmtDateShort(latest.reference_eto_total_mm)}, suhu{" "}
              {fmtDateShort(latest.temperature_mean_c)}. Hari setelahnya tetap kosong.
            </p>
          )}
        </>
      )}
    </Disclosure>
  );
}

function SoilPanel({ context, crops, onPlace }: { context: ContextResponse; crops: CropReference[]; onPlace: (place: Place) => void }) {
  const soil = context.layers.soil;
  const ph = soil.ph_0_5cm;
  const prop = (name: string) => soil.properties.find((p) => p.property === name && p.depth === "0-5cm" && p.statistic === "mean");
  const texture = ["sand", "silt", "clay"].map(prop);
  const soc = prop("soc");
  const cec = prop("cec");
  return (
    <Disclosure
      title={
        <>
          Tanah <span className="disclosure__source">· Prediksi SoilGrids</span>
        </>
      }
      status={<StatusBadge status={soil.status} compact />}
      meta={<p className="meta">Sel 250 m pada koordinat titik, tanpa pengganti titik terdekat. Bukan hasil uji laboratorium.</p>}
    >
      {ph.value === null ? (
        soil.status === "outside_coverage" ? (
          <OutsideCoverage text="Data tanah belum tersedia untuk titik ini." onPlace={onPlace} />
        ) : (
          <p className="meta">Nilai pH pada sel ini tidak valid (nodata sumber) dan tidak diganti.</p>
        )
      ) : (
        <>
          <div className="big-figure">
            <p className="big-figure__value num">
              pH {num(ph.value, 1)} <span className="big-figure__unit">kedalaman 0–5 cm</span>
            </p>
            <p className="meta num">
              Rentang prediksi Q05–Q95: {num(ph.q05, 1)}–{num(ph.q95, 1)}
            </p>
          </div>
          <PhRange
            value={ph.value}
            q05={ph.q05}
            q95={ph.q95}
            optima={crops.map((crop) => ({ label: `Optimum ${CROPS[crop.crop_id].name.toLowerCase()}`, min: crop.species_soil_ph_optimum.min, max: crop.species_soil_ph_optimum.max }))}
          />
          <p className="meta">Optimum spesies dari FAO ECOCROP. Berada di luar optimum tidak membuktikan kegagalan tanaman.</p>
          <dl className="mini-facts num">
            {texture.every(Boolean) && (
              <div>
                <dt>Tekstur 0–5 cm</dt>
                <dd>
                  Pasir {num(texture[0]!.value, 0)}% · Debu {num(texture[1]!.value, 0)}% · Liat {num(texture[2]!.value, 0)}%
                </dd>
              </div>
            )}
            {soc && (
              <div>
                <dt>Karbon organik</dt>
                <dd>{num(soc.value, 1)} g/kg</dd>
              </div>
            )}
            {cec && (
              <div>
                <dt>KTK</dt>
                <dd>{num(cec.value, 1)} cmol(c)/kg</dd>
              </div>
            )}
          </dl>
          <SourceButton
            item={{
              title: "pH tanah 0–5 cm",
              value: `pH ${num(ph.value, 1)} · Q05–Q95 ${num(ph.q05, 1)}–${num(ph.q95, 1)}`,
              kind: "model_prediction",
              sourceRefs: soil.source_refs,
              support: "Sel native 250 m yang memuat koordinat, dengan mask sumber",
              limitations: soil.warnings,
            }}
          />
        </>
      )}
    </Disclosure>
  );
}

function VegetationPanel({ context, period, onPlace }: { context: ContextResponse; period: Period; onPlace: (place: Place) => void }) {
  const [index, setIndex] = useState<"ndvi" | "evi">("ndvi");
  const vegetation = context.layers.vegetation;
  const window = context.window ?? { start_date: period.start, end_exclusive: period.endExclusive };
  return (
    <Disclosure
      title={
        <>
          Vegetasi <span className="disclosure__source">· MODIS Terra &amp; Aqua</span>
        </>
      }
      status={<StatusBadge status={vegetation.status} compact />}
      meta={<p className="meta">Komposit 16 hari. Grafik hanya memakai observasi yang lolos kualitas (strict-good); tidak diinterpolasi.</p>}
    >
      {vegetation.series.length === 0 ? (
        <OutsideCoverage text="Seri vegetasi hanya tersedia untuk dua piksel contoh Klaten." onPlace={onPlace} />
      ) : (
        <>
          <div className="veg__controls">
            <fieldset className="mini-toggle">
              <legend className="visually-hidden">Indeks vegetasi</legend>
              {(["ndvi", "evi"] as const).map((value) => (
                <label key={value}>
                  <input type="radio" name="veg-index" checked={index === value} onChange={() => setIndex(value)} />
                  <span>{value.toUpperCase()}</span>
                </label>
              ))}
            </fieldset>
            <p className="veg__legend meta">
              <span className="veg__key veg__key--terra" aria-hidden="true" /> Terra
              <span className="veg__key veg__key--aqua" aria-hidden="true" /> Aqua
              <span className="veg__key veg__key--gap" aria-hidden="true" /> Tidak ada observasi yang lolos kualitas
            </p>
          </div>
          <VegetationPanels series={vegetation.series} start={window.start_date} endExclusive={window.end_exclusive} index={index} />
          <p className="caption">Piksel campuran; jenis tanaman dan tanggal tanam tidak dapat disimpulkan dari grafik ini.</p>
          <SourceButton
            item={{
              title: "Vegetasi MODIS (NDVI/EVI)",
              kind: "public_data",
              sourceRefs: vegetation.source_refs,
              period: fmtWindow(window.start_date, window.end_exclusive),
              support: "Footprint piksel MODIS ±232 m, tutupan lahan campuran",
              validity: vegetation.series.map((s) => `${s.platform}: ${s.summary.n_good_strict}/${s.summary.n_selected_observations} komposit lolos kualitas`).join(" · "),
              limitations: vegetation.warnings,
            }}
          />
        </>
      )}
    </Disclosure>
  );
}

function OtherContext({ context, onPlace }: { context: ContextResponse; onPlace: (place: Place) => void }) {
  const { terrain, landcover, gaez } = context.layers;
  const footprint = landcover.footprints[0];
  const histogram = footprint ? Object.entries(footprint.stats.class_histogram).sort((a, b) => b[1].cells - a[1].cells) : [];
  const status: Status = [terrain.status, landcover.status, gaez.status].includes("outside_coverage") ? "review_required" : "evidence_available";
  return (
    <Disclosure title="Medan, tutupan lahan, dan kategori GAEZ" status={<StatusBadge status={status} compact label="Tinjau per layer" />} className="other-context">
      <div className="divided-row">
        <section>
          <h4>Elevasi &amp; lereng</h4>
          {terrain.status === "outside_coverage" ? (
            <OutsideCoverage text="Data medan belum tersedia untuk titik ini." onPlace={onPlace} />
          ) : (
            <>
              <p className="figure num">
                {num(terrain.elevation_m.value, 1)} <span>m</span>
              </p>
              <p className="meta num">Lereng {num(terrain.slope_degrees.value, 1)}° · sel 30 m</p>
              <p className="meta">Copernicus DEM GLO-30 adalah model permukaan; bangunan dan kanopi dapat memengaruhi nilai.</p>
              <SourceButton
                item={{
                  title: "Elevasi dan lereng",
                  value: `${num(terrain.elevation_m.value, 1)} m · lereng ${num(terrain.slope_degrees.value, 1)}°`,
                  kind: "public_data",
                  sourceRefs: terrain.source_refs,
                  support: "Sel 30 m pada proyeksi UTM 49S",
                  limitations: terrain.warnings,
                }}
              />
            </>
          )}
        </section>
        <section>
          <h4>Tutupan lahan 2021</h4>
          {footprint ? (
            <>
              <ul className="share-list num">
                {histogram.map(([code, entry]) => (
                  <li key={code}>
                    <span>{LANDCOVER_CLASS[code] ?? entry.label}</span>
                    <span>{percent(entry.cells / footprint.stats.valid_cells)}</span>
                  </li>
                ))}
              </ul>
              <p className="meta">Di dalam footprint MODIS Terra; bukan batas petak atau kondisi saat ini.</p>
              <SourceButton
                item={{
                  title: "Tutupan lahan ESA WorldCover 2021",
                  kind: "public_data",
                  sourceRefs: landcover.source_refs,
                  period: "2021",
                  support: `${footprint.stats.valid_cells} sel 10 m di dalam footprint MODIS`,
                }}
              />
            </>
          ) : (
            <OutsideCoverage text="Tutupan lahan dihitung hanya di dalam footprint piksel contoh." onPlace={onPlace} />
          )}
        </section>
        <section>
          <h4>Kategori GAEZ historis</h4>
          {gaez.rows.length ? (
            <>
              <table className="mini-table gaez-table">
                <thead>
                  <tr>
                    <th scope="col">Tanaman</th>
                    <th scope="col">{GAEZ_REGIME.HRLM}</th>
                    <th scope="col">{GAEZ_REGIME.HILM}</th>
                  </tr>
                </thead>
                <tbody>
                  {(["RCW", "MZE", "SOY"] as const).map((code) => {
                    const cell = (regime: "HRLM" | "HILM") => gaez.rows.find((row) => row.crop_code === code && row.regime === regime);
                    return (
                      <tr key={code}>
                        <th scope="row">{GAEZ_CROP[code]}</th>
                        {(["HRLM", "HILM"] as const).map((regime) => {
                          const row = cell(regime);
                          return (
                            <td key={regime}>
                              {row ? (
                                <>
                                  {row.class_label.replace(/^SI\s*/, "SI ").replace(/\s*:\s*/, ": ")}
                                  <span className="meta"> · kelas {row.class_code}</span>
                                </>
                              ) : (
                                "—"
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              <p className="meta">Kategori model 2001–2020, bukan skor kesesuaian atau hasil lahan sekarang.</p>
              <SourceButton
                item={{
                  title: "Kategori GAEZ v5",
                  kind: "model_prediction",
                  sourceRefs: gaez.source_refs,
                  period: `${gaez.support.period} · ${gaez.support.climate} · ${gaez.support.scenario}`,
                  support: "Sel 5 arc-menit yang memuat titik",
                  limitations: gaez.warnings,
                }}
              />
            </>
          ) : (
            <OutsideCoverage text="Kategori GAEZ belum diekstrak untuk titik ini." onPlace={onPlace} />
          )}
        </section>
      </div>
    </Disclosure>
  );
}
