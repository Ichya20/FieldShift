import { CROPS, CALENDAR_ISSUES, GAEZ_CROP, GAEZ_REGIME, RELATION, TRANSITION_STATUS, missingLabel, statusOf } from "../../lib/labels";
import { fmtDateShort, fmtWindowShort, num, signed } from "../../lib/format";
import type { AnyClimateSummary, ClimateMetric, CropId, Finding, GaezRow, RuleId, Strategy } from "../../lib/types";

const GAEZ_CODE: Record<CropId, string> = { padi: "RCW", jagung: "MZE", kedelai: "SOY" };

function metric(summary: AnyClimateSummary | null | undefined, key: ClimateMetric): number | null {
  if (!summary) return null;
  if (summary.mode === "historical_analogue_not_forecast") return summary.statistics[key].mean;
  return summary[key];
}

const known = (value: unknown) => (value === null || value === undefined ? "belum diisi" : Array.isArray(value) ? (value.length ? "ada catatan" : "tidak ada catatan") : String(value));

const VALUE_LABEL: Record<string, string> = {
  good_reported: "baik (dilaporkan)",
  poor_reported: "buruk (dilaporkan)",
  variable_reported: "bervariasi (dilaporkan)",
  locally_verified: "terverifikasi lokal",
  other_documented: "lainnya, terdokumentasi",
  can_supply_and_drain_reported: "bisa memasukkan dan membuang",
  supply_only_reported: "hanya memasukkan",
  drain_only_reported: "hanya membuang",
  no_control_reported: "tidak bisa mengatur",
  flooded_paddy: "digenangi",
  intermittently_flooded_paddy: "genangan berselang",
  nonflooded_aerobic: "tidak digenangi",
  mixed_or_variable: "campuran",
};

const show = (value: unknown) => {
  const text = known(value);
  return VALUE_LABEL[text] ?? text;
};

/** Rule-specific evidence for one strategy, from the numbers the backend actually returned. */
export function RuleEvidence({ rule, strategy }: { rule: RuleId; strategy: Strategy }) {
  const finding = strategy.findings.find((item) => item.rule_id === rule) as Finding;
  const inputs = finding.inputs_used as Record<string, unknown>;
  const cycles = strategy.cycles;
  const rows: string[] = [];

  switch (rule) {
    case "calendar":
      for (const cycle of cycles) {
        const c = cycle.calendar;
        const name = CROPS[cycle.crop_id].name;
        if (c.status === "calendar_computed") {
          const harvest = c.earliest_harvest_date === c.latest_harvest_date ? fmtDateShort(c.earliest_harvest_date) : `${fmtDateShort(c.earliest_harvest_date)}–${fmtDateShort(c.latest_harvest_date)}`;
          rows.push(`${name}: menempati petak ${fmtDateShort(c.field_start)}, panen ${harvest}, petak lepas ${fmtDateShort(c.earliest_release_date)}.`);
        } else {
          rows.push(`${name}: kalender belum dihitung${c.missing_inputs.length ? ` (perlu ${c.missing_inputs.map((code) => missingLabel(code).toLowerCase()).join(", ")})` : ""}.`);
        }
        for (const issue of cycle.issues) rows.push(`${name}: ${CALENDAR_ISSUES[issue.code] ?? issue.code}`);
      }
      for (const transition of strategy.transitions) {
        const status = TRANSITION_STATUS[transition.status]?.label ?? transition.status;
        rows.push(
          transition.next_field_start
            ? `Slot ${transition.previous_slot_index + 1} → ${transition.next_slot_index + 1}: siap ${fmtDateShort(transition.earliest_ready_date)} setelah jeda ${transition.preparation_gap_days ?? "?"} hari, mulai berikutnya ${fmtDateShort(transition.next_field_start)}. ${status}.`
            : `Slot ${transition.previous_slot_index + 1} → ${transition.next_slot_index + 1}: ${status}.`,
        );
      }
      break;
    case "climate_exposure":
      for (const cycle of cycles) {
        const window = cycle.environment_windows.find((w) => w.endpoint === "earliest");
        const summary = window?.climate?.summary;
        if (!window || window.status !== "overlaps_horizon" || !summary) {
          rows.push(`${CROPS[cycle.crop_id].name}: jendela okupansi belum tersedia.`);
          continue;
        }
        rows.push(
          `${CROPS[cycle.crop_id].name} (${fmtWindowShort(window.start_date, window.end_exclusive)}): hujan ${num(metric(summary, "rainfall_total_mm"), 1)} mm · ETo ${num(metric(summary, "reference_eto_total_mm"), 1)} mm · P−ETo ${signed(metric(summary, "rain_minus_reference_eto_total_mm"), 1)} mm.`,
        );
      }
      rows.push("Total satu periode sama untuk ketiga strategi; selisih jendela tanam bukan air yang dihemat.");
      break;
    case "ph_reference": {
      const ph = inputs.soil_ph as { value: number | null; q05: number | null; q95: number | null } | undefined;
      if (ph?.value !== undefined && ph.value !== null) rows.push(`pH ${num(ph.value, 1)} (Q05–Q95 ${num(ph.q05, 1)}–${num(ph.q95, 1)}), prediksi SoilGrids 0–5 cm.`);
      for (const cycle of cycles) {
        const ref = cycle.ph_reference;
        rows.push(
          `${CROPS[cycle.crop_id].name}: optimum ${num(ref.optimum[0], 1)}–${num(ref.optimum[1], 1)}, rerata ${RELATION[ref.mean_relation] ?? ref.mean_relation}${ref.prediction_interval_extends_beyond_optimum ? "; rentang prediksi melewati optimum" : ""}.`,
        );
      }
      break;
    }
    case "temperature_reference":
      for (const cycle of cycles) {
        const ref = cycle.temperature_reference;
        const earliest = ref.endpoint_comparisons.find((item) => item.endpoint === "earliest");
        rows.push(
          `${CROPS[cycle.crop_id].name}: rerata ${num(earliest?.mean_temperature_c ?? null, 2)} °C, optimum ${num(ref.optimum_c[0], 0)}–${num(ref.optimum_c[1], 0)} °C, ${RELATION[earliest?.mean_relation ?? "unknown"]}.`,
        );
      }
      break;
    case "seasonal_et_reference":
      for (const cycle of cycles) {
        const ref = cycle.seasonal_et_reference;
        rows.push(`${CROPS[cycle.crop_id].name}: ${num(ref.min, 0)}–${num(ref.max, 0)} mm per musim (FAO, ${ref.source_locator}). Rentang umum, bukan kebutuhan irigasi lokal.`);
      }
      break;
    case "paddy_upland_transition":
      rows.push(
        `Rezim air padi: ${show(inputs.rice_water_regime)} · drainase: ${show(inputs.drainage)} · kontrol air: ${show(inputs.water_control)} · pengelolaan tanah: ${show(inputs.soil_management)}.`,
      );
      break;
    case "legume_mechanism":
      rows.push(
        `Nodulasi: ${show(inputs.nodulation)} · inokulasi: ${show(inputs.inoculation)} · residu: ${show(inputs.residue_fate)} · neraca hara: ${show(inputs.nutrient_balance)}.`,
      );
      break;
    case "pest_break":
      rows.push(`Organisme lokal: ${show(inputs.local_pest_or_pathogen)} · kisaran inang: ${show(inputs.host_range)} · riwayat pengendalian: ${show(inputs.management_history)}.`);
      break;
    case "vegetation_context": {
      const series = (inputs.series as { platform: string; summary: { n_good_strict: number; n_selected_observations: number } }[] | undefined) ?? [];
      rows.push(...series.map((s) => `${s.platform}: ${s.summary.n_good_strict} dari ${s.summary.n_selected_observations} komposit lolos kualitas.`));
      if (!series.length) rows.push("Tidak ada piksel MODIS yang memuat titik ini.");
      break;
    }
    case "gaez_context": {
      const gaezRows = (inputs.rows as GaezRow[] | undefined) ?? [];
      const crops = Array.from(new Set(strategy.sequence ?? []));
      for (const crop of crops) {
        const matches = gaezRows.filter((row) => row.crop_code === GAEZ_CODE[crop]);
        if (matches.length) rows.push(`${GAEZ_CROP[GAEZ_CODE[crop]]}: ${matches.map((row) => `${GAEZ_REGIME[row.regime]} ${row.class_label}`).join("; ")}.`);
      }
      break;
    }
    case "coverage": {
      const support = (inputs.layer_support as Record<string, { status: string }> | undefined) ?? {};
      const names: Record<string, string> = { climate: "Iklim", soil: "Tanah", terrain: "Medan", vegetation: "Vegetasi", gaez: "GAEZ", landcover: "Tutupan lahan" };
      rows.push(Object.entries(support).map(([key, value]) => `${names[key] ?? key}: ${statusOf(value.status).label.toLowerCase()}`).join(" · "));
      break;
    }
    case "economics":
      rows.push("Hasil panen, harga, dan biaya belum dihitung pada MVP.");
      break;
  }
  return (
    <ul className="rule-evidence">
      {rows.map((row, index) => (
        <li key={index}>{row}</li>
      ))}
    </ul>
  );
}
