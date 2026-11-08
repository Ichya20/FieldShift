"""Stateless rotation exploration over explicitly selected public context.

Candidate order is deterministic enumeration, never an agronomic ranking.
Transport validation and public-source extraction belong to their own modules.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date

from scripts.method.rotation_reference import calendar_cycle, check_transition, generate_candidates


PRIORITY_RULES = {
    "water_context": {"climate_exposure", "seasonal_et_reference", "paddy_upland_transition"},
    "soil_context": {"ph_reference", "legume_mechanism", "paddy_upland_transition"},
    "pest_management": {"pest_break"},
    "calendar_constraints": {"calendar"},
    "economic_information": {"economics"},
}
STRATEGY_IDS = ("existing", "candidate_1", "candidate_2")
NEUTRAL_REASONS = {
    "existing": "Kelanjutan yang dikonfirmasi secara eksplisit; bukan riwayat lahan hasil inferensi.",
    "candidate_1": "Perubahan paling sedikit dari kelanjutan yang diisi, dengan urutan ID tanaman untuk pemecah seri; bukan peringkat agronomi.",
    "candidate_2": "Variasi komposisi atau urutan yang berbeda dari kandidat pertama; bukan peringkat manfaat.",
}


def _mapping(value):
    return value if isinstance(value, dict) else {}


def _known(value):
    """False, zero and explicitly empty records remain distinct from unknown."""
    return value is not None


def _unique(values):
    return list(dict.fromkeys(values))


def _valid_horizon(horizon):
    if not isinstance(horizon, dict):
        return False
    try:
        first = date.fromisoformat(horizon["start_date"])
        end = date.fromisoformat(horizon["end_exclusive"])
        return first < end and first.isoformat() == horizon["start_date"] and end.isoformat() == horizon["end_exclusive"]
    except (KeyError, TypeError, ValueError):
        return False


def _metric(summary, key):
    summary = _mapping(summary)
    if summary.get("mode") == "historical_analogue_not_forecast":
        return _mapping(_mapping(summary.get("statistics")).get(key)).get("mean")
    return summary.get(key)


def _relation(value, low, high):
    if value is None:
        return "unknown"
    return "within_reference_optimum" if low <= value <= high else "outside_reference_optimum_requires_review"


class AnalysisService:
    def __init__(self, repository):
        self.repository = repository
        self.method = repository.method
        self.crops = {crop["crop_id"]: crop for crop in repository.crops}
        self.rules = {rule["id"]: rule for rule in self.method["rules"]}

    def compare(self, payload: dict) -> dict:
        document = _mapping(payload.get("document"))
        planning = _mapping(document.get("planning"))
        farm = _mapping(document.get("farm"))
        request_context = _mapping(document.get("context"))
        assumptions = list(payload.get("assumptions") or [])
        input_kind = payload.get("input_kind")
        horizon = planning.get("horizon")
        usable_horizon = horizon if _valid_horizon(horizon) else None
        time_mode = request_context.get("time_mode")
        location = deepcopy(_mapping(payload.get("location")))
        # Missing mode must not accidentally request a historical analysis.
        context = self.repository.context(location, usable_horizon if time_mode else None,
                                          time_mode or "historical_replay")
        context = deepcopy(context)
        context["requested_time_mode"] = time_mode
        if time_mode is None:
            context["time_mode"] = None
            _mapping(_mapping(context.get("layers")).get("climate"))["time_mode"] = None
            context.setdefault("missing_inputs", []).append("context.time_mode")

        generation = generate_candidates({key: planning.get(key) for key in (
            "horizon", "allowed_crop_ids", "excluded_crop_ids", "existing_sequence",
            "slot_start_dates", "locked_prefix_length", "continuation_confirmed")})
        selected = planning.get("selected_priorities") or []
        highlighted = set().union(*(PRIORITY_RULES.get(priority, set()) for priority in selected))
        strategies = []
        malformed = generation["generation_status"] == "invalid_input"
        for strategy_id in STRATEGY_IDS:
            sequence = generation["strategies"][strategy_id]
            strategy = self._strategy(strategy_id, sequence, payload, planning, farm,
                                      context, usable_horizon, time_mode, assumptions, highlighted)
            strategies.append(strategy)
            malformed |= strategy.pop("_malformed_input", False)
        missing = ["planning." + field for field in generation["missing_inputs"]]
        missing += list(context.get("missing_inputs") or [])
        for strategy in strategies:
            missing += strategy["missing_inputs"]
        warnings = list(context.get("warnings") or []) + generation["warnings"]
        warnings.append("Urutan kandidat tidak menyatakan peringkat agronomi atau manfaat.")
        if input_kind == "user_reported":
            warnings.append("Isian dilaporkan pengguna dan belum merupakan verifikasi lapangan.")
        return {
            "method_id": self.method["method_id"], "method_version": self.method["method_version"],
            "input_kind": input_kind, "assumptions": assumptions,
            "generation": generation, "context": context, "strategies": strategies,
            "analysis_status": "invalid_input" if malformed else "partial" if any(
                s["status"] != "complete_for_selected_checks" for s in strategies
            ) else "complete_for_selected_checks",
            "missing_inputs": _unique(missing), "warnings": warnings,
            "input_sources": self._input_sources(planning, payload, input_kind),
            "input_processing": [
                "Konteks lingkungan dihitung dari sumber publik repository pada lokasi dan periode yang dipilih; catatan referensi konteks yang dikirim pengguna tidak menggantikan layer tersebut.",
                "Tidak ada agregasi atas batas lahan, model hasil, perhitungan ekonomi atau rekomendasi lapangan tervalidasi.",
                "Prioritas hanya menyoroti aturan; urutan kandidat tetap netral.",
            ],
            "local_agronomic_validation": False,
        }

    def _input_sources(self, planning, payload, input_kind):
        sources = {}
        durations = list(_mapping(planning.get("duration_by_crop")).values())
        durations += [_mapping(slot).get("duration") for slot in payload.get("slot_inputs") or []]
        for duration in durations:
            duration = _mapping(duration)
            source_id = duration.get("source_id")
            if source_id:
                sources[source_id] = {
                    "kind": duration.get("source_kind") or input_kind,
                    "role": "submitted_duration_provenance",
                    "verification": "Submitted identifier; does not establish external source verification.",
                }
        return sources

    def _finding(self, rule_id, status, explanation, inputs, assumptions, missing=None, action=None):
        return {
            "rule_id": rule_id, "status": status,
            "scope": "submitted_inputs_with_public_source_context",
            "inputs_used": inputs, "source_refs": list(self.rules[rule_id]["source_refs"]),
            "assumptions": list(assumptions), "explanation": explanation,
            "missing_inputs": list(missing or []), "next_action": action,
        }

    def _slot_plan(self, index, crop_id, strategy_id, payload, planning):
        slots = payload.get("slot_inputs")
        slot = _mapping(slots[index]) if isinstance(slots, list) and index < len(slots) else {}
        if not slot and strategy_id == "existing":
            baseline = payload.get("cycle_inputs")
            slot = _mapping(baseline[index]) if isinstance(baseline, list) and index < len(baseline) else {}
        # Internally derived baseline records carry crop_id; explicit shared
        # scenario slot inputs deliberately omit it.
        if slot.get("crop_id") not in (None, crop_id):
            slot = {}
        settings = _mapping(_mapping(payload.get("crop_settings")).get(crop_id))
        plan = {key: slot.get(key, settings.get(key)) for key in (
            "production_method", "sowing_date", "transplanting_date", "nursery_off_main_field")}
        for key, plural in (("sowing_date", "sowing_dates"), ("transplanting_date", "transplanting_dates")):
            dates = settings.get(plural)
            if plan[key] is None and isinstance(dates, list) and index < len(dates):
                plan[key] = dates[index]
        existing = planning.get("existing_sequence") or []
        same_locked = index < (planning.get("locked_prefix_length") or 0) and index < len(existing) and existing[index] == crop_id
        duration = slot.get("duration") if strategy_id == "existing" or same_locked else None
        if duration is None:
            duration = _mapping(planning.get("duration_by_crop")).get(crop_id)
        plan.update(crop_id=crop_id, duration=deepcopy(duration))
        return plan

    def _cycle(self, index, crop_id, strategy_id, payload, planning, horizon, time_mode, ph):
        plan = self._slot_plan(index, crop_id, strategy_id, payload, planning)
        calendar = calendar_cycle(plan)
        issues = []
        starts = planning.get("slot_start_dates")
        declared_start = starts[index] if isinstance(starts, list) and index < len(starts) else None
        if calendar["field_start"] and declared_start and calendar["field_start"] != declared_start:
            issues.append({"status": "input_conflict", "code": "field_start_disagrees_with_slot_start",
                           "declared_start": declared_start, "field_start": calendar["field_start"]})
        submitted = _mapping(_mapping(payload.get("submitted_document")).get("planning"))
        records = submitted.get("existing_sequence")
        record = _mapping(records[index]) if isinstance(records, list) and index < len(records) else {}
        same_locked = index < (planning.get("locked_prefix_length") or 0) and record.get("crop_id") == crop_id
        if plan.get("production_method") == "transplanted" and plan.get("nursery_off_main_field") is True:
            slot_ref = record.get("nursery_location_ref") if record.get("crop_id") == crop_id else None
            if not slot_ref and not planning.get("nursery_location_ref"):
                issues.append({"status": "needs_input", "code": "nursery_location_ref_unknown"})
        recorded_harvest = record.get("harvest_date") if strategy_id == "existing" or same_locked else None
        if recorded_harvest and calendar["status"] == "calendar_computed":
            if not calendar["earliest_harvest_date"] <= recorded_harvest <= calendar["latest_harvest_date"]:
                issues.append({"status": "input_conflict", "code": "recorded_harvest_outside_duration_range",
                               "recorded_harvest_date": recorded_harvest})
        endpoints = []
        if calendar["status"] == "calendar_computed" and horizon:
            start = max(calendar["field_start"], horizon["start_date"])
            for endpoint in ("earliest", "latest"):
                release = calendar[endpoint + "_release_date"]
                end = min(release, horizon["end_exclusive"])
                if start >= end:
                    endpoints.append({"endpoint": endpoint, "status": "outside_horizon",
                                      "start_date": start, "end_exclusive": end, "climate": None})
                else:
                    layer = (self.repository.climate_window(payload.get("location") or {}, start, end, time_mode)
                             if time_mode else {"status": "needs_input", "summary": None,
                                                "missing_inputs": ["context.time_mode"]})
                    endpoints.append({"endpoint": endpoint, "status": "overlaps_horizon",
                                      "start_date": start, "end_exclusive": end, "climate": layer})
            if all(e["status"] == "outside_horizon" for e in endpoints):
                issues.append({"status": "input_conflict", "code": "crop_has_no_occupation_overlap_with_horizon"})
            elif any(e["status"] == "outside_horizon" for e in endpoints):
                issues.append({"status": "review_required", "code": "uncertain_occupation_overlap_with_horizon"})
        crop = self.crops[crop_id]
        slot_gap = record.get("preparation_gap_days") if strategy_id == "existing" or same_locked else None
        temp = crop["species_temperature_optimum_c"]
        optimum = crop["species_soil_ph_optimum"]
        temperatures = [{"endpoint": e["endpoint"],
                         "mean_temperature_c": _metric(_mapping(e.get("climate")).get("summary"), "temperature_mean_c"),
                         "mean_relation": _relation(_metric(_mapping(e.get("climate")).get("summary"), "temperature_mean_c"), temp["min"], temp["max"])}
                        for e in endpoints]
        return {
            "slot_index": index, "crop_id": crop_id, "calendar_inputs": plan, "calendar": calendar,
            "issues": issues, "environment_windows": endpoints,
            "rice_context": self._rice_context(index, crop_id, payload, planning, record),
            "preparation_gap_after": slot_gap if slot_gap is not None else planning.get("preparation_gap_days"),
            "preparation_gap_source": (f"planning.existing_sequence[{index}].preparation_gap_days"
                                       if slot_gap is not None else "planning.preparation_gap_days"),
            "endpoint_interpretation": "Alternative duration-endpoint windows; not universal numerical bounds on signed P−ETo or temperature.",
            "temperature_reference": {"optimum_c": [temp["min"], temp["max"]], "endpoint_comparisons": temperatures,
                                      "meaning": "Historical species optimum; not a Tmax stress/failure threshold."},
            "ph_reference": {"optimum": [optimum["min"], optimum["max"]],
                             "mean_relation": _relation(ph.get("value"), optimum["min"], optimum["max"]),
                             "prediction_interval_extends_beyond_optimum": (
                                 ph["q05"] < optimum["min"] or ph["q95"] > optimum["max"]
                             ) if ph.get("q05") is not None and ph.get("q95") is not None else None},
            "seasonal_et_reference": deepcopy(crop["seasonal_crop_water_need_indicative_mm"]),
        }

    @staticmethod
    def _rice_context(index, crop_id, payload, planning, record):
        context = {"rice_water_regime": None, "rice_ecosystem": None, "source": None}
        if crop_id != "padi":
            return context
        if record.get("crop_id") == "padi":
            for key in ("rice_water_regime", "rice_ecosystem"):
                context[key] = record.get(key)
            context["source"] = f"planning.existing_sequence[{index}]"
        current = _mapping(_mapping(_mapping(payload.get("document")).get("farm")).get("current_crop"))
        if index == 0 and (planning.get("locked_prefix_length") or 0) > 0 and current.get("crop_id") == "padi":
            for key in ("rice_water_regime", "rice_ecosystem"):
                if context[key] is None:
                    context[key] = current.get(key)
            if context["source"] is None:
                context["source"] = "farm.current_crop (first locked matching crop only)"
        return context

    def _ph(self, farm, layers, input_kind):
        lab = _mapping(farm.get("soil_lab"))
        if lab.get("ph_h2o") is not None:
            needed = ["method", "sampling_date", "depth_top_cm", "depth_bottom_cm", "laboratory"]
            missing = ["farm.soil_lab." + key for key in needed if not _known(lab.get(key))]
            return {"value": lab["ph_h2o"] if not missing else None,
                    "reported_value": lab["ph_h2o"],
                    "origin": ("scenario_assumed_laboratory_record" if input_kind == "scenario_assumption"
                               else "user_reported_laboratory_record_not_verified"),
                    "top_cm": lab.get("depth_top_cm"), "bottom_cm": lab.get("depth_bottom_cm"),
                    "method": lab.get("method"), "sampling_date": lab.get("sampling_date"),
                    "q05": None, "q95": None, "missing_inputs": missing}
        return deepcopy(_mapping(_mapping(layers.get("soil")).get("ph_0_5cm")))

    def _strategy(self, strategy_id, sequence, payload, planning, farm, context, horizon, time_mode, assumptions, highlighted):
        layers = _mapping(context.get("layers"))
        ph = self._ph(farm, layers, payload.get("input_kind"))
        cycles = [self._cycle(i, crop_id, strategy_id, payload, planning, horizon, time_mode, ph)
                  for i, crop_id in enumerate(sequence or [])]
        transitions = []
        for previous, following in zip(cycles, cycles[1:]):
            transition = check_transition(previous["calendar"], following["calendar"], previous["preparation_gap_after"])
            transition.update(preparation_gap_days=previous["preparation_gap_after"],
                              preparation_gap_source=previous["preparation_gap_source"],
                              previous_slot_index=previous["slot_index"], next_slot_index=following["slot_index"])
            transitions.append(transition)
        findings = self._findings(sequence, cycles, transitions, planning, farm, context, ph, assumptions)
        missing = _unique([item for finding in findings for item in finding["missing_inputs"]])
        malformed = any(c["calendar"]["status"] == "invalid_input" for c in cycles)
        return {
            "strategy_id": strategy_id, "sequence": deepcopy(sequence),
            "status": "partial" if sequence is None or any(f["status"] in {
                "needs_input", "input_conflict", "review_required", "outside_coverage"} for f in findings
            ) else "complete_for_selected_checks",
            "generated_reason": NEUTRAL_REASONS[strategy_id] if sequence is not None else "Urutan belum tersedia; tidak dibuat dari riwayat yang tidak diketahui.",
            "cycles": cycles, "transitions": transitions, "findings": findings,
            "highlighted_rule_ids": [r["id"] for r in self.method["rules"] if r["id"] in highlighted],
            "whole_horizon_environment": deepcopy(_mapping(layers.get("climate"))),
            "missing_inputs": missing, "local_agronomic_validation": False,
            **{key: None for key in self.method["unavailable_outputs"]},
            "_malformed_input": malformed,
        }

    def _findings(self, sequence, cycles, transitions, planning, farm, context, ph, assumptions):
        findings = []
        layers = _mapping(context.get("layers"))

        def add(rule_id, status, text, inputs, missing=None, action=None):
            findings.append(self._finding(rule_id, status, text, inputs, assumptions, missing, action))

        support = {name: {key: layer.get(key) for key in ("status", "support", "source_refs")}
                   for name, layer in layers.items() if isinstance(layer, dict)}
        add("coverage", "review_required", "Dukungan ruang diperiksa per layer. Titik contoh atau laporan pengguna belum menjadi batas lahan terverifikasi.",
            {"location": context.get("location"), "layer_support": support},
            list(context.get("missing_inputs") or []), "Tinjau cakupan dan sumber setiap layer.")

        calendar_missing = [] if sequence is not None else ["planning.existing_sequence", "planning.continuation_confirmed"]
        calendar_errors = []
        for cycle in cycles:
            prefix = f"slot_inputs[{cycle['slot_index']}]"
            calendar_missing += [prefix + "." + key for key in cycle["calendar"]["missing_inputs"]]
            calendar_errors += cycle["calendar"]["errors"]
            calendar_missing += [issue["code"] for issue in cycle["issues"] if issue["status"] == "needs_input"]
        for transition in transitions:
            calendar_missing += transition["missing_inputs"]
        statuses = {t["status"] for t in transitions}
        issues = [issue for cycle in cycles for issue in cycle["issues"]]
        has_review = any(c["calendar"]["review_issues"] for c in cycles)
        if calendar_errors or "calendar_conflict" in statuses or any(i["status"] == "input_conflict" for i in issues):
            calendar_status = "input_conflict"
        elif calendar_missing or any(c["calendar"]["status"] == "needs_input" for c in cycles):
            calendar_status = "needs_input"
        elif "potential_calendar_conflict" in statuses or has_review or any(i["status"] == "review_required" for i in issues):
            calendar_status = "review_required"
        else:
            calendar_status = "evidence_available"
        add("calendar", calendar_status, "Kalender memakai asal durasi, rentang dan jeda yang diisi. Konflik pasti dan kemungkinan konflik ditampilkan; hasil ini bukan sertifikat agronomi.",
            {"calendars": [c["calendar"] for c in cycles], "issues": issues, "transitions": transitions,
             "preparation_gap_days": planning.get("preparation_gap_days")}, _unique(calendar_missing),
            "Lengkapi tanggal, durasi bersumber, jeda dan sumber daya persemaian yang relevan.")

        climate = _mapping(layers.get("climate"))
        windows = [e for c in cycles for e in c["environment_windows"]]
        available = any(_metric(_mapping(e.get("climate")).get("summary"), "temperature_mean_c") is not None for e in windows)
        climate_missing = []
        if not planning.get("horizon"):
            climate_missing.append("planning.horizon")
        if not context.get("requested_time_mode"):
            climate_missing.append("context.time_mode")
        if not cycles or any(c["calendar"]["status"] != "calendar_computed" for c in cycles):
            climate_missing.append("calendar.field_occupation_windows")
        if climate.get("summary") is None:
            climate_missing.append("location.climate_context_id")
        endpoint_layers = [_mapping(e.get("climate")) for e in windows if e.get("climate")]
        incomplete = any(layer.get("status") == "review_required" for layer in endpoint_layers)
        climate_status = ("needs_input" if climate_missing else "review_required" if available and incomplete else
                          "evidence_available" if available else "outside_coverage" if climate.get("status") == "outside_coverage" else "needs_input")
        add("climate_exposure", climate_status, "P, ETo dan P−ETo adalah paparan lingkungan pada tanggal okupansi. Total horizon sama untuk semua strategi; tidak menghitung konsumsi atau penghematan air tanaman.",
            {"whole_horizon": climate, "endpoint_windows": windows}, climate_missing,
            "Pertahankan cakupan hari valid, kohort analog dan konteks regional secara eksplisit.")

        if sequence is None:
            ph_status, ph_missing = "needs_input", ["planning.existing_sequence"]
        elif ph.get("value") is None:
            ph_status = "outside_coverage" if _mapping(layers.get("soil")).get("status") == "outside_coverage" else "needs_input"
            ph_missing = ph.get("missing_inputs") or ["pH_origin_depth_method_date_or_model_epoch_valid_value"]
        else:
            ph_status, ph_missing = "review_required", []
        add("ph_reference", ph_status, "pH dibandingkan dengan optimum spesies historis beserta asal, kedalaman dan ketidakpastian. Prediksi model dan catatan laboratorium pengguna tetap berbeda; luar optimum tidak membuktikan kegagalan.",
            {"soil_ph": ph, "crop_comparisons": [{"crop_id": c["crop_id"], **c["ph_reference"]} for c in cycles]}, ph_missing,
            "Tinjau metode, kedalaman dan kondisi zona akar bersama pendamping lokal.")
        add("temperature_reference", "evidence_available" if available else "needs_input",
            "Rerata suhu pada jendela historis dibandingkan dengan optimum spesies. Tidak ada hari stres dari Tmax atau prediksi kehilangan hasil.",
            {"comparisons": [{"crop_id": c["crop_id"], **c["temperature_reference"]} for c in cycles]},
            [] if available else ["historical_temperature_summary", "crop_calendar"])
        add("seasonal_et_reference", "evidence_available" if cycles else "needs_input",
            "ET seluruh musim merupakan rentang referensi umum. Rentang tidak diskalakan, dikurangi hujan tahunan, atau dipakai memberi peringkat hemat air.",
            {"references": [{"crop_id": c["crop_id"], "reference": c["seasonal_et_reference"]} for c in cycles]},
            [] if cycles else ["crop_id"])

        irrigation = _mapping(farm.get("irrigation"))
        management = _mapping(farm.get("management"))
        has_transition = any(a == "padi" and b in {"jagung", "kedelai"} for a, b in zip(sequence or [], (sequence or [])[1:]))
        rice_transitions = [{"slot_index": i, **cycle["rice_context"]} for i, cycle in enumerate(cycles[:-1])
                            if cycle["crop_id"] == "padi" and cycles[i + 1]["crop_id"] in {"jagung", "kedelai"}]
        regimes_known = bool(rice_transitions) and all(t["rice_water_regime"] is not None for t in rice_transitions)
        transition_inputs = {"sequence": sequence,
                             "rice_water_regime": rice_transitions[0]["rice_water_regime"] if len(rice_transitions) == 1 else None,
                             "rice_transitions": rice_transitions,
                             "drainage": irrigation.get("drainage_condition"), "water_control": irrigation.get("water_control"),
                             "soil_management": management.get("soil_management_for_transition")}
        transition_missing = (["rice_water_regime"] if not regimes_known else []) + [key for key in (
            "drainage", "water_control", "soil_management") if transition_inputs[key] is None]
        add("paddy_upland_transition", "needs_input" if sequence is None or has_transition and transition_missing else "review_required" if has_transition else "not_applicable",
            "Tanam langsung/pindah tanam tidak menentukan ekosistem atau genangan. Transisi padi ke jagung/kedelai memerlukan penilaian rezim air, drainase, kontrol air dan pengelolaan setempat.",
            transition_inputs, transition_missing if has_transition else ["sequence"] if sequence is None else [],
            "Tinjau transisi dan kondisi tiap siklus bersama penyuluh; laporan drainase baik belum membuktikan kelayakan.")

        legume_inputs = {"sequence": sequence, "nodulation": management.get("nodulation_observations"),
                         "inoculation": management.get("legume_inoculation"), "residue_fate": management.get("residue_fate"),
                         "nutrient_balance": management.get("nutrient_balance")}
        legume_missing = [key for key in ("nodulation", "inoculation", "residue_fate", "nutrient_balance") if legume_inputs[key] is None]
        has_soy = "kedelai" in (sequence or [])
        add("legume_mechanism", "needs_input" if sequence is None or has_soy and legume_missing else "review_required" if has_soy else "not_applicable",
            "Kedelai membuka peninjauan mekanisme fiksasi nitrogen yang bergantung nodulasi dan pengelolaan. Tidak ada kredit nitrogen atau penghematan pupuk yang dihitung.",
            legume_inputs, legume_missing if has_soy else ["sequence"] if sequence is None else [],
            "Periksa nodulasi, inokulasi, residu dan neraca hara lokal.")
        pest_inputs = {"local_pest_or_pathogen": management.get("pest_disease_weed_history"),
                       "host_range": management.get("local_host_range_evidence"),
                       "management_history": management.get("pesticide_history")}
        pest_missing = [key for key, value in pest_inputs.items() if value is None]
        add("pest_break", "needs_input" if pest_missing else "review_required",
            "Pergantian nama tanaman belum membuktikan pemutusan hama/penyakit. Organisme, inang dan riwayat pengelolaan memerlukan bukti lokal.",
            {"sequence": sequence, **pest_inputs}, pest_missing, "Validasi identifikasi organisme dan hubungan tanaman inangnya.")
        vegetation = _mapping(layers.get("vegetation"))
        series = vegetation.get("series") or []
        good = any(_mapping(s.get("summary")).get("n_good_strict", 0) > 0 for s in series)
        add("vegetation_context", "review_required" if good else "outside_coverage" if vegetation.get("status") == "outside_coverage" else "needs_input",
            "MODIS memberi konteks piksel campuran dengan QA strict-good dan gap. Sensor tetap terpisah; spesies, riwayat rotasi, tanggal tanam dan lahan kosong tidak disimpulkan.",
            vegetation, [] if good else ["strict_good_observations_in_selected_window"])
        gaez = _mapping(layers.get("gaez"))
        add("gaez_context", "review_required" if gaez.get("rows") else "outside_coverage" if gaez.get("status") == "outside_coverage" else "needs_input",
            "GAEZ adalah kategori model historis. Rezim HRLM/HILM tetap terpisah dan RCW berarti wetland rice; kategori tidak menjadi skor atau hasil lahan sekarang.",
            gaez, ["management_regime_or_explicit_unknown"] if gaez.get("rows") else ["containing_extracted_gaez_cell"])
        add("economics", "needs_input", "Ekonomi ditunda dari MVP. Referensi varietas, kesesuaian atau kehijauan satelit tidak menghasilkan keuntungan atau prediksi hasil.",
            {"status": "deferred_from_MVP", "marketable_yield": None, "profit_difference_idr_ha": None},
            ["marketable_yield", "farm_gate_price", "costs", "units", "time_and_location_basis"],
            "Pertahankan hasil ekonomi kosong sampai cakupan metode dan data lokal tersedia.")
        # Output order follows the method specification, independently of highlights.
        by_id = {finding["rule_id"]: finding for finding in findings}
        return [by_id[rule["id"]] for rule in self.method["rules"]]
