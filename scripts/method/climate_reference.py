"""Small, auditable reference calculations; no crop ET or irrigation model.

Input: data/prepared/climate/daily.csv (NASA POWER regional daily LST and
derived FAO56 grass-reference ETo). Dates remain source LST calendar dates.
All windows are half-open. Missing observations are never imputed.
"""
from __future__ import annotations

import csv
from datetime import date, timedelta
import math
from pathlib import Path
from typing import Mapping

NumericRow = dict[str, float | None]
DailyData = Mapping[str, Mapping[str, float | None]]

METRICS = (
    "rainfall_total_mm",
    "reference_eto_total_mm",
    "rain_minus_reference_eto_total_mm",
    "temperature_mean_c",
)
_METADATA_COLUMNS = {"date", "location_id", "time_standard", "period", "qa_flags"}
_GUARD_FLAG = "rs_rso_bounded_0.3_1_operational_guard"


def _iso_date(value: str) -> date:
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError(f"Expected ISO YYYY-MM-DD date, got {value!r}")
    return parsed


def _window(start: str, end_exclusive: str) -> tuple[date, date, int]:
    first, end = _iso_date(start), _iso_date(end_exclusive)
    days = (end - first).days
    if days <= 0:
        raise ValueError("end_exclusive must be after start")
    return first, end, days


def _number(value: float | None) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    numeric = float(value)
    return numeric if math.isfinite(numeric) else None


def _csv_number(value: str | None) -> float | None:
    if value is None or value.strip().lower() in {"", "null", "none", "nan"}:
        return None
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"Non-finite numeric value {value!r}")
    return result


def load_daily(path: str | Path) -> dict[str, NumericRow]:
    """Read the prepared CSV into unique ISO-date keys and numeric-only rows.

    Blank numeric cells become None. Original POWER sentinel -999 becomes None
    only in uppercase POWER fields, not in derived signed metrics. Metadata
    columns are omitted; eto_operational_guard is a numeric 0/1 derived from
    qa_flags. Malformed numbers, missing required columns and duplicates fail.
    """
    data: dict[str, NumericRow] = {}
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"date", "PRECTOTCORR", "T2M", "eto_fao56_mm_day", "qa_flags"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"Missing daily columns: {sorted(required - set(reader.fieldnames or []))}")
        numeric_columns = [name for name in reader.fieldnames or [] if name not in _METADATA_COLUMNS]
        for line, row in enumerate(reader, start=2):
            day = _iso_date(row["date"]).isoformat()
            if day in data:
                raise ValueError(f"Duplicate daily date {day} at CSV line {line}")
            prepared: NumericRow = {}
            for name in numeric_columns:
                try:
                    value = _csv_number(row[name])
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"Invalid {name} at CSV line {line}: {row[name]!r}") from exc
                prepared[name] = None if name.isupper() and value == -999 else value
            prepared["eto_operational_guard"] = float(_GUARD_FLAG in (row["qa_flags"] or "").split(";"))
            data[day] = prepared
    return data


def window_summary(data: DailyData, start: str, end_exclusive: str) -> dict:
    """Aggregate complete daily metrics; P-ETo requires all matched pairs.

    Individual P, ETo and temperature coverage is evaluated independently.
    A partial sum is not returned as a full-window total. Guarded ETo values
    remain valid, with eto_guard_days exposing the operational assumption.
    """
    first, end, days = _window(start, end_exclusive)
    values: dict[str, list[float]] = {metric: [] for metric in METRICS}
    guard_days = 0
    for offset in range(days):
        row = data.get((first + timedelta(days=offset)).isoformat(), {})
        rain = _number(row.get("PRECTOTCORR"))
        eto = _number(row.get("eto_fao56_mm_day"))
        temperature = _number(row.get("T2M"))
        if rain is not None:
            values["rainfall_total_mm"].append(rain)
        if eto is not None:
            values["reference_eto_total_mm"].append(eto)
        if rain is not None and eto is not None:
            values["rain_minus_reference_eto_total_mm"].append(rain - eto)
        if temperature is not None:
            values["temperature_mean_c"].append(temperature)
        guard_days += int((_number(row.get("eto_operational_guard")) or 0) > 0)
    aggregates = {
        metric: math.fsum(samples) / (days if metric == "temperature_mean_c" else 1)
        if len(samples) == days else None
        for metric, samples in values.items()
    }
    return {"start": first.isoformat(), "end_exclusive": end.isoformat(),
            "days_expected": days, **aggregates,
            "valid_days": {metric: len(samples) for metric, samples in values.items()},
            "eto_guard_days": guard_days}


def _percentile_type7(ordered: list[float], probability: float) -> float | None:
    if len(ordered) < 2:
        return None
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _statistics(values: list[float]) -> dict:
    ordered = sorted(values)
    count = len(ordered)
    median = None
    if count:
        middle = count // 2
        median = ordered[middle] if count % 2 else (ordered[middle - 1] + ordered[middle]) / 2
    return {"count": count, "mean": math.fsum(ordered) / count if count else None,
            "median": median, "p10": _percentile_type7(ordered, .1),
            "p90": _percentile_type7(ordered, .9)}


def historical_analogue(data: DailyData, start: str, end_exclusive: str,
                        baseline_start_year: int = 1991,
                        baseline_end_year: int = 2020) -> dict:
    """Map both month/day endpoints, preserving target year offset and duration.

    Invalid Feb 29, duration changes and windows crossing the baseline boundary
    are skipped explicitly. Each metric independently uses complete mapped
    windows. Percentiles use paired annual P-ETo values, never differences of
    marginal percentiles. A singleton has mean/median but null p10/p90.
    """
    first, end, days = _window(start, end_exclusive)
    if not 1 <= baseline_start_year <= baseline_end_year <= 9998:
        raise ValueError("Baseline years must satisfy 1 <= start <= end <= 9998")
    baseline_first = date(baseline_start_year, 1, 1)
    baseline_end = date(baseline_end_year + 1, 1, 1)
    year_offset = end.year - first.year
    values: dict[str, list[float]] = {metric: [] for metric in METRICS}
    mapped, skipped = [], []
    for anchor in range(baseline_start_year, baseline_end_year + 1):
        if not 1 <= anchor + year_offset <= 9999:
            skipped.append({"anchor_year": anchor, "reason": "mapped_year_out_of_range"})
            continue
        try:
            mapped_first = date(anchor, first.month, first.day)
            mapped_end = date(anchor + year_offset, end.month, end.day)
        except ValueError:
            skipped.append({"anchor_year": anchor, "reason": "invalid_february_29"})
            continue
        record = {"anchor_year": anchor, "start": mapped_first.isoformat(),
                  "end_exclusive": mapped_end.isoformat()}
        mapped_days = (mapped_end - mapped_first).days
        if mapped_first < baseline_first or mapped_end > baseline_end:
            skipped.append({**record, "reason": "outside_baseline_range"})
            continue
        if mapped_days != days:
            skipped.append({**record, "reason": "duration_mismatch", "mapped_days": mapped_days,
                            "target_days": days})
            continue
        summary = window_summary(data, record["start"], record["end_exclusive"])
        incomplete = []
        for metric in METRICS:
            if summary[metric] is None:
                incomplete.append(metric)
            else:
                values[metric].append(summary[metric])
        mapped.append({"anchor_year": anchor, "summary": summary,
                       "incomplete_metrics": incomplete})
    statistics = {metric: _statistics(samples) for metric, samples in values.items()}
    return {"mode": "historical_analogue_not_forecast", "start": first.isoformat(),
            "end_exclusive": end.isoformat(), "days_expected": days,
            "baseline_start_year": baseline_start_year, "baseline_end_year": baseline_end_year,
            "counts_by_metric": {metric: stats["count"] for metric, stats in statistics.items()},
            "statistics": statistics, "mapped_windows": mapped, "skipped_years": skipped,
            "mapping_policy": "month_day_endpoints_same_year_offset_and_duration; all days inside baseline"}


def modis_window(csvpath: str | Path, point_id: str, start: str, end: str) -> dict:
    """Describe strict-good selected observations only; no crop/species inference.

    end is exclusive. Counts refer to discrete selected observations, not daily
    coverage; no expected cloud-free observation count or interpolation is made.
    """
    first, last, days = _window(start, end)
    selected, point_exists = [], False
    with Path(csvpath).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"point_id", "selected_observation_date", "quality_status", "ndvi", "evi"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Missing required MODIS columns")
        for row in reader:
            if row["point_id"] != point_id:
                continue
            point_exists = True
            if not row["selected_observation_date"]:
                continue
            observed = _iso_date(row["selected_observation_date"])
            if first <= observed < last:
                if row["quality_status"] not in {"good_strict", "marginal_review", "excluded"}:
                    raise ValueError(f"Unknown MODIS quality_status {row['quality_status']!r}")
                selected.append(row)
    good = [row for row in selected if row["quality_status"] == "good_strict"]
    means, valid = {}, {}
    for index in ("ndvi", "evi"):
        samples = [_csv_number(row[index]) for row in good]
        usable = [value for value in samples if value is not None]
        valid[index] = len(usable)
        means[index + "_good_mean"] = math.fsum(usable) / len(good) if good and len(usable) == len(good) else None
    status = ("point_not_in_prepared_data" if not point_exists else
              "no_selected_observations" if not selected else
              "no_good_observations" if not good else "has_good_observations")
    return {"mode": "historical_vegetation_context", "point_id": point_id,
            "start": first.isoformat(), "end_exclusive": last.isoformat(), "days_expected": days,
            "point_in_prepared_data": point_exists, "n_selected_observations": len(selected),
            "n_good_strict": len(good), "n_marginal_review": sum(row["quality_status"] == "marginal_review" for row in selected),
            "n_excluded": sum(row["quality_status"] == "excluded" for row in selected),
            "valid_good_observations": valid, **means,
            "good_observation_dates": sorted(row["selected_observation_date"] for row in good),
            "coverage_status": status, "interpolated": False,
            "interpretation": "Mixed-pixel vegetation context; no species, planting, harvest or fallow inference"}
