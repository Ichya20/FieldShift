"""Bounded public-data supplements. Never writes to data/prepared or old code.

Windows curl.exe validates TLS using Schannel. At most two requests in flight,
at most three attempts per URL. Sensor series remain separate.
"""
from __future__ import annotations

import argparse
import calendar
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data/supplemental/environment"
PREPARED = ROOT / "data/prepared"
AS_OF = "2026-11-08"
PARAMS = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "RH2M", "WS2M",
          "ALLSKY_SFC_SW_DWN", "GWETTOP", "GWETROOT", "EVPTRNS", "PS", "T2MDEW"]
NEEDED_ETO = ["T2M_MAX", "T2M_MIN", "T2MDEW", "WS2M", "ALLSKY_SFC_SW_DWN", "PS"]
SOURCES, FAILURES = {}, []


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def fetch(url, path, offline=False):
    """An atomic cache plus source sidecar; failures are recorded, not hidden."""
    key = path.relative_to(OUT).as_posix()
    sidecar = path.with_suffix(path.suffix + ".source.json")
    # Preserve the cap across reruns: a failed URL is not automatically tried
    # again after its three recorded attempts.
    if not path.exists() and (OUT / "manifest.json").exists():
        previous = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
        prior_failure = next((entry for entry in previous.get("failed_sources", []) if entry["url"] == url), None)
        if prior_failure:
            FAILURES.append(prior_failure)
            raise RuntimeError(f"Previous three-attempt failure retained without retry: {url}")
    if path.exists() and path.stat().st_size:
        obj = json.loads(path.read_text(encoding="utf-8")) if path.suffix == ".json" else None
        record = json.loads(sidecar.read_text(encoding="utf-8")) if sidecar.exists() else {
            "url": url, "retrieved_at_utc": dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc).isoformat(),
            "retrieval_time_basis": "file modification time of successful same-session curl probe",
            "http_status": None, "status_note": "Probe succeeded with curl --fail; exact status was not captured"}
        record.update(file=key, bytes=path.stat().st_size, sha256=sha(path))
        SOURCES[key] = record
        write_json(sidecar, record)
        return obj
    if offline:
        raise RuntimeError(f"Not cached: {key}")
    attempts = []
    partial = path.with_suffix(path.suffix + ".part")
    for attempt in range(1, 4):
        started = utc()
        result = subprocess.run(["curl.exe", "--silent", "--show-error", "--location", "--fail",
                                 "--max-time", "75", "--output", str(partial),
                                 "--write-out", "%{http_code}|%{url_effective}", url],
                                capture_output=True, text=True, timeout=85)
        record = {"attempt": attempt, "started_at_utc": started, "ended_at_utc": utc(),
                  "return_code": result.returncode, "result": result.stdout.strip(),
                  "error": result.stderr.strip()}
        attempts.append(record)
        if result.returncode == 0 and partial.exists() and partial.stat().st_size:
            try:
                obj = json.loads(partial.read_text(encoding="utf-8")) if path.suffix == ".json" else None
                status, effective = result.stdout.strip().split("|", 1)
                partial.replace(path)
                source = {"file": key, "url": url, "effective_url": effective,
                          "http_status": int(status), "retrieved_at_utc": utc(), "attempts": attempts,
                          "bytes": path.stat().st_size, "sha256": sha(path),
                          "transport": "Windows curl Schannel TLS verification enabled"}
                SOURCES[key] = source
                write_json(sidecar, source)
                return obj
            except (ValueError, json.JSONDecodeError) as exc:
                record["error"] = str(exc)
        if attempt < 3:
            time.sleep(attempt * 2)
    failure = {"file": key, "url": url, "attempts": attempts, "status": "failed_after_three_attempts"}
    FAILURES.append(failure)
    raise RuntimeError(f"Failed after three attempts: {url}")


def modis_url(product, endpoint, **params):
    base = f"https://modis.ornl.gov/rst/api/v1/{product}/{endpoint}"
    return base + "?" + urlencode(params) if params else base


def frozen_snapshot():
    return {path.relative_to(ROOT).as_posix(): {"sha256": sha(path), "bytes": path.stat().st_size}
            for path in sorted(PREPARED.rglob("*")) if path.is_file()}


def qa_decode(value):
    names = ["modland_qa", "vi_usefulness", "aerosol_quantity", "adjacent_cloud", "brdf_correction",
             "mixed_cloud", "land_water", "possible_snow_ice", "possible_shadow"]
    if value is None or not 0 <= value <= 65534:
        return dict.fromkeys(names)
    return dict(zip(names, [value & 3, value >> 2 & 15, value >> 6 & 3, value >> 8 & 1,
                           value >> 9 & 1, value >> 10 & 1, value >> 11 & 7, value >> 14 & 1, value >> 15 & 1]))


def classify(reliability, qa, ndvi, evi, observed):
    reasons = []
    if ndvi is None or evi is None:
        reasons.append("vi_fill_or_out_of_range")
    if not observed:
        reasons.append("invalid_or_unresolved_selected_day")
    if reliability not in (0, 1):
        reasons.append({-1: "reliability_fill", 2: "reliability_snow_ice", 3: "reliability_cloudy"}.get(reliability, "invalid_reliability"))
    if qa["modland_qa"] is None:
        reasons.append("invalid_qa")
    else:
        if qa["modland_qa"] > 1:
            reasons.append("modland_not_good_or_checkable")
        if qa["vi_usefulness"] > 10:
            reasons.append("very_low_vi_usefulness")
        if qa["aerosol_quantity"] == 3:
            reasons.append("high_aerosol")
        for name in ["adjacent_cloud", "mixed_cloud", "possible_snow_ice", "possible_shadow"]:
            if qa[name]:
                reasons.append(name)
        if qa["land_water"] != 1:
            reasons.append("not_pure_land_flag")
    if reasons:
        return "excluded", ";".join(reasons)
    if reliability == 0 and qa["modland_qa"] == 0 and qa["vi_usefulness"] <= 2 and qa["aerosol_quantity"] <= 1:
        return "good_strict", ""
    return "marginal_review", "passes_basic_masks_but_not_strict_policy"


def parse_subset(product, point, payload, path):
    assert payload["nrows"] == 1 and payload["ncols"] == 1
    grouped = defaultdict(dict)
    for item in payload["subset"]:
        assert len(item["data"]) == 1
        grouped[item["modis_date"]][item["band"]] = item
    rows = []
    for modis_date, group in sorted(grouped.items()):
        def field(name):
            return group["250m_16_days_" + name]
        raw = {name: int(field(name)["data"][0]) for name in
               ["NDVI", "EVI", "pixel_reliability", "VI_Quality", "composite_day_of_the_year"]}
        nominal = dt.date.fromisoformat(field("NDVI")["calendar_date"])
        doy = raw["composite_day_of_the_year"]
        observed = ""
        if 1 <= doy <= (366 if calendar.isleap(nominal.year) else 365):
            candidate = dt.date(nominal.year, 1, 1) + dt.timedelta(days=doy - 1)
            if nominal <= candidate <= nominal + dt.timedelta(days=15):
                observed = candidate.isoformat()
        ndvi = round(raw["NDVI"] * .0001, 4) if -2000 <= raw["NDVI"] <= 10000 else None
        evi = round(raw["EVI"] * .0001, 4) if -2000 <= raw["EVI"] <= 10000 else None
        qa = qa_decode(raw["VI_Quality"])
        quality, reason = classify(raw["pixel_reliability"], qa, ndvi, evi, observed)
        rows.append({"product": product, "platform": "Terra" if product == "MOD13Q1" else "Aqua",
                     "point_id": point["id"], "sample_role": point["sample_role"],
                     "latitude": point["latitude"], "longitude": point["longitude"],
                     "composite_start_date": nominal.isoformat(), "modis_date": modis_date,
                     "selected_observation_date": observed, "composite_day_of_year": doy,
                     "ndvi_raw": raw["NDVI"], "evi_raw": raw["EVI"], "ndvi": ndvi, "evi": evi,
                     "pixel_reliability": raw["pixel_reliability"], "vi_quality_raw": raw["VI_Quality"],
                     **qa, "quality_status": quality, "quality_reason": reason,
                     "tile": field("NDVI").get("tile"), "processing_date_raw": field("NDVI").get("proc_date"),
                     "source_file": path.relative_to(OUT).as_posix()})
    return rows


def reference_eto(day, tmax, tmin, dew, wind, solar, pressure, latitude, altitude):
    """Same FAO56 equation/operational guard as frozen prepare_climate.py."""
    def saturation(value):
        return .6108 * math.exp(17.27 * value / (value + 237.3))
    es, ea = (saturation(tmax) + saturation(tmin)) / 2, saturation(dew)
    if ea > es or tmax < tmin or wind < 0 or solar < 0 or pressure <= 0:
        return None, "invalid_eto_inputs"
    avg, j, phi = (tmax + tmin) / 2, day.timetuple().tm_yday, math.radians(latitude)
    dr, decl = 1 + .033 * math.cos(2 * math.pi * j / 365), .409 * math.sin(2 * math.pi * j / 365 - 1.39)
    ws = math.acos(max(-1, min(1, -math.tan(phi) * math.tan(decl))))
    ra = 24 * 60 / math.pi * .0820 * dr * (ws * math.sin(phi) * math.sin(decl) + math.cos(phi) * math.cos(decl) * math.sin(ws))
    ratio = solar / ((.75 + 2e-5 * altitude) * ra)
    bounded = max(.3, min(1., ratio))
    rnl = 4.903e-9 * (((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2) * (.34 - .14 * math.sqrt(ea)) * (1.35 * bounded - .35)
    delta, gamma = 4098 * saturation(avg) / (avg + 237.3) ** 2, .000665 * pressure
    eto = (.408 * delta * (.77 * solar - rnl) + gamma * 900 / (avg + 273) * wind * (es - ea)) / (delta + gamma * (1 + .34 * wind))
    return (round(eto, 4), "rs_rso_bounded_0.3_1_operational_guard" if bounded != ratio else "") if eto >= 0 else (None, "negative_eto_not_published")


def monthly_rows(rows, product, points):
    output = []
    first_year = 2026 if product == "MOD13Q1" else 2021
    for point in points:
        for year in range(first_year, 2027):
            for month in range(1, 13 if year < 2026 else 12):
                prefix = f"{year:04}-{month:02}"
                selected = [row for row in rows if row["point_id"] == point["id"] and row["selected_observation_date"].startswith(prefix)]
                good = [row for row in selected if row["quality_status"] == "good_strict"]
                counts = Counter(row["quality_status"] for row in selected)
                nominal = [row for row in rows if row["point_id"] == point["id"] and row["composite_start_date"].startswith(prefix)]
                output.append({"product": product, "point_id": point["id"], "observation_month": prefix,
                               "n_composites_nominal_start_month": len(nominal),
                               "n_selected_observations": len(selected), "n_good_strict": len(good),
                               "n_marginal_review": counts["marginal_review"], "n_excluded": counts["excluded"],
                               "ndvi_good_mean": round(sum(row["ndvi"] for row in good) / len(good), 4) if good else None,
                               "evi_good_mean": round(sum(row["evi"] for row in good) / len(good), 4) if good else None,
                               "interpolated": False, "coverage_status": "has_good_observations" if good else
                               "observations_present_without_strict_good" if selected else "no_selected_observations_with_resolved_date"})
    return output


def main(offline=False):
    for directory in [OUT, OUT / "raw", OUT / "sources"]:
        directory.mkdir(parents=True, exist_ok=True)
    frozen_path = OUT / "frozen-prepared-before.json"
    if not frozen_path.exists():
        write_json(frozen_path, {"captured_at_utc": utc(), "files": frozen_snapshot()})
    frozen_before = json.loads(frozen_path.read_text(encoding="utf-8"))["files"]
    before_summary = json.loads((PREPARED / "vegetation/summary.json").read_text(encoding="utf-8"))
    climate_before = json.loads((PREPARED / "climate/summary.json").read_text(encoding="utf-8"))
    points = before_summary["points"]
    tasks, planned = [], []
    for product in ["MOD13Q1", "MYD13Q1"]:
        bands = fetch(modis_url(product, "bands"), OUT / "sources" / f"{product}-bands.json", offline)
        indices = {band["band"]: band for band in bands["bands"]}
        for index in ["NDVI", "EVI"]:
            assert float(indices["250m_16_days_" + index]["scale_factor"]) == .0001
        primary = points[0]
        dates = fetch(modis_url(product, "dates", latitude=primary["latitude"], longitude=primary["longitude"]),
                      OUT / "raw" / f"{product}-dates-primary.json", offline)
        earliest = "2026-01-01" if product == "MOD13Q1" else "2021-01-01"
        selected = [day for day in dates["dates"] if earliest <= day["calendar_date"] <= AS_OF]
        for point in points:
            planned.append({"product": product, "point_id": point["id"], "expected_composites": len(selected),
                            "first_catalog_date": selected[0]["calendar_date"] if selected else None,
                            "last_catalog_date": selected[-1]["calendar_date"] if selected else None})
            for offset in range(0, len(selected), 10):
                chunk = selected[offset:offset + 10]
                start, end = chunk[0]["modis_date"], chunk[-1]["modis_date"]
                path = OUT / "raw" / f"{product}-{point['id']}-{start}-{end}.json"
                url = modis_url(product, "subset", latitude=point["latitude"], longitude=point["longitude"],
                                startDate=start, endDate=end, kmAboveBelow=0, kmLeftRight=0)
                tasks.append((product, point, chunk, path, url))
    power_url = "https://power.larc.nasa.gov/api/temporal/daily/point?" + urlencode({
        "parameters": ",".join(PARAMS), "community": "AG", "longitude": 110.37, "latitude": -7.8,
        "start": "20261025", "end": "20261107", "format": "JSON", "time-standard": "LST"})
    power_path = OUT / "raw/power-regional-20261025-20261107.json"
    tasks.insert(0, ("POWER", None, None, power_path, power_url))
    qa_url = "https://ladsweb.modaps.eosdis.nasa.gov/filespec/MODIS/61/MYD13Q1"
    tasks.insert(0, ("QA_DOC", None, None, OUT / "sources/MYD13Q1-v61-filespec.html", qa_url))
    aqua_catalog_url = "https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MYD13Q1"
    tasks.insert(0, ("QA_ALT_DOC", None, None, OUT / "sources/MYD13Q1-earthengine-catalog.html", aqua_catalog_url))
    def acquire(task):
        product, point, chunk, path, url = task
        try:
            payload = fetch(url, path, offline)
            if chunk is not None:
                assert {row["modis_date"] for row in payload["subset"]} == {row["modis_date"] for row in chunk}
            print(f"OK {path.name}", flush=True)
            return task, payload, None
        except Exception as error:
            print(f"FAILED {path.name}: {error}", flush=True)
            return task, None, str(error)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(acquire, tasks))
    all_rows, footprints, power = [], [], None
    raw_modis_band_entries = 0
    local_errors, optional_reference_errors = [], []
    for task, payload, error in results:
        product, point, chunk, path, url = task
        if error:
            record = {"file": path.relative_to(OUT).as_posix(), "error": error}
            (optional_reference_errors if product in {"QA_DOC", "QA_ALT_DOC"} else local_errors).append(record)
            continue
        if product == "POWER":
            power = payload
        elif product not in {"QA_DOC", "QA_ALT_DOC"}:
            raw_modis_band_entries += len(payload["subset"])
            all_rows.extend(parse_subset(product, point, payload, path))
            geometry = {key: payload.get(key) for key in ["xllcorner", "yllcorner", "cellsize", "nrows", "ncols"]}
            footprints.append({"product": product, "point_id": point["id"], **geometry,
                               "grid_difference_m_from_prepared_Terra": {
                                   key: float(geometry[key]) - float(point["spatial_subset"][key]) for key in ["xllcorner", "yllcorner", "cellsize"]},
                               "source_file": path.relative_to(OUT).as_posix()})
    assert len({(row["product"], row["point_id"], row["modis_date"]) for row in all_rows}) == len(all_rows)
    months = {}
    for product in ["MOD13Q1", "MYD13Q1"]:
        rows = [row for row in all_rows if row["product"] == product]
        write_csv(OUT / f"{product}-supplemental-qa.csv", rows)
        months[product] = monthly_rows(rows, product, points)
        write_csv(OUT / f"{product}-monthly-good-only.csv", months[product])
    write_json(OUT / "footprint-comparison.json", {"records": footprints, "note": "Each sensor retains its header footprint. No resampling or index fusion."})
    power_rows, power_after = [], {"status": "unavailable"}
    if power:
        assert power["header"]["time_standard"] == "LST"
        parameters = power["properties"]["parameter"]
        for key in sorted(set().union(*(values.keys() for values in parameters.values()))):
            day = dt.datetime.strptime(key, "%Y%m%d").date()
            row = {"date": day.isoformat(), "location_id": "power_regional_yogyakarta", "time_standard": "LST", "role": "same_point_publication_recheck"}
            fill = power["header"].get("fill_value", -999)
            for parameter in PARAMS:
                value = parameters.get(parameter, {}).get(key)
                row[parameter] = value if value is not None and value != fill and math.isfinite(value) else None
            eto, flags = None, "missing_eto_inputs"
            if all(row[name] is not None for name in NEEDED_ETO):
                eto, flags = reference_eto(day, *(row[name] for name in NEEDED_ETO), -7.8, power["geometry"]["coordinates"][2])
            row["eto_fao56_mm_day"], row["qa_flags"] = eto, flags
            row["rain_minus_reference_eto_mm_day"] = round(row["PRECTOTCORR"] - eto, 4) if row["PRECTOTCORR"] is not None and eto is not None else None
            power_rows.append(row)
        write_csv(OUT / "POWER-recent-recheck.csv", power_rows)
        power_after = {"status": "numeric_recheck_downloaded", "period": [power_rows[0]["date"], power_rows[-1]["date"]],
                       "last_valid_date_by_parameter": {name: max((row["date"] for row in power_rows if row[name] is not None), default=None) for name in PARAMS + ["eto_fao56_mm_day"]},
                       "valid_days_by_parameter": {name: sum(row[name] is not None for row in power_rows) for name in PARAMS + ["eto_fao56_mm_day"]},
                       "units": power["parameters"], "header": power["header"], "geometry": power["geometry"],
                       "source_file": power_path.relative_to(OUT).as_posix()}
        with (PREPARED / "climate/daily.csv").open(newline="", encoding="utf-8") as stream:
            old_climate = {row["date"]: row for row in csv.DictReader(stream)}
        overlap = {}
        for name in PARAMS + ["eto_fao56_mm_day"]:
            newly_available, now_missing, revised = [], [], []
            for row in power_rows:
                if row["date"] not in old_climate:
                    continue
                previous = old_climate[row["date"]][name]
                before = float(previous) if previous != "" else None
                after = row[name]
                if before is None and after is not None:
                    newly_available.append(row["date"])
                elif before is not None and after is None:
                    now_missing.append(row["date"])
                elif before is not None and after is not None and abs(before - after) > 1e-9:
                    revised.append({"date": row["date"], "before": before, "after": after})
            overlap[name] = {"newly_available_dates": newly_available,
                             "no_longer_available_dates": now_missing, "revised_values": revised}
        power_after["overlap_comparison_to_frozen_data"] = overlap
        power_after["eto_method"] = {"formula": "FAO56 equation6 daily grass reference, G=0, albedo0.23; dewpoint-derived vapour pressure; supplied2m wind",
                                     "guard": "Rs/Rso bounded to0.3..1 with explicit flag; same operational assumption as frozen reference",
                                     "reference_code": "scripts/data/prepare_climate.py", "reference_code_sha256": sha(ROOT / "scripts/data/prepare_climate.py"),
                                     "reference_equation_validation": "data/prepared/climate/method-validation.json",
                                     "reference_equation_validation_sha256": sha(PREPARED / "climate/method-validation.json"),
                                     "scientific_reference": "https://www.fao.org/4/x0490e/x0490e06.htm"}
    with (PREPARED / "vegetation/modis_16day_qa.csv").open(newline="", encoding="utf-8") as stream:
        old_rows = list(csv.DictReader(stream))
    availability = []
    for point in points:
        terra = {row["selected_observation_date"][:7] for row in old_rows if row["point_id"] == point["id"] and row["quality_status"] == "good_strict"}
        aqua = {row["selected_observation_date"][:7] for row in all_rows if row["product"] == "MYD13Q1" and row["point_id"] == point["id"] and row["quality_status"] == "good_strict" and row["selected_observation_date"] < "2026-01-01"}
        availability.append({"point_id": point["id"], "history_months": 60, "before_Terra_good_months": len(terra),
                             "Aqua_good_months_separately": len(aqua), "additional_months_with_Aqua_observation": sorted(aqua - terra),
                             "months_with_either_sensor_good_observation": len(terra | aqua),
                             "remaining_months_without_either_sensor_good_observation": 60 - len(terra | aqua),
                             "role": "availability diagnostic only; no merged NDVI/EVI means, no cross-sensor calibration"})
    series = []
    for item in planned:
        rows = [row for row in all_rows if row["product"] == item["product"] and row["point_id"] == item["point_id"]]
        good = [row for row in rows if row["quality_status"] == "good_strict"]
        series.append({**item, "downloaded_composites": len(rows), "quality_counts": dict(Counter(row["quality_status"] for row in rows)),
                       "quality_counts_by_year": {str(year): dict(Counter(row["quality_status"] for row in rows if row["composite_start_date"].startswith(str(year))))
                                                  for year in sorted({int(row["composite_start_date"][:4]) for row in rows})},
                       "first_selected_observation": min((row["selected_observation_date"] for row in rows if row["selected_observation_date"]), default=None),
                       "last_selected_observation": max((row["selected_observation_date"] for row in rows if row["selected_observation_date"]), default=None),
                       "last_strict_good_observation": max((row["selected_observation_date"] for row in good), default=None)})
    frozen_after = frozen_snapshot()
    changed = [key for key in sorted(set(frozen_before) | set(frozen_after)) if frozen_before.get(key) != frozen_after.get(key)]
    expected_count = sum(item["expected_composites"] for item in planned)
    passed = not changed and not local_errors and len(all_rows) == expected_count
    verification = {"checked_at_utc": utc(), "pass": passed,
                    "status": "passed" if passed else "incomplete_or_changed",
                    "scope": "Integrity and requested catalog-available numeric samples only; not completeness of all field or agronomic knowledge",
                    "frozen_prepared_files_before": len(frozen_before), "frozen_prepared_files_after": len(frozen_after),
                    "changed_frozen_files": changed, "unique_product_point_composite_keys": True,
                    "actual_composites": len(all_rows), "expected_composites": sum(item["expected_composites"] for item in planned),
                    "strict_good_rows": sum(row["quality_status"] == "good_strict" for row in all_rows),
                    "maximum_grid_discrepancy_from_frozen_Terra_m": max((abs(value) for record in footprints for value in record["grid_difference_m_from_prepared_Terra"].values()), default=None),
                    "failed_acquisitions": local_errors, "warnings": optional_reference_errors,
                    "local_verifier": "scripts/data/supplemental_environment/verify_environment.py"}
    write_json(OUT / "verification.json", verification)
    write_json(OUT / "summary.json", {"prepared_at_utc": utc(), "as_of_client_date": AS_OF,
        "purpose": "Supplement public environmental context before backend; frozen prepared package is unchanged",
        "before": {"vegetation": {"product": "Terra MOD13Q1", "period": ["2021-01-01", "2025-12-31"], "composites": 230,
                                   "primary_months_with_strict_good": 31, "comparison_months_with_strict_good": 32},
                   "climate": {"period": [climate_before["start"], climate_before["end"]], "last_valid_eto": climate_before["last_valid_eto_date"], "last_valid_rain": climate_before["last_valid_date_by_parameter"]["PRECTOTCORR"]}},
        "after": {"additional_vegetation_series": series, "historical_availability_diagnostic": availability, "climate_publication_recheck": power_after,
                  "new_raw_rows": {"vegetation_composites": len(all_rows), "modis_band_pixel_entries": raw_modis_band_entries,
                                   "power_daily_dates": len(power_rows), "power_parameter_values_including_nulls": len(power_rows) * len(PARAMS)}},
        "remaining_gaps": ["Cloud/snow/shadow and marginal observations remain excluded from primary statistics; no interpolation",
                           "Terra/Aqua remain separate sensors; no calibrated combined index series has been validated",
                           "Collection version is not explicit in ORNL subset response; C6.1 QA definition is a reference, not proof of subset collection version",
                           "Historical WorldCover fractions do not prove current crop, field boundary or 2026 land use",
                           "Observation and processing/publication latency remain; downloads are not real-time field monitoring",
                           "POWER forcing remains coarse regional model context, ETo is reference grass ET and P-ETo is not irrigation requirement",
                           "No seasonal forecast or future field weather inferred from historical/rechecked data",
                           "Farmer history, cultivar, irrigation availability and farm observations still unavailable"],
        "units": {"NDVI_EVI": "dimensionless; integer times 0.0001", "POWER": "Original API units retained; EVPTRNS MJ/m2/day, not mm/day", "ETo": "derived FAO56 grass-reference mm/day"},
        "qa_policy": before_summary["qa_policy"], "validation": verification,
        "optional_reference_failures": optional_reference_errors,
        "aqua_alternative_reference": {"file": "sources/MYD13Q1-earthengine-catalog.html",
                                        "status": "downloaded" if (OUT / "sources/MYD13Q1-earthengine-catalog.html").exists() else "unavailable",
                                        "role": "Provider catalog describes Aqua DetailedQA bit definitions; actual ORNL subset collection version remains unverified"},
        "qa_definition_sources": [
            {"file": "data/prepared/vegetation/sources/mod13q1-v61-filespec.html", "sha256": sha(PREPARED / "vegetation/sources/mod13q1-v61-filespec.html"),
             "role": "Frozen NASA MODIS VI bitfield definition; numeric Aqua API band metadata separately checked; ORNL collection version remains unverified"},
            {"file": "sources/MYD13Q1-bands.json", "sha256": sha(OUT / "sources/MYD13Q1-bands.json"),
             "role": "Aqua current band names, valid ranges, fill and scale metadata"}],
        "source_hashes": [{"file": record["file"], "sha256": record["sha256"], "url": record["url"]} for record in SOURCES.values()]})
    manifest = {"created_at_utc": utc(), "sources": list(SOURCES.values()), "failed_sources": FAILURES,
                "derived_files": [{"file": path.relative_to(OUT).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)}
                                  for path in sorted(OUT.glob("*")) if path.is_file() and path.name not in {"manifest.json", "local-verification.json"}],
                "read_only_frozen_inputs": {name: {"bytes": (ROOT / name).stat().st_size, "sha256": sha(ROOT / name)} for name in [
                    "data/prepared/climate/daily.csv", "data/prepared/climate/summary.json", "data/prepared/vegetation/modis_16day_qa.csv",
                    "data/prepared/vegetation/summary.json", "scripts/data/prepare_climate.py", "scripts/data/vegetation/prepare_modis.py"]}}
    write_json(OUT / "manifest.json", manifest)
    print(json.dumps({"series": series, "availability": availability, "climate": power_after["status"], "validation": verification}, indent=2), flush=True)
    if changed or local_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true")
    main(parser.parse_args().offline)
