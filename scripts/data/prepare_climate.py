"""Download bounded NASA POWER history and prepare transparent regional features.

Run: py -3.11 scripts/data/prepare_climate.py
Only standard library is required. Cached responses are reused.
"""
from __future__ import annotations

import calendar
import csv
import datetime as dt
import hashlib
import json
import math
import shutil
import statistics
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/prepared/climate"
RAW = OUT / "raw"
LAT, LON = -7.8, 110.37
AS_OF = "2026-11-08"
PARAMS = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "RH2M", "WS2M",
          "ALLSKY_SFC_SW_DWN", "GWETTOP", "GWETROOT", "EVPTRNS", "PS", "T2MDEW"]
DOCS = ["https://power.larc.nasa.gov/docs/services/api/temporal/daily/",
        "https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/",
        "https://www.fao.org/4/x0490e/x0490e06.htm",
        "https://www.fao.org/4/x0490e/x0490e07.htm",
        "https://www.fao.org/4/x0490e/x0490e08.htm"]


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def fetch(start, end):
    query = dict(parameters=",".join(PARAMS), community="AG", longitude=LON, latitude=LAT,
                 start=start, end=end, format="JSON", **{"time-standard": "LST"})
    url = "https://power.larc.nasa.gov/api/temporal/daily/point?" + urllib.parse.urlencode(query)
    path = RAW / f"power-{start}-{end}.json"
    if not path.exists():
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "FieldShift-data-preparation/1.0"})
                with urllib.request.urlopen(req, timeout=55) as response:
                    payload = response.read(15_000_000)
                obj = json.loads(payload)
                assert "parameter" in obj.get("properties", {}), str(obj)[:500]
                path.write_bytes(payload)
                write_json(path.with_suffix(".provenance.json"), {
                    "source_url": url, "accessed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "bytes": len(payload), "http_status": 200})
                print(f"Downloaded {path.name}: {len(payload)} bytes", flush=True)
                break
            except Exception as error:
                print(f"Attempt {attempt + 1}: {start}-{end}: {error}", flush=True)
                if attempt == 2:
                    raise
                time.sleep(3 * (attempt + 1))
    return json.loads(path.read_text(encoding="utf-8")), path


def saturation(t):
    return 0.6108 * math.exp(17.27 * t / (t + 237.3))


def reference_eto(date, tmax, tmin, dew, wind, solar, pressure, latitude, altitude):
    """FAO56 daily grass-reference ETo; operational radiation guard is exposed."""
    avg = (tmax + tmin) / 2
    es = (saturation(tmax) + saturation(tmin)) / 2
    ea = saturation(dew)
    flags = []
    if ea > es or tmax < tmin or wind < 0 or solar < 0 or pressure <= 0:
        return None, "invalid_eto_inputs"
    j = date.timetuple().tm_yday
    phi = math.radians(latitude)
    dr = 1 + 0.033 * math.cos(2 * math.pi * j / 365)
    decl = 0.409 * math.sin(2 * math.pi * j / 365 - 1.39)
    ws = math.acos(max(-1, min(1, -math.tan(phi) * math.tan(decl))))
    ra = (24 * 60 / math.pi) * 0.0820 * dr * (
        ws * math.sin(phi) * math.sin(decl) + math.cos(phi) * math.cos(decl) * math.sin(ws))
    clear_sky = (0.75 + 2e-5 * altitude) * ra
    ratio = solar / clear_sky
    bounded = max(0.3, min(1.0, ratio))
    if bounded != ratio:
        flags.append("rs_rso_bounded_0.3_1_operational_guard")
    rnl = 4.903e-9 * (((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2) * (
        0.34 - 0.14 * math.sqrt(ea)) * (1.35 * bounded - 0.35)
    rn = 0.77 * solar - rnl
    delta = 4098 * saturation(avg) / (avg + 237.3) ** 2
    gamma = 0.000665 * pressure
    eto = (0.408 * delta * rn + gamma * (900 / (avg + 273)) * wind * (es - ea)) / (
        delta + gamma * (1 + 0.34 * wind))
    if eto < 0:
        return None, "negative_eto_not_published"
    return round(eto, 4), ";".join(flags)


def percentile(values, q):
    vals = sorted(values)
    pos = (len(vals) - 1) * q
    a, b = math.floor(pos), math.ceil(pos)
    return vals[a] + (vals[b] - vals[a]) * (pos - a)


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    # Independent numerical validation against FAO56 chapter 4, published example 18.
    ea = 1.409
    log = math.log(ea / 0.6108)
    dew = 237.3 * log / (17.27 - log)
    result, _ = reference_eto(dt.date(2001, 7, 6), 21.5, 12.3, dew, 2.078, 22.07, 100.1, 50.8, 100)
    assert abs(result - 3.9) < 0.08, result
    write_json(OUT / "method-validation.json", {"source": DOCS[-1], "example": 18,
        "published_eto_mm_day_rounded": 3.9, "calculated_eto_mm_day": result,
        "tolerance_mm_day": 0.08, "pass": True,
        "scope": "Checks equation and radiation implementation, not local field accuracy"})
    parts = []
    for start, end in [("19910101", "20001231"), ("20010101", "20101231"),
                       ("20110101", "20201231")]:
        parts.append(fetch(start, end))
    old = ROOT / "work/data-audit/power-yogyakarta-2021-2025.json"
    copied = RAW / "power-20210101-20251231.json"
    if not copied.exists():
        shutil.copyfile(old, copied)
    parts.append((json.loads(copied.read_text(encoding="utf-8")), copied))
    recent_error = None
    try:
        parts.append(fetch("20260101", "20261107"))
    except Exception as error:
        recent_error = str(error)
    rows, metadata, files, seen = [], {}, [], set()
    missing = defaultdict(int)
    for obj, path in parts:
        data = obj["properties"]["parameter"]
        for name, info in obj["parameters"].items():
            if name in metadata:
                assert metadata[name]["units"] == info["units"], f"Unit changed for {name}"
        assert obj["header"]["time_standard"] == "LST"
        metadata.update(obj["parameters"])
        keys = sorted(set().union(*(v.keys() for v in data.values())))
        fill = obj["header"].get("fill_value", -999)
        elevation = obj["geometry"]["coordinates"][2]
        provenance = path.with_suffix(".provenance.json")
        files.append({"path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size,
            "header": obj["header"], "geometry": obj["geometry"], "messages": obj.get("messages", []),
            "retrieval": json.loads(provenance.read_text()) if provenance.exists() else {
                "source_url": "https://power.larc.nasa.gov/api/temporal/daily/point?" + urllib.parse.urlencode(dict(
                    parameters=",".join(PARAMS), community="AG", longitude=LON, latitude=LAT,
                    start="20210101", end="20251231", format="JSON", **{"time-standard": "LST"})),
                "note": "Existing sample audited 2026-11-08; exact original access timestamp unavailable"}})
        for key in keys:
            date = dt.datetime.strptime(key, "%Y%m%d").date()
            assert date not in seen, f"Duplicate date {key}"
            seen.add(date)
            row = {"date": date.isoformat(), "location_id": "power_regional_yogyakarta",
                   "time_standard": "LST", "period": "baseline_1991_2020" if date.year <= 2020 else (
                       "historical_2021_2025" if date.year <= 2025 else "recent_2026_partial")}
            flags = []
            for parameter in PARAMS:
                value = data.get(parameter, {}).get(key)
                if value is None or value == fill or not math.isfinite(value):
                    missing[parameter] += 1
                    flags.append("missing_" + parameter)
                    value = None
                row[parameter] = value
            needed = ["T2M_MAX", "T2M_MIN", "T2MDEW", "WS2M", "ALLSKY_SFC_SW_DWN", "PS"]
            eto, eto_flags = (None, "missing_eto_inputs")
            if all(row[k] is not None for k in needed):
                eto, eto_flags = reference_eto(date, *(row[k] for k in needed), LAT, elevation)
            row["eto_fao56_mm_day"] = eto
            row["rain_minus_reference_eto_mm_day"] = (round(row["PRECTOTCORR"] - eto, 4)
                if eto is not None and row["PRECTOTCORR"] is not None else None)
            row["qa_flags"] = ";".join(flags + ([eto_flags] if eto_flags else []))
            rows.append(row)
    rows.sort(key=lambda r: r["date"])
    write_csv(OUT / "daily.csv", rows)
    groups = defaultdict(list)
    for row in rows:
        groups[row["date"][:7]].append(row)
    monthly = []
    metrics = {"temperature_mean_c": ("T2M", "mean"), "temperature_max_mean_c": ("T2M_MAX", "mean"),
        "rainfall_total_mm": ("PRECTOTCORR", "sum"), "reference_eto_total_mm": ("eto_fao56_mm_day", "sum"),
        "rain_minus_reference_eto_total_mm": ("rain_minus_reference_eto_mm_day", "sum"),
        "root_wetness_mean_unitless": ("GWETROOT", "mean")}
    for month, items in sorted(groups.items()):
        year, num = map(int, month.split("-"))
        expected = calendar.monthrange(year, num)[1]
        rec = {"month": month, "location_id": "power_regional_yogyakarta", "days_expected": expected,
               "days_present": len(items), "complete_month": len(items) == expected}
        for name, (col, mode) in metrics.items():
            vals = [r[col] for r in items if r[col] is not None]
            rec[name] = round(sum(vals) if mode == "sum" else statistics.mean(vals), 4) if len(vals) == expected else None
            rec[name + "_valid_days"] = len(vals)
        rain = [r["PRECTOTCORR"] for r in items]
        dry_run = longest = 0
        for value in rain:
            dry_run = dry_run + 1 if value is not None and value < 1.0 else 0
            longest = max(longest, dry_run)
        rec["dry_days_lt_1mm"] = sum(v is not None and v < 1 for v in rain) if len(rain) == expected and None not in rain else None
        rec["longest_dry_spell_within_month_days"] = longest if len(rain) == expected and None not in rain else None
        monthly.append(rec)
    baseline = []
    for month in range(1, 13):
        subset = [r for r in monthly if int(r["month"][:4]) <= 2020 and int(r["month"][5:]) == month]
        rec = {"calendar_month": month, "baseline_start": 1991, "baseline_end": 2020}
        for name in metrics:
            vals = [r[name] for r in subset if r[name] is not None]
            rec[name + "_years"] = len(vals)
            for suffix, q in [("p10", 0.1), ("median", 0.5), ("p90", 0.9)]:
                rec[name + "_" + suffix] = round(percentile(vals, q), 4) if vals else None
            rec[name + "_mean"] = round(statistics.mean(vals), 4) if vals else None
        baseline.append(rec)
    for rec in monthly:
        clim = baseline[int(rec["month"][5:]) - 1]
        for name in metrics:
            base = clim[name + "_mean"]
            value = rec[name]
            rec[name + "_anomaly_from_1991_2020_mean"] = round(value - base, 4) if value is not None and base is not None else None
    write_csv(OUT / "monthly.csv", monthly)
    write_csv(OUT / "baseline-1991-2020.csv", baseline)
    dictionary = {p: {**metadata[p], "origin": "NASA POWER", "missing": "null in JSON, empty numeric CSV field"} for p in PARAMS}
    dictionary.update({"eto_fao56_mm_day": {"units": "mm/day", "origin": "derived", "meaning": "FAO56 grass-reference ETo from regional forcing; not crop ET or irrigation requirement"},
        "rain_minus_reference_eto_mm_day": {"units": "mm/day", "origin": "derived", "meaning": "Climatic indicator P-ETo; excludes runoff, effective rainfall, storage, crop coefficient and irrigation"},
        "EVPTRNS": {**metadata["EVPTRNS"], "origin": "NASA POWER", "meaning": "Energy flux retained in original units; never relabel as mm/day"}})
    write_json(OUT / "data-dictionary.json", dictionary)
    dates = [dt.date.fromisoformat(r["date"]) for r in rows]
    gaps = [d.isoformat() for i in range((dates[-1] - dates[0]).days + 1)
            if (d := dates[0] + dt.timedelta(days=i)) not in seen]
    summary = {"area": "Yogyakarta-Klaten regional context; one representative POWER point, no field boundaries",
        "coordinate": [LON, LAT], "records": len(rows), "parameters": len(PARAMS),
        "start": rows[0]["date"], "end": rows[-1]["date"], "baseline_days": sum(r["period"] == "baseline_1991_2020" for r in rows),
        "baseline_months": sum(r["month"] < "2021" for r in monthly), "missing_parameter_values": dict(missing),
        "missing_dates_within_series": gaps, "eto_valid_days": sum(r["eto_fao56_mm_day"] is not None for r in rows),
        "eto_operational_guard_days": sum("rs_rso_bounded" in r["qa_flags"] for r in rows),
        "last_valid_date_by_parameter": {p: next((r["date"] for r in reversed(rows) if r[p] is not None), None) for p in PARAMS},
        "missing_dates_by_parameter": {p: [r["date"] for r in rows if r[p] is None] for p in PARAMS},
        "last_valid_eto_date": next((r["date"] for r in reversed(rows) if r["eto_fao56_mm_day"] is not None), None),
        "recent_request_error": recent_error, "numeric_status": "downloaded_and_checked", "farm_recommendation_ready": False}
    write_json(OUT / "summary.json", summary)
    write_json(OUT / "manifest.json", {"checked_date": AS_OF, "timezone": "Asia/Jakarta", "files": files,
        "documentation": DOCS, "scope": summary["area"], "baseline": "1991-2020 calculated from daily data, not claimed to be station normals",
        "resolution": "Meteorology native 0.5 degree latitude x 0.625 degree longitude; other parameters follow original source grids",
        "method": {"eto": "FAO56 eq6, es from Tmax/Tmin, ea from daily dewpoint, u2 as provided, P from POWER, daily G=0, albedo=0.23, extraterrestrial radiation latitude/day, Rso uses POWER coordinate elevation",
                   "operational_guard": "Rs/Rso clipped to [0.3,1] to keep empirical cloud term physical; flagged per day; additional implementation assumption, not a measured input",
                   "aggregation": "Totals and means are null unless every calendar day valid; anomalies are against same calendar month in baseline",
                   "quantile": "Linear interpolation between ordered monthly observations (type7)",
                   "dry_spell": "Rain <1 mm/day, count resets at month boundary and on missing values; descriptive threshold, not crop failure threshold"},
        "limitations": ["Regional model estimates, not in-field observations", "Recent 2026 partial and may be revised; not seasonal forecasts",
            "Daily LST is not timezone Asia/Jakarta", "ETo and P-ETo are screening indicators; irrigation requires crop/stage/soil/management",
            "Five-year historical sample retained as originally downloaded; fresh earlier and recent requests can reflect different reprocessing vintages"]})
    (OUT / "README.md").write_text("""# Iklim regional Yogyakarta-Klaten

Data NASA POWER harian, titik contoh 110.37,-7.8. `daily.csv` mempertahankan 12 parameter dan unit aslinya. Baseline 1991-2020 dihitung dari data harian. Data 2026 bersifat parsial dan dapat direvisi. Lokasi ini representatif untuk konteks regional, bukan pengukuran pada setiap petak.

`monthly.csv` berisi agregat kalender dan anomali terhadap bulan yang sama pada 1991-2020. Agregat yang tidak memiliki seluruh hari valid dikosongkan. `baseline-1991-2020.csv` berisi mean, median, persentil 10/90 dan jumlah tahun valid per metrik. Tidak ada imputasi.

ETo adalah estimasi referensi rumput FAO56 dengan forcing regional. Ini bukan ET aktual tanaman atau kebutuhan irigasi. P-ETo tidak memperhitungkan limpasan, simpanan air tanah, koefisien tanaman, irigasi atau efisiensinya. Penjagaan Rs/Rso 0.3-1 adalah asumsi operasional tambahan dan ditandai pada QA harian. Lihat method-validation.json untuk pemeriksaan terhadap contoh terbitan FAO, serta manifest.json untuk metode dan sumber.

EVPTRNS tetap MJ/m²/hari. GWETROOT/GWETTOP adalah kebasahan tanah model, bukan kadar air volumetrik yang diukur pada petak. Resolusi meteorologi sekitar puluhan km. Data LST mengikuti waktu matahari, bukan definisi zona waktu WIB.

Reproduksi dari root proyek: `py -3.11 scripts/data/prepare_climate.py`. Raw respons disimpan dan digunakan kembali. Periode 2021-2025 berasal dari sampel audit awal, dengan hash yang tercatat. Tidak ada aplikasi atau rekomendasi rotasi dibuat oleh skrip ini.
""", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
