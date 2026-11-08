"""HTTP integration tests over real, immutable public evidence snapshots.

Run: .venv/Scripts/python.exe -m unittest discover -s tests/backend -p test_api.py -v
No network server, downloads, farm-data writes or evidence mutations are used.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
import csv
import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
PRIMARY = "klaten_cropland_primary"
PREFIX = "/api/v1"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def records(payload, field):
    """Collection envelopes are incidental; record identity is the contract."""
    return payload if isinstance(payload, list) else payload[field]


class APIIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from backend.fieldshift.app import create_app
        from backend.fieldshift.repository import DataRepository
        cls.create_app = staticmethod(create_app)
        cls.repository = DataRepository(ROOT)
        cls.client = TestClient(create_app(repository=cls.repository))
        cls.before = {name: sha(ROOT / name) for name in (
            "data/prepared/file-manifest.json", "data/supplemental/file-manifest.json",
            "data/prepared/climate/daily.csv", "data/prepared/vegetation/modis_16day_qa.csv",
            "data/supplemental/environment/MYD13Q1-supplemental-qa.csv",
            "data/supplemental/agronomy/farm-input-complete.schema.json",
            "data/supplemental/agronomy/farm-input-complete-template.json",
        )}

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        for name, expected in cls.before.items():
            if sha(ROOT / name) != expected:
                raise AssertionError(f"Read-only HTTP requests changed evidence: {name}")

    def context(self, **changes):
        request = {"location": {"example_id": PRIMARY},
                   "window": {"start_date": "2025-05-01", "end_exclusive": "2025-09-01"},
                   "time_mode": "historical_replay"}
        request.update(changes)
        return self.client.post(PREFIX + "/context", json=request)

    def demo(self):
        response = self.client.get(PREFIX + "/demo")
        self.assertEqual(response.status_code, 200, response.text[:500])
        payload = response.json()
        self.assertIn("request", payload)
        self.assertIn("analysis", payload)
        return payload

    def assert_finite_json(self, value):
        if isinstance(value, dict):
            for child in value.values():
                self.assert_finite_json(child)
        elif isinstance(value, list):
            for child in value:
                self.assert_finite_json(child)
        elif isinstance(value, float):
            self.assertTrue(math.isfinite(value))

    def assert_error(self, response, status, code):
        self.assertEqual(response.status_code, status, response.text[:500])
        error = response.json()["error"]
        self.assertEqual(error["code"], code)
        self.assertIsInstance(error["message"], str)
        self.assertIsInstance(error["details"], list)
        self.assert_finite_json(error)

    def assert_source_refs_resolve(self, value, sources):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "source_refs":
                    for identifier in child:
                        self.assertIn(identifier, sources, f"Unresolved source identifier {identifier}")
                else:
                    self.assert_source_refs_resolve(child, sources)
        elif isinstance(value, list):
            for child in value:
                self.assert_source_refs_resolve(child, sources)

    def test_discovery_routes_expose_real_sources_contract_and_examples(self):
        for route in ("/health", PREFIX + "/catalog", PREFIX + "/locations", PREFIX + "/crops", PREFIX + "/input-contract"):
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200, response.text[:400])
                self.assert_finite_json(response.json())
        catalog = self.client.get(PREFIX + "/catalog").json()
        self.assertEqual(catalog["project"], "FieldShift")
        self.assertIn("historical_analogue_not_forecast", catalog["time_modes"])
        locations = records(self.client.get(PREFIX + "/locations").json(), "locations")
        self.assertEqual({row["id"] for row in locations}, {PRIMARY, "klaten_cropland_candidate"})
        self.assertTrue(all(row["is_verified_farm"] is False for row in locations))
        crops = records(self.client.get(PREFIX + "/crops").json(), "crops")
        self.assertEqual({crop["crop_id"] for crop in crops}, {"padi", "jagung", "kedelai"})
        contract = self.client.get(PREFIX + "/input-contract").json()
        text = json.dumps(contract)
        self.assertIn("planning", text)
        self.assertIn("duration_by_crop", text)
        self.assertIn("additionalProperties", text)
        health = self.client.get("/health").json()
        self.assertEqual(health["data_integrity"], "verified_at_load")
        self.assertEqual(health["storage"], "stateless_read_only")
        for source in self.repository.sources().values():
            if source.get("path") and source.get("sha256"):
                self.assertEqual(sha(ROOT / source["path"]), source["sha256"].lower())

    def test_historical_context_has_known_numbers_and_sensor_separation(self):
        response = self.context()
        self.assertEqual(response.status_code, 200, response.text[:500])
        payload = response.json()
        climate = payload["layers"]["climate"]
        summary = climate["summary"]
        self.assertAlmostEqual(summary["rainfall_total_mm"], 733.79, places=4)
        self.assertAlmostEqual(summary["reference_eto_total_mm"], 441.2481, places=4)
        self.assertAlmostEqual(summary["rain_minus_reference_eto_total_mm"], 292.5419, places=4)
        self.assertEqual(summary["days_expected"], 123)
        vegetation = payload["layers"]["vegetation"]
        self.assertTrue(vegetation["support"]["products_kept_separate"])
        self.assertFalse(vegetation["support"]["interpolated"])
        self.assertEqual({series["product"] for series in vegetation["series"]}, {"MOD13Q1", "MYD13Q1"})
        for series in vegetation["series"]:
            good = [row for row in series["observations"] if row["quality_status"] == "good_strict"]
            self.assertEqual(series["summary"]["n_good_strict"], len(good))
            self.assertIsNone(series["support"]["collection_version"])
            self.assertTrue(series["support"]["mixed_pixel"])
            if good:
                self.assertAlmostEqual(series["summary"]["ndvi_good_mean"], sum(row["ndvi"] for row in good) / len(good))
        sources = payload.get("sources", self.repository.sources())
        self.assert_source_refs_resolve(payload, sources)
        self.assert_finite_json(payload)

    def test_recent_partial_preserves_metric_specific_nulls(self):
        response = self.context(window={"start_date": "2026-11-01", "end_exclusive": "2026-11-06"}, time_mode="recent_partial")
        self.assertEqual(response.status_code, 200, response.text[:500])
        climate = response.json()["layers"]["climate"]
        self.assertEqual(climate["status"], "review_required")
        self.assertAlmostEqual(climate["summary"]["rainfall_total_mm"], 25.09, places=4)
        self.assertIsNone(climate["summary"]["reference_eto_total_mm"])
        self.assertIsNone(climate["summary"]["rain_minus_reference_eto_total_mm"])
        self.assertEqual(climate["summary"]["valid_days"]["reference_eto_total_mm"], 2)
        self.assertTrue(climate["warnings"])

    def test_analogue_is_labelled_and_february_29_is_not_inserted(self):
        response = self.context(window={"start_date": "2028-02-29", "end_exclusive": "2028-03-02"}, time_mode="historical_analogue_not_forecast")
        self.assertEqual(response.status_code, 200, response.text[:500])
        summary = response.json()["layers"]["climate"]["summary"]
        self.assertEqual(summary["mode"], "historical_analogue_not_forecast")
        self.assertEqual(summary["counts_by_metric"]["rainfall_total_mm"], 8)
        self.assertEqual(len(summary["skipped_years"]), 22)
        self.assertTrue(all(year["reason"] == "invalid_february_29" for year in summary["skipped_years"]))

    def test_outside_location_never_receives_nearest_example(self):
        response = self.context(location={"longitude": 106.8, "latitude": -6.2})
        self.assertEqual(response.status_code, 200, response.text[:500])
        payload = response.json()
        self.assertEqual(payload["location"]["id"], "custom_coordinate")
        self.assertIsNone(payload["location"]["example_id"])
        self.assertIsNone(payload["layers"]["climate"]["summary"])
        self.assertEqual(payload["layers"]["vegetation"]["status"], "outside_coverage")
        self.assertEqual(payload["layers"]["vegetation"]["series"], [])
        self.assertEqual(payload["layers"]["soil"]["status"], "outside_coverage")
        self.assertEqual(payload["layers"]["landcover"]["footprints"], [])
        explicit = self.context(location={"longitude": 106.8, "latitude": -6.2, "climate_context_id": "power_regional_yogyakarta"})
        self.assertEqual(explicit.status_code, 200, explicit.text[:500])
        assigned = explicit.json()["layers"]["climate"]
        self.assertEqual(assigned["support"]["assignment"], "explicit_user_context")

    def test_cloudy_only_window_has_null_primary_vi(self):
        with (ROOT / "data/prepared/vegetation/modis_16day_qa.csv").open(newline="", encoding="utf-8") as stream:
            cloudy = next(row for row in csv.DictReader(stream) if row["point_id"] == PRIMARY and "reliability_cloudy" in row["quality_reason"])
        observed = date.fromisoformat(cloudy["selected_observation_date"])
        response = self.context(window={"start_date": observed.isoformat(), "end_exclusive": (observed + timedelta(days=1)).isoformat()})
        self.assertEqual(response.status_code, 200, response.text[:500])
        terra = next(series for series in response.json()["layers"]["vegetation"]["series"] if series["product"] == "MOD13Q1")
        self.assertEqual(terra["summary"]["n_good_strict"], 0)
        self.assertIsNone(terra["summary"]["ndvi_good_mean"])
        self.assertIsNone(terra["summary"]["evi_good_mean"])
        self.assertFalse(terra["summary"]["interpolated"])

    def test_demo_request_round_trips_as_explicit_hypothetical_comparison(self):
        demo = self.demo()
        self.assertEqual(demo["request"]["input_kind"], "scenario_assumption")
        self.assertTrue(demo["request"]["assumptions"])
        response = self.client.post(PREFIX + "/compare", json=demo["request"])
        self.assertEqual(response.status_code, 200, response.text[:600])
        analysis = response.json()
        self.assertEqual(analysis["input_kind"], "scenario_assumption")
        self.assertFalse(analysis["local_agronomic_validation"])
        strategies = analysis["strategies"]
        self.assertEqual([row["strategy_id"] for row in strategies], ["existing", "candidate_1", "candidate_2"])
        self.assertEqual(len({tuple(row["sequence"]) for row in strategies}), 3)
        horizon = [strategy["whole_horizon_environment"] for strategy in strategies]
        self.assertEqual(horizon[0], horizon[1])
        self.assertEqual(horizon[1], horizon[2])
        for strategy in strategies:
            self.assertFalse(strategy["local_agronomic_validation"])
            for key in self.repository.method["unavailable_outputs"]:
                self.assertIn(key, strategy)
                self.assertIsNone(strategy[key], f"Unsupported claim should remain null: {key}")
            self.assertTrue(strategy["cycles"])
        self.assertEqual(analysis["generation"], demo["analysis"]["generation"])
        sources = analysis.get("sources", {**self.repository.sources(), **analysis.get("input_sources", {})})
        self.assert_source_refs_resolve(analysis, sources)
        self.assert_finite_json(analysis)

    def test_partial_input_does_not_create_farmer_history_or_priorities(self):
        request = {"location": {"example_id": PRIMARY}, "input_kind": "user_reported", "document": {}}
        response = self.client.post(PREFIX + "/compare", json=request)
        self.assertEqual(response.status_code, 200, response.text[:600])
        result = response.json()
        self.assertEqual(result["analysis_status"], "partial")
        self.assertTrue(result["missing_inputs"])
        self.assertIsNone(result["context"]["layers"]["climate"]["summary"])
        for strategy in result["strategies"]:
            self.assertIsNone(strategy["sequence"])
            self.assertEqual(strategy["cycles"], [])
            self.assertEqual(strategy["highlighted_rule_ids"], [])
            for key in self.repository.method["unavailable_outputs"]:
                self.assertIsNone(strategy[key])

    def test_missing_durations_preserve_sequences_but_never_invent_harvest(self):
        request = deepcopy(self.demo()["request"])
        request["document"]["planning"].pop("duration_by_crop")
        response = self.client.post(PREFIX + "/compare", json=request)
        self.assertEqual(response.status_code, 200, response.text[:600])
        result = response.json()
        self.assertEqual(result["analysis_status"], "partial")
        for strategy in result["strategies"]:
            self.assertIsNotNone(strategy["sequence"])
            for cycle in strategy["cycles"]:
                self.assertNotEqual(cycle["calendar"]["status"], "calendar_computed")
                self.assertIsNone(cycle["calendar"]["earliest_release_date"])
                self.assertIsNone(cycle["calendar"]["latest_release_date"])
                self.assertEqual(cycle["environment_windows"], [])

    def test_validation_rejects_extra_coerced_invalid_and_conflicting_inputs(self):
        compare = {"location": {"example_id": PRIMARY}, "input_kind": "user_reported", "document": {}}
        cases = [
            ("/context", {"location": {"example_id": PRIMARY}, "extra": True}),
            ("/context", {"location": {"longitude": 110.5}}),
            ("/context", {"location": {"longitude": "110.5", "latitude": -7.7}}),
            ("/context", {"location": {"longitude": 181., "latitude": -7.7}}),
            ("/context", {"location": {"example_id": PRIMARY}, "window": {"start_date": "2025-02-30", "end_exclusive": "2025-03-03"}}),
            ("/context", {"location": {"example_id": PRIMARY}, "time_mode": "forecast"}),
            ("/compare", {**compare, "extra": 1}),
            ("/compare", {**compare, "input_kind": "scenario_assumption", "assumptions": []}),
            ("/compare", {**compare, "document": {"farm": {"invented_field": 1}}}),
            ("/compare", {**compare, "document": {"farm": {"soil_lab": {"ph_h2o": "5.6"}}}}),
            ("/compare", {**compare, "document": {"planning": {"allowed_crop_ids": ["tomato"]}}}),
            ("/compare", {**compare, "document": {"planning": {"horizon": {"start_date": "2025-05-01", "end_exclusive": "2025-04-01"}}}}),
            ("/compare", {**compare, "document": {"farm": {"soil_lab": {"depth_top_cm": 20, "depth_bottom_cm": 5}}}}),
        ]
        for route, request in cases:
            with self.subTest(route=route, request=request):
                response = self.client.post(PREFIX + route, json=request)
                self.assert_error(response, 422, "invalid_input")
        conflict = {"location": {"example_id": PRIMARY, "longitude": 110.8, "latitude": -7.8}}
        response = self.client.post(PREFIX + "/context", json=conflict)
        self.assert_error(response, 422, "invalid_input")

    def test_calendar_schema_and_location_conflicts_are_rejected(self):
        base = self.demo()["request"]
        requests = []
        mismatch = deepcopy(base)
        mismatch["document"]["farm"] = {"location": {"representative_longitude": 110.8, "representative_latitude": -7.8}}
        requests.append(mismatch)
        observed = deepcopy(base)
        observed["document"]["planning"]["existing_sequence"][0]["date_status"] = "observed"
        requests.append(observed)
        count = deepcopy(base)
        count["slot_inputs"] = [{"production_method": "direct_seeded", "sowing_date": "2025-01-01"}]
        requests.append(count)
        reversed_duration = deepcopy(base)
        reversed_duration["document"]["planning"]["duration_by_crop"][0].update(minimum_days=121, maximum_days=120)
        requests.append(reversed_duration)
        climate_mismatch = deepcopy(base)
        climate_mismatch["document"]["context"]["climate_window"] = {"start_date": "2024-01-01", "end_exclusive": "2025-01-01"}
        requests.append(climate_mismatch)
        for request in requests:
            with self.subTest(request=request):
                self.assert_error(self.client.post(PREFIX + "/compare", json=request), 422, "invalid_input")

    def test_raw_nan_and_infinity_are_rejected_without_response_serialization_errors(self):
        bodies = [
            '{"location":{"longitude":NaN,"latitude":-7.7}}',
            '{"location":{"longitude":Infinity,"latitude":-7.7}}',
            '{"location":{"example_id":"klaten_cropland_primary"},"input_kind":"user_reported","document":{"farm":{"soil_lab":{"ph_h2o":NaN}}}}',
        ]
        for index, body in enumerate(bodies):
            with self.subTest(body=body):
                endpoint = "/context" if index < 2 else "/compare"
                response = self.client.post(PREFIX + endpoint, content=body, headers={"Content-Type": "application/json"})
                self.assert_error(response, 422, "invalid_input")

    def test_malformed_json_is_a_structured_client_error(self):
        response = self.client.post(PREFIX + "/compare", content=b'{"document":', headers={"Content-Type": "application/json"})
        self.assert_error(response, 422, "invalid_input")

    def test_oversize_body_is_413_before_json_domain_processing(self):
        body = json.dumps({"location": {"example_id": PRIMARY}, "padding": "x" * (256 * 1024)})
        response = self.client.post(PREFIX + "/context", content=body, headers={"Content-Type": "application/json"})
        self.assert_error(response, 413, "request_too_large")
        # Streaming transport can omit Content-Length; the actual body still
        # has to obey the same cap.
        response = self.client.post(PREFIX + "/context", content=iter([b"x" * (128 * 1024)] * 3), headers={"Content-Type": "application/json"})
        self.assert_error(response, 413, "request_too_large")

    def test_unavailable_repository_is_503_without_leaking_local_paths(self):
        from backend.fieldshift.repository import DataRepository, DataUnavailableError
        with tempfile.TemporaryDirectory() as directory:
            try:
                DataRepository(Path(directory))
            except DataUnavailableError as error:
                missing_error = error
            else:
                self.fail("Empty repository must not be considered ready")
        with patch("backend.fieldshift.app.DataRepository", side_effect=missing_error):
            with TestClient(self.create_app()) as client:
                for route in ("/health", PREFIX + "/catalog"):
                    with self.subTest(route=route):
                        response = client.get(route)
                        self.assert_error(response, 503, "data_unavailable")
                        self.assertNotIn(directory, response.text)

    def test_cors_accepts_explicit_local_origin_and_blocks_untrusted_origin(self):
        headers = {"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"}
        response = self.client.options(PREFIX + "/compare", headers=headers)
        self.assertEqual(response.status_code, 200, response.text[:500])
        self.assertEqual(response.headers.get("access-control-allow-origin"), "http://localhost:5173")
        self.assertNotEqual(response.headers.get("access-control-allow-origin"), "*")
        bad = self.client.options(PREFIX + "/compare", headers={**headers, "Origin": "https://untrusted.example"})
        self.assertNotIn("access-control-allow-origin", bad.headers)
        self.assertGreaterEqual(bad.status_code, 400)


if __name__ == "__main__":
    unittest.main()
