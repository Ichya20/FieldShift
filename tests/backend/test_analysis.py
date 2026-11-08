"""Regression checks for analysis semantics, not an HTTP transport contract."""
from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path
import unittest

from backend.fieldshift.analysis import AnalysisService
from scripts.method.climate_reference import historical_analogue, window_summary


ROOT = Path(__file__).resolve().parents[2]


class FakeRepository:
    def __init__(self):
        self.method = json.loads((ROOT / "specs/rotation-method-v1.json").read_text(encoding="utf8"))
        self.crops = json.loads((ROOT / "data/prepared/agronomy/crop-reference.json").read_text(encoding="utf8"))["crops"]
        self.daily = {}
        for year in range(1991, 2027):
            first, end = date(year, 1, 1), date(year + 1, 1, 1)
            for offset in range((end - first).days):
                self.daily[(first + timedelta(days=offset)).isoformat()] = {
                    "PRECTOTCORR": 2.0, "eto_fao56_mm_day": 3.0,
                    "T2M": 26.0, "eto_operational_guard": 0.0}

    def climate_window(self, location, start, end, time_mode):
        if not location.get("climate_context_id"):
            return {"status": "needs_input", "summary": None, "source_refs": ["nasa-power"]}
        summary = historical_analogue(self.daily, start, end) if time_mode == "historical_analogue_not_forecast" else window_summary(self.daily, start, end)
        return {"status": "evidence_available", "summary": summary,
                "source_refs": ["nasa-power", "fao56"], "support": "explicit_regional_context"}

    def context(self, location, window=None, time_mode="historical_replay"):
        climate = self.climate_window(location, window["start_date"], window["end_exclusive"], time_mode) if window else {"status": "needs_input", "summary": None}
        return {"location": {**location, "is_verified_farm": False}, "window": window,
                "time_mode": time_mode, "missing_inputs": [], "warnings": [],
                "layers": {
                    "climate": climate,
                    "soil": {"status": "evidence_available", "source_refs": ["soil-manifest"],
                             "ph_0_5cm": {"status": "evidence_available", "value": 5.8, "q05": 4.2, "q95": 7.9,
                                           "origin": "soilgrids_prediction", "depth": "0-5cm"}},
                    "vegetation": {"status": "evidence_available", "series": [{"product": "MOD13Q1", "summary": {"n_good_strict": 3}}]},
                    "gaez": {"status": "historical_reference_only", "rows": [{"crop_code": "RCW", "class_code": 4, "regime": "HRLM"}]},
                }}


def request():
    return {
        "location": {"example_id": "klaten_cropland_primary", "climate_context_id": "power_regional_yogyakarta"},
        "input_kind": "scenario_assumption", "assumptions": ["Hypothetical continuation and calendar; not farm history."],
        "document": {"farm": {}, "planning": {
            "horizon": {"start_date": "2025-01-01", "end_exclusive": "2026-01-01"},
            "allowed_crop_ids": ["padi", "jagung", "kedelai"], "excluded_crop_ids": [],
            "existing_sequence": ["padi", "padi"], "slot_start_dates": ["2025-01-01", "2025-06-01"],
            "locked_prefix_length": 1, "continuation_confirmed": True, "preparation_gap_days": 14,
            "duration_by_crop": {crop: {"min_days": duration, "max_days": duration, "basis": "sowing",
                                        "source_kind": "scenario_assumption", "source_id": "assumed-duration-" + crop}
                                 for crop, duration in [("padi", 120), ("jagung", 100), ("kedelai", 90)]},
            "selected_priorities": []},
            "context": {"time_mode": "historical_replay"}},
        "slot_inputs": [{"production_method": "direct_seeded", "sowing_date": start, "transplanting_date": None,
                         "nursery_off_main_field": None} for start in ["2025-01-01", "2025-06-01"]],
    }


def finding(strategy, rule_id):
    return next(row for row in strategy["findings"] if row["rule_id"] == rule_id)


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repository = FakeRepository()
        cls.service = AnalysisService(cls.repository)

    def test_complete_scenario_has_three_distinct_neutral_strategies_and_all_rules(self):
        payload = request()
        before = deepcopy(payload)
        result = self.service.compare(payload)
        self.assertEqual(payload, before)
        self.assertEqual([s["sequence"] for s in result["strategies"]], [["padi", "padi"], ["padi", "jagung"], ["padi", "kedelai"]])
        self.assertFalse(result["local_agronomic_validation"])
        self.assertEqual(result["analysis_status"], "partial")
        for strategy in result["strategies"]:
            self.assertEqual([x["rule_id"] for x in strategy["findings"]], [r["id"] for r in self.repository.method["rules"]])
            self.assertTrue(all(set(self.repository.method["finding_fields"]) <= set(x) for x in strategy["findings"]))
            self.assertTrue(all(x["status"] in self.repository.method["check_statuses"] for x in strategy["findings"]))
            self.assertTrue(all(strategy[name] is None for name in self.repository.method["unavailable_outputs"]))
        self.assertIn("bukan peringkat", result["strategies"][1]["generated_reason"])
        self.assertEqual(result["input_sources"]["assumed-duration-padi"]["verification"], "Submitted identifier; does not establish external source verification.")

    def test_missing_continuation_never_fabricates_existing_or_alternatives(self):
        payload = request()
        payload["document"]["planning"]["existing_sequence"] = None
        payload["document"]["planning"]["continuation_confirmed"] = None
        result = self.service.compare(payload)
        self.assertEqual(len(result["strategies"]), 3)
        self.assertTrue(all(s["sequence"] is None and s["cycles"] == [] for s in result["strategies"]))
        self.assertIn("planning.existing_sequence", result["missing_inputs"])

    def test_whole_horizon_is_invariant_and_crop_windows_vary_only_by_calendar(self):
        result = self.service.compare(request())
        whole = result["context"]["layers"]["climate"]
        self.assertTrue(all(s["whole_horizon_environment"] == whole for s in result["strategies"]))
        second_days = [s["cycles"][1]["environment_windows"][0]["climate"]["summary"]["days_expected"] for s in result["strategies"]]
        self.assertEqual(second_days, [121, 101, 91])
        self.assertEqual(whole["summary"]["days_expected"], 365)

    def test_priorities_highlight_findings_without_reordering_or_ranking(self):
        payload = request()
        plain = self.service.compare(payload)
        payload["document"]["planning"]["selected_priorities"] = ["water_context", "economic_information"]
        selected = self.service.compare(payload)
        self.assertEqual(plain["generation"], selected["generation"])
        for left, right in zip(plain["strategies"], selected["strategies"]):
            self.assertEqual(left["sequence"], right["sequence"])
            self.assertEqual(left["findings"], right["findings"])
            self.assertIn("climate_exposure", right["highlighted_rule_ids"])
            self.assertIn("economics", right["highlighted_rule_ids"])

    def test_uncertain_duration_preserves_endpoint_windows(self):
        payload = request()
        payload["document"]["planning"]["duration_by_crop"]["jagung"]["max_days"] = 110
        result = self.service.compare(payload)
        cycle = result["strategies"][1]["cycles"][1]
        endpoints = cycle["environment_windows"]
        self.assertEqual([e["endpoint"] for e in endpoints], ["earliest", "latest"])
        self.assertEqual([e["climate"]["summary"]["days_expected"] for e in endpoints], [101, 111])
        self.assertIn("not universal", cycle["endpoint_interpretation"])
        self.assertLess(endpoints[1]["climate"]["summary"]["rain_minus_reference_eto_total_mm"], endpoints[0]["climate"]["summary"]["rain_minus_reference_eto_total_mm"])

    def test_locked_carry_in_preserves_origin_and_clips_exposure(self):
        payload = request()
        payload["document"]["planning"]["slot_start_dates"][0] = "2024-12-15"
        payload["slot_inputs"][0]["sowing_date"] = "2024-12-15"
        result = self.service.compare(payload)
        cycle = result["strategies"][0]["cycles"][0]
        self.assertEqual(cycle["calendar"]["field_start"], "2024-12-15")
        self.assertEqual(cycle["environment_windows"][0]["start_date"], "2025-01-01")
        self.assertEqual(cycle["calendar"]["earliest_harvest_date"], "2025-04-14")

    def test_finished_crop_before_horizon_is_input_conflict_not_ongoing(self):
        payload = request()
        payload["document"]["planning"]["slot_start_dates"][0] = "2024-01-01"
        payload["slot_inputs"][0]["sowing_date"] = "2024-01-01"
        result = self.service.compare(payload)
        self.assertEqual(result["analysis_status"], "partial")
        self.assertEqual(finding(result["strategies"][0], "calendar")["status"], "input_conflict")
        self.assertTrue(all(e["status"] == "outside_horizon" for e in result["strategies"][0]["cycles"][0]["environment_windows"]))

    def test_conflicting_main_field_dates_are_reported_not_hidden(self):
        payload = request()
        payload["document"]["planning"]["slot_start_dates"][1] = "2025-02-01"
        payload["slot_inputs"][1]["sowing_date"] = "2025-02-01"
        result = self.service.compare(payload)
        self.assertEqual(result["strategies"][0]["transitions"][0]["status"], "calendar_conflict")
        self.assertEqual(finding(result["strategies"][0], "calendar")["status"], "input_conflict")
        self.assertEqual(result["analysis_status"], "partial")

    def test_potential_conflict_is_review_and_unknown_gap_is_unknown(self):
        payload = request()
        duration = payload["document"]["planning"]["duration_by_crop"]["padi"]
        duration.update(min_days=50, max_days=200)
        result = self.service.compare(payload)
        self.assertEqual(result["strategies"][0]["transitions"][0]["status"], "potential_calendar_conflict")
        self.assertEqual(finding(result["strategies"][0], "calendar")["status"], "review_required")
        payload["document"]["planning"]["preparation_gap_days"] = None
        result = self.service.compare(payload)
        self.assertEqual(finding(result["strategies"][0], "calendar")["status"], "needs_input")

    def test_no_implicit_establishment_or_dates(self):
        payload = request()
        del payload["slot_inputs"]
        result = self.service.compare(payload)
        self.assertTrue(all(c["calendar"]["status"] == "needs_input" for s in result["strategies"] for c in s["cycles"]))
        self.assertTrue(all(c["calendar"]["field_start"] is None for s in result["strategies"] for c in s["cycles"]))

    def test_malformed_calendar_date_marks_invalid_input(self):
        payload = request()
        payload["slot_inputs"][0]["sowing_date"] = "2025-02-30"
        result = self.service.compare(payload)
        self.assertEqual(result["analysis_status"], "invalid_input")

    def test_explicit_slot_date_disagreement_is_calendar_conflict(self):
        payload = request()
        payload["slot_inputs"][1]["sowing_date"] = "2025-06-02"
        result = self.service.compare(payload)
        self.assertEqual(finding(result["strategies"][0], "calendar")["status"], "input_conflict")

    def test_transplanting_keeps_sowing_based_duration_and_reviews_nursery(self):
        payload = request()
        payload["slot_inputs"][0].update(production_method="transplanted", sowing_date="2024-12-10", transplanting_date="2025-01-01", nursery_off_main_field=True)
        result = self.service.compare(payload)
        cycle = result["strategies"][0]["cycles"][0]
        self.assertEqual(cycle["calendar"]["earliest_harvest_date"], "2025-04-09")
        self.assertEqual(cycle["calendar"]["field_start"], "2025-01-01")
        self.assertIn("nursery_location_ref_unknown", finding(result["strategies"][0], "calendar")["missing_inputs"])

    def test_no_explicit_climate_context_gives_no_climate_fallback(self):
        payload = request()
        del payload["location"]["climate_context_id"]
        result = self.service.compare(payload)
        for strategy in result["strategies"]:
            self.assertEqual(finding(strategy, "climate_exposure")["status"], "needs_input")
            self.assertEqual(finding(strategy, "temperature_reference")["status"], "needs_input")

    def test_missing_climate_mode_does_not_skip_calendar_occupation_validation(self):
        payload = request()
        payload["document"]["context"]["time_mode"] = None
        payload["document"]["planning"]["slot_start_dates"][0] = "2024-01-01"
        payload["slot_inputs"][0]["sowing_date"] = "2024-01-01"
        result = self.service.compare(payload)
        self.assertIsNone(result["context"]["time_mode"])
        self.assertEqual(finding(result["strategies"][0], "calendar")["status"], "input_conflict")
        self.assertEqual(finding(result["strategies"][0], "climate_exposure")["status"], "needs_input")

    def test_future_analogue_is_labeled_and_retains_source_cohorts(self):
        payload = request()
        planning = payload["document"]["planning"]
        planning["horizon"] = {"start_date": "2050-01-01", "end_exclusive": "2051-01-01"}
        planning["slot_start_dates"] = ["2050-01-01", "2050-06-01"]
        for slot, start in zip(payload["slot_inputs"], planning["slot_start_dates"]):
            slot["sowing_date"] = start
        payload["document"]["context"]["time_mode"] = "historical_analogue_not_forecast"
        result = self.service.compare(payload)
        summary = result["context"]["layers"]["climate"]["summary"]
        self.assertEqual(summary["mode"], "historical_analogue_not_forecast")
        self.assertEqual(summary["counts_by_metric"]["temperature_mean_c"], 22)
        self.assertTrue(summary["mapped_windows"])
        self.assertEqual(finding(result["strategies"][0], "temperature_reference")["status"], "evidence_available")

    def test_farmer_reported_lab_ph_requires_provenance_and_keeps_zero(self):
        payload = request()
        payload["document"]["farm"]["soil_lab"] = {"ph_h2o": 0}
        result = self.service.compare(payload)
        row = finding(result["strategies"][0], "ph_reference")
        self.assertEqual(row["status"], "needs_input")
        self.assertEqual(row["inputs_used"]["soil_ph"]["reported_value"], 0)
        self.assertEqual(row["inputs_used"]["soil_ph"]["origin"], "scenario_assumed_laboratory_record")
        payload["input_kind"] = "user_reported"
        payload["document"]["farm"]["soil_lab"].update(method="pH water documented ratio", laboratory="reported-lab", sampling_date="2025-01-01", depth_top_cm=0, depth_bottom_cm=5)
        result = self.service.compare(payload)
        row = finding(result["strategies"][0], "ph_reference")
        self.assertEqual(row["inputs_used"]["soil_ph"]["value"], 0)
        self.assertEqual(row["inputs_used"]["soil_ph"]["origin"], "user_reported_laboratory_record_not_verified")
        self.assertEqual(row["inputs_used"]["crop_comparisons"][0]["mean_relation"], "outside_reference_optimum_requires_review")

    def test_direct_seeding_never_proves_rice_water_regime(self):
        result = self.service.compare(request())
        transition = finding(result["strategies"][1], "paddy_upland_transition")
        self.assertEqual(transition["status"], "needs_input")
        self.assertIsNone(transition["inputs_used"]["rice_water_regime"])
        self.assertIn("rice_water_regime", transition["missing_inputs"])

    def test_supplied_management_still_requires_local_review_and_has_no_benefits(self):
        payload = request()
        payload["document"]["farm"] = {
            "current_crop": {"crop_id": "padi", "rice_water_regime": "flooded_paddy"},
            "irrigation": {"drainage_condition": "good_reported", "water_control": "can_supply_and_drain_reported"},
            "management": {"soil_management_for_transition": [], "nodulation_observations": [], "legume_inoculation": [],
                           "residue_fate": [], "nutrient_balance": [], "pest_disease_weed_history": [],
                           "local_host_range_evidence": [], "pesticide_history": []}}
        result = self.service.compare(payload)
        soybean = result["strategies"][2]
        for rule in ["legume_mechanism", "pest_break", "paddy_upland_transition"]:
            self.assertEqual(finding(soybean, rule)["status"], "review_required")
        self.assertIsNone(soybean["nitrogen_credit_kg_ha"])
        self.assertIsNone(soybean["profit_difference_idr_ha"])

    def test_current_rice_water_regime_does_not_assign_future_rice_slots(self):
        payload = request()
        planning = payload["document"]["planning"]
        planning.update(existing_sequence=["padi", "padi", "jagung"], slot_start_dates=["2025-01-01", "2025-05-15", "2025-10-01"])
        payload["slot_inputs"] = [{"production_method": "direct_seeded", "sowing_date": start} for start in planning["slot_start_dates"]]
        payload["document"]["farm"] = {"current_crop": {"crop_id": "padi", "rice_water_regime": "flooded_paddy"}}
        result = self.service.compare(payload)
        row = finding(result["strategies"][0], "paddy_upland_transition")
        self.assertIsNone(row["inputs_used"]["rice_transitions"][0]["rice_water_regime"])
        self.assertEqual(row["status"], "needs_input")

    def test_baseline_per_slot_duration_is_not_applied_to_candidates(self):
        payload = request()
        payload["slot_inputs"][1]["duration"] = {"min_days": 70, "max_days": 70, "basis": "sowing", "source_kind": "scenario_assumption", "source_id": "explicit-baseline-slot"}
        result = self.service.compare(payload)
        self.assertEqual(result["strategies"][0]["cycles"][1]["calendar_inputs"]["duration"]["min_days"], 70)
        self.assertEqual(result["strategies"][1]["cycles"][1]["calendar_inputs"]["duration"]["min_days"], 100)

    def test_locked_crop_preserves_per_slot_duration_in_every_strategy(self):
        payload = request()
        payload["slot_inputs"][0]["duration"] = {"min_days": 70, "max_days": 70, "basis": "sowing", "source_kind": "scenario_assumption", "source_id": "explicit-locked-duration"}
        result = self.service.compare(payload)
        self.assertTrue(all(s["cycles"][0]["calendar"]["earliest_harvest_date"] == "2025-03-12" for s in result["strategies"]))
        self.assertIn("explicit-locked-duration", result["input_sources"])

    def test_baseline_derived_production_is_not_assigned_to_changed_crops(self):
        payload = request()
        for slot in payload["slot_inputs"]:
            slot["crop_id"] = "padi"
        result = self.service.compare(payload)
        self.assertEqual(result["strategies"][0]["cycles"][1]["calendar"]["status"], "calendar_computed")
        for strategy in result["strategies"][1:]:
            self.assertEqual(strategy["cycles"][1]["calendar"]["status"], "needs_input")
            self.assertIsNone(strategy["cycles"][1]["calendar_inputs"]["production_method"])

    def test_recorded_harvest_disagreement_is_visible(self):
        payload = request()
        payload["submitted_document"] = {"planning": {"existing_sequence": [{"crop_id": "padi", "harvest_date": "2025-03-01"}, {"crop_id": "padi"}]}}
        result = self.service.compare(payload)
        self.assertEqual(finding(result["strategies"][0], "calendar")["status"], "input_conflict")
        self.assertIn("recorded_harvest_outside_duration_range", [i["code"] for i in result["strategies"][0]["cycles"][0]["issues"]])
        self.assertTrue(all(finding(s, "calendar")["status"] == "input_conflict" for s in result["strategies"]))

    def test_locked_slot_zero_gap_overrides_global_with_provenance(self):
        payload = request()
        payload["submitted_document"] = {"planning": {"existing_sequence": [{"crop_id": "padi", "preparation_gap_days": 0}, {"crop_id": "padi"}]}}
        result = self.service.compare(payload)
        for strategy in result["strategies"]:
            self.assertEqual(strategy["transitions"][0]["preparation_gap_days"], 0)
            self.assertEqual(strategy["transitions"][0]["preparation_gap_source"], "planning.existing_sequence[0].preparation_gap_days")

    def test_mutable_slot_gap_does_not_propagate_to_candidates(self):
        payload = request()
        planning = payload["document"]["planning"]
        planning["locked_prefix_length"] = 0
        payload["submitted_document"] = {"planning": {"existing_sequence": [{"crop_id": "padi", "preparation_gap_days": 0}, {"crop_id": "padi"}]}}
        result = self.service.compare(payload)
        self.assertEqual(result["strategies"][0]["transitions"][0]["preparation_gap_days"], 0)
        self.assertTrue(all(s["transitions"][0]["preparation_gap_days"] == 14 for s in result["strategies"][1:]))

    def test_explicit_slot_nursery_reference_closes_only_its_resource_input(self):
        payload = request()
        payload["slot_inputs"][0].update(production_method="transplanted", sowing_date="2024-12-10", transplanting_date="2025-01-01", nursery_off_main_field=True)
        payload["submitted_document"] = {"planning": {"existing_sequence": [{"crop_id": "padi", "nursery_location_ref": "explicit-separate-nursery"}, {"crop_id": "padi"}]}}
        result = self.service.compare(payload)
        self.assertNotIn("nursery_location_ref_unknown", finding(result["strategies"][0], "calendar")["missing_inputs"])


if __name__ == "__main__":
    unittest.main()
