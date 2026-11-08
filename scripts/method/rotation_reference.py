"""Small, deterministic scenario/calendar reference; no agronomic ranking.

Inputs and outputs are ordinary dictionaries. Dates are ISO date-only strings;
unknown values stay None. This module uses only the Python 3.11 standard library.
"""
from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from itertools import product
import re


CROP_IDS = ("padi", "jagung", "kedelai")
_CROP_ORDER = {crop: index for index, crop in enumerate(CROP_IDS)}


def _missing(items: list[str], field: str) -> None:
    if field not in items:
        items.append(field)


def _error(items: list[dict], field: str, code: str) -> None:
    items.append({"field": field, "code": code})


def _integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _date_value(value: object, field: str, errors: list[dict]) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        _error(errors, field, "expected_iso_date_only")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        _error(errors, field, "invalid_date")
        return None


def _crop_list(value: object, field: str, missing: list[str], errors: list[dict]) -> list | None:
    if value is None:
        _missing(missing, field)
        return None
    if not isinstance(value, list):
        _error(errors, field, "expected_list")
        return None
    if any(not isinstance(crop, str) or crop not in CROP_IDS for crop in value):
        _error(errors, field, "unsupported_crop_id")
        return None
    if field != "existing_sequence" and len(set(value)) != len(value):
        _error(errors, field, "duplicate_crop_id")
        return None
    return list(value)


def generate_candidates(request: dict) -> dict:
    """Generate up to two alternatives by edits and explicit future crop policy.

    Mutable slots require dated starts inside the same half-open horizon. A
    locked prefix may start earlier, but its occupancy still needs checking
    against biological release dates outside this generator. The first result
    minimizes sequence edits; stable crop-ID order resolves ties.
    The second prefers a different composition, without assigning benefit scores.
    """
    result = {
        "strategies": {"existing": None, "candidate_1": None, "candidate_2": None},
        "generated_count": 0,
        "generation_status": "needs_input",
        "missing_inputs": [],
        "warnings": [],
        "errors": [],
    }
    missing, errors = result["missing_inputs"], result["errors"]
    if not isinstance(request, dict):
        _error(errors, "request", "expected_object")
        result["generation_status"] = "invalid_input"
        return result

    allowed = _crop_list(request.get("allowed_crop_ids"), "allowed_crop_ids", missing, errors)
    excluded = _crop_list(request.get("excluded_crop_ids"), "excluded_crop_ids", missing, errors)
    existing = _crop_list(request.get("existing_sequence"), "existing_sequence", missing, errors)
    if existing is not None and not 1 <= len(existing) <= 3:
        _error(errors, "existing_sequence", "expected_one_to_three_slots")
    if allowed is not None and excluded is not None and set(allowed) & set(excluded):
        _error(errors, "allowed_crop_ids", "allowed_excluded_overlap")

    confirmed = request.get("continuation_confirmed")
    if confirmed is None or confirmed is False:
        _missing(missing, "continuation_confirmed")
    elif confirmed is not True:
        _error(errors, "continuation_confirmed", "expected_boolean")
    if confirmed is True and existing and 1 <= len(existing) <= 3:
        result["strategies"]["existing"] = list(existing)

    locked = request.get("locked_prefix_length")
    if locked is None:
        _missing(missing, "locked_prefix_length")
    elif not _integer(locked) or locked < 0 or (existing is not None and locked > len(existing)):
        _error(errors, "locked_prefix_length", "invalid_prefix_length")

    horizon = request.get("horizon")
    start = end = None
    if horizon is None:
        _missing(missing, "horizon")
    elif not isinstance(horizon, dict):
        _error(errors, "horizon", "expected_object")
    else:
        for key in ("start_date", "end_exclusive"):
            if horizon.get(key) is None:
                _missing(missing, f"horizon.{key}")
        start = _date_value(horizon.get("start_date"), "horizon.start_date", errors)
        end = _date_value(horizon.get("end_exclusive"), "horizon.end_exclusive", errors)
        if start is not None and end is not None and start >= end:
            _error(errors, "horizon", "empty_or_reversed_horizon")

    raw_dates = request.get("slot_start_dates")
    dates = []
    if raw_dates is None:
        _missing(missing, "slot_start_dates")
    elif not isinstance(raw_dates, list):
        _error(errors, "slot_start_dates", "expected_list")
    elif existing is not None and len(raw_dates) != len(existing):
        _error(errors, "slot_start_dates", "slot_count_mismatch")
    else:
        for index, value in enumerate(raw_dates):
            field = f"slot_start_dates[{index}]"
            if value is None:
                _missing(missing, field)
            parsed = _date_value(value, field, errors)
            dates.append(parsed)
            if parsed is not None and start is not None and end is not None and _integer(locked):
                if parsed >= end:
                    _error(errors, field, "slot_start_at_or_after_horizon_end")
                elif index >= locked and parsed < start:
                    _error(errors, field, "mutable_start_outside_horizon")
                elif index < locked and parsed < start:
                    result["warnings"].append({
                        "code": "requires_occupancy_overlap_check", "slot_index": index,
                        "field_start": parsed.isoformat(), "horizon_start": start.isoformat(),
                    })
        if all(value is not None for value in dates) and any(a >= b for a, b in zip(dates, dates[1:])):
            _error(errors, "slot_start_dates", "dates_not_strictly_increasing")

    if existing is not None and _integer(locked) and 0 <= locked <= len(existing):
        for index, crop in enumerate(existing[locked:], start=locked):
            if (allowed is not None and crop not in allowed) or (excluded is not None and crop in excluded):
                result["warnings"].append({"code": "baseline_future_crop_outside_policy", "slot_index": index, "crop_id": crop})

    if errors:
        result["generation_status"] = "invalid_input"
        return result
    if missing:
        return result

    effective = [crop for crop in CROP_IDS if crop in allowed and crop not in excluded]
    prefix = existing[:locked]
    alternatives = [prefix + list(tail) for tail in product(effective, repeat=len(existing) - locked)]
    alternatives = [sequence for sequence in alternatives if sequence != existing]
    alternatives.sort(key=lambda sequence: (
        sum(a != b for a, b in zip(sequence, existing)),
        tuple(_CROP_ORDER[crop] for crop in sequence),
    ))
    if alternatives:
        first = alternatives[0]
        result["strategies"]["candidate_1"] = first
        remaining = alternatives[1:]
        different_composition = [sequence for sequence in remaining if Counter(sequence) != Counter(first)]
        if remaining:
            result["strategies"]["candidate_2"] = (different_composition or remaining)[0]
    result["generated_count"] = sum(result["strategies"][key] is not None for key in ("candidate_1", "candidate_2"))
    result["generation_status"] = "complete" if result["generated_count"] == 2 else "insufficient_alternatives"
    return result


def _day_range(value: object, field: str, minimum: int, missing: list[str], errors: list[dict]) -> tuple[int, int] | None:
    if value is None:
        _missing(missing, field)
        return None
    if _integer(value):
        low = high = value
    elif isinstance(value, dict):
        low, high = value.get("min_days"), value.get("max_days")
        for key, item in (("min_days", low), ("max_days", high)):
            if item is None:
                _missing(missing, f"{field}.{key}")
        if low is None or high is None:
            return None
    else:
        _error(errors, field, "expected_integer_or_day_range")
        return None
    if not _integer(low) or not _integer(high) or low < minimum or low > high:
        _error(errors, field, "invalid_day_range")
        return None
    return low, high


def calendar_cycle(plan: dict) -> dict:
    """Keep biological dates unchanged; horizon clipping belongs to exposure checks."""
    result = {
        "field_start": None,
        "earliest_harvest_date": None, "latest_harvest_date": None,
        "earliest_release_date": None, "latest_release_date": None,
        "status": "needs_input", "missing_inputs": [], "review_issues": [], "errors": [],
        "notes": ["Day 0 is the duration origin; endpoints are not averaged.", "Harvest day is occupied; release starts the following day."],
    }
    missing, errors = result["missing_inputs"], result["errors"]
    if not isinstance(plan, dict):
        _error(errors, "plan", "expected_object")
        result["status"] = "invalid_input"
        return result
    crop = plan.get("crop_id")
    if crop is None:
        _missing(missing, "crop_id")
    elif crop not in CROP_IDS:
        _error(errors, "crop_id", "unsupported_crop_id")
    method = plan.get("production_method")
    if method is None:
        _missing(missing, "production_method")
    elif method not in ("direct_seeded", "transplanted"):
        _error(errors, "production_method", "unsupported_production_method")
    sowing = _date_value(plan.get("sowing_date"), "sowing_date", errors)
    transplanting = _date_value(plan.get("transplanting_date"), "transplanting_date", errors)
    field_start = sowing if method == "direct_seeded" else transplanting if method == "transplanted" else None
    if field_start is not None:
        result["field_start"] = field_start.isoformat()
    if method == "direct_seeded" and plan.get("sowing_date") is None:
        _missing(missing, "sowing_date")
    if method == "direct_seeded" and plan.get("transplanting_date") is not None:
        _error(errors, "transplanting_date", "direct_seeded_has_transplanting_date")
    if method == "transplanted" and plan.get("transplanting_date") is None:
        _missing(missing, "transplanting_date")
    if sowing is not None and transplanting is not None and sowing > transplanting:
        _error(errors, "transplanting_date", "transplanting_before_sowing")

    duration = plan.get("duration")
    days = basis = origin = None
    if duration is None:
        _missing(missing, "duration")
    elif not isinstance(duration, dict):
        _error(errors, "duration", "expected_object")
    else:
        days = _day_range(duration, "duration", 1, missing, errors)
        basis = duration.get("basis")
        if basis is None:
            _missing(missing, "duration.basis")
        elif basis not in ("sowing", "transplanting"):
            _error(errors, "duration.basis", "unsupported_duration_basis")
        elif basis == "transplanting" and method == "direct_seeded":
            _error(errors, "duration.basis", "direct_seeded_cannot_use_transplanting_basis")
        else:
            origin = sowing if basis == "sowing" else transplanting
            if plan.get("sowing_date" if basis == "sowing" else "transplanting_date") is None:
                _missing(missing, "sowing_date" if basis == "sowing" else "transplanting_date")
        for key in ("source_kind", "source_id"):
            value = duration.get(key)
            if value is None:
                _missing(missing, f"duration.{key}")
            elif not isinstance(value, str) or not value.strip():
                _error(errors, f"duration.{key}", "expected_nonempty_string")
    nursery = plan.get("nursery_off_main_field")
    if nursery is not None and not isinstance(nursery, bool):
        _error(errors, "nursery_off_main_field", "expected_boolean_or_null")
    elif method == "transplanted":
        if nursery is None:
            result["review_issues"].append("nursery_location_unknown")
            result["notes"].append("Nursery location is unknown; no nursery resource assumption was made.")
        elif nursery is False:
            result["review_issues"].append("nursery_on_main_field_requires_separate_overlap_review")
        if basis == "sowing":
            result["notes"].append("Sowing-based duration already includes nursery time; no nursery days were added.")
    if errors:
        result["status"] = "invalid_input"
        return result
    if missing:
        return result
    try:
        earliest, latest = (origin + timedelta(days=days[0]), origin + timedelta(days=days[1]))
        if earliest < field_start:
            _error(errors, "duration", "harvest_range_before_field_start")
        else:
            result.update(
                earliest_harvest_date=earliest.isoformat(), latest_harvest_date=latest.isoformat(),
                earliest_release_date=(earliest + timedelta(days=1)).isoformat(),
                latest_release_date=(latest + timedelta(days=1)).isoformat(), status="calendar_computed",
            )
    except (OverflowError, ValueError):
        _error(errors, "duration", "date_overflow")
    if errors:
        result["status"] = "invalid_input"
    return result


def check_transition(previous_calendar: dict, next_calendar: dict, prep_gap_days: int | dict | None) -> dict:
    """Check main-field release/preparation only; this is no agronomic verdict."""
    result = {
        "status": "needs_input", "earliest_ready_date": None, "latest_ready_date": None,
        "next_field_start": None, "missing_inputs": [], "errors": [],
        "notes": ["This checks the main-field calendar, not agronomic suitability or nursery resource overlap."],
    }
    missing, errors = result["missing_inputs"], result["errors"]
    for field, value in (("previous_calendar", previous_calendar), ("next_calendar", next_calendar)):
        if not isinstance(value, dict):
            _error(errors, field, "expected_object")
        elif value.get("status") == "invalid_input":
            _error(errors, field, "invalid_calendar")
    gap = _day_range(prep_gap_days, "prep_gap_days", 0, missing, errors)
    dates = {}
    for calendar, key, field in (
        (previous_calendar, "earliest_release_date", "previous_calendar.earliest_release_date"),
        (previous_calendar, "latest_release_date", "previous_calendar.latest_release_date"),
        (next_calendar, "field_start", "next_calendar.field_start"),
    ):
        value = calendar.get(key) if isinstance(calendar, dict) else None
        if value is None:
            _missing(missing, field)
        dates[key] = _date_value(value, field, errors)
    early, late, next_start = dates["earliest_release_date"], dates["latest_release_date"], dates["field_start"]
    if early is not None and late is not None and early > late:
        _error(errors, "previous_calendar", "reversed_release_range")
    if errors:
        result["status"] = "invalid_input"
        return result
    if missing:
        return result
    try:
        earliest_ready, latest_ready = early + timedelta(days=gap[0]), late + timedelta(days=gap[1])
    except (OverflowError, ValueError):
        _error(errors, "prep_gap_days", "date_overflow")
        result["status"] = "invalid_input"
        return result
    result.update(earliest_ready_date=earliest_ready.isoformat(), latest_ready_date=latest_ready.isoformat(), next_field_start=next_start.isoformat())
    result["status"] = (
        "no_calendar_conflict" if next_start >= latest_ready
        else "calendar_conflict" if next_start < earliest_ready
        else "potential_calendar_conflict"
    )
    return result
