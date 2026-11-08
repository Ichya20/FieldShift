"""Scientific-method regressions, with real prepared-data examples and edge cases."""
from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path
import tempfile
import unittest

from scripts.method.climate_reference import (
    METRICS, historical_analogue, load_daily, modis_window, window_summary,
)

ROOT = Path(__file__).resolve().parents[2]
DAILY_PATH = ROOT / "data/prepared/climate/daily.csv"
MODIS_PATH = ROOT / "data/prepared/vegetation/modis_16day_qa.csv"


def constant_days(start: str, end: str, rain=2., eto=1., temperature=25.):
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    return {(first + timedelta(days=i)).isoformat(): {
        "PRECTOTCORR": rain, "eto_fao56_mm_day": eto, "T2M": temperature,
        "eto_operational_guard": 0.,
    } for i in range((last - first).days)}


class ClimateReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.daily = load_daily(DAILY_PATH)

    def test_actual_historical_windows(self):
        for year, rain, eto, difference in [(2023, 306.50, 480.9418, -174.4418),
                                             (2025, 733.79, 441.2481, 292.5419)]:
            with self.subTest(year=year):
                result = window_summary(self.daily, f"{year}-05-01", f"{year}-09-01")
                self.assertEqual(result["days_expected"], 123)
                self.assertAlmostEqual(result["rainfall_total_mm"], rain, places=4)
                self.assertAlmostEqual(result["reference_eto_total_mm"], eto, places=4)
                self.assertAlmostEqual(result["rain_minus_reference_eto_total_mm"], difference, places=4)
                self.assertEqual(set(result["valid_days"].values()), {123})

    def test_recent_rain_complete_but_eto_and_difference_null(self):
        result = window_summary(self.daily, "2026-11-01", "2026-11-06")
        self.assertEqual(result["days_expected"], 5)
        self.assertAlmostEqual(result["rainfall_total_mm"], 25.09, places=4)
        self.assertIsNone(result["reference_eto_total_mm"])
        self.assertIsNone(result["rain_minus_reference_eto_total_mm"])
        self.assertEqual(result["valid_days"]["rainfall_total_mm"], 5)
        self.assertEqual(result["valid_days"]["reference_eto_total_mm"], 2)
        self.assertEqual(result["valid_days"]["rain_minus_reference_eto_total_mm"], 2)

    def test_half_open_boundaries_zero_rain_and_independent_metrics(self):
        data = constant_days("2025-01-01", "2025-01-04", rain=0.)
        data["2025-01-02"]["T2M"] = None
        data["2025-01-03"]["PRECTOTCORR"] = 1000.
        result = window_summary(data, "2025-01-01", "2025-01-03")
        self.assertEqual(result["rainfall_total_mm"], 0.)
        self.assertEqual(result["reference_eto_total_mm"], 2.)
        self.assertEqual(result["rain_minus_reference_eto_total_mm"], -2.)
        self.assertIsNone(result["temperature_mean_c"])
        self.assertEqual(result["valid_days"]["temperature_mean_c"], 1)
        data.pop("2025-01-02")
        result = window_summary(data, "2025-01-01", "2025-01-03")
        self.assertTrue(all(result[metric] is None for metric in METRICS))
        disjoint = constant_days("2025-01-01", "2025-01-03")
        disjoint["2025-01-01"]["eto_fao56_mm_day"] = None
        disjoint["2025-01-02"]["PRECTOTCORR"] = None
        result = window_summary(disjoint, "2025-01-01", "2025-01-03")
        self.assertEqual(result["valid_days"]["rainfall_total_mm"], 1)
        self.assertEqual(result["valid_days"]["reference_eto_total_mm"], 1)
        self.assertEqual(result["valid_days"]["rain_minus_reference_eto_total_mm"], 0)

    def test_guard_is_exposed_not_silently_discarded(self):
        result = window_summary(self.daily, "2025-01-01", "2025-05-01")
        self.assertEqual(result["eto_guard_days"], 2)
        self.assertEqual(result["valid_days"]["reference_eto_total_mm"], 120)
        self.assertIsNotNone(result["reference_eto_total_mm"])

    def test_strategy_calendar_partitions_preserve_full_horizon_environment(self):
        whole = window_summary(self.daily, "2025-01-01", "2026-01-01")
        for boundaries in [("2025-01-01", "2025-05-01", "2025-09-01", "2026-01-01"),
                           ("2025-01-01", "2025-04-01", "2025-07-01", "2025-10-01", "2026-01-01")]:
            parts = [window_summary(self.daily, start, end) for start, end in zip(boundaries, boundaries[1:])]
            self.assertEqual(sum(part["days_expected"] for part in parts), whole["days_expected"])
            for metric in METRICS[:3]:
                self.assertAlmostEqual(sum(part[metric] for part in parts), whole[metric], places=8)
            self.assertAlmostEqual(sum(part["temperature_mean_c"] * part["days_expected"] for part in parts) / whole["days_expected"], whole["temperature_mean_c"], places=8)
            self.assertEqual(sum(part["eto_guard_days"] for part in parts), whole["eto_guard_days"])

    def test_baseline_thirty_complete_calendar_matched_windows(self):
        # A full-length Jan–Dec target cannot keep 30 samples under strict
        # duration matching. Mar 1–Mar 1 is likewise 365/366; use calendar
        # year totals separately and test a leap-independent growing window.
        result = historical_analogue(self.daily, "2027-05-01", "2027-09-01")
        self.assertEqual(result["mode"], "historical_analogue_not_forecast")
        self.assertEqual(set(result["counts_by_metric"].values()), {30})
        self.assertEqual(result["skipped_years"], [])
        self.assertEqual(len(result["mapped_windows"]), 30)

    def test_full_annual_baseline_exposes_duration_policy(self):
        result = historical_analogue(self.daily, "2027-01-01", "2028-01-01")
        # Eight leap years in 1991–2020 cannot be silently reduced to 365 days.
        self.assertEqual(set(result["counts_by_metric"].values()), {22})
        self.assertEqual(len(result["skipped_years"]), 8)
        self.assertTrue(all(row["reason"] == "duration_mismatch" for row in result["skipped_years"]))

    def test_cross_year_baseline_never_uses_outside_day(self):
        result = historical_analogue(self.daily, "2027-11-01", "2028-02-01")
        self.assertEqual(set(result["counts_by_metric"].values()), {29})
        self.assertEqual(result["skipped_years"], [{"anchor_year": 2020, "start": "2020-11-01",
                                                  "end_exclusive": "2021-02-01", "reason": "outside_baseline_range"}])

    def test_february_29_and_internal_leap_day_are_explicit(self):
        leap_endpoint = historical_analogue(self.daily, "2028-02-29", "2028-03-02")
        self.assertEqual(set(leap_endpoint["counts_by_metric"].values()), {8})
        self.assertEqual(len(leap_endpoint["skipped_years"]), 22)
        self.assertTrue(all(row["reason"] == "invalid_february_29" for row in leap_endpoint["skipped_years"]))
        internal_leap_day = historical_analogue(self.daily, "2028-02-28", "2028-03-02")
        self.assertEqual(set(internal_leap_day["counts_by_metric"].values()), {8})
        self.assertTrue(all(row["reason"] == "duration_mismatch" for row in internal_leap_day["skipped_years"]))

    def test_per_metric_analogue_counts_and_paired_distribution(self):
        data = {}
        for year, rain, eto in [(1991, 10., 9.), (1992, 20., 1.), (1993, 30., 20.)]:
            data.update(constant_days(f"{year}-05-01", f"{year}-05-02", rain, eto))
        result = historical_analogue(data, "2027-05-01", "2027-05-02", 1991, 1993)
        difference = result["statistics"]["rain_minus_reference_eto_total_mm"]
        self.assertAlmostEqual(difference["p10"], 2.8)
        self.assertAlmostEqual(difference["p90"], 17.2)
        self.assertNotEqual(difference["p10"], result["statistics"]["rainfall_total_mm"]["p10"] - result["statistics"]["reference_eto_total_mm"]["p10"])
        data["1992-05-01"]["eto_fao56_mm_day"] = None
        result = historical_analogue(data, "2027-05-01", "2027-05-02", 1991, 1993)
        self.assertEqual(result["counts_by_metric"]["rainfall_total_mm"], 3)
        self.assertEqual(result["counts_by_metric"]["reference_eto_total_mm"], 2)
        self.assertEqual(result["counts_by_metric"]["rain_minus_reference_eto_total_mm"], 2)

    def test_singleton_and_empty_distributions_have_null_percentiles(self):
        data = constant_days("1991-05-01", "1991-05-02")
        result = historical_analogue(data, "2027-05-01", "2027-05-02", 1991, 1991)
        stats = result["statistics"]["rainfall_total_mm"]
        self.assertEqual((stats["count"], stats["mean"], stats["median"]), (1, 2., 2.))
        self.assertIsNone(stats["p10"])
        self.assertIsNone(stats["p90"])
        empty = historical_analogue({}, "2027-05-01", "2027-05-02", 1991, 1991)
        self.assertEqual(empty["statistics"]["rainfall_total_mm"], {"count": 0, "mean": None, "median": None, "p10": None, "p90": None})

    def test_numeric_loader_missing_and_duplicate_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "daily.csv"
            header = "date,PRECTOTCORR,T2M,eto_fao56_mm_day,qa_flags\n"
            path.write_text(header + "2025-01-01,0,-999,,rs_rso_bounded_0.3_1_operational_guard\n", encoding="utf-8")
            data = load_daily(path)
            self.assertEqual(data["2025-01-01"]["PRECTOTCORR"], 0.)
            self.assertIsNone(data["2025-01-01"]["T2M"])
            self.assertIsNone(data["2025-01-01"]["eto_fao56_mm_day"])
            self.assertEqual(data["2025-01-01"]["eto_operational_guard"], 1.)
            self.assertTrue(all(value is None or isinstance(value, float) for value in data["2025-01-01"].values()))
            path.write_text(header + "2025-01-01,0,25,1,\n2025-01-01,0,25,1,\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                load_daily(path)

    def test_invalid_or_empty_windows_fail(self):
        for start, end in [("2025-01-01", "2025-01-01"), ("2025-01-02", "2025-01-01"), ("20250101", "2025-01-02")]:
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                window_summary(self.daily, start, end)

    def test_modis_cloudy_only_stays_null_and_unknown_point_explicit(self):
        with MODIS_PATH.open(newline="", encoding="utf-8") as stream:
            rows = [row for row in csv.DictReader(stream) if row["point_id"] == "klaten_cropland_primary"]
        cloudy = next(row for row in rows if "reliability_cloudy" in row["quality_reason"])
        marginal = next(row for row in rows if row["quality_status"] == "marginal_review")
        for row, count_key in [(cloudy, "n_excluded"), (marginal, "n_marginal_review")]:
            with self.subTest(quality=row["quality_status"]):
                observed = date.fromisoformat(row["selected_observation_date"])
                result = modis_window(MODIS_PATH, "klaten_cropland_primary", observed.isoformat(), (observed + timedelta(days=1)).isoformat())
                self.assertEqual(result["n_good_strict"], 0)
                self.assertGreater(result[count_key], 0)
                self.assertEqual(result["coverage_status"], "no_good_observations")
                self.assertIsNone(result["ndvi_good_mean"])
                self.assertIsNone(result["evi_good_mean"])
                self.assertFalse(result["interpolated"])
        unknown = modis_window(MODIS_PATH, "unextracted_farm", "2025-01-01", "2026-01-01")
        self.assertEqual(unknown["coverage_status"], "point_not_in_prepared_data")


if __name__ == "__main__":
    unittest.main()
