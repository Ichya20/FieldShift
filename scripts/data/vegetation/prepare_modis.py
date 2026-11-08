"""Download a small MOD13Q1 point history and preserve explicit quality exclusions.

Run with Python 3 from any directory. Requires Windows curl.exe using system TLS.
Only the documented cropland-candidate SAMPLE coordinate is queried; no farm is inferred.
"""
from __future__ import annotations

import argparse
import calendar
import collections
import concurrent.futures
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import time
import urllib.parse

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "prepared" / "vegetation"
BASE = "https://modis.ornl.gov/rst/api/v1/MOD13Q1"
POINTS = [
    {"id": "klaten_cropland_primary", "latitude": -7.721875031299882, "longitude": 110.55354472008753,
     "sample_role": "primary_demonstration_pixel", "mixed_landcover_pixel": True,
     "selection_basis": "WorldCover 2021 ranking of 74 complete MODIS grid cells in Klaten sample bbox: 84.469% cropland, 11.727% grassland, 3.803% tree cover, 0% built-up. Derived grid-center coordinate, not GPS field precision or 2026 land-cover confirmation.",
     "selection_evidence": "data/prepared/soil-terrain/modis-cropland-pixel-candidates.json",
     "footprint_landcover_evidence": "data/prepared/soil-terrain/modis-primary-footprint-landcover-summary.json",
     "footprint_cropland_fraction_worldcover2021": 0.8446909667194928},
    {"id": "klaten_cropland_candidate", "latitude": -7.7240416666666665, "longitude": 110.546875,
     "sample_role": "mixed_pixel_comparison", "mixed_landcover_pixel": True,
     "selection_basis": "WorldCover 2021 center class cropland; actual reported MODIS grid footprint: 69.206% cropland, 19.683% tree cover, 7.619% built-up, 3.492% grassland. Not proof of 2026 land cover or farm boundary.",
     "selection_evidence": "data/prepared/soil-terrain/landcover-summary.json",
     "footprint_landcover_evidence": "data/prepared/soil-terrain/modis-footprint-landcover-summary.json",
     "footprint_cropland_fraction_worldcover2021": 0.692063492063492}
]
QA_URL = "https://ladsweb.modaps.eosdis.nasa.gov/filespec/MODIS/61/MOD13Q1"
SOURCE_LOG = {}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def download(url, path):
    """Keep cached raw data. New requests verify TLS via native Windows curl."""
    key = str(path.relative_to(OUT)).replace("\\", "/")
    sidecar = path.with_suffix(path.suffix + ".source.json")
    if path.exists() and path.stat().st_size:
        try:
            data = json.loads(path.read_text(encoding="utf-8")) if path.suffix == ".json" else None
        except json.JSONDecodeError:
            backup = path.with_suffix(path.suffix + ".invalid-interrupted")
            path.rename(backup)
            return download(url, path)
        record = json.loads(sidecar.read_text(encoding="utf-8")) if sidecar.exists() else {
            "url": url, "retrieved_at_utc": dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc).isoformat(),
            "retrieval_time_basis": "local_file_modification_time_from_same-session_download",
            "transport": "curl.exe with Windows Schannel TLS validation", "cached": True}
        record["file"] = key
        record["bytes"] = path.stat().st_size
        record["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        SOURCE_LOG[key] = record
        write_json(sidecar, record)
        return data
    last_error = None
    for attempt in range(3):
        started = now()
        result = subprocess.run(["curl.exe", "--silent", "--show-error", "--location", "--fail",
                                 "--max-time", "90", "--output", str(path),
                                 "--write-out", "%{http_code}|%{url_effective}", url],
                                capture_output=True, text=True, timeout=100)
        if result.returncode == 0 and path.exists() and path.stat().st_size:
            try:
                data = json.loads(path.read_text(encoding="utf-8")) if path.suffix == ".json" else None
                status, effective_url = result.stdout.strip().split("|", 1)
                record = {"file": key, "url": url, "effective_url": effective_url,
                          "request_started_at_utc": started, "retrieved_at_utc": now(),
                          "http_status": int(status), "transport": "curl.exe with Windows Schannel TLS validation",
                          "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                SOURCE_LOG[key] = record
                write_json(sidecar, record)
                return data
            except (ValueError, json.JSONDecodeError) as exc:
                last_error = str(exc)
        else:
            last_error = result.stderr.strip() or result.stdout.strip()
        time.sleep(2 + attempt * 2)
    raise RuntimeError(f"Download failed after 3 attempts: {url}: {last_error}")


def query(endpoint, **parameters):
    return f"{BASE}/{endpoint}?{urllib.parse.urlencode(parameters)}"


def write_csv(path, rows, fields=None):
    fields = fields or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def decode_qa(qa):
    if qa is None or not 0 <= qa <= 65534:
        return {k: None for k in ("modland_qa", "vi_usefulness", "aerosol_quantity", "adjacent_cloud", "brdf_correction", "mixed_cloud", "land_water", "possible_snow_ice", "possible_shadow")}
    return {"modland_qa": qa & 3, "vi_usefulness": (qa >> 2) & 15,
            "aerosol_quantity": (qa >> 6) & 3, "adjacent_cloud": (qa >> 8) & 1,
            "brdf_correction": (qa >> 9) & 1, "mixed_cloud": (qa >> 10) & 1,
            "land_water": (qa >> 11) & 7, "possible_snow_ice": (qa >> 14) & 1,
            "possible_shadow": (qa >> 15) & 1}


def quality(reliability, qa, ndvi, evi, observation_date):
    reasons = []
    if ndvi is None or evi is None:
        reasons.append("vi_fill_or_out_of_range")
    if not observation_date:
        reasons.append("invalid_composite_day")
    if reliability not in (0, 1):
        reasons.append({-1: "reliability_fill", 2: "reliability_snow_ice", 3: "reliability_cloudy"}.get(reliability, "invalid_reliability"))
    if qa["modland_qa"] is None:
        reasons.append("qa_fill_or_out_of_range")
    else:
        if qa["modland_qa"] > 1:
            reasons.append("modland_qa_not_produced_or_cloudy")
        if qa["vi_usefulness"] > 10:
            reasons.append("very_low_vi_usefulness")
        if qa["aerosol_quantity"] == 3:
            reasons.append("high_aerosol")
        for flag in ("adjacent_cloud", "mixed_cloud", "possible_snow_ice", "possible_shadow"):
            if qa[flag]:
                reasons.append(flag)
        if qa["land_water"] != 1:
            reasons.append("not_pure_land_flag")
    if reasons:
        return "excluded", ";".join(reasons)
    if reliability == 0 and qa["modland_qa"] == 0 and qa["vi_usefulness"] <= 2 and qa["aerosol_quantity"] <= 1:
        return "good_strict", ""
    return "marginal_review", "passes_basic_masks_but_not_strict_policy"


def prepare(offline=False):
    for folder in (OUT / "raw", OUT / "sources"):
        folder.mkdir(parents=True, exist_ok=True)
    bands = download(BASE + "/bands", OUT / "sources" / "bands.json")
    download(QA_URL, OUT / "sources" / "mod13q1-v61-filespec.html")
    planned_dates = {}
    tasks = []
    prefetch_failures = {}
    for point in POINTS:
        date_url = query("dates", latitude=point["latitude"], longitude=point["longitude"])
        doc = download(date_url, OUT / "raw" / f"dates-{point['id']}.json")
        dates = [d for d in doc["dates"] if "2021-01-01" <= d["calendar_date"] <= "2025-12-31"]
        planned_dates[point["id"]] = dates
        for offset in range(0, len(dates), 10):
            chunk = dates[offset:offset + 10]
            start, end = chunk[0]["modis_date"], chunk[-1]["modis_date"]
            file = OUT / "raw" / f"{point['id']}-{start}-{end}.json"
            url = query("subset", latitude=point["latitude"], longitude=point["longitude"],
                        startDate=start, endDate=end, kmAboveBelow=0, kmLeftRight=0)
            tasks.append((url, file))
    def prefetch(task):
        url, file = task
        try:
            if offline and not file.exists():
                raise RuntimeError("Not cached in offline mode")
            download(url, file)
            print(f"Cached {file.name}", flush=True)
        except Exception as exc:
            prefetch_failures[str(file)] = str(exc)
            print(f"FAILED {file.name}: {exc}", flush=True)
    # Two small requests at most; all raw downloads finish before parsing.
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(prefetch, tasks))
    rows = []
    expected = {}
    failures = []
    spatial = {}
    for point in POINTS:
        dates = planned_dates[point["id"]]
        expected[point["id"]] = len(dates)
        subsets = []
        for offset in range(0, len(dates), 10):
            chunk = dates[offset:offset + 10]
            start, end = chunk[0]["modis_date"], chunk[-1]["modis_date"]
            file = OUT / "raw" / f"{point['id']}-{start}-{end}.json"
            url = query("subset", latitude=point["latitude"], longitude=point["longitude"],
                        startDate=start, endDate=end, kmAboveBelow=0, kmLeftRight=0)
            try:
                if str(file) in prefetch_failures:
                    raise RuntimeError(prefetch_failures[str(file)])
                if offline and not file.exists():
                    raise RuntimeError("Not cached in offline mode")
                data = download(url, file)
                assert data.get("nrows") == 1 and data.get("ncols") == 1, "Expected one pixel only"
                assert len({x["modis_date"] for x in data["subset"]}) == len(chunk), "Returned date count differs from requested batch"
                spatial[point["id"]] = {k: data.get(k) for k in ("xllcorner", "yllcorner", "cellsize", "nrows", "ncols", "latitude", "longitude")}
                for entry in data["subset"]:
                    subsets.append((entry, str(file.relative_to(OUT)).replace("\\", "/")))
                print(f"{point['id']} {start}..{end}: {len(chunk)} dates", flush=True)
            except Exception as exc:
                failures.append({"point_id": point["id"], "start": start, "end": end, "url": url, "error": str(exc)})
                print(f"FAILED {point['id']} {start}: {exc}", flush=True)
        grouped = collections.defaultdict(dict)
        for entry, source_file in subsets:
            grouped[entry["modis_date"]][entry["band"]] = (entry, source_file)
        for modis_date, group in sorted(grouped.items()):
            required = ["NDVI", "EVI", "pixel_reliability", "VI_Quality", "composite_day_of_the_year"]
            values = {}
            for suffix in required:
                band = f"250m_16_days_{suffix}"
                assert band in group, f"Missing {band} for {point['id']} {modis_date}"
                entry, source_file = group[band]
                assert len(entry["data"]) == 1
                values[suffix] = int(entry["data"][0])
            entry = group["250m_16_days_NDVI"][0]
            nominal_date = entry["calendar_date"]
            year = int(nominal_date[:4])
            doy = values["composite_day_of_the_year"]
            observation_date = (dt.date(year, 1, 1) + dt.timedelta(days=doy - 1)).isoformat() if 1 <= doy <= (366 if calendar.isleap(year) else 365) else ""
            ndvi = round(values["NDVI"] * .0001, 4) if -2000 <= values["NDVI"] <= 10000 else None
            evi = round(values["EVI"] * .0001, 4) if -2000 <= values["EVI"] <= 10000 else None
            qa = decode_qa(values["VI_Quality"])
            status, reason = quality(values["pixel_reliability"], qa, ndvi, evi, observation_date)
            rows.append({"point_id": point["id"], "sample_role": point["sample_role"], "sample_latitude": point["latitude"], "sample_longitude": point["longitude"],
                         "composite_start_date": nominal_date, "modis_date": modis_date,
                         "selected_observation_date": observation_date, "composite_day_of_year": doy,
                         "tile": entry.get("tile", ""), "processing_date_raw": entry.get("proc_date", ""),
                         "ndvi_raw": values["NDVI"], "evi_raw": values["EVI"], "ndvi": ndvi, "evi": evi,
                         "pixel_reliability": values["pixel_reliability"], "vi_quality_raw": values["VI_Quality"],
                         **qa, "quality_status": status, "quality_reason": reason, "source_file": source_file})
    assert len({(r["point_id"], r["modis_date"]) for r in rows}) == len(rows), "Duplicate point-date keys"
    monthly = []
    for point in POINTS:
        point_rows = [r for r in rows if r["point_id"] == point["id"]]
        for year in range(2021, 2026):
            for month in range(1, 13):
                prefix = f"{year:04}-{month:02}"
                group = [r for r in point_rows if r["selected_observation_date"].startswith(prefix)]
                nominal = [r for r in point_rows if r["composite_start_date"].startswith(prefix)]
                good = [r for r in group if r["quality_status"] == "good_strict"]
                count = collections.Counter(r["quality_status"] for r in group)
                monthly.append({"point_id": point["id"], "observation_month": prefix,
                                "n_composites_nominal_start_month": len(nominal), "n_selected_observations": len(group),
                                "n_good_strict": len(good), "n_marginal_review": count["marginal_review"], "n_excluded": count["excluded"],
                                "ndvi_good_mean": round(sum(r["ndvi"] for r in good) / len(good), 4) if good else None,
                                "evi_good_mean": round(sum(r["evi"] for r in good) / len(good), 4) if good else None,
                                "coverage_status": "sparse_single_observation" if len(good) == 1 else "has_multiple_good_observations" if len(good) > 1 else "no_good_observation",
                                "interpolated": False})
    write_csv(OUT / "modis_16day_qa.csv", rows)
    write_csv(OUT / "modis_monthly_good_only.csv", monthly)
    summary = {"created_at_utc": now(), "purpose": "Public sample-point history and QA, not verified farm observations or rotation recommendations",
               "period": {"start": "2021-01-01", "end": "2025-12-31"},
               "product": "MOD13Q1 ORNL DAAC REST subset; collection version not stated in subset response",
               "nominal_spatial_resolution_m": 250, "subset_sinusoidal_cellsize_m": 231.656358264,
               "scale_factor_ndvi_evi": 0.0001, "index_units": "dimensionless", "expected_composites_by_point": expected,
               "points": [], "failed_batches": failures, "total_rows": len(rows), "monthly_rows": len(monthly),
               "qa_policy": {"name": "Project conservative selection; QA bit definitions from NASA LAADS MOD13Q1 C6.1 filespec",
                             "primary": "reliability=0; MODLAND=0; usefulness<=2; aerosol<=1; all cloud/snow/shadow flags=0; pure-land=1; valid NDVI/EVI/date",
                             "marginal": "reliability in {0,1}; MODLAND<=1; usefulness<=10; aerosol<=2; cloud/snow/shadow flags=0; pure-land=1; valid values, but not primary",
                             "excluded": "All remaining observations; raw values preserved, never used in monthly means",
                             "monthly_assignment": "Selected pixel observation date, not composite interval start; no interpolation",
                             "threshold_note": "Strict usefulness/aerosol thresholds are project choices, not a NASA validated crop recommendation criterion"}}
    for point in POINTS:
        group = [r for r in rows if r["point_id"] == point["id"]]
        mgroup = [r for r in monthly if r["point_id"] == point["id"]]
        summary["points"].append({**point, "is_verified_user_farm": False,
                                  "spatial_subset": spatial.get(point["id"]),
                                  "n_composites": len(group), "quality_counts": dict(collections.Counter(r["quality_status"] for r in group)),
                                  "pixel_reliability_counts": dict(collections.Counter(r["pixel_reliability"] for r in group)),
                                  "months_with_primary_data": sum(r["n_good_strict"] > 0 for r in mgroup),
                                  "months_without_primary_data": sum(r["n_good_strict"] == 0 for r in mgroup)})
    write_json(OUT / "summary.json", summary)
    records = list(SOURCE_LOG.values())
    for filename in ("modis_16day_qa.csv", "modis_monthly_good_only.csv", "summary.json"):
        path = OUT / filename
        records.append({"file": filename, "type": "derived", "bytes": path.stat().st_size,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "derivation_script": "scripts/data/vegetation/prepare_modis.py"})
    context_files = []
    context_folder = OUT / "raw" / "excluded_context_points"
    for path in sorted(context_folder.glob("*")):
        if path.is_file():
            context_files.append({"file": str(path.relative_to(OUT)).replace("\\", "/"),
                                  "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                  "usage": "Excluded context only; old Yogyakarta urban sample, not used in primary CSV or monthly means"})
    write_json(OUT / "manifest.json", {"created_at_utc": now(), "sources": records,
                                      "download_bytes": sum(x["bytes"] for x in SOURCE_LOG.values()),
                                      "auth": "public, no account or credentials used", "failures": failures,
                                      "excluded_context_files": context_files})
    print(json.dumps(summary, indent=2), flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="Rebuild from already cached subset responses")
    args = parser.parse_args()
    prepare(offline=args.offline)
