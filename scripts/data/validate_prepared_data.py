"""Independent integrity and climate aggregation checks; no network requests."""
from __future__ import annotations
import calendar
import csv
import datetime as dt
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/prepared"


def reject_constant(value):
    raise ValueError("Non-finite JSON value: " + value)


def load_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    checks, errors = [], []

    def check(name, condition, detail=None):
        entry = {"check": name, "pass": bool(condition)}
        if detail is not None:
            entry["detail"] = detail
        checks.append(entry)
        if not condition:
            errors.append(name)

    parsed = 0
    for path in sorted(DATA.rglob("*.json")):
        if path.name == "validation-report.json":
            continue
        try:
            json.loads(path.read_text(encoding="utf-8-sig"), parse_constant=reject_constant)
            parsed += 1
        except (ValueError, OSError) as error:
            check(str(path.relative_to(ROOT)) + " JSON", False, str(error))
    check("Prepared JSON documents parse with no NaN/Infinity", parsed > 0, {"documents": parsed})

    daily = load_csv(DATA / "climate/daily.csv")
    dates = [dt.date.fromisoformat(r["date"]) for r in daily]
    check("Climate daily dates are unique and sorted", dates == sorted(set(dates)))
    start, end = dates[0], dates[-1]
    check("Climate daily rows are contiguous", len(dates) == (end - start).days + 1)
    baseline = [r for r in daily if "1991-01-01" <= r["date"] <= "2020-12-31"]
    check("30-year daily baseline has 10958 records", len(baseline) == 10958)
    by_month = defaultdict(list)
    for row in daily:
        by_month[row["date"][:7]].append(row)
    monthly = load_csv(DATA / "climate/monthly.csv")
    aggregate_failures = []
    for row in monthly:
        items = by_month[row["month"]]
        year, month = map(int, row["month"].split("-"))
        expected = calendar.monthrange(year, month)[1]
        for column, metric, operation in [
            ("PRECTOTCORR", "rainfall_total_mm", sum),
            ("T2M", "temperature_mean_c", statistics.mean),
            ("eto_fao56_mm_day", "reference_eto_total_mm", sum),
        ]:
            values = [float(r[column]) for r in items if r[column] != ""]
            if len(values) == expected:
                if row[metric] == "" or abs(float(row[metric]) - operation(values)) > 0.00011:
                    aggregate_failures.append([row["month"], metric])
            elif row[metric] != "":
                aggregate_failures.append([row["month"], metric, "partial month was published as complete"])
    check("Monthly climate aggregates agree with independent daily calculations", not aggregate_failures, aggregate_failures[:10])
    climatology = load_csv(DATA / "climate/baseline-1991-2020.csv")
    years = [int(r[k]) for r in climatology for k in r if k.endswith("_years")]
    check("All baseline calendar-month metrics have 30 complete years", len(climatology) == 12 and set(years) == {30})
    invalid = []
    for row in daily:
        if all(row[p] for p in ["T2M_MIN", "T2M", "T2M_MAX"]):
            if not float(row["T2M_MIN"]) <= float(row["T2M"]) <= float(row["T2M_MAX"]):
                invalid.append([row["date"], "temperature order"])
        for col, lo, hi in [("RH2M", 0, 100), ("GWETTOP", 0, 1), ("GWETROOT", 0, 1),
                             ("PRECTOTCORR", 0, 3000), ("WS2M", 0, 100),
                             ("ALLSKY_SFC_SW_DWN", 0, 60), ("PS", 50, 110)]:
            if row[col] and not lo <= float(row[col]) <= hi:
                invalid.append([row["date"], col, row[col]])
        for col in ["eto_fao56_mm_day", "rain_minus_reference_eto_mm_day"]:
            if row[col] and not math.isfinite(float(row[col])):
                invalid.append([row["date"], col, row[col]])
    check("Climate physical ranges and finite derived values", not invalid, invalid[:10])
    method = json.loads((DATA / "climate/method-validation.json").read_text())
    check("FAO56 calculation matches published independent numerical example", method["pass"], method)

    soil_summary = json.loads((DATA / "soil-terrain/summary.json").read_text())["soil"]
    soil_cells = load_csv(DATA / "soil-terrain/processed/soil-cells.csv")
    combinations = defaultdict(int)
    bad_soil = []
    for cell in soil_cells:
        combinations[(cell["property"], cell["depth"], cell["statistic"]) ] += 1
        if cell["value"] and not math.isfinite(float(cell["value"])):
            bad_soil.append("non-finite")
        if float(cell["raw_value"]) == 0 and cell["value"]:
            bad_soil.append("unresolved zero given physical value")
    check("Soil complete small-grid combinations and finite values", len(soil_cells) == soil_summary["cell_records"]
          and len(combinations) == 180 and set(combinations.values()) == {72} and not bad_soil, bad_soil[:10])

    veg = load_csv(DATA / "vegetation/modis_16day_qa.csv")
    veg_monthly = load_csv(DATA / "vegetation/modis_monthly_good_only.csv")
    identifiers = [(r["point_id"], r["modis_date"]) for r in veg]
    check("Two vegetation series have 230 unique composites", len(veg) == 230 and len(set(identifiers)) == 230)
    bad_veg, monthly_good = [], defaultdict(list)
    for row in veg:
        for metric in ["ndvi", "evi"]:
            if row[metric] and abs(float(row[metric]) - int(row[metric + "_raw"]) * 0.0001) > 1e-8:
                bad_veg.append("index scale")
        if row["quality_status"] == "good_strict":
            packed = int(row["vi_quality_raw"])
            if not (int(row["pixel_reliability"]) == 0 and packed & 3 == 0
                    and (packed >> 2) & 15 <= 2 and (packed >> 6) & 3 <= 1
                    and (packed >> 8) & 1 == 0 and (packed >> 10) & 1 == 0
                    and (packed >> 11) & 7 == 1 and (packed >> 14) & 1 == 0
                    and (packed >> 15) & 1 == 0):
                bad_veg.append("strict QA accepted invalid packed bits")
            monthly_good[(row["point_id"], row["selected_observation_date"][:7])].append(row)
    for row in veg_monthly:
        accepted = monthly_good[(row["point_id"], row["observation_month"])]
        for metric in ["ndvi", "evi"]:
            value = row[metric + "_good_mean"]
            if accepted:
                expected = statistics.mean(float(r[metric]) for r in accepted)
                # Module publishes means to four decimal places, matching index precision.
                if value == "" or abs(float(value) - expected) > 0.00005001:
                    bad_veg.append("monthly mean")
            elif value != "":
                bad_veg.append("empty good month not left empty")
        if row["interpolated"].lower() != "false":
            bad_veg.append("unexpected interpolation")
    check("Vegetation scale, packed strict-QA bits and independent good-only monthly aggregation", not bad_veg and len(veg_monthly) == 120, bad_veg[:10])

    farm = json.loads((DATA / "agronomy/farm-input-template.json").read_text())["farm"]
    def leaves(value):
        if isinstance(value, dict):
            return [leaf for child in value.values() for leaf in leaves(child)]
        return [value]
    farm_values = leaves(farm)
    check("Farmer inputs remain 91 unknown values", len(farm_values) == 91 and all(v is None for v in farm_values))
    strategies = json.loads((DATA / "agronomy/strategy-comparison-template.json").read_text())
    check("Three strategy slots are unfilled and economics unavailable", len(strategies["strategies"]) == 3
          and all(s["rotation_sequence"] is None and s["net_income_idr_ha"] is None for s in strategies["strategies"])
          and strategies["economics_available"] is False)

    modules = {}
    for name in ["climate", "vegetation", "soil-terrain", "agronomy"]:
        summary = DATA / name / "summary.json"
        manifest = DATA / name / "manifest.json"
        modules[name] = summary.exists() and manifest.exists()
        check(name + " has source manifest and summary", modules[name])
    report = {"validated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "checks": checks, "errors": errors, "pass": not errors,
              "scope": "File integrity, independent climate aggregation and physical ranges; module-specific QA remains in module reports. Passing is not local agronomic validation."}
    (DATA / "validation-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
