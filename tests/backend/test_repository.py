"""Semantic integration tests against frozen data and source support geometry."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest

from rasterio.warp import transform
from rasterio.transform import xy

from backend.fieldshift.repository import CLIMATE_ID, DataRepository, DataUnavailableError, SINUSOIDAL
from scripts.method.climate_reference import historical_analogue, window_summary


ROOT = Path(__file__).resolve().parents[2]
PRIMARY = {"example_id": "klaten_cropland_primary"}
CANDIDATE = {"example_id": "klaten_cropland_candidate"}
WINDOW = {"start_date": "2025-01-01", "end_exclusive": "2025-02-01"}


class RepositoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = DataRepository(ROOT)

    def test_public_examples_are_explicitly_unverified_and_regional(self):
        examples = self.repo.locations()
        self.assertEqual({row["id"] for row in examples}, {PRIMARY["example_id"], CANDIDATE["example_id"]})
        self.assertTrue(all(row["is_verified_farm"] is False and row["climate_context_id"] == CLIMATE_ID for row in examples))
        self.assertEqual(self.repo.resolve_location(PRIMARY), examples[0])

    def test_primary_ph_uses_actual_coordinate_native_cell(self):
        soil = self.repo.context(PRIMARY)["layers"]["soil"]
        ph = soil["ph_0_5cm"]
        self.assertEqual((ph["value"], ph["q05"], ph["q95"]), (5.8, 4.2, 7.9))
        self.assertEqual((ph["support"]["row"], ph["support"]["column"]), (5, 6))
        self.assertEqual(len(soil["properties"]), 180)
        zeros = [row for row in soil["properties"] if row["value"] == 0]
        self.assertEqual(len(zeros), 5)
        self.assertTrue(all(row["property"] == "cfvo" and row["statistic"] == "Q0.05" for row in zeros))

    def test_legacy_center_and_actual_primary_remain_distinct(self):
        context = self.repo.context({"longitude": 110.55444444444444, "latitude": -7.72125})
        ph = context["layers"]["soil"]["ph_0_5cm"]
        self.assertEqual((ph["value"], ph["q05"], ph["q95"]), (5.8, 4.2, 7.8))
        self.assertEqual(context["layers"]["climate"]["status"], "needs_input")

    def test_example_coordinate_conflict_is_rejected(self):
        with self.assertRaises(ValueError):
            self.repo.context(dict(PRIMARY, longitude=110.55, latitude=-7.72))
        exact = self.repo.locations()[0]["coordinate"]
        self.repo.context(dict(PRIMARY, **exact))

    def test_invalid_and_partial_coordinates_are_rejected(self):
        for query in ({"longitude": 110.55}, {"longitude": float("nan"), "latitude": -7.72}, {"longitude": True, "latitude": -7.72}, {"longitude": 181, "latitude": 0}):
            with self.subTest(query=query), self.assertRaises(ValueError):
                self.repo.context(query)

    def test_outside_location_never_uses_nearest_example(self):
        layers = self.repo.context({"longitude": 111.0, "latitude": -7.72})["layers"]
        for name in ("soil", "terrain", "vegetation", "gaez", "landcover"):
            self.assertEqual(layers[name]["status"], "outside_coverage", name)
        self.assertIsNone(layers["soil"]["ph_0_5cm"]["value"])
        self.assertEqual(layers["vegetation"]["series"], [])

    def test_native_source_hole_remains_null(self):
        layer = self.repo._soil["native_soil_layers"][0]
        raster = self.repo._raster(layer["path"])
        rows, columns = (raster["mask"] == 0).nonzero()
        x, y = xy(raster["transform"], int(rows[0]), int(columns[0]))
        lon, lat = transform(raster["crs"], "EPSG:4326", [x], [y])
        soil = self.repo.context({"longitude": lon[0], "latitude": lat[0]})["layers"]["soil"]
        self.assertEqual(soil["status"], "review_required")
        self.assertTrue(all(row["value"] is None and row["qa_status"] == "source_nodata" for row in soil["properties"]))

    def test_negative_pixel_offset_does_not_truncate_into_grid(self):
        layer = self.repo._soil["native_soil_layers"][0]
        raster = self.repo._raster(layer["path"])
        grid = raster["transform"]
        x, y = grid.c - .01 * grid.a, grid.f + 3.5 * grid.e
        lon, lat = transform(raster["crs"], "EPSG:4326", [x], [y])
        soil = self.repo.context({"longitude": lon[0], "latitude": lat[0]})["layers"]["soil"]
        self.assertEqual(soil["status"], "outside_coverage")
        self.assertEqual(soil["ph_0_5cm"]["support"]["column"], -1)

    def test_climate_is_only_assigned_for_example_or_explicit_context(self):
        point = {"longitude": 110.55, "latitude": -7.72}
        missing = self.repo.climate_window(point, "2025-01-01", "2025-02-01", "historical_replay")
        self.assertEqual(missing["status"], "needs_input")
        self.assertIsNone(missing["summary"])
        explicit = self.repo.climate_window(dict(point, climate_context_id=CLIMATE_ID), "2025-01-01", "2025-02-01", "historical_replay")
        example = self.repo.climate_window(PRIMARY, "2025-01-01", "2025-02-01", "historical_replay")
        self.assertEqual(explicit["summary"], example["summary"])
        self.assertEqual(explicit["support"]["coordinate"], {"longitude": 110.37, "latitude": -7.8})

    def test_signed_climate_difference_and_complete_counts(self):
        result = self.repo.climate_window(PRIMARY, "2025-08-01", "2025-09-01", "historical_replay")
        expected = window_summary(self.repo.daily, "2025-08-01", "2025-09-01")
        self.assertEqual(result["summary"], expected)
        self.assertLess(expected["rain_minus_reference_eto_total_mm"], 0)
        self.assertTrue(all(value == 31 for value in expected["valid_days"].values()))

    def test_recent_partial_retains_null_full_totals_and_valid_days(self):
        result = self.repo.climate_window(PRIMARY, "2026-11-01", "2026-11-08", "recent_partial")
        summary = result["summary"]
        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["time_mode"], "recent_partial")
        self.assertEqual(summary["days_expected"], 7)
        self.assertEqual(summary["valid_days"]["reference_eto_total_mm"], 2)
        self.assertEqual(summary["valid_days"]["rainfall_total_mm"], 5)
        self.assertIsNone(summary["rain_minus_reference_eto_total_mm"])

    def test_historical_analogue_preserves_actual_mode_and_cohorts(self):
        result = self.repo.climate_window(PRIMARY, "2030-01-01", "2030-02-01", "historical_analogue_not_forecast")
        expected = historical_analogue(self.repo.daily, "2030-01-01", "2030-02-01")
        self.assertEqual(result["summary"], expected)
        self.assertEqual(result["summary"]["mode"], "historical_analogue_not_forecast")
        self.assertEqual(expected["counts_by_metric"]["rainfall_total_mm"], 30)

    def test_only_canonical_modes_and_half_open_windows(self):
        for mode in ("recent_observed", "historical_analogue", "forecast"):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.repo.context(PRIMARY, WINDOW, mode)
        with self.assertRaises(ValueError):
            self.repo.context(PRIMARY, {"start_date": "2025-01-01", "end_exclusive": "2025-01-01"})

    def test_none_window_has_availability_without_assigned_dates(self):
        result = self.repo.context(PRIMARY)
        self.assertIsNone(result["window"])
        self.assertIsNone(result["layers"]["climate"]["summary"])
        for series in result["layers"]["vegetation"]["series"]:
            self.assertNotIn("start", series["summary"])

    def test_products_are_separate_and_terra_is_concatenated_without_duplicates(self):
        series = self.repo.context(PRIMARY)["layers"]["vegetation"]["series"]
        by_product = {row["product"]: row for row in series}
        self.assertEqual(set(by_product), {"MOD13Q1", "MYD13Q1"})
        self.assertEqual(len(by_product["MOD13Q1"]["observations"]), 134)
        self.assertEqual(len(by_product["MYD13Q1"]["observations"]), 133)
        for product, row in by_product.items():
            keys = [(item["product"], item["point_id"], item["modis_date"]) for item in row["observations"]]
            self.assertEqual(len(keys), len(set(keys)))
            self.assertTrue(all(item["product"] == product for item in row["observations"]))

    def test_modis_strict_good_means_exclude_marginal_and_cloudy(self):
        for series in self.repo.context(PRIMARY)["layers"]["vegetation"]["series"]:
            rows = series["observations"]
            good = [row for row in rows if row["quality_status"] == "good_strict" and row["selected_observation_date"]]
            summary = series["summary"]
            self.assertGreater(summary["n_excluded"], 0)
            self.assertGreater(summary["n_marginal_review"], 0)
            self.assertEqual(summary["n_good_strict"], len(good))
            self.assertAlmostEqual(summary["ndvi_good_mean"], math.fsum(row["ndvi"] for row in good) / len(good))
            gaps = [row for row in series["monthly"] if row["n_good_strict"] == 0]
            self.assertTrue(gaps)
            self.assertTrue(all(row["ndvi_good_mean"] is None and row["interpolated"] is False for row in gaps))

    def test_vegetation_queries_require_actual_product_footprint(self):
        grid = self.repo._footprints[("MOD13Q1", PRIMARY["example_id"])]
        x, y = grid["xllcorner"] - 1, grid["yllcorner"] + grid["cellsize"] / 2
        lon, lat = transform(SINUSOIDAL, "EPSG:4326", [x], [y])
        result = self.repo.context({"longitude": lon[0], "latitude": lat[0]})
        self.assertEqual(result["layers"]["vegetation"]["status"], "outside_coverage")
        self.assertEqual(result["layers"]["landcover"]["status"], "outside_coverage")

    def test_gaez_cells_have_half_open_boundaries_and_distinct_regimes(self):
        rows = self.repo.context(PRIMARY)["layers"]["gaez"]["rows"]
        self.assertEqual(len(rows), 6)
        self.assertEqual({(row["crop_code"], row["regime"]) for row in rows}, {(crop, regime) for crop in ("RCW", "MZE", "SOY") for regime in ("HRLM", "HILM")})
        self.assertTrue(all(row["continuous_suitability_score"] is None for row in rows))
        bounds = rows[0]["pixel_bounds"]
        inside = self.repo._gaez_layer({"longitude": bounds["west"], "latitude": -7.72})
        east = self.repo._gaez_layer({"longitude": bounds["east"], "latitude": -7.72})
        south = self.repo._gaez_layer({"longitude": 110.55, "latitude": bounds["south"]})
        self.assertEqual(inside["status"], "evidence_available")
        self.assertEqual(east["status"], "outside_coverage")
        self.assertEqual(south["status"], "outside_coverage")

    def test_landcover_uses_actual_2021_footprints(self):
        expected = ((PRIMARY, .8446909667194928), (CANDIDATE, .692063492063492))
        for location, fraction in expected:
            footprint = self.repo.context(location)["layers"]["landcover"]["footprints"][0]
            self.assertEqual(footprint["epoch"], 2021)
            self.assertEqual(footprint["stats"]["cropland_fraction_valid_cells"], fraction)

    def test_sources_resolve_method_and_layer_references_without_absolute_paths(self):
        sources = self.repo.sources()
        self.assertTrue(set(self.repo.method["additional_source_refs"]) <= sources.keys())
        context = self.repo.context(PRIMARY)
        for layer in context["layers"].values():
            self.assertTrue(set(layer["source_refs"]) <= sources.keys())
        self.assertIn("kementan-variety-catalog-brmp", sources)
        self.assertIn("fao56-table12", sources)
        self.assertNotIn(str(ROOT), json.dumps(self.repo.catalog()))
        self.assertNotIn(str(ROOT), json.dumps(sources))

    def test_source_catalog_is_defensively_copied(self):
        sources = self.repo.sources()
        sources["nasa-power"]["url"] = "changed"
        self.assertNotEqual(self.repo.sources()["nasa-power"]["url"], "changed")

    def test_complete_context_serializes_with_standard_json(self):
        context = self.repo.context(PRIMARY, WINDOW)
        # Native raster row/column scalars must be builtin ints for HTTP JSON.
        encoded = json.dumps(context, allow_nan=False)
        self.assertEqual(json.loads(encoded), context)
        ph = context["layers"]["soil"]["ph_0_5cm"]
        self.assertIs(type(ph["support"]["row"]), int)
        self.assertIs(type(context["layers"]["terrain"]["elevation_m"]["support"]["column"]), int)

    def test_empty_location_remains_missing(self):
        context = self.repo.context({})
        self.assertTrue(all(layer["status"] == "needs_input" for layer in context["layers"].values()))
        self.assertEqual(set(context["missing_inputs"]), {"location.coordinate", "location.climate_context_id"})


class RepositoryIntegrityTests(unittest.TestCase):
    def test_missing_manifest_raises_data_unavailable(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(DataUnavailableError):
                DataRepository(Path(folder))

    def test_corrupt_source_hash_raises_data_unavailable(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "data/prepared").mkdir(parents=True)
            (root / "source.txt").write_text("corrupt", encoding="utf-8")
            manifest = {"files": [{"path": "source.txt", "sha256": hashlib.sha256(b"expected").hexdigest()}]}
            (root / "data/prepared/file-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(DataUnavailableError, "checksum"):
                DataRepository(root)

    def test_malformed_manifest_raises_data_unavailable(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "data/prepared").mkdir(parents=True)
            (root / "data/prepared/file-manifest.json").write_text('{"files": []}', encoding="utf-8")
            with self.assertRaisesRegex(DataUnavailableError, "Invalid evidence manifest"):
                DataRepository(root)


if __name__ == "__main__":
    unittest.main()
