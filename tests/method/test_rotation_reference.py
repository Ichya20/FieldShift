"""Behavioral checks for explicit scenarios, dates, and uncertainty."""
import copy
import unittest

from scripts.method.rotation_reference import calendar_cycle, check_transition, generate_candidates


def request():
    return {
        "horizon": {"start_date": "2025-01-01", "end_exclusive": "2026-01-01"},
        "allowed_crop_ids": ["padi", "jagung", "kedelai"], "excluded_crop_ids": [],
        "existing_sequence": ["padi", "padi"],
        "slot_start_dates": ["2025-01-01", "2025-06-01"],
        "locked_prefix_length": 1, "continuation_confirmed": True,
    }


def plan(**updates):
    result = {
        "crop_id": "padi", "production_method": "direct_seeded", "sowing_date": "2025-01-01",
        "transplanting_date": None, "nursery_off_main_field": None,
        "duration": {"min_days": 120, "max_days": 120, "basis": "sowing",
                     "source_kind": "scenario_assumption", "source_id": "synthetic-demo"},
    }
    result.update(updates)
    return result


class CandidateTests(unittest.TestCase):
    def test_demo_is_deterministic_and_preserves_input(self):
        value = request()
        original = copy.deepcopy(value)
        result = generate_candidates(value)
        self.assertEqual(result["generation_status"], "complete")
        self.assertEqual(result["strategies"], {
            "existing": ["padi", "padi"], "candidate_1": ["padi", "jagung"], "candidate_2": ["padi", "kedelai"],
        })
        self.assertEqual(value, original)
        value["allowed_crop_ids"].reverse()
        self.assertEqual(result, generate_candidates(value))

    def test_missing_allowed_is_not_an_empty_allowed_list(self):
        value = request()
        value["allowed_crop_ids"] = None
        missing = generate_candidates(value)
        self.assertEqual(missing["generation_status"], "needs_input")
        self.assertIn("allowed_crop_ids", missing["missing_inputs"])
        value["allowed_crop_ids"] = []
        empty = generate_candidates(value)
        self.assertEqual(empty["generation_status"], "insufficient_alternatives")
        self.assertEqual(empty["generated_count"], 0)
        self.assertEqual(empty["strategies"]["existing"], ["padi", "padi"])

    def test_one_alternative_does_not_fill_two_slots(self):
        value = request()
        value["allowed_crop_ids"] = ["jagung"]
        result = generate_candidates(value)
        self.assertEqual(result["generation_status"], "insufficient_alternatives")
        self.assertEqual(result["generated_count"], 1)
        self.assertEqual(result["strategies"]["candidate_1"], ["padi", "jagung"])
        self.assertIsNone(result["strategies"]["candidate_2"])

    def test_baseline_is_not_returned_as_an_alternative(self):
        value = request()
        value["allowed_crop_ids"] = ["padi"]
        self.assertEqual(generate_candidates(value)["generated_count"], 0)

    def test_locked_prefix_can_keep_a_future_excluded_crop(self):
        value = request()
        value["allowed_crop_ids"] = ["jagung", "kedelai"]
        value["excluded_crop_ids"] = ["padi"]
        result = generate_candidates(value)
        self.assertEqual(result["generation_status"], "complete")
        self.assertEqual(result["strategies"]["existing"], ["padi", "padi"])
        self.assertTrue(all(sequence[0] == "padi" for sequence in result["strategies"].values()))
        self.assertEqual(result["warnings"][0]["slot_index"], 1)

    def test_unconfirmed_continuation_leaves_existing_null(self):
        value = request()
        value["continuation_confirmed"] = False
        result = generate_candidates(value)
        self.assertEqual(result["generation_status"], "needs_input")
        self.assertTrue(all(sequence is None for sequence in result["strategies"].values()))

    def test_missing_existing_dates_and_exclusions_are_needed(self):
        for key in ("existing_sequence", "slot_start_dates", "excluded_crop_ids", "locked_prefix_length"):
            with self.subTest(field=key):
                value = request()
                value[key] = None
                result = generate_candidates(value)
                self.assertEqual(result["generation_status"], "needs_input")
                self.assertIn(key, result["missing_inputs"])

    def test_overlap_is_invalid_even_if_locked_crop_is_preserved(self):
        value = request()
        value["excluded_crop_ids"] = ["padi"]
        self.assertEqual(generate_candidates(value)["generation_status"], "invalid_input")

    def test_mutable_dates_outside_horizon_are_not_distinct_candidates(self):
        for day in ("2024-12-31", "2026-01-01", "2026-02-01"):
            with self.subTest(day=day):
                value = request()
                value["slot_start_dates"][0] = "2024-12-01"
                value["slot_start_dates"][1] = day
                result = generate_candidates(value)
                self.assertEqual(result["generation_status"], "invalid_input")
                self.assertEqual(result["generated_count"], 0)

    def test_locked_current_start_can_precede_horizon(self):
        value = request()
        value["slot_start_dates"][0] = "2024-12-01"
        original = copy.deepcopy(value)
        result = generate_candidates(value)
        self.assertEqual(result["generation_status"], "complete")
        self.assertTrue(all(sequence[0] == "padi" for sequence in result["strategies"].values()))
        self.assertIn({
            "code": "requires_occupancy_overlap_check", "slot_index": 0,
            "field_start": "2024-12-01", "horizon_start": "2025-01-01",
        }, result["warnings"])
        self.assertEqual(value, original)
        cycle = calendar_cycle(plan(sowing_date="2024-12-01"))
        self.assertEqual(cycle["field_start"], "2024-12-01")
        self.assertEqual(cycle["latest_release_date"], "2025-04-01")

    def test_pre_horizon_crop_ending_earlier_requires_separate_occupancy_validation(self):
        value = request()
        value["slot_start_dates"][0] = "2024-01-01"
        result = generate_candidates(value)
        cycle = calendar_cycle(plan(sowing_date="2024-01-01"))
        self.assertEqual(cycle["latest_release_date"], "2024-05-01")
        self.assertLess(cycle["latest_release_date"], value["horizon"]["start_date"])
        self.assertEqual(cycle["field_start"], "2024-01-01")
        self.assertEqual(result["generation_status"], "complete")
        self.assertIn("requires_occupancy_overlap_check", [warning["code"] for warning in result["warnings"]])

    def test_locked_starts_at_or_after_horizon_end_are_invalid(self):
        for day in ("2026-01-01", "2026-02-01"):
            with self.subTest(day=day):
                value = request()
                value.update(locked_prefix_length=2, slot_start_dates=[day, "2026-06-01"])
                result = generate_candidates(value)
                self.assertEqual(result["generation_status"], "invalid_input")
                self.assertEqual(result["generated_count"], 0)

    def test_second_prefers_different_composition(self):
        value = request()
        value.update(existing_sequence=["padi", "jagung"], locked_prefix_length=0)
        result = generate_candidates(value)
        self.assertEqual(result["strategies"]["candidate_1"], ["padi", "padi"])
        self.assertEqual(result["strategies"]["candidate_2"], ["padi", "kedelai"])

    def test_composition_preference_can_require_more_edits_for_second(self):
        value = request()
        value.update(
            existing_sequence=["padi", "padi", "padi"], locked_prefix_length=0,
            allowed_crop_ids=["padi", "jagung"],
            slot_start_dates=["2025-01-01", "2025-05-01", "2025-09-01"],
        )
        result = generate_candidates(value)
        self.assertEqual(result["strategies"]["candidate_1"], ["padi", "padi", "jagung"])
        self.assertEqual(result["strategies"]["candidate_2"], ["padi", "jagung", "jagung"])

    def test_all_locked_gives_no_alternative(self):
        value = request()
        value["locked_prefix_length"] = 2
        self.assertEqual(generate_candidates(value)["generated_count"], 0)

    def test_bad_slot_count_or_dates_are_invalid(self):
        for changes in (
            {"existing_sequence": []}, {"slot_start_dates": ["2025-01-01"]},
            {"slot_start_dates": ["2025-06-01", "2025-01-01"]},
            {"slot_start_dates": ["2025-01-01", "2025-02-30"]},
            {"locked_prefix_length": True}, {"allowed_crop_ids": ["unknown"]},
            {"continuation_confirmed": 1},
        ):
            with self.subTest(changes=changes):
                value = request()
                value.update(changes)
                self.assertEqual(generate_candidates(value)["generation_status"], "invalid_input")


class CalendarTests(unittest.TestCase):
    def test_synthetic_direct_seeded_duration_has_day_zero_origin(self):
        value = plan()
        original = copy.deepcopy(value)
        result = calendar_cycle(value)
        self.assertEqual(result["status"], "calendar_computed")
        self.assertEqual(result["field_start"], "2025-01-01")
        self.assertEqual(result["earliest_harvest_date"], "2025-05-01")
        self.assertEqual(result["latest_release_date"], "2025-05-02")
        self.assertEqual(value, original)

    def test_hss_and_hst_have_different_origins_without_double_nursery(self):
        value = plan(production_method="transplanted", transplanting_date="2025-01-21", nursery_off_main_field=True)
        hss = calendar_cycle(value)
        self.assertEqual(hss["field_start"], "2025-01-21")
        self.assertEqual(hss["earliest_harvest_date"], "2025-05-01")
        value["duration"]["basis"] = "transplanting"
        hst = calendar_cycle(value)
        self.assertEqual(hst["earliest_harvest_date"], "2025-05-21")

    def test_ranges_keep_both_endpoints(self):
        value = plan()
        value["duration"].update(min_days=100, max_days=120)
        result = calendar_cycle(value)
        self.assertEqual(result["earliest_harvest_date"], "2025-04-11")
        self.assertEqual(result["latest_harvest_date"], "2025-05-01")

    def test_missing_duration_basis_or_start_has_no_invented_harvest(self):
        for changes in ({"basis": None}, {"min_days": None}, {"source_id": None}):
            value = plan()
            value["duration"].update(changes)
            result = calendar_cycle(value)
            self.assertEqual(result["status"], "needs_input")
            self.assertIsNone(result["earliest_harvest_date"])
        self.assertEqual(calendar_cycle(plan(sowing_date=None))["status"], "needs_input")

    def test_unknown_nursery_is_a_review_issue_without_resource_assumption(self):
        result = calendar_cycle(plan(production_method="transplanted", transplanting_date="2025-01-21"))
        self.assertEqual(result["status"], "calendar_computed")
        self.assertIn("nursery_location_unknown", result["review_issues"])
        self.assertEqual(result["field_start"], "2025-01-21")

    def test_main_field_nursery_requires_separate_overlap_review(self):
        result = calendar_cycle(plan(production_method="transplanted", transplanting_date="2025-01-21", nursery_off_main_field=False))
        self.assertIn("nursery_on_main_field_requires_separate_overlap_review", result["review_issues"])

    def test_transplanting_basis_does_not_require_unknown_sowing_date(self):
        value = plan(production_method="transplanted", sowing_date=None, transplanting_date="2025-01-21", nursery_off_main_field=True)
        value["duration"]["basis"] = "transplanting"
        self.assertEqual(calendar_cycle(value)["status"], "calendar_computed")

    def test_inconsistent_transplanting_dates_cannot_produce_harvest(self):
        for day in ("2024-12-31", "2025-06-01"):
            with self.subTest(transplanting_date=day):
                result = calendar_cycle(plan(production_method="transplanted", transplanting_date=day))
                self.assertEqual(result["status"], "invalid_input")
                self.assertIsNone(result["earliest_harvest_date"])

    def test_leap_day_and_cross_year(self):
        value = plan(sowing_date="2024-02-28")
        value["duration"].update(min_days=1, max_days=2)
        result = calendar_cycle(value)
        self.assertEqual(result["earliest_harvest_date"], "2024-02-29")
        self.assertEqual(result["latest_harvest_date"], "2024-03-01")
        value["sowing_date"] = "2025-12-31"
        self.assertEqual(calendar_cycle(value)["earliest_harvest_date"], "2026-01-01")

    def test_invalid_calendar_inputs(self):
        for changes in (
            {"sowing_date": "20250101"}, {"sowing_date": "2025-01-01T00:00:00Z"},
            {"sowing_date": "2025-02-29"}, {"production_method": "unknown"},
            {"transplanting_date": "2025-01-02"}, {"nursery_off_main_field": 0},
        ):
            with self.subTest(changes=changes):
                self.assertEqual(calendar_cycle(plan(**changes))["status"], "invalid_input")
        for low, high in ((120, 100), (0, 100), (True, 100), (1, 10**20)):
            value = plan()
            value["duration"].update(min_days=low, max_days=high)
            self.assertEqual(calendar_cycle(value)["status"], "invalid_input")


class TransitionTests(unittest.TestCase):
    def test_unknown_gap_differs_from_zero(self):
        previous = calendar_cycle(plan())
        next_cycle = calendar_cycle(plan(sowing_date="2025-05-02"))
        self.assertEqual(check_transition(previous, next_cycle, None)["status"], "needs_input")
        self.assertEqual(check_transition(previous, next_cycle, 0)["status"], "no_calendar_conflict")
        next_cycle["field_start"] = "2025-05-01"
        self.assertEqual(check_transition(previous, next_cycle, 0)["status"], "calendar_conflict")

    def test_uncertain_release_and_gap_make_three_distinct_states(self):
        previous = {"earliest_release_date": "2025-05-02", "latest_release_date": "2025-05-12"}
        for day, expected in (
            ("2025-05-15", "calendar_conflict"),
            ("2025-05-16", "potential_calendar_conflict"),
            ("2025-05-31", "potential_calendar_conflict"),
            ("2025-06-01", "no_calendar_conflict"),
        ):
            with self.subTest(day=day):
                result = check_transition(previous, {"field_start": day}, {"min_days": 14, "max_days": 20})
                self.assertEqual(result["status"], expected)
                self.assertEqual(result["earliest_ready_date"], "2025-05-16")
                self.assertEqual(result["latest_ready_date"], "2025-06-01")

    def test_demo_gap_fourteen_days(self):
        existing = calendar_cycle(plan())
        future = calendar_cycle(plan(sowing_date="2025-06-01"))
        self.assertEqual(check_transition(existing, future, 14)["status"], "no_calendar_conflict")

    def test_missing_previous_release_or_next_start_is_not_success(self):
        self.assertEqual(check_transition({}, {"field_start": "2025-06-01"}, 0)["status"], "needs_input")
        self.assertEqual(check_transition({"earliest_release_date": "2025-05-01", "latest_release_date": "2025-05-01"}, {}, 0)["status"], "needs_input")

    def test_invalid_gap_and_reversed_release_range(self):
        previous = {"earliest_release_date": "2025-05-02", "latest_release_date": "2025-05-12"}
        for gap in (-1, True, {"min_days": 5, "max_days": 2}, "0"):
            self.assertEqual(check_transition(previous, {"field_start": "2025-06-01"}, gap)["status"], "invalid_input")
        previous["earliest_release_date"] = "2025-05-13"
        self.assertEqual(check_transition(previous, {"field_start": "2025-06-01"}, 0)["status"], "invalid_input")


if __name__ == "__main__":
    unittest.main()
