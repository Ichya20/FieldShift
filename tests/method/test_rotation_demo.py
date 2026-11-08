"""Integration checks against the real prepared data and labelled demo fixture."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
METHOD_PATH = str(ROOT / "scripts/method")
# The reference runner is also directly executable and imports its sibling files.
sys.path.insert(0, METHOD_PATH)
try:
    from scripts.method.build_rotation_demo import build_report, gaez_at_point, soil_ph_at_point
finally:
    sys.path.remove(METHOD_PATH)


def read_json(relative_path):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8-sig"))


class RotationDemoIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = read_json("specs/rotation-method-v1.json")
        cls.fixture = read_json("specs/fixtures/rotation-demo.json")
        cls.manifest = read_json("data/prepared/file-manifest.json")
        cls.report = build_report()
        cls.strategies = {item["strategy_id"]: item for item in cls.report["strategies"]}

    def test_three_distinct_filled_strategies_retain_scenario_identity(self):
        expected = {
            "existing": ["padi", "padi"],
            "candidate_1": ["padi", "jagung"],
            "candidate_2": ["padi", "kedelai"],
        }
        self.assertEqual(self.report["generation"]["generation_status"], "complete")
        self.assertEqual(self.report["generation"]["generated_count"], 2)
        self.assertEqual(self.report["generation"]["strategies"], expected)
        self.assertEqual({key: item["sequence"] for key, item in self.strategies.items()}, expected)
        self.assertEqual(len({tuple(item["sequence"]) for item in self.strategies.values()}), 3)
        self.assertTrue(self.report["is_synthetic_scenario"])
        self.assertFalse(self.report["is_verified_farm"])
        self.assertFalse(self.report["application_implemented"])

    def test_fixture_calendars_and_exposure_include_the_harvest_day(self):
        second_dates = {
            "existing": ("2025-09-29", "2025-09-30", 121),
            "candidate_1": ("2025-09-09", "2025-09-10", 101),
            "candidate_2": ("2025-08-30", "2025-08-31", 91),
        }
        for strategy_id, strategy in self.strategies.items():
            with self.subTest(strategy=strategy_id):
                self.assertEqual(len(strategy["cycles"]), 2)
                first, second = strategy["cycles"]
                self.assertEqual(first["calendar"]["field_start"], "2025-01-01")
                self.assertEqual(first["calendar"]["earliest_harvest_date"], "2025-05-01")
                self.assertEqual(first["calendar"]["latest_release_date"], "2025-05-02")
                harvest, release, occupied_days = second_dates[strategy_id]
                self.assertEqual(second["calendar"]["field_start"], "2025-06-01")
                self.assertEqual(second["calendar"]["earliest_harvest_date"], harvest)
                self.assertEqual(second["calendar"]["latest_harvest_date"], harvest)
                self.assertEqual(second["calendar"]["latest_release_date"], release)
                self.assertEqual(second["environment_window"]["start"], "2025-06-01")
                self.assertEqual(second["environment_window"]["end_exclusive"], release)
                self.assertEqual(second["environment_window"]["days_expected"], occupied_days)
                self.assertEqual(len(strategy["transitions"]), 1)
                self.assertEqual(strategy["transitions"][0]["status"], "no_calendar_conflict")
                self.assertEqual(strategy["transitions"][0]["latest_ready_date"], "2025-05-16")
                for cycle in strategy["cycles"]:
                    duration = cycle["calendar_inputs"]["duration"]
                    self.assertEqual(duration["source_kind"], "scenario_assumption")
                    self.assertEqual(duration, self.fixture["duration_assumptions"][cycle["crop_id"]])

    def test_common_horizon_environment_is_not_changed_by_crop_occupancy(self):
        context = self.report["comparison_context"]
        whole = context["whole_horizon_environment"]
        self.assertEqual((whole["start"], whole["end_exclusive"], whole["days_expected"]),
                         ("2025-01-01", "2026-01-01", 365))
        for strategy in self.strategies.values():
            self.assertEqual(strategy["whole_horizon_environment"], whole)
        self.assertEqual(context["climate_context_id"], self.fixture["climate_context_id"])
        self.assertFalse(context["is_verified_farm"])

    def test_all_twelve_rules_have_valid_statuses_and_resolvable_sources(self):
        expected_rules = {
            "coverage", "calendar", "climate_exposure", "ph_reference", "temperature_reference",
            "seasonal_et_reference", "paddy_upland_transition", "legume_mechanism", "pest_break",
            "vegetation_context", "gaez_context", "economics",
        }
        registered = {item["id"] for item in read_json("data/prepared/agronomy/source-evidence.json")["sources"]}
        registered.update(self.spec["additional_source_refs"])
        self.assertEqual({rule["id"] for rule in self.spec["rules"]}, expected_rules)
        for strategy_id, strategy in self.strategies.items():
            self.assertEqual({item["rule_id"] for item in strategy["findings"]}, expected_rules)
            for finding in strategy["findings"]:
                with self.subTest(strategy=strategy_id, rule=finding["rule_id"]):
                    self.assertTrue(set(self.spec["finding_fields"]) <= finding.keys())
                    self.assertIn(finding["status"], self.spec["check_statuses"])
                    self.assertTrue(finding["source_refs"])
                    self.assertTrue(set(finding["source_refs"]) <= registered)
                    self.assertTrue(finding["explanation"].strip())
                    self.assertTrue(finding["assumptions"])

    def test_missing_management_inputs_remain_open_in_the_full_demo(self):
        for strategy_id, strategy in self.strategies.items():
            findings = {item["rule_id"]: item for item in strategy["findings"]}
            self.assertEqual(findings["economics"]["status"], "needs_input")
            self.assertTrue(findings["economics"]["missing_inputs"])
            self.assertEqual(findings["pest_break"]["status"], "needs_input")
            transition = findings["paddy_upland_transition"]
            self.assertIsNone(transition["inputs_used"]["rice_water_regime"])
            self.assertEqual(transition["status"], "not_applicable" if strategy_id == "existing" else "needs_input")
            legume = findings["legume_mechanism"]
            self.assertEqual(legume["status"], "needs_input" if strategy_id == "candidate_2" else "not_applicable")

    def test_unavailable_outputs_stay_null_and_analysis_stays_partial(self):
        self.assertTrue(self.spec["unavailable_outputs"])
        for strategy_id, strategy in self.strategies.items():
            with self.subTest(strategy=strategy_id):
                self.assertEqual(strategy["analysis_status"], "partial")
                self.assertFalse(strategy["local_agronomic_validation"])
                for output in self.spec["unavailable_outputs"]:
                    self.assertIn(output, strategy)
                    self.assertIsNone(strategy[output])

    def test_all_390_prepared_files_still_match_their_original_hashes(self):
        entries = self.manifest["files"]
        self.assertEqual(len(entries), 390)
        self.assertEqual(len({entry["path"] for entry in entries}), 390)
        for entry in entries:
            with self.subTest(path=entry["path"]):
                actual = hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest()
                self.assertEqual(actual, entry["sha256"])
        self.assertEqual(self.report["source_integrity"]["sha256_files_verified"], 390)
        self.assertTrue(self.report["source_integrity"]["all_match_preparation_manifest"])

    def test_primary_soil_ph_uses_the_containing_cell_and_its_quantiles(self):
        point = self.fixture["coordinate"]
        result = soil_ph_at_point(point["longitude"], point["latitude"])
        self.assertEqual(result["status"], "evidence_available")
        self.assertEqual((result["row"], result["column"]), (4, 6))
        self.assertEqual((result["value"], result["q05"], result["q95"]), (5.8, 4.2, 7.8))
        self.assertEqual(result["depth"], "0-5cm")
        self.assertEqual(result["origin"], "SoilGrids_prediction_not_laboratory")
        self.assertEqual(self.report["comparison_context"]["soil_ph_0_5cm"], result)

    def test_soil_outside_the_extracted_grid_has_no_nearest_cell_fallback(self):
        for longitude, latitude in (
            (110.539999, -7.72), (110.56, -7.72),
            (110.55, -7.73), (110.55, -7.709999), (110.37, -7.8),
        ):
            with self.subTest(point=(longitude, latitude)):
                result = soil_ph_at_point(longitude, latitude)
                self.assertEqual(result["status"], "outside_coverage")
                self.assertIsNone(result["value"])
                self.assertIsNone(result.get("q05"))
                self.assertIsNone(result.get("q95"))

    def test_gaez_outside_extracted_cells_does_not_take_the_nearest_sample(self):
        point = self.fixture["coordinate"]
        covered = gaez_at_point(point["longitude"], point["latitude"])
        self.assertEqual(len(covered["rows"]), 6)
        self.assertIsNone(covered["management_regime_selected"])
        for record in covered["rows"]:
            bounds = record["bounds"]
            self.assertLessEqual(bounds["west"], point["longitude"])
            self.assertLess(point["longitude"], bounds["east"])
            self.assertLess(bounds["south"], point["latitude"])
            self.assertLessEqual(point["latitude"], bounds["north"])
        rows = read_json("data/prepared/agronomy/gaez-baseline-point.json")["rows"]
        just_outside_east = max(record["pixel_bounds"]["east"] for record in rows) + 1e-6
        for longitude, latitude in ((just_outside_east, point["latitude"]), (110.45, -7.8), (0, 0)):
            with self.subTest(point=(longitude, latitude)):
                result = gaez_at_point(longitude, latitude)
                self.assertEqual(result["rows"], [])
                self.assertIsNone(result["management_regime_selected"])


if __name__ == "__main__":
    unittest.main()
