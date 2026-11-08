import type { CropId, Priority, RuleId, Status, StrategyId, TimeMode } from "./types";

export type Tone = "info" | "review" | "conflict" | "neutral";

export const STATUS: Record<Status, { label: string; tone: Tone }> = {
  evidence_available: { label: "Bukti tersedia", tone: "info" },
  needs_input: { label: "Perlu informasi", tone: "review" },
  review_required: { label: "Perlu tinjauan", tone: "review" },
  input_conflict: { label: "Ada konflik input", tone: "conflict" },
  outside_coverage: { label: "Di luar cakupan", tone: "neutral" },
  not_applicable: { label: "Tidak berlaku", tone: "neutral" },
  partial: { label: "Analisis sebagian", tone: "neutral" },
  invalid_input: { label: "Periksa isian", tone: "conflict" },
  insufficient_alternatives: { label: "Alternatif belum lengkap", tone: "review" },
  complete_for_selected_checks: { label: "Pemeriksaan terpilih lengkap", tone: "info" },
};

export function statusOf(value: string | null | undefined): { label: string; tone: Tone } {
  return (value && STATUS[value as Status]) || { label: "Status tidak dikenal", tone: "neutral" };
}

export const CROPS: Record<CropId, { name: string; scientific: string; colorVar: string }> = {
  padi: { name: "Padi", scientific: "Oryza sativa", colorVar: "var(--crop-padi)" },
  jagung: { name: "Jagung", scientific: "Zea mays", colorVar: "var(--crop-jagung)" },
  kedelai: { name: "Kedelai", scientific: "Glycine max", colorVar: "var(--crop-kedelai)" },
};

export const CROP_IDS: CropId[] = ["padi", "jagung", "kedelai"];

export const sequenceLabel = (sequence: CropId[] | null | undefined) =>
  sequence && sequence.length ? sequence.map((crop) => CROPS[crop].name).join(" → ") : "Belum ada urutan";

export const STRATEGY_LABEL: Record<StrategyId, string> = {
  existing: "Rotasi berjalan",
  candidate_1: "Alternatif 1",
  candidate_2: "Alternatif 2",
};

export const TIME_MODES: { id: TimeMode; label: string; help: string }[] = [
  { id: "historical_replay", label: "Riwayat historis", help: "Memakai observasi pada tanggal yang dipilih." },
  { id: "recent_partial", label: "Data terbaru parsial", help: "Observasi terbaru dengan jeda pemrosesan; hari yang belum tersedia tetap kosong." },
  {
    id: "historical_analogue_not_forecast",
    label: "Analog historis · bukan prakiraan",
    help: "Statistik tanggal yang sama pada 1991–2020. Ini bukan prakiraan musim.",
  },
];

export const timeModeLabel = (mode: TimeMode | null | undefined) =>
  TIME_MODES.find((item) => item.id === mode)?.label ?? "Mode waktu belum dipilih";

export const RULES: Record<RuleId, { label: string; about: string }> = {
  coverage: { label: "Cakupan data", about: "Dukungan ruang tiap layer pada titik yang dipilih." },
  calendar: { label: "Kalender & jeda", about: "Okupansi petak, jeda persiapan, dan benturan tanggal." },
  climate_exposure: { label: "Paparan hujan & ETo", about: "Hujan, ETo referensi, dan P−ETo selama tanaman menempati petak." },
  ph_reference: { label: "Referensi pH tanah", about: "Prediksi pH dibandingkan dengan optimum spesies." },
  temperature_reference: { label: "Referensi suhu", about: "Rerata suhu jendela tanam dibandingkan dengan optimum spesies." },
  seasonal_et_reference: { label: "Referensi kebutuhan air musiman", about: "Rentang umum ET tanaman dari literatur FAO." },
  paddy_upland_transition: { label: "Transisi padi ke tanaman lahan kering", about: "Rezim air, drainase, dan kontrol air saat padi diganti." },
  legume_mechanism: { label: "Mekanisme legum", about: "Syarat peninjauan fiksasi nitrogen kedelai." },
  pest_break: { label: "Tinjauan siklus hama", about: "Organisme, inang, dan riwayat pengendalian lokal." },
  vegetation_context: { label: "Konteks vegetasi", about: "NDVI/EVI MODIS yang lolos kualitas pada piksel campuran." },
  gaez_context: { label: "Kategori GAEZ historis", about: "Kelas model 2001–2020 per rezim pengelolaan." },
  economics: { label: "Informasi ekonomi · belum dihitung", about: "Harga, biaya, dan hasil belum menjadi bagian MVP." },
};

export const RULE_ORDER: RuleId[] = [
  "coverage",
  "calendar",
  "climate_exposure",
  "ph_reference",
  "temperature_reference",
  "seasonal_et_reference",
  "paddy_upland_transition",
  "legume_mechanism",
  "pest_break",
  "vegetation_context",
  "gaez_context",
  "economics",
];

export const PRIORITIES: { id: Priority; label: string; note?: string; rules: RuleId[] }[] = [
  { id: "water_context", label: "Konteks air", rules: ["climate_exposure", "seasonal_et_reference", "paddy_upland_transition"] },
  { id: "soil_context", label: "Kondisi tanah", rules: ["ph_reference", "legume_mechanism", "paddy_upland_transition"] },
  { id: "pest_management", label: "Pengelolaan hama", rules: ["pest_break"] },
  { id: "calendar_constraints", label: "Kalender tanam", rules: ["calendar"] },
  { id: "economic_information", label: "Informasi ekonomi", note: "Belum dihitung pada MVP", rules: ["economics"] },
];

const MISSING: Record<string, string> = {
  local_pest_or_pathogen: "Organisme pengganggu yang teridentifikasi secara lokal",
  host_range: "Bukti kisaran inang lokal",
  management_history: "Riwayat pengendalian hama",
  management_regime_or_explicit_unknown: "Rezim pengelolaan GAEZ yang sesuai, atau pernyataan belum diketahui",
  marketable_yield: "Hasil panen yang dapat dijual",
  farm_gate_price: "Harga di tingkat petani",
  costs: "Biaya produksi",
  units: "Satuan dan dasar perhitungan",
  time_and_location_basis: "Dasar waktu dan lokasi data ekonomi",
  rice_water_regime: "Rezim air padi",
  drainage: "Kondisi drainase",
  water_control: "Kemampuan mengatur air masuk/keluar",
  soil_management: "Pengelolaan tanah untuk transisi",
  nodulation: "Pengamatan nodulasi kedelai",
  inoculation: "Catatan inokulasi legum",
  residue_fate: "Pengelolaan residu tanaman",
  nutrient_balance: "Neraca hara lokal",
  "location.coordinate": "Koordinat lokasi",
  "location.climate_context_id": "Pilihan konteks iklim regional",
  "context.time_mode": "Mode waktu",
  "calendar.field_occupation_windows": "Kalender okupansi petak yang lengkap",
  historical_temperature_summary: "Ringkasan suhu historis pada jendela tanam",
  crop_calendar: "Kalender tanaman",
  crop_id: "Tanaman",
  sequence: "Urutan tanaman",
  strict_good_observations_in_selected_window: "Observasi MODIS yang lolos kualitas pada periode ini",
  containing_extracted_gaez_cell: "Sel GAEZ yang memuat titik",
  "pH_origin_depth_method_date_or_model_epoch_valid_value": "Nilai pH dengan asal, kedalaman, dan metode",
  nursery_location_ref_unknown: "Lokasi persemaian",
  prep_gap_days: "Jeda persiapan antar musim",
  "previous_calendar.earliest_release_date": "Tanggal petak lepas dari tanaman sebelumnya",
  "previous_calendar.latest_release_date": "Tanggal petak lepas dari tanaman sebelumnya",
  "next_calendar.field_start": "Tanggal mulai tanaman berikutnya",
  "planning.horizon": "Periode perbandingan",
  "planning.horizon.start_date": "Tanggal mulai periode",
  "planning.horizon.end_exclusive": "Tanggal akhir periode",
  "planning.allowed_crop_ids": "Tanaman yang boleh dicoba",
  "planning.excluded_crop_ids": "Tanaman yang dihindari",
  "planning.existing_sequence": "Urutan rotasi berjalan",
  "planning.continuation_confirmed": "Konfirmasi kelanjutan rotasi",
  "planning.locked_prefix_length": "Jumlah slot yang dikunci",
  "planning.slot_start_dates": "Tanggal mulai tiap slot",
};

const SLOT_FIELD: Record<string, string> = {
  production_method: "Metode tanam",
  sowing_date: "Tanggal semai",
  transplanting_date: "Tanggal pindah tanam",
  duration: "Durasi tanaman",
  "duration.min_days": "Durasi minimum",
  "duration.max_days": "Durasi maksimum",
  "duration.basis": "Asal hitung durasi",
  "duration.source_kind": "Jenis sumber durasi",
  "duration.source_id": "Sumber durasi",
  crop_id: "Tanaman",
};

export function missingLabel(code: string): string {
  if (MISSING[code]) return MISSING[code];
  const slot = code.match(/^slot_inputs\[(\d+)\]\.(.+)$/);
  if (slot) return `${SLOT_FIELD[slot[2]] ?? slot[2]} · slot ${Number(slot[1]) + 1}`;
  const start = code.match(/^(?:planning\.)?slot_start_dates\[(\d+)\]$/);
  if (start) return `Tanggal mulai slot ${Number(start[1]) + 1}`;
  if (code.startsWith("farm.soil_lab.")) return `Catatan uji tanah: ${code.slice(14).replace(/_/g, " ")}`;
  if (code.startsWith("planning.")) return MISSING[code] ?? `Rencana: ${code.slice(9).replace(/_/g, " ")}`;
  return code.replace(/_/g, " ");
}

// Backend notes are English method notes; the interface shows them in Indonesian.
const NOTES: Record<string, string> = {
  "Day 0 is the duration origin; endpoints are not averaged.": "Hari ke-0 adalah asal durasi; ujung rentang tidak dirata-ratakan.",
  "Harvest day is occupied; release starts the following day.": "Hari panen masih menempati petak; petak lepas pada hari berikutnya.",
  "This checks the main-field calendar, not agronomic suitability or nursery resource overlap.":
    "Ini memeriksa kalender petak utama, bukan kelayakan agronomi atau benturan sumber daya persemaian.",
  "Nursery location is unknown; no nursery resource assumption was made.": "Lokasi persemaian belum diketahui; tidak ada asumsi sumber daya persemaian.",
  "Sowing-based duration already includes nursery time; no nursery days were added.":
    "Durasi sejak semai sudah mencakup masa persemaian; tidak ada hari persemaian yang ditambahkan.",
  "Incomplete metric coverage; full-window totals remain null.": "Cakupan hari belum lengkap; total periode tetap kosong.",
  "Recent observations retain provider latency and partial coverage; this is not a forecast.":
    "Observasi terbaru memiliki jeda pemrosesan dan cakupan sebagian; ini bukan prakiraan.",
  "No complete historical analogue windows for one or more metrics.": "Tidak ada jendela analog lengkap untuk satu atau lebih metrik.",
  "Public example evidence is not a verified farmer field. Source resolutions and dates differ; no nearest-point fallback or imputation is used.":
    "Bukti publik pada titik contoh bukan lahan petani terverifikasi. Resolusi dan tanggal sumber berbeda; tidak ada pengganti titik terdekat atau imputasi.",
  "Prediction quantiles are not measured field variation. Total nitrogen is not plant-available nitrogen; retention is not current soil moisture.":
    "Kuantil prediksi bukan variasi lapangan terukur. N total bukan N tersedia bagi tanaman; retensi air bukan kelembapan tanah saat ini.",
  "DSM includes buildings and vegetation; derived slopes omit edge cells.": "DSM memuat bangunan dan vegetasi; lereng turunan tidak menghitung sel tepi.",
  "QA excludes cloudy and marginal samples from strict-good means. Collection version is unverified in subset responses.":
    "QA mengecualikan sampel berawan dan marginal dari rerata strict-good. Versi koleksi tidak disebut dalam respons subset.",
  "Historical coarse categorical model classes are not current field suitability or a continuous score.":
    "Kelas kategori model historis yang kasar bukan kesesuaian lahan saat ini atau skor kontinu.",
  "Urutan kandidat tidak menyatakan peringkat agronomi atau manfaat.": "Urutan kandidat tidak menyatakan peringkat agronomi atau manfaat.",
  "Isian dilaporkan pengguna dan belum merupakan verifikasi lapangan.": "Isian dilaporkan pengguna dan belum merupakan verifikasi lapangan.",
};

export const translateNote = (note: string) => NOTES[note] ?? note;

export const GENERATION_ERRORS: Record<string, string> = {
  allowed_excluded_overlap: "Tanaman yang sama tidak bisa sekaligus boleh dicoba dan dihindari.",
  expected_one_to_three_slots: "Rotasi memerlukan satu sampai tiga slot tanaman.",
  invalid_prefix_length: "Jumlah slot terkunci melebihi jumlah slot.",
  empty_or_reversed_horizon: "Periode perbandingan terbalik atau kosong.",
  slot_count_mismatch: "Jumlah tanggal mulai harus sama dengan jumlah slot.",
  slot_start_at_or_after_horizon_end: "Tanggal mulai slot berada pada atau setelah akhir periode.",
  mutable_start_outside_horizon: "Slot yang tidak dikunci harus mulai di dalam periode.",
  dates_not_strictly_increasing: "Tanggal mulai slot harus berurutan dan tidak sama.",
  duplicate_crop_id: "Tanaman tercantum dua kali dalam daftar.",
  unsupported_crop_id: "Tanaman belum didukung.",
};

export const CALENDAR_ISSUES: Record<string, string> = {
  field_start_disagrees_with_slot_start: "Tanggal okupansi berbeda dari tanggal mulai slot.",
  recorded_harvest_outside_duration_range: "Tanggal panen tercatat berada di luar rentang durasi.",
  crop_has_no_occupation_overlap_with_horizon: "Tanaman tidak menempati petak di dalam periode.",
  uncertain_occupation_overlap_with_horizon: "Sebagian rentang panen berada di luar periode.",
  nursery_location_ref_unknown: "Lokasi persemaian belum diketahui.",
  harvest_range_before_field_start: "Rentang panen jatuh sebelum tanaman menempati petak.",
  direct_seeded_has_transplanting_date: "Tanam langsung tidak memakai tanggal pindah tanam.",
  transplanting_before_sowing: "Tanggal pindah tanam lebih awal dari tanggal semai.",
  direct_seeded_cannot_use_transplanting_basis: "Tanam langsung tidak bisa memakai durasi sejak pindah tanam.",
};

export const TRANSITION_STATUS: Record<string, { label: string; tone: Tone }> = {
  no_calendar_conflict: { label: "Tidak ada benturan kalender", tone: "info" },
  potential_calendar_conflict: { label: "Kemungkinan benturan kalender", tone: "review" },
  calendar_conflict: { label: "Benturan okupansi petak", tone: "conflict" },
  needs_input: { label: "Perlu tanggal atau jeda", tone: "review" },
  invalid_input: { label: "Periksa isian kalender", tone: "conflict" },
};

export const RELATION: Record<string, string> = {
  within_reference_optimum: "di dalam optimum referensi",
  outside_reference_optimum_requires_review: "di luar optimum referensi · perlu tinjauan",
  unknown: "belum dapat dibandingkan",
};

export const GAEZ_CROP: Record<string, string> = { RCW: "Padi sawah", MZE: "Jagung", SOY: "Kedelai" };
export const GAEZ_REGIME: Record<string, string> = {
  HRLM: "Tadah hujan · input tinggi",
  HILM: "Irigasi · input tinggi",
};

export const LANDCOVER_CLASS: Record<string, string> = {
  "10": "Tutupan pohon",
  "20": "Semak",
  "30": "Padang rumput",
  "40": "Lahan pertanian",
  "50": "Terbangun",
  "60": "Lahan terbuka",
  "80": "Air permanen",
  "90": "Lahan basah",
};

export const METHOD_LABEL: Record<string, string> = {
  direct_seeded: "Tanam langsung (tabela)",
  transplanted: "Pindah tanam",
};

export const DATE_STATUS_LABEL: Record<string, string> = {
  observed: "Tanggal teramati",
  planned: "Tanggal rencana",
  scenario_assumption: "Asumsi skenario",
};
