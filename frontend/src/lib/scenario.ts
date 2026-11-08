import { addDays, daysBetween, isIsoDate } from "./dates";
import { DEMO } from "./demo";
import type { CompareRequestBody, CropId, InputKind, LocationBody, Priority, SlotInputBody, TimeMode } from "./types";
import { CROP_IDS, CROPS } from "./labels";

// ---- Place shared by "Kondisi lokasi" and the scenario form -----------------

export type Place =
  | { kind: "example"; exampleId: "klaten_cropland_primary" | "klaten_cropland_candidate" }
  | { kind: "custom"; lat: number | null; lng: number | null; regionalClimate: boolean };

export function placeToLocation(place: Place): LocationBody | null {
  if (place.kind === "example") return { example_id: place.exampleId };
  if (place.lat === null || place.lng === null) return null;
  return {
    longitude: place.lng,
    latitude: place.lat,
    ...(place.regionalClimate ? { climate_context_id: "power_regional_yogyakarta" as const } : {}),
  };
}

// ---- Form state ----------------------------------------------------------------

export type Method = "direct_seeded" | "transplanted";
export type DateStatus = "observed" | "planned" | "scenario_assumption";
export type RiceEcosystem = "irrigated_lowland" | "rainfed_lowland" | "rainfed_upland" | "flood_prone";
export type RiceWaterRegime = "flooded_paddy" | "intermittently_flooded_paddy" | "nonflooded_aerobic" | "mixed_or_variable" | "other_documented";

export interface SlotForm {
  key: string;
  cropId: CropId | "";
  method: Method | "";
  sowingDate: string;
  transplantingDate: string;
  harvestDate: string;
  dateStatus: DateStatus | "";
  nursery: "separate" | "main_field" | "";
  riceEcosystem: RiceEcosystem | "";
  riceWaterRegime: RiceWaterRegime | "";
}

export interface DurationForm {
  min: string;
  max: string;
  basis: "sowing" | "transplanting" | "";
  source: string;
  referenceId: string | null;
  originWording: string;
  cultivar: string;
}

export type AdvancedKey =
  | "pest_disease_weed_history"
  | "local_host_range_evidence"
  | "pesticide_history"
  | "soil_management_for_transition"
  | "residue_fate"
  | "legume_inoculation"
  | "nodulation_observations"
  | "nutrient_balance";

export interface AdvancedEntry {
  state: "unknown" | "none" | "note";
  note: string;
}

export interface ScenarioForm {
  inputKind: InputKind | "";
  assumptions: string;
  start: string;
  endInclusive: string;
  timeMode: TimeMode | "";
  slots: SlotForm[];
  continuationConfirmed: boolean;
  lockedPrefix: number;
  cropPolicy: Record<CropId, "allowed" | "excluded" | "">;
  durations: Record<CropId, DurationForm>;
  prepGap: string;
  sharedCalendar: boolean;
  sharedCalendarNote: string;
  irrigationSystem: "" | "none" | "surface" | "sprinkler" | "drip" | "mixed" | "other_documented";
  rainfed: "" | "yes" | "no";
  drainage: "" | "good_reported" | "poor_reported" | "variable_reported" | "other_documented";
  waterControl: "" | "can_supply_and_drain_reported" | "supply_only_reported" | "drain_only_reported" | "no_control_reported" | "other_documented";
  priorities: Priority[];
  advanced: Record<AdvancedKey, AdvancedEntry>;
}

let slotCounter = 0;
export const newSlot = (): SlotForm => ({
  key: `slot-${++slotCounter}`,
  cropId: "",
  method: "",
  sowingDate: "",
  transplantingDate: "",
  harvestDate: "",
  dateStatus: "",
  nursery: "",
  riceEcosystem: "",
  riceWaterRegime: "",
});

const emptyDuration = (): DurationForm => ({ min: "", max: "", basis: "", source: "", referenceId: null, originWording: "", cultivar: "" });

export const ADVANCED: { key: AdvancedKey; label: string; rule: string }[] = [
  { key: "pest_disease_weed_history", label: "Riwayat hama, penyakit, atau gulma", rule: "Tinjauan siklus hama" },
  { key: "local_host_range_evidence", label: "Bukti kisaran inang lokal", rule: "Tinjauan siklus hama" },
  { key: "pesticide_history", label: "Riwayat pengendalian atau pestisida", rule: "Tinjauan siklus hama" },
  { key: "soil_management_for_transition", label: "Pengelolaan tanah saat beralih dari padi", rule: "Transisi padi ke lahan kering" },
  { key: "residue_fate", label: "Pengelolaan residu tanaman", rule: "Mekanisme legum" },
  { key: "legume_inoculation", label: "Inokulasi kedelai", rule: "Mekanisme legum" },
  { key: "nodulation_observations", label: "Pengamatan nodulasi kedelai", rule: "Mekanisme legum" },
  { key: "nutrient_balance", label: "Neraca hara lokal", rule: "Mekanisme legum" },
];

export function initialForm(period: { start: string; endExclusive: string }, timeMode: TimeMode): ScenarioForm {
  return {
    inputKind: "",
    assumptions: "",
    start: period.start,
    endInclusive: addDays(period.endExclusive, -1),
    timeMode,
    slots: [newSlot()],
    continuationConfirmed: false,
    lockedPrefix: 0,
    cropPolicy: { padi: "", jagung: "", kedelai: "" },
    durations: { padi: emptyDuration(), jagung: emptyDuration(), kedelai: emptyDuration() },
    prepGap: "",
    sharedCalendar: false,
    sharedCalendarNote: "",
    irrigationSystem: "",
    rainfed: "",
    drainage: "",
    waterControl: "",
    priorities: [],
    advanced: Object.fromEntries(ADVANCED.map(({ key }) => [key, { state: "unknown", note: "" }])) as Record<AdvancedKey, AdvancedEntry>,
  };
}

export function demoForm(): ScenarioForm {
  const slot = (start: string): SlotForm => ({
    ...newSlot(),
    cropId: "padi",
    method: "direct_seeded",
    sowingDate: start,
    dateStatus: "scenario_assumption",
  });
  const duration = (crop: CropId): DurationForm => ({
    min: String(DEMO.durations[crop]),
    max: String(DEMO.durations[crop]),
    basis: "sowing",
    source: `demo-assumed-duration-${crop}`,
    referenceId: null,
    originWording: "",
    cultivar: "",
  });
  return {
    ...initialForm({ start: DEMO.horizonStart, endExclusive: DEMO.horizonEndExclusive }, "historical_replay"),
    inputKind: "scenario_assumption",
    assumptions: DEMO.assumptions.join("\n"),
    slots: DEMO.slotStarts.map(slot),
    continuationConfirmed: true,
    lockedPrefix: 1,
    cropPolicy: { padi: "allowed", jagung: "allowed", kedelai: "allowed" },
    durations: { padi: duration("padi"), jagung: duration("jagung"), kedelai: duration("kedelai") },
    prepGap: String(DEMO.prepGapDays),
    sharedCalendar: true,
    sharedCalendarNote: DEMO.sharedCalendarNote,
  };
}

/** True when the user has typed or chosen anything beyond the period defaults. */
export function hasEntries(form: ScenarioForm): boolean {
  const slotTouched = form.slots.some((s) => s.cropId || s.method || s.sowingDate || s.transplantingDate || s.harvestDate || s.dateStatus);
  const durationTouched = CROP_IDS.some((crop) => {
    const d = form.durations[crop];
    return d.min || d.max || d.basis || d.source;
  });
  return Boolean(
    form.inputKind ||
      form.assumptions.trim() ||
      slotTouched ||
      form.slots.length > 1 ||
      durationTouched ||
      form.prepGap ||
      form.continuationConfirmed ||
      form.sharedCalendar ||
      form.irrigationSystem ||
      form.rainfed ||
      form.drainage ||
      form.waterControl ||
      form.priorities.length ||
      CROP_IDS.some((crop) => form.cropPolicy[crop]) ||
      Object.values(form.advanced).some((entry) => entry.state !== "unknown"),
  );
}

export function fieldStart(slot: SlotForm): string | null {
  if (slot.method === "direct_seeded") return slot.sowingDate || null;
  if (slot.method === "transplanted") return slot.transplantingDate || null;
  return null;
}

// ---- Validation and request ---------------------------------------------------

export type Step = 1 | 2 | 3;

export interface FormIssue {
  field: string;
  step: Step;
  message: string;
}

const positiveInt = (value: string, min: number, max: number) => /^\d+$/.test(value) && Number(value) >= min && Number(value) <= max;

export function validate(form: ScenarioForm, place: Place): FormIssue[] {
  const issues: FormIssue[] = [];
  const add = (field: string, step: Step, message: string) => issues.push({ field, step, message });

  if (place.kind === "custom" && (place.lat === null || place.lng === null)) {
    add("place-custom", 1, "Isi koordinat titik atau pilih contoh Klaten.");
  }
  if (!form.inputKind) add("input-kind", 1, "Pilih jenis isian: skenario asumsi atau isian pengguna.");
  if (form.inputKind === "scenario_assumption" && !assumptionLines(form).length) {
    add("assumptions", 1, "Skenario asumsi perlu catatan asumsi yang digunakan.");
  }
  const start = isIsoDate(form.start);
  const end = isIsoDate(form.endInclusive);
  if (!start) add("period-start", 1, "Isi tanggal mulai periode dengan format yang valid.");
  if (!end) add("period-end", 1, "Isi tanggal akhir periode dengan format yang valid.");
  if (start && end) {
    const span = daysBetween(form.start, addDays(form.endInclusive, 1));
    if (span <= 0) add("period-end", 1, "Tanggal akhir harus sama dengan atau sesudah tanggal mulai.");
    else if (span > 3660) add("period-end", 1, "Periode paling panjang 3.660 hari.");
    const years = [form.start, form.endInclusive].map((iso) => Number(iso.slice(0, 4)));
    if (years.some((year) => year < 1900 || year > 2099)) add("period-start", 1, "Tanggal harus berada pada 1900–2099.");
  }

  const cropped = form.slots.filter((slot) => slot.cropId);
  if (cropped.length && cropped.length !== form.slots.length) {
    form.slots.forEach((slot, index) => {
      if (!slot.cropId) add(`slot-${index}-crop`, 2, `Pilih tanaman untuk slot ${index + 1}, atau hapus slot tersebut.`);
    });
  }
  form.slots.forEach((slot, index) => {
    const label = `slot ${index + 1}`;
    for (const [key, value] of [["sowing", slot.sowingDate], ["transplanting", slot.transplantingDate], ["harvest", slot.harvestDate]] as const) {
      if (value && !isIsoDate(value)) add(`slot-${index}-${key}`, 2, `Tanggal pada ${label} tidak valid.`);
    }
    if (slot.method === "direct_seeded" && slot.transplantingDate) {
      add(`slot-${index}-transplanting`, 2, `Tanam langsung tidak memakai tanggal pindah tanam (${label}).`);
    }
    const ordered = [slot.sowingDate, slot.method === "transplanted" ? slot.transplantingDate : "", slot.harvestDate].filter(Boolean);
    if (ordered.join() !== [...ordered].sort().join()) {
      add(`slot-${index}-harvest`, 2, `Urutan semai, pindah tanam, dan panen pada ${label} terbalik.`);
    }
    if (form.inputKind === "scenario_assumption" && slot.dateStatus === "observed") {
      add(`slot-${index}-status`, 2, `Skenario asumsi tidak dapat memberi label "teramati" pada tanggal ${label}.`);
    }
  });
  const starts = form.slots.map(fieldStart);
  if (starts.every(Boolean) && starts.some((value, index) => index > 0 && (value as string) <= (starts[index - 1] as string))) {
    add(`slot-${form.slots.length - 1}-sowing`, 2, "Tanggal mulai tiap slot harus berurutan dan tidak sama.");
  }
  for (const crop of CROP_IDS) {
    const d = form.durations[crop];
    const name = CROPS[crop].name.toLowerCase();
    if (d.min && !positiveInt(d.min, 1, 1000)) add(`duration-${crop}-min`, 2, `Durasi minimum ${name} harus 1–1.000 hari.`);
    if (d.max && !positiveInt(d.max, 1, 1000)) add(`duration-${crop}-max`, 2, `Durasi maksimum ${name} harus 1–1.000 hari.`);
    if (positiveInt(d.min, 1, 1000) && positiveInt(d.max, 1, 1000) && Number(d.min) > Number(d.max)) {
      add(`duration-${crop}-max`, 2, `Rentang durasi ${name} terbalik.`);
    }
  }
  if (form.prepGap && !positiveInt(form.prepGap, 0, 1000)) add("prep-gap", 2, "Jeda persiapan berupa jumlah hari 0–1.000.");
  if (form.sharedCalendar && !form.sharedCalendarNote.trim()) {
    add("shared-note", 2, "Kalender bersama untuk alternatif memerlukan catatan asumsi.");
  }
  form.slots.forEach((slot, index) => {
    if (form.sharedCalendar && !slot.method) add(`slot-${index}-method`, 2, `Kalender bersama memerlukan metode tanam pada slot ${index + 1}.`);
  });
  return issues;
}

function assumptionLines(form: ScenarioForm): string[] {
  return form.assumptions
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

const known = <T,>(value: T | "" | null | undefined): value is T => value !== "" && value !== null && value !== undefined;

function advancedRecord(key: AdvancedKey, note: string): Record<string, unknown> {
  if (key === "local_host_range_evidence") return { scope_and_limitations: note };
  if (key === "soil_management_for_transition") return { description: note };
  return { source: { notes: note } };
}

export function buildRequest(form: ScenarioForm, place: Place): CompareRequestBody | null {
  const location = placeToLocation(place);
  if (!location || !form.inputKind) return null;

  const cropped = form.slots.some((slot) => slot.cropId);
  const records = form.slots.map((slot) => {
    const record: Record<string, unknown> = {};
    if (slot.cropId) record.crop_id = slot.cropId;
    if (slot.dateStatus) record.date_status = slot.dateStatus;
    if (slot.method) record.establishment_method = slot.method;
    if (slot.sowingDate) record.sowing_date = slot.sowingDate;
    if (slot.method === "transplanted" && slot.transplantingDate) record.transplanting_date = slot.transplantingDate;
    if (slot.harvestDate) record.harvest_date = slot.harvestDate;
    if (slot.method === "transplanted" && slot.nursery) record.nursery_separate_from_main_field = slot.nursery === "separate";
    if (slot.cropId === "padi") {
      if (slot.riceEcosystem) record.rice_ecosystem = slot.riceEcosystem;
      if (slot.riceWaterRegime) record.rice_water_regime = slot.riceWaterRegime;
    }
    return record;
  });

  const decided = CROP_IDS.filter((crop) => form.cropPolicy[crop]);
  const durations = CROP_IDS.filter((crop) => form.durations[crop].min || form.durations[crop].max).map((crop) => {
    const d = form.durations[crop];
    const record: Record<string, unknown> = {
      crop_id: crop,
      minimum_days: d.min ? Number(d.min) : null,
      maximum_days: d.max ? Number(d.max) : null,
      basis_event: d.basis || null,
      counting_convention: "elapsed_day_zero",
      source_ref: d.source.trim() || null,
      normalization_policy: "no_rounding_needed",
    };
    if (d.originWording) record.source_origin_wording = d.originWording;
    if (d.cultivar) record.cultivar = d.cultivar;
    if (d.referenceId) {
      record.source_minimum_days = d.min ? Number(d.min) : null;
      record.source_maximum_days = d.max ? Number(d.max) : null;
    }
    return record;
  });

  const planning: Record<string, unknown> = {
    horizon: { start_date: form.start, end_exclusive: addDays(form.endInclusive, 1) },
    locked_prefix_length: Math.min(form.lockedPrefix, form.slots.length),
  };
  if (decided.length) {
    planning.allowed_crop_ids = CROP_IDS.filter((crop) => form.cropPolicy[crop] === "allowed");
    planning.excluded_crop_ids = CROP_IDS.filter((crop) => form.cropPolicy[crop] === "excluded");
  }
  if (cropped) {
    planning.existing_sequence = records;
    planning.slot_start_dates = form.slots.map(fieldStart);
  }
  if (form.continuationConfirmed) planning.continuation_confirmed = true;
  if (durations.length) planning.duration_by_crop = durations;
  if (form.prepGap) planning.preparation_gap_days = Number(form.prepGap);
  if (form.priorities.length) planning.selected_priorities = form.priorities;

  const irrigation: Record<string, unknown> = {};
  if (form.irrigationSystem) irrigation.system = form.irrigationSystem;
  if (form.rainfed) irrigation.rainfed = form.rainfed === "yes";
  if (form.drainage) irrigation.drainage_condition = form.drainage;
  if (form.waterControl) irrigation.water_control = form.waterControl;

  const management: Record<string, unknown> = {};
  for (const { key } of ADVANCED) {
    const entry = form.advanced[key];
    if (entry.state === "none") management[key] = [];
    else if (entry.state === "note" && entry.note.trim()) management[key] = [advancedRecord(key, entry.note.trim())];
  }

  const farm: Record<string, unknown> = {};
  if (Object.keys(irrigation).length) farm.irrigation = irrigation;
  if (Object.keys(management).length) farm.management = management;

  const document: Record<string, unknown> = { planning };
  if (Object.keys(farm).length) document.farm = farm;
  if (form.timeMode) document.context = { time_mode: form.timeMode };

  const assumptions = assumptionLines(form);
  if (form.sharedCalendar && form.sharedCalendarNote.trim()) assumptions.push(form.sharedCalendarNote.trim());

  const body: CompareRequestBody = { location, input_kind: form.inputKind, assumptions: assumptions.slice(0, 30), document };
  if (form.sharedCalendar && cropped) {
    body.slot_inputs = form.slots.map(
      (slot): SlotInputBody => ({
        production_method: known(slot.method) ? slot.method : null,
        sowing_date: slot.sowingDate || null,
        transplanting_date: slot.method === "transplanted" ? slot.transplantingDate || null : null,
        nursery_off_main_field: slot.method === "transplanted" && slot.nursery ? slot.nursery === "separate" : null,
      }),
    );
  }
  return body;
}

/** Maps backend 422 detail paths (e.g. "document.planning.horizon") to form fields. */
export function fieldForApiPath(path: string): { field: string; step: Step } {
  const slot = path.match(/existing_sequence\.(\d+)|slot_inputs\.(\d+)/);
  if (slot) return { field: `slot-${slot[1] ?? slot[2]}-crop`, step: 2 };
  if (path.includes("duration_by_crop")) return { field: "durations", step: 2 };
  if (path.includes("horizon")) return { field: "period-start", step: 1 };
  if (path.includes("location")) return { field: "place-custom", step: 1 };
  if (path.includes("assumptions") || path === "body") return { field: "assumptions", step: 1 };
  if (path.includes("irrigation") || path.includes("management")) return { field: "conditions", step: 3 };
  return { field: "input-kind", step: 1 };
}
