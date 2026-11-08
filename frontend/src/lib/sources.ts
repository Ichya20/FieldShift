import type { SourceEntry } from "./types";

export type DataKind = "public_data" | "model_prediction" | "app_calculation" | "user_input" | "scenario_assumption" | "reference";

export const DATA_KIND: Record<DataKind, string> = {
  public_data: "Data publik",
  model_prediction: "Prediksi model",
  app_calculation: "Perhitungan aplikasi",
  user_input: "Isian pengguna",
  scenario_assumption: "Asumsi skenario",
  reference: "Referensi literatur",
};

interface SourceInfo {
  name: string;
  org: string;
  kind: DataKind;
  url?: string;
  nasa?: boolean;
}

// Display names and attribution. URLs, access times and hashes come from /api/v1/catalog when present.
const SOURCES: Record<string, SourceInfo> = {
  "nasa-power": { name: "NASA POWER, data harian", org: "NASA Langley Research Center, POWER Project", kind: "public_data", nasa: true },
  fao56: { name: "FAO-56 Penman–Monteith (ETo referensi)", org: "FAO", kind: "reference" },
  "climate-manifest": { name: "Manifest iklim FieldShift", org: "Paket data FieldShift", kind: "app_calculation" },
  "modis-terra": {
    name: "MODIS Terra MOD13Q1 (NDVI/EVI 16 hari)",
    org: "NASA, subset melalui ORNL DAAC",
    kind: "public_data",
    url: "https://modis.ornl.gov/data/modis_webservice.html",
    nasa: true,
  },
  "modis-aqua": {
    name: "MODIS Aqua MYD13Q1 (NDVI/EVI 16 hari)",
    org: "NASA, subset melalui ORNL DAAC",
    kind: "public_data",
    url: "https://modis.ornl.gov/data/modis_webservice.html",
    nasa: true,
  },
  "modis-supplement": { name: "Snapshot MODIS tambahan 2021–2026", org: "NASA, subset melalui ORNL DAAC", kind: "public_data", nasa: true },
  "modis-manifest": { name: "Manifest vegetasi FieldShift", org: "Paket data FieldShift", kind: "app_calculation" },
  "soilgrids-native": {
    name: "SoilGrids 250 m (native)",
    org: "ISRIC — World Soil Information",
    kind: "model_prediction",
    url: "https://docs.isric.org/globaldata/soilgrids/",
  },
  "soil-manifest": { name: "Manifest tanah FieldShift", org: "Paket data FieldShift", kind: "app_calculation" },
  "copernicus-dem": {
    name: "Copernicus DEM GLO-30 (DSM)",
    org: "ESA / Program Copernicus",
    kind: "public_data",
    url: "https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM",
  },
  "esa-worldcover-2021": { name: "ESA WorldCover 2021 v200", org: "ESA", kind: "public_data", url: "https://esa-worldcover.org/" },
  "gaez-v5": { name: "FAO GAEZ v5 (2001–2020, AgERA5, HIST)", org: "FAO dan IIASA", kind: "model_prediction", url: "https://gaez.fao.org/" },
  "gaez-six-legend": { name: "Legenda kelas GAEZ v5 (SIX)", org: "FAO", kind: "reference" },
  "gaez-user-guide": { name: "Panduan pengguna GAEZ v5", org: "FAO", kind: "reference" },
  "ecocrop-rice": { name: "FAO ECOCROP · padi", org: "FAO", kind: "reference" },
  "ecocrop-maize": { name: "FAO ECOCROP · jagung", org: "FAO", kind: "reference" },
  "ecocrop-soybean": { name: "FAO ECOCROP · kedelai", org: "FAO", kind: "reference" },
  "fao-seasonal-water": { name: "FAO, Irrigation Water Management: kebutuhan air musiman (Tabel 14)", org: "FAO", kind: "reference" },
  "fao-crop-rotation": { name: "FAO, diversifikasi spesies dan rotasi", org: "FAO", kind: "reference" },
  "fao-paddy-irrigation": { name: "FAO, irigasi padi", org: "FAO", kind: "reference" },
  "fao-aquacrop-inputs": { name: "FAO AquaCrop, kebutuhan input", org: "FAO", kind: "reference" },
  "kementan-inpari32": { name: "Inpari 32 HDB (referensi varietas)", org: "BRMP, Kementerian Pertanian", kind: "reference" },
  "kementan-jakarin": { name: "Jakarin (referensi varietas)", org: "BRMP, Kementerian Pertanian", kind: "reference" },
  "kementan-anjasmoro": { name: "Anjasmoro (referensi varietas)", org: "BPPSDMP, Kementerian Pertanian", kind: "reference" },
  "kementan-variety-catalog-brmp": { name: "Katalog varietas tanaman pangan", org: "BRMP, Kementerian Pertanian", kind: "reference" },
  "analysis-profile": { name: "Profil analisis dan cakupan FieldShift", org: "Paket data FieldShift", kind: "app_calculation" },
  "method-calendar-policy": { name: "Kebijakan kalender metode FieldShift 0.1.0", org: "Metode FieldShift", kind: "app_calculation" },
  "method-accounting-boundary": { name: "Batas perhitungan metode FieldShift", org: "Metode FieldShift", kind: "app_calculation" },
};

export interface ResolvedSource extends SourceInfo {
  id: string;
  accessed?: string;
  sha256?: string;
  path?: string;
}

export function resolveSource(id: string, catalog?: Record<string, SourceEntry>): ResolvedSource {
  const info = SOURCES[id] ?? { name: id, org: "Sumber tercatat", kind: "reference" as DataKind };
  const entry = catalog?.[id];
  return {
    id,
    ...info,
    url: info.url ?? entry?.final_url ?? entry?.url,
    accessed: entry?.accessed_at_utc ?? entry?.retrieved_at_utc ?? entry?.access_date,
    sha256: entry?.sha256,
    path: entry?.path,
  };
}

/** Attribution shown in the closing section; NASA is credited where its data is used, without implying endorsement. */
export const ATTRIBUTION = [
  { id: "nasa-power", role: "Hujan, suhu, dan variabel ETo harian 1991–2026 (konteks regional)." },
  { id: "modis-terra", role: "NDVI/EVI 16 hari pada dua piksel contoh, beserta flag kualitas." },
  { id: "modis-aqua", role: "Seri Aqua dipisahkan dari Terra, tanpa interpolasi." },
  { id: "soilgrids-native", role: "Prediksi sifat tanah 0–100 cm dengan kuantil 5 dan 95." },
  { id: "copernicus-dem", role: "Elevasi dan lereng 30 m dari model permukaan (DSM)." },
  { id: "esa-worldcover-2021", role: "Tutupan lahan 2021 di dalam footprint MODIS." },
  { id: "gaez-v5", role: "Kelas kesesuaian historis per tanaman dan rezim pengelolaan." },
  { id: "fao56", role: "Persamaan ETo referensi untuk indikator P−ETo." },
  { id: "ecocrop-rice", role: "Optimum suhu dan pH spesies padi, jagung, dan kedelai (ECOCROP)." },
  { id: "kementan-inpari32", role: "Referensi umur varietas yang dapat dipilih pengguna." },
];
