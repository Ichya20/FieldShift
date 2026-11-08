"""Validate the audited input vocabulary and normalize its transport records."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from .models import CompareRequest, Window, finite_json, parse_date


class InvalidInput(ValueError):
    def __init__(self, details):
        super().__init__("Input tidak valid.")
        self.details = details


def fail(field, code, message):
    raise InvalidInput([{"field": field, "code": code, "message": message}])


def optional_records(value):
    """Omitted record members remain unknown, with their original types intact."""
    if isinstance(value, dict):
        value.pop("required", None)
        for child in value.values():
            optional_records(child)
    elif isinstance(value, list):
        for child in value:
            optional_records(child)


class DocumentValidator:
    def __init__(self, root: Path):
        original = root / "data/supplemental/agronomy/farm-input-complete.schema.json"
        self.schema = json.loads(original.read_text(encoding="utf-8"))
        optional_records(self.schema)
        self.schema["$id"] = "https://fieldshift.invalid/contracts/api-document-1.0"
        self.schema["title"] = "FieldShift partial input document; omitted fields remain unknown"
        # A submitted document is no longer required to identify itself as an empty template.
        self.schema["properties"]["is_template"] = {"type": "boolean"}
        Draft202012Validator.check_schema(self.schema)
        self.validator = Draft202012Validator(self.schema, format_checker=FormatChecker())

    def normalize(self, request: CompareRequest) -> dict:
        submitted = deepcopy(request.document)
        try:
            finite_json(submitted)
        except ValueError as error:
            fail("document", "invalid_json_value", str(error))
        errors = sorted(self.validator.iter_errors(submitted), key=lambda e: str(list(e.path)))
        if errors:
            raise InvalidInput([{"field": "document." + ".".join(map(str, error.path)),
                                 "code": "schema_validation", "message": "Tipe, nilai atau struktur field tidak sesuai kontrak input."}
                                for error in errors[:20]])
        normalized = deepcopy(submitted)
        planning = normalized.setdefault("planning", {})
        farm = normalized.setdefault("farm", {})
        context = normalized.setdefault("context", {})
        priorities = farm.get("priorities") or {}
        for old, canonical in (("excluded_crops", "excluded_crop_ids"),):
            if priorities.get(old) is not None:
                if planning.get(canonical) is None:
                    planning[canonical] = deepcopy(priorities[old])
                elif priorities[old] != planning[canonical]:
                    fail(f"farm.priorities.{old}", "conflicting_alias", "Isian lama dan rencana berbeda.")
        horizon = planning.get("horizon")
        if horizon is None and any(priorities.get(key) is not None for key in ("planning_horizon_start", "planning_horizon_end")):
            horizon = {"start_date": priorities.get("planning_horizon_start"), "end_exclusive": priorities.get("planning_horizon_end")}
            planning["horizon"] = horizon
        if horizon is not None:
            for old, key in (("planning_horizon_start", "start_date"), ("planning_horizon_end", "end_exclusive")):
                if priorities.get(old) is not None and priorities[old] != horizon.get(key):
                    fail(f"farm.priorities.{old}", "conflicting_alias", "Periode lama dan rencana berbeda.")
            self._window(horizon, "planning.horizon")
        if context.get("climate_window") is not None:
            self._window(context["climate_window"], "context.climate_window")
            if horizon is not None and context["climate_window"] != horizon:
                fail("context.climate_window", "comparison_window_mismatch", "Perbandingan dan konteks iklim harus memakai periode yang sama.")
        records = planning.get("existing_sequence")
        if records is not None and not 1 <= len(records) <= 3:
            fail("planning.existing_sequence", "unsupported_slot_count", "Generator mendukung satu sampai tiga slot.")
        if records is not None:
            for index, record in enumerate(records):
                self._dates(record, f"planning.existing_sequence.{index}")
                if request.input_kind == "scenario_assumption" and record.get("date_status") == "observed":
                    fail(f"planning.existing_sequence.{index}.date_status", "assumption_marked_observed", "Tanggal skenario asumsi tidak dapat diberi label observasi.")
        self._dates(farm.get("current_crop") or {}, "farm.current_crop")
        lab = farm.get("soil_lab") or {}
        if lab.get("depth_top_cm") is not None and lab.get("depth_bottom_cm") is not None and lab["depth_bottom_cm"] <= lab["depth_top_cm"]:
            fail("farm.soil_lab", "reversed_depth", "Kedalaman bawah harus lebih besar dari kedalaman atas.")
        if lab.get("field_capacity_fraction") is not None and lab.get("wilting_point_fraction") is not None and lab["field_capacity_fraction"] < lab["wilting_point_fraction"]:
            fail("farm.soil_lab", "invalid_water_retention", "Kapasitas lapang tidak dapat lebih kecil dari titik layu.")
        location = request.location.model_dump()
        selected_climate = context.get("explicit_climate_context")
        if selected_climate is not None:
            if selected_climate != "power_regional_yogyakarta":
                fail("context.explicit_climate_context", "unknown_climate_context", "Konteks iklim belum tersedia.")
            if location["climate_context_id"] is not None and location["climate_context_id"] != selected_climate:
                fail("location.climate_context_id", "conflicting_context", "Konteks iklim berbeda.")
            location["climate_context_id"] = selected_climate
        coordinate = farm.get("location") or {}
        if coordinate.get("geometry_geojson") is not None:
            fail("farm.location.geometry_geojson", "unsupported_geometry", "Versi ini menganalisis titik; analisis batas poligon belum tersedia.")
        if (coordinate.get("representative_longitude") is None) != (coordinate.get("representative_latitude") is None):
            fail("farm.location", "incomplete_coordinate", "Bujur dan lintang petak harus diisi bersama.")
        for key, farm_key in (("longitude", "representative_longitude"), ("latitude", "representative_latitude")):
            if coordinate.get(farm_key) is not None and location[key] is not None and abs(coordinate[farm_key] - location[key]) > 1e-9:
                fail(f"farm.location.{farm_key}", "location_mismatch", "Koordinat dokumen berbeda dari lokasi analisis.")
        durations = planning.get("duration_by_crop")
        duration_map = {}
        for index, record in enumerate(durations or []):
            crop_id = record.get("crop_id")
            if crop_id is None:
                fail(f"planning.duration_by_crop.{index}.crop_id", "missing_crop_id", "Catatan durasi harus menyebut tanaman.")
            if crop_id in duration_map:
                fail("planning.duration_by_crop", "duplicate_crop_duration", "Gunakan satu catatan durasi per tanaman.")
            duration_map[crop_id] = self._duration(record, request.input_kind, "planning.duration_by_crop")
        planning["duration_by_crop"] = duration_map if durations is not None else None
        if records is not None:
            planning["existing_sequence"] = [record.get("crop_id") for record in records]
        slots = [slot.model_dump() for slot in request.slot_inputs] if request.slot_inputs is not None else None
        if slots is None and records is not None:
            slots = [{"crop_id": r.get("crop_id"),
                      "production_method": r.get("establishment_method") if r.get("establishment_method") in {"direct_seeded", "transplanted"} else None,
                      "sowing_date": r.get("sowing_date"), "transplanting_date": r.get("transplanting_date"),
                      "nursery_off_main_field": r.get("nursery_separate_from_main_field")} for r in records]
        if slots is not None and records is not None and len(slots) != len(records):
            fail("slot_inputs", "slot_count_mismatch", "Jumlah input kalender dan urutan harus sama.")
        start_dates = planning.get("slot_start_dates")
        if start_dates is not None and len(start_dates) > 3:
            fail("planning.slot_start_dates", "unsupported_slot_count", "Paling banyak tiga tanggal mulai.")
        if slots is not None:
            for index, slot in enumerate(slots):
                if records is not None and records[index].get("duration") is not None:
                    duration = records[index]["duration"]
                    if duration.get("crop_id") not in (None, records[index].get("crop_id")):
                        fail(f"planning.existing_sequence.{index}.duration", "duration_crop_mismatch", "Tanaman pada durasi dan slot berbeda.")
                    slot["duration"] = self._duration(duration, request.input_kind, f"planning.existing_sequence.{index}.duration")
                self._dates(slot, f"slot_inputs.{index}")
                start = slot.get("sowing_date") if slot.get("production_method") == "direct_seeded" else slot.get("transplanting_date") if slot.get("production_method") == "transplanted" else None
                if start_dates is not None and index < len(start_dates) and start is not None and start != start_dates[index]:
                    fail(f"slot_inputs.{index}", "slot_start_mismatch", "Tanggal okupansi petak harus sama dengan tanggal slot.")
                if records is not None:
                    method = records[index].get("establishment_method")
                    if method in {"direct_seeded", "transplanted"} and slot.get("production_method") is not None and method != slot["production_method"]:
                        fail(f"slot_inputs.{index}.production_method", "calendar_record_mismatch", "Metode tanam slot dan catatan rotasi berbeda.")
                    nursery = records[index].get("nursery_separate_from_main_field")
                    if nursery is not None and slot.get("nursery_off_main_field") is not None and nursery != slot["nursery_off_main_field"]:
                        fail(f"slot_inputs.{index}.nursery_off_main_field", "calendar_record_mismatch", "Lokasi persemaian slot dan catatan rotasi berbeda.")
                    for key in ("sowing_date", "transplanting_date"):
                        if records[index].get(key) is not None and slot.get(key) is not None and records[index][key] != slot[key]:
                            fail(f"slot_inputs.{index}.{key}", "calendar_record_mismatch", "Tanggal slot dan catatan rotasi berbeda.")
        return {"location": location, "document": normalized, "submitted_document": submitted,
                "input_kind": request.input_kind, "assumptions": list(request.assumptions), "slot_inputs": slots}

    @staticmethod
    def _duration(record, input_kind, field):
        minimum, maximum = record.get("minimum_days"), record.get("maximum_days")
        if (minimum is not None and not 1 <= minimum <= 1000) or (maximum is not None and not 1 <= maximum <= 1000):
            fail(field, "invalid_duration", "Durasi kalender harus 1–1.000 hari.")
        if minimum is not None and maximum is not None and minimum > maximum:
            fail(field, "reversed_duration", "Rentang durasi terbalik.")
        source_min, source_max = record.get("source_minimum_days"), record.get("source_maximum_days")
        if source_min is not None and source_max is not None and source_min > source_max:
            fail(field, "reversed_source_duration", "Rentang durasi sumber terbalik.")
        converted = any(original is not None and used is not None and original != used
                        for original, used in ((source_min, minimum), (source_max, maximum)))
        if converted and record.get("normalization_policy") not in {"explicit_source_integer_alternative", "documented_external_conversion"}:
            fail(field, "undeclared_duration_conversion", "Durasi berbeda dari sumber; kebijakan normalisasi harus dinyatakan.")
        if converted and not record.get("normalization_note"):
            fail(field, "undocumented_duration_conversion", "Perubahan durasi sumber memerlukan catatan eksplisit.")
        if record.get("normalization_policy") == "documented_external_conversion" and not record.get("normalization_note"):
            fail(field, "undocumented_duration_conversion", "Konversi durasi memerlukan catatan eksplisit.")
        return {"min_days": minimum, "max_days": maximum,
                "basis": record.get("basis_event") if record.get("counting_convention") == "elapsed_day_zero" else None,
                "source_kind": input_kind, "source_id": record.get("source_ref"),
                "submitted_provenance": {key: record.get(key) for key in (
                    "source_origin_wording", "source_minimum_days", "source_maximum_days",
                    "counting_convention", "normalization_policy", "normalization_note", "cultivar")}}

    @staticmethod
    def _window(value, field):
        if value.get("start_date") is not None and value.get("end_exclusive") is not None:
            try:
                Window(**value)
            except ValueError:
                fail(field, "invalid_window", "Periode harus berurutan, paling panjang 3.660 hari, dengan tanggal 1900–2100.")

    @staticmethod
    def _dates(record, field):
        for key, value in record.items():
            if isinstance(value, str) and (key.endswith("_date") or key in {"sowing_date", "transplanting_date", "harvest_date"}):
                try:
                    parse_date(value)
                except ValueError:
                    fail(f"{field}.{key}", "invalid_date", "Tanggal kalender tidak valid.")
        order = [record[key] for key in ("sowing_date", "transplanting_date", "harvest_date", "expected_harvest_date") if record.get(key) is not None]
        if order != sorted(order):
            fail(field, "reversed_crop_dates", "Urutan semai, pindah tanam dan panen tidak valid.")
