// Shapes returned by the FieldShift FastAPI backend (backend/fieldshift). Only fields the UI reads are typed.

export type CropId = "padi" | "jagung" | "kedelai";
export type TimeMode = "historical_replay" | "recent_partial" | "historical_analogue_not_forecast";
export type ExampleId = "klaten_cropland_primary" | "klaten_cropland_candidate";
export type InputKind = "scenario_assumption" | "user_reported";
export type Priority = "water_context" | "soil_context" | "pest_management" | "calendar_constraints" | "economic_information";

export type Status =
  | "evidence_available"
  | "needs_input"
  | "review_required"
  | "input_conflict"
  | "outside_coverage"
  | "not_applicable"
  | "partial"
  | "invalid_input"
  | "insufficient_alternatives"
  | "complete_for_selected_checks";

export type RuleId =
  | "coverage"
  | "calendar"
  | "climate_exposure"
  | "ph_reference"
  | "temperature_reference"
  | "seasonal_et_reference"
  | "paddy_upland_transition"
  | "legume_mechanism"
  | "pest_break"
  | "vegetation_context"
  | "gaez_context"
  | "economics";

export type ClimateMetric =
  | "rainfall_total_mm"
  | "reference_eto_total_mm"
  | "rain_minus_reference_eto_total_mm"
  | "temperature_mean_c";

export interface Coordinate {
  longitude: number | null;
  latitude: number | null;
}

export interface ResolvedLocation {
  id: string | null;
  example_id: ExampleId | null;
  coordinate: Coordinate;
  is_verified_farm: boolean;
  climate_context_id: string | null;
  climate_context_assignment: string | null;
  role: string;
}

export interface DateWindow {
  start_date: string;
  end_exclusive: string;
}

export interface ClimateSummary {
  mode?: undefined;
  start: string;
  end_exclusive: string;
  days_expected: number;
  rainfall_total_mm: number | null;
  reference_eto_total_mm: number | null;
  rain_minus_reference_eto_total_mm: number | null;
  temperature_mean_c: number | null;
  valid_days: Record<ClimateMetric, number>;
  eto_guard_days: number;
}

export interface AnalogueStatistics {
  count: number;
  mean: number | null;
  median: number | null;
  p10: number | null;
  p90: number | null;
}

export interface AnalogueSummary {
  mode: "historical_analogue_not_forecast";
  start: string;
  end_exclusive: string;
  days_expected: number;
  baseline_start_year: number;
  baseline_end_year: number;
  counts_by_metric: Record<ClimateMetric, number>;
  statistics: Record<ClimateMetric, AnalogueStatistics>;
  mapping_policy: string;
}

export type AnyClimateSummary = ClimateSummary | AnalogueSummary;

export interface ClimateSupport {
  context_id: string | null;
  coordinate: Coordinate;
  spatial_support: string;
  time_standard: string;
  available_start: string;
  available_end_inclusive: string;
  assignment: string | null;
}

export interface ClimateLayer {
  status: Status;
  summary: AnyClimateSummary | null;
  source_refs: string[];
  support: ClimateSupport;
  time_mode: TimeMode | null;
  warnings: string[];
  missing_inputs?: string[];
}

export interface RasterQuery {
  value: number | null;
  status: Status;
  reason: string;
}

export interface SoilProperty {
  property: string;
  depth: string;
  statistic: "mean" | "Q0.05" | "Q0.95";
  value: number | null;
  unit: string;
  status: Status;
  qa_status: string;
}

export interface SoilLayer {
  status: Status;
  source_refs: string[];
  support: { resolution_m: number; product: string; is_measured_soil_test: boolean; query_policy: string; retention_phase: string };
  ph_0_5cm: { value: number | null; q05: number | null; q95: number | null; unit: string; depth: string; status: Status };
  properties: SoilProperty[];
  warnings: string[];
}

export interface TerrainLayer {
  status: Status;
  source_refs: string[];
  support: { source_product: string; resolution_m: number; is_surveyed_microtopography: boolean };
  elevation_m: RasterQuery;
  slope_degrees: RasterQuery;
  warnings: string[];
}

export type QualityStatus = "good_strict" | "marginal_review" | "excluded";

export interface VegetationObservation {
  composite_start_date: string;
  selected_observation_date: string;
  ndvi: number | null;
  evi: number | null;
  quality_status: QualityStatus;
  quality_reason: string;
  product: string;
  platform: string;
}

export interface VegetationSummary {
  n_selected_observations: number;
  n_good_strict: number;
  n_marginal_review: number;
  n_excluded: number;
  good_observation_dates: string[];
  coverage_status: "has_good_observations" | "no_good_observations" | "no_selected_observations";
  ndvi_good_mean: number | null;
  evi_good_mean: number | null;
}

export interface VegetationMonth extends VegetationSummary {
  month: string;
}

export interface VegetationSeries {
  product: "MOD13Q1" | "MYD13Q1";
  platform: "Terra" | "Aqua";
  point_id: string;
  status: Status;
  summary: VegetationSummary;
  observations: VegetationObservation[];
  monthly: VegetationMonth[];
  source_refs: string[];
  support: {
    crs: string;
    xllcorner: number;
    yllcorner: number;
    cellsize: number;
    nrows: number;
    ncols: number;
    nominal_resolution_m: number;
    mixed_pixel: boolean;
  };
}

export interface VegetationLayer {
  status: Status;
  source_refs: string[];
  series: VegetationSeries[];
  warnings: string[];
}

export interface GaezRow {
  layer_code: string;
  crop_code: "RCW" | "MZE" | "SOY";
  regime: "HRLM" | "HILM";
  class_code: number;
  class_label: string;
  pixel_bounds: { west: number; east: number; north: number; south: number };
  source_url: string;
}

export interface GaezLayer {
  status: Status;
  source_refs: string[];
  support: { period: string; scenario: string; climate: string; resolution_degrees: number };
  rows: GaezRow[];
  warnings: string[];
}

export interface LandcoverFootprint {
  point_id: string;
  epoch: number;
  stats: {
    grid_cells: number;
    valid_cells: number;
    class_histogram: Record<string, { label: string; cells: number }>;
    cropland_fraction_valid_cells: number;
    built_up_fraction_valid_cells: number;
  };
  sinusoidal_bounds_m: number[];
}

export interface LandcoverLayer {
  status: Status;
  source_refs: string[];
  support: { epoch: number; product: string };
  footprints: LandcoverFootprint[];
}

export interface ContextResponse {
  location: ResolvedLocation;
  window: DateWindow | null;
  time_mode: TimeMode | null;
  layers: {
    climate: ClimateLayer;
    soil: SoilLayer;
    terrain: TerrainLayer;
    vegetation: VegetationLayer;
    gaez: GaezLayer;
    landcover: LandcoverLayer;
  };
  missing_inputs: string[];
  warnings: string[];
}

export interface MonthlyClimateMonth {
  month: string;
  start: string;
  end_exclusive: string;
  whole_calendar_month: boolean;
  status: Status;
  summary: AnyClimateSummary | null;
  warnings: string[];
}

export interface MonthlyClimateResponse {
  location: ResolvedLocation;
  window: DateWindow;
  time_mode: TimeMode;
  status: Status;
  support: ClimateSupport;
  source_refs: string[];
  months: MonthlyClimateMonth[];
  latest_valid_dates: Record<ClimateMetric, string | null> | null;
}

export interface CropReference {
  crop_id: CropId;
  common_name_id: string;
  scientific_name: string;
  gaez_crop_code: "RCW" | "MZE" | "SOY";
  species_temperature_optimum_c: { min: number; max: number; source_id: string };
  species_soil_ph_optimum: { min: number; max: number; source_id: string };
  seasonal_crop_water_need_indicative_mm: { min: number; max: number; source_id: string; source_locator: string };
  local_variety_reference: {
    name: string;
    duration_days_min: number;
    duration_days_max: number;
    duration_start_event: string;
    source_id: string;
    limitations: string;
  };
}

export interface SourceEntry {
  url?: string;
  final_url?: string;
  path?: string;
  kind?: string;
  description?: string;
  accessed_at_utc?: string;
  access_date?: string;
  retrieved_at_utc?: string;
  sha256?: string;
  provider?: string;
  status?: string;
}

export interface CatalogResponse {
  project: string;
  data_status: string;
  time_modes: TimeMode[];
  examples: ResolvedLocation[];
  layers: Record<string, unknown> & {
    climate: { available_start: string; available_end_inclusive: string };
  };
  missing_farm_inputs: string[];
  sources: Record<string, SourceEntry>;
}

// ---- Comparison -------------------------------------------------------------

export interface CycleCalendar {
  field_start: string | null;
  earliest_harvest_date: string | null;
  latest_harvest_date: string | null;
  earliest_release_date: string | null;
  latest_release_date: string | null;
  status: "calendar_computed" | "needs_input" | "invalid_input" | string;
  missing_inputs: string[];
  review_issues: unknown[];
  errors: { field: string; code: string }[];
  notes: string[];
}

export interface EnvironmentWindow {
  endpoint: "earliest" | "latest";
  status: "overlaps_horizon" | "outside_horizon";
  start_date: string;
  end_exclusive: string;
  climate: ClimateLayer | null;
}

export interface Cycle {
  slot_index: number;
  crop_id: CropId;
  calendar_inputs: {
    production_method: "direct_seeded" | "transplanted" | null;
    sowing_date: string | null;
    transplanting_date: string | null;
    duration: { min_days: number | null; max_days: number | null; basis: string | null; source_kind: string; source_id: string | null } | null;
  };
  calendar: CycleCalendar;
  issues: { status: Status; code: string; [key: string]: unknown }[];
  environment_windows: EnvironmentWindow[];
  rice_context: { rice_water_regime: string | null; rice_ecosystem: string | null; source: string | null };
  preparation_gap_after: number | null;
  temperature_reference: {
    optimum_c: [number, number];
    endpoint_comparisons: { endpoint: string; mean_temperature_c: number | null; mean_relation: string }[];
  };
  ph_reference: { optimum: [number, number]; mean_relation: string; prediction_interval_extends_beyond_optimum: boolean | null };
  seasonal_et_reference: { min: number; max: number; source_id: string; source_locator: string };
}

export interface Transition {
  status: "no_calendar_conflict" | "potential_calendar_conflict" | "calendar_conflict" | "needs_input" | string;
  earliest_ready_date: string | null;
  latest_ready_date: string | null;
  next_field_start: string | null;
  missing_inputs: string[];
  errors: unknown[];
  notes: string[];
  preparation_gap_days: number | null;
  previous_slot_index: number;
  next_slot_index: number;
}

export interface Finding {
  rule_id: RuleId;
  status: Status;
  inputs_used: Record<string, unknown>;
  source_refs: string[];
  assumptions: string[];
  explanation: string;
  missing_inputs: string[];
  next_action: string | null;
}

export type StrategyId = "existing" | "candidate_1" | "candidate_2";

export interface Strategy {
  strategy_id: StrategyId;
  sequence: CropId[] | null;
  status: Status;
  generated_reason: string;
  cycles: Cycle[];
  transitions: Transition[];
  findings: Finding[];
  highlighted_rule_ids: RuleId[];
  whole_horizon_environment: ClimateLayer;
  missing_inputs: string[];
  local_agronomic_validation: boolean;
}

export interface CompareResponse {
  method_id: string;
  method_version: string;
  input_kind: InputKind;
  assumptions: string[];
  generation: {
    strategies: Record<StrategyId, CropId[] | null>;
    generated_count: number;
    generation_status: "complete" | "insufficient_alternatives" | "needs_input" | "invalid_input";
    missing_inputs: string[];
    warnings: ({ code: string; slot_index?: number; crop_id?: string } | string)[];
    errors: { field: string; code: string }[];
  };
  context: ContextResponse & { requested_time_mode: TimeMode | null };
  strategies: Strategy[];
  analysis_status: "partial" | "complete_for_selected_checks" | "invalid_input";
  missing_inputs: string[];
  warnings: string[];
  local_agronomic_validation: boolean;
}

export interface DemoResponse {
  request: CompareRequestBody;
  analysis: CompareResponse;
}

// ---- Requests ---------------------------------------------------------------

export interface LocationBody {
  example_id?: ExampleId;
  longitude?: number;
  latitude?: number;
  climate_context_id?: "power_regional_yogyakarta";
}

export interface ContextRequestBody {
  location: LocationBody;
  window: DateWindow;
  time_mode: TimeMode;
}

export interface SlotInputBody {
  production_method: "direct_seeded" | "transplanted" | null;
  sowing_date: string | null;
  transplanting_date: string | null;
  nursery_off_main_field: boolean | null;
}

export interface CompareRequestBody {
  location: LocationBody;
  input_kind: InputKind;
  assumptions: string[];
  slot_inputs?: SlotInputBody[];
  document: Record<string, unknown>;
}

export interface ApiErrorDetail {
  field: string;
  code: string;
  message: string;
}
