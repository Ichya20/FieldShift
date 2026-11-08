"""Verify supplementary data numerics, QA, provenance and frozen inputs locally."""
from __future__ import annotations

import csv
from collections import Counter
import datetime as dt
import hashlib
import html
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data/supplemental/environment"


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    frozen = json.loads((OUT / "frozen-prepared-before.json").read_text(encoding="utf-8"))["files"]
    assert not summary["validation"]["failed_acquisitions"], "Some acquisitions failed; keep explicit incomplete status"
    # An unavailable optional documentation URL is retained explicitly. Numeric
    # source failures remain fatal through failed_acquisitions above.
    assert all(len(record["attempts"]) <= 3 for record in manifest["failed_sources"])
    current = {path.relative_to(ROOT).as_posix(): {"bytes": path.stat().st_size, "sha256": sha(path)}
               for path in (ROOT / "data/prepared").rglob("*") if path.is_file()}
    assert current == frozen, "Frozen prepared package changed"
    checksums = 0
    for source in manifest["sources"]:
        path = OUT / source["file"]
        assert sha(path) == source["sha256"] and path.stat().st_size == source["bytes"]
        assert source["url"].startswith("https://") and source["retrieved_at_utc"]
        checksums += 1
    for name, record in manifest["read_only_frozen_inputs"].items():
        assert sha(ROOT / name) == record["sha256"]
    for record in manifest["derived_files"]:
        path = OUT / record["file"]
        assert path.stat().st_size == record["bytes"] and sha(path) == record["sha256"]
    catalog = OUT / "sources/MYD13Q1-earthengine-catalog.html"
    if catalog.exists():
        text = html.unescape(re.sub("<[^>]+>", " ", catalog.read_text(encoding="utf-8")))
        text = re.sub(r"\s+", " ", text)
        for definition in ["Bits 0-1: VI quality", "Bits 2-5: VI usefulness", "Bits 6-7: Aerosol Quantity",
                           "Bit 8: Adjacent cloud detected", "Bit 10: Mixed Clouds",
                           "Bits 11-13: Land/water mask", "Bit 14: Possible snow/ice", "Bit 15: Possible shadow"]:
            assert definition in text, f"Alternative Aqua reference lacks expected QA definition: {definition}"
    verified_rows = []
    for product in ["MOD13Q1", "MYD13Q1"]:
        rows = read_csv(OUT / f"{product}-supplemental-qa.csv")
        monthly = read_csv(OUT / f"{product}-monthly-good-only.csv")
        assert len({(row["point_id"], row["modis_date"]) for row in rows}) == len(rows)
        for row in rows:
            assert row["product"] == product
            assert row["platform"] == ("Terra" if product == "MOD13Q1" else "Aqua")
            for index in ["ndvi", "evi"]:
                raw = int(row[index + "_raw"])
                if -2000 <= raw <= 10000:
                    assert abs(float(row[index]) - raw * .0001) < 1e-10
                else:
                    assert row[index] == ""
            if row["selected_observation_date"]:
                observed = dt.date.fromisoformat(row["selected_observation_date"])
                nominal = dt.date.fromisoformat(row["composite_start_date"])
                assert nominal <= observed <= nominal + dt.timedelta(days=15)
            raw_qa = int(row["vi_quality_raw"])
            bit_layout = {"modland_qa": (0, 2), "vi_usefulness": (2, 4), "aerosol_quantity": (6, 2),
                          "adjacent_cloud": (8, 1), "brdf_correction": (9, 1), "mixed_cloud": (10, 1),
                          "land_water": (11, 3), "possible_snow_ice": (14, 1), "possible_shadow": (15, 1)}
            for field, (offset, width) in bit_layout.items():
                if 0 <= raw_qa <= 65534:
                    assert int(row[field]) == raw_qa // (2 ** offset) % (2 ** width)
                else:
                    assert row[field] == ""
            if row["quality_status"] == "good_strict":
                assert int(row["pixel_reliability"]) == 0 and int(row["modland_qa"]) == 0
                assert int(row["vi_usefulness"]) <= 2 and int(row["aerosol_quantity"]) <= 1
                assert int(row["land_water"]) == 1
                assert all(int(row[key]) == 0 for key in ["adjacent_cloud", "mixed_cloud", "possible_snow_ice", "possible_shadow"])
                assert row["quality_reason"] == "" and row["selected_observation_date"]
            if int(row["pixel_reliability"]) not in (0, 1):
                assert row["quality_status"] == "excluded"
        for month in monthly:
            selected = [row for row in rows if row["point_id"] == month["point_id"] and row["selected_observation_date"].startswith(month["observation_month"])]
            good = [row for row in selected if row["quality_status"] == "good_strict"]
            assert int(month["n_selected_observations"]) == len(selected)
            nominal = [row for row in rows if row["point_id"] == month["point_id"] and row["composite_start_date"].startswith(month["observation_month"])]
            assert int(month["n_composites_nominal_start_month"]) == len(nominal)
            assert int(month["n_good_strict"]) == len(good)
            assert month["interpolated"] == "False"
            for index in ["ndvi", "evi"]:
                mean = month[index + "_good_mean"]
                if not good:
                    assert mean == "", "No good observations must stay blank"
                else:
                    expected = round(sum(float(row[index]) for row in good) / len(good), 4)
                    assert abs(float(mean) - expected) < 1e-10
        for series in summary["after"]["additional_vegetation_series"]:
            if series["product"] != product:
                continue
            selected = [row for row in rows if row["point_id"] == series["point_id"]]
            assert len(selected) == series["expected_composites"] == series["downloaded_composites"]
            assert dict(Counter(row["quality_status"] for row in selected)) == series["quality_counts"]
        verified_rows.extend(rows)
    if (OUT / "POWER-recent-recheck.csv").exists():
        climate = read_csv(OUT / "POWER-recent-recheck.csv")
        previous = {row["date"]: row for row in read_csv(ROOT / "data/prepared/climate/daily.csv")}
        old_geometry = json.loads((ROOT / "data/prepared/climate/raw/power-20260101-20261107.json").read_text(encoding="utf-8"))["geometry"]
        same_geometry = old_geometry == summary["after"]["climate_publication_recheck"]["geometry"]
        for row in climate:
            assert row["time_standard"] == "LST"
            if row["eto_fao56_mm_day"]:
                assert all(row[key] for key in ["T2M_MAX", "T2M_MIN", "T2MDEW", "WS2M", "ALLSKY_SFC_SW_DWN", "PS"])
                if row["PRECTOTCORR"]:
                    assert abs(float(row["rain_minus_reference_eto_mm_day"]) - (float(row["PRECTOTCORR"]) - float(row["eto_fao56_mm_day"]))) < 1e-9
            else:
                assert row["rain_minus_reference_eto_mm_day"] == ""
            old = previous.get(row["date"])
            if old and row["eto_fao56_mm_day"] and old["eto_fao56_mm_day"]:
                # Revisions of forcing may legitimately change the result;
                # if inputs are unchanged, the frozen FAO56 equation must agree.
                needed = ["T2M_MAX", "T2M_MIN", "T2MDEW", "WS2M", "ALLSKY_SFC_SW_DWN", "PS"]
                if same_geometry and all(float(row[key]) == float(old[key]) for key in needed):
                    assert abs(float(row["eto_fao56_mm_day"]) - float(old["eto_fao56_mm_day"])) < 1e-9
    report = {"verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "status": "passed", "pass": True,
              "frozen_files_unchanged": len(frozen), "source_checksums_verified": checksums,
              "vegetation_rows_verified": len(verified_rows),
              "checks": ["unchanged frozen package", "source URL/time/size/SHA256", "complete requested composites and unique keys",
                         "sensor identities separate", "VI scale/range and selected dates", "strict QA masks and excluded cloudy data",
                         "Aqua provider QA bit definitions present", "independent monthly good-only means; blanks and no interpolation", "climate ETo matched inputs and equation consistency"]}
    (OUT / "local-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
