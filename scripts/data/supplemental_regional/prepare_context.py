"""Validate a bounded official weather snapshot; never make a crop forecast."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/supplemental/regional-context"


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(name, value):
    (DATA / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main():
    evidence = load(DATA / "source-evidence.json")
    for source in evidence["sources"]:
        assert hashlib.sha256((DATA / source["path"]).read_bytes()).hexdigest() == source["sha256"]
    raw = load(DATA / "sources/bmkg-klaten-forecast.json")
    location = raw["lokasi"]
    assert location["adm4"] == "33.10.25.1003"
    assert location["desa"] == "Klaten" and location["kotkab"] == "Klaten"
    assert len(raw["data"]) == 1
    station = raw["data"][0]
    assert station["lokasi"]["adm4"] == location["adm4"]
    rows = [r for group in station["cuaca"] for r in group]
    times = [datetime.fromisoformat(r["datetime"].replace("Z", "+00:00")) for r in rows]
    assert times == sorted(set(times)) and times
    assert all(b-a == timedelta(hours=3) for a, b in zip(times, times[1:]))
    documents = (DATA / "sources/bmkg-forecast-docs.html").read_text(encoding="utf-8")
    assert "km/jam" in documents and "analysis_date" in documents and "60" in documents
    processed = []
    for row, instant in zip(rows, times):
        utc_clock = datetime.strptime(row["utc_datetime"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        local_clock = datetime.strptime(row["local_datetime"], "%Y-%m-%d %H:%M:%S")
        assert utc_clock == instant
        assert local_clock == (instant + timedelta(hours=7)).replace(tzinfo=None)
        assert -60 <= row["t"] <= 60 and 0 <= row["hu"] <= 100 and 0 <= row["tcc"] <= 100
        assert 0 <= row["ws"] < 300 and row["weather_desc"]
        assert row["analysis_date"]
        processed.append({"valid_time_utc": instant.isoformat(), "valid_time_local": row["local_datetime"],
                          "issue_time_utc": row["analysis_date"] + "+00:00",
                          "temperature_c": row["t"], "relative_humidity_percent": row["hu"],
                          "wind_speed_km_h": row["ws"], "wind_from": row["wd"],
                          "cloud_cover_percent": row["tcc"], "weather_description_id": row["weather_desc"]})
    null_fields = Counter(k for row in rows for k, value in row.items() if value is None)
    summary = {
        "prepared_at_utc": datetime.now(timezone.utc).isoformat(),
        "module": "regional-context", "data_kind": "official_short_term_weather_forecast_snapshot",
        "source": "BMKG — Badan Meteorologi, Klimatologi, dan Geofisika",
        "source_evidence": "source-evidence.json", "location": location,
        "location_role": "Explicit Klaten village administrative forecast context; not the example cropland pixel or a verified farm.",
        "farm_boundary_verified": False, "automatically_assigned_to_demo_crop_pixel": False,
        "records": len(processed), "start_valid_utc": times[0].isoformat(),
        "last_valid_timestamp_utc": times[-1].isoformat(),
        "issue_times_utc": sorted({r["issue_time_utc"] for r in processed}),
        "temporal_resolution_hours": 3,
        "operational_use": "Refetch and check current issue/valid times before display; this saved snapshot expires. No live service is implemented.",
        "seasonal_forecast_available": False, "merged_with_nasa_history": False,
        "raw_null_fields": dict(null_fields), "null_policy": "Unreported values stay null in the raw source; no inferred visibility.",
        "withheld_fields": {"tp": "Field is in raw response but amount unit and accumulation interval are not defined in the captured public API docs; do not publish rainfall totals from it.",
                            "vs": "Raw visibility is unreported; no substitution from other weather fields."},
        "what_filled": ["Verified public API access and exact administrative forecast location",
                        "Temperature, humidity, wind and cloud forecast with issue and valid times",
                        "Source attribution, cadence, units and saved evidence"],
        "remaining_gaps": ["Operational seasonal forecast/crop calendar is not acquired",
                           "The actual farm and its water supply are unknown",
                           "Forecast rainfall amount semantics are not yet verified",
                           "Ongoing refresh is a future implementation task"],
        "validation": {"pass": True, "unique_sorted_times": True, "three_hour_intervals": True,
                       "utc_local_consistent": True, "physical_ranges": True, "source_hashes": len(evidence["sources"])},
        "provider_terms": {"attribution_required": "BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)",
                           "nominal_refreshes_per_day": 2, "request_limit_per_minute_per_ip": 60,
                           "documentation_url": "https://data.bmkg.go.id/prakiraan-cuaca/"},
    }
    write("bmkg-klaten-forecast-prepared.json", {"summary": summary, "forecast": processed})
    write("summary.json", summary)
    (DATA / "README.md").write_text(
        "# Konteks cuaca regional BMKG\n\n"
        "Snapshot resmi prakiraan cuaca kelurahan Klaten, Klaten Tengah. Lokasinya dipilih secara eksplisit "
        "sebagai konteks administratif dan tidak menggantikan data piksel contoh atau kondisi lahan. "
        "Suhu, kelembapan, angin dan awan tersedia per tiga jam dengan waktu produksi dan waktu berlaku. "
        "Snapshot harus diperbarui sebelum penggunaan operasional; prakiraan cuaca ini bukan prakiraan musim tanam.\n\n"
        "Sumber asli disimpan di `sources/`, beserta URL, waktu unduh dan SHA-256 di `source-evidence.json`. "
        "`tp` dan visibility tidak dipakai dalam angka olahan: semantik jumlah hujan belum terverifikasi dan visibility null dari sumber. "
        "Tidak ada pengisian nilai kosong atau penggabungan dengan riwayat NASA.\n\n"
        "Unduh: `pwsh -File scripts/data/supplemental_regional/fetch_sources.ps1` (tambahkan `-Refresh` untuk data baru). "
        "Validasi/olah: `py -3.11 scripts/data/supplemental_regional/prepare_context.py`.\n",
        encoding="utf-8")
    print(json.dumps({"records": len(processed), "validation": summary["validation"],
                      "last_valid_timestamp_utc": summary["last_valid_timestamp_utc"]}, indent=2))


if __name__ == "__main__":
    main()
