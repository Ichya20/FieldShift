"""Input regressions that prevent assumptions replacing unknown field records."""
from copy import deepcopy
from pathlib import Path
import unittest

from backend.fieldshift.demo import demo_request
from backend.fieldshift.models import CompareRequest, ContextRequest
from backend.fieldshift.validation import DocumentValidator, InvalidInput
from pydantic import ValidationError


class InputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = DocumentValidator(Path(__file__).resolve().parents[2])

    def normalize(self, request=None):
        return self.validator.normalize(CompareRequest(**(request or demo_request())))

    def test_demo_normalizes_records_without_mutating_submission(self):
        request = demo_request()
        original = deepcopy(request)
        payload = self.normalize(request)
        self.assertEqual(request, original)
        self.assertEqual(payload["document"]["planning"]["existing_sequence"], ["padi", "padi"])
        self.assertEqual(payload["document"]["planning"]["duration_by_crop"]["jagung"]["min_days"], 100)
        self.assertEqual(payload["submitted_document"], request["document"])

    def test_partial_preserves_unknown(self):
        p = self.normalize({"location": {"example_id": "klaten_cropland_primary"},
                            "input_kind": "user_reported"})
        self.assertIsNone(p["slot_inputs"])
        self.assertIsNone(p["document"]["planning"]["duration_by_crop"])

    def test_duration_needs_explicit_counting_convention(self):
        r = demo_request()
        r["document"]["planning"]["duration_by_crop"][0].pop("counting_convention")
        self.assertIsNone(self.normalize(r)["document"]["planning"]["duration_by_crop"]["padi"]["basis"])

    def test_baseline_slot_duration_preserved_separately(self):
        r = demo_request()
        r["document"]["planning"]["existing_sequence"][0]["duration"] = {
            "crop_id": "padi", "minimum_days": 110, "maximum_days": 115,
            "basis_event": "sowing", "counting_convention": "elapsed_day_zero"}
        p = self.normalize(r)
        self.assertEqual(p["slot_inputs"][0]["duration"]["max_days"], 115)
        self.assertEqual(p["document"]["planning"]["duration_by_crop"]["padi"]["max_days"], 120)

    def test_invalid_domain_records_rejected(self):
        mutations = [
            lambda d: d["planning"]["duration_by_crop"].append(d["planning"]["duration_by_crop"][0]),
            lambda d: d["planning"]["duration_by_crop"][0].update(minimum_days=200),
            lambda d: d["planning"]["duration_by_crop"][0].update(minimum_days=0),
            lambda d: d["planning"]["duration_by_crop"][0].update(normalization_policy="documented_external_conversion"),
            lambda d: d["planning"]["existing_sequence"][0].update(date_status="observed"),
            lambda d: d["planning"]["existing_sequence"][0].update(transplanting_date="2024-12-01"),
            lambda d: d["planning"]["existing_sequence"][0].update(duration={"crop_id": "jagung"}),
            lambda d: d["planning"].update(horizon={"start_date": "2026-01-01", "end_exclusive": "2025-01-01"}),
            lambda d: d["context"].update(climate_window={"start_date": "2025-02-01", "end_exclusive": "2026-01-01"}),
            lambda d: d.update(farm={"priorities": {"planning_horizon_start": "2025-02-01"}}),
            lambda d: d.update(farm={"location": {"representative_longitude": 110.5}}),
            lambda d: d.update(farm={"location": {"geometry_geojson": {"type": "Polygon", "coordinates": [[[110., -7.], [110.1, -7.], [110., -7.1], [110., -7.]]]}}}),
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                r = demo_request()
                mutate(r["document"])
                with self.assertRaises(InvalidInput):
                    self.normalize(r)

    def test_conflicting_transport_slot_method_rejected(self):
        r = demo_request()
        r["slot_inputs"] = [{"production_method": "transplanted"}, {}]
        with self.assertRaises(InvalidInput):
            self.normalize(r)

    def test_source_duration_conversion_requires_consistent_policy_and_note(self):
        r = demo_request()
        duration = r["document"]["planning"]["duration_by_crop"][0]
        duration.update(source_minimum_days=82.5, source_maximum_days=92.5)
        with self.assertRaises(InvalidInput):
            self.normalize(r)
        duration.update(normalization_policy="documented_external_conversion")
        with self.assertRaises(InvalidInput):
            self.normalize(r)
        duration.update(normalization_note="Explicit hypothetical conversion, not a verified cultivar claim.")
        p = self.normalize(r)
        self.assertEqual(p["document"]["planning"]["duration_by_crop"]["padi"]["submitted_provenance"]["source_minimum_days"], 82.5)
        duration.update(source_minimum_days=95.)
        with self.assertRaises(InvalidInput):
            self.normalize(r)

    def test_contradictory_nursery_flags_rejected(self):
        r = demo_request()
        r["document"]["planning"]["existing_sequence"][0]["nursery_separate_from_main_field"] = False
        r["slot_inputs"] = [{"nursery_off_main_field": True}, {}]
        with self.assertRaises(InvalidInput):
            self.normalize(r)

    def test_nonfinite_and_extra_fields_rejected(self):
        for value in (float("nan"), float("inf")):
            r = demo_request()
            r["document"]["planning"]["preparation_gap_days"] = value
            with self.assertRaises(InvalidInput):
                self.normalize(r)
        r = demo_request()
        r["document"]["invented_field"] = 1
        with self.assertRaises(InvalidInput):
            self.normalize(r)

    def test_transport_strictness_and_finite_dates(self):
        for patch in ({"input_kind": "scenario_assumption", "assumptions": []},
                      {"location": {"longitude": True, "latitude": -7.}},
                      {"location": {"longitude": 110.}},
                      {"slot_inputs": [{"sowing_date": "2025-02-30"}]}):
            r = demo_request()
            r.update(patch)
            with self.assertRaises(ValidationError):
                CompareRequest(**r)
        with self.assertRaises(ValidationError):
            ContextRequest(location={"example_id": "klaten_cropland_primary"},
                           window={"start_date": "20250101", "end_exclusive": "2026-01-01"})


if __name__ == "__main__":
    unittest.main()
