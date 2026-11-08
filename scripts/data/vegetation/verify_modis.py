"""Independent integrity and quality-aggregation checks for the prepared data."""
import collections
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "prepared" / "vegetation"


def main():
    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    with (OUT / "modis_16day_qa.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    with (OUT / "modis_monthly_good_only.csv").open(newline="", encoding="utf-8") as stream:
        monthly = list(csv.DictReader(stream))
    assert not summary["failed_batches"] and not manifest["failures"], "Failed download batches remain"
    assert len(rows) == 230 and len(monthly) == 120, "Expected 115 composites and 60 months per point"
    assert len({(r["point_id"], r["modis_date"]) for r in rows}) == len(rows), "Duplicate point/composite keys"
    assert len({(r["point_id"], r["observation_month"]) for r in monthly}) == len(monthly), "Duplicate point/month keys"
    checksums = 0
    for record in manifest["sources"] + manifest["excluded_context_files"]:
        path = OUT / record["file"]
        assert path.is_file(), f"Missing manifest file {path}"
        assert path.stat().st_size == record["bytes"], f"Size mismatch {path}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"], f"SHA mismatch {path}"
        checksums += 1
    point_reports = []
    for point in summary["points"]:
        point_rows = [r for r in rows if r["point_id"] == point["id"]]
        assert len(point_rows) == summary["expected_composites_by_point"][point["id"]] == 115
        assert collections.Counter(r["composite_start_date"][:4] for r in point_rows) == {str(y): 23 for y in range(2021, 2026)}
        assert all(abs(float(r["sample_latitude"]) - point["latitude"]) < 1e-12 and abs(float(r["sample_longitude"]) - point["longitude"]) < 1e-12 for r in point_rows)
        for row in point_rows:
            for index in ("ndvi", "evi"):
                raw = int(row[index + "_raw"])
                assert not row[index] or abs(float(row[index]) - raw * .0001) < 1e-10
            nominal = dt.date.fromisoformat(row["composite_start_date"])
            observed = dt.date.fromisoformat(row["selected_observation_date"])
            assert nominal <= observed <= min(nominal + dt.timedelta(days=15), dt.date(nominal.year, 12, 31)), "Selected observation outside composite interval"
            if row["quality_status"] == "good_strict":
                assert int(row["pixel_reliability"]) == 0 and int(row["modland_qa"]) == 0
                assert int(row["vi_usefulness"]) <= 2 and int(row["aerosol_quantity"]) <= 1
                assert all(int(row[k]) == 0 for k in ("adjacent_cloud", "mixed_cloud", "possible_snow_ice", "possible_shadow"))
                assert int(row["land_water"]) == 1 and row["quality_reason"] == ""
            if int(row["pixel_reliability"]) in (-1, 2, 3):
                assert row["quality_status"] == "excluded", "Cloud/snow/fill must be excluded"
        point_months = [m for m in monthly if m["point_id"] == point["id"]]
        assert len(point_months) == 60
        for month in point_months:
            selected = [r for r in point_rows if r["selected_observation_date"].startswith(month["observation_month"])]
            good = [r for r in selected if r["quality_status"] == "good_strict"]
            assert int(month["n_selected_observations"]) == len(selected)
            assert int(month["n_good_strict"]) == len(good)
            assert month["interpolated"] == "False"
            assert int(month["n_marginal_review"]) == sum(r["quality_status"] == "marginal_review" for r in selected)
            assert int(month["n_excluded"]) == sum(r["quality_status"] == "excluded" for r in selected)
            for index in ("ndvi", "evi"):
                actual = month[index + "_good_mean"]
                if good:
                    expected = round(sum(float(r[index]) for r in good) / len(good), 4)
                    assert actual != "" and abs(float(actual) - expected) < 1e-10, "Monthly mean differs from good-only mean"
                else:
                    assert actual == "", "No good observations must produce a blank, not zero"
        counts = dict(collections.Counter(r["quality_status"] for r in point_rows))
        assert counts == point["quality_counts"]
        point_reports.append({"point_id": point["id"], "sample_role": point["sample_role"], "composites": len(point_rows),
                              "quality_counts": counts, "months_with_strict_good_data": sum(int(m["n_good_strict"]) > 0 for m in point_months),
                              "months_without_strict_good_data": sum(int(m["n_good_strict"]) == 0 for m in point_months)})
    report = {"verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "status": "passed",
              "checks": ["complete expected date coverage", "unique keys", "consistent coordinates", "raw-to-scaled units",
                         "selected day lies within composite interval", "strict quality selection and cloudy exclusions",
                         "monthly counts and means recomputed from primary-quality data only", "missing months blank, no interpolation",
                         "source and derived SHA-256 and sizes"],
              "files_checksums_verified": checksums, "rows_verified": len(rows), "monthly_rows_verified": len(monthly), "points": point_reports}
    (OUT / "verification_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
