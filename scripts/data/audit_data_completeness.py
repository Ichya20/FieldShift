"""Audit public-demo readiness and package additive data; no backend or network.

Run after each supplemental module has completed its own source/QA checks.
The original prepared snapshot and its manifest are never rewritten.
"""
from __future__ import annotations

from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
PREPARED = ROOT / "data/prepared"
SUPPLEMENT = ROOT / "data/supplemental"
OUTPUT = ROOT / "outputs"
MODULES = ("environment", "soil-terrain", "agronomy", "regional-context", "crop-water")


def reject_constant(value):
    raise ValueError(f"Non-finite JSON value: {value}")


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"), parse_constant=reject_constant)


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    summaries = {name: read(SUPPLEMENT / name / "summary.json") for name in MODULES}
    checks = []

    def check(name, passed, detail=None):
        checks.append({"check": name, "pass": bool(passed), "detail": detail})
        if not passed:
            raise ValueError(f"Data readiness check failed: {name}: {detail}")

    original_manifest = read(PREPARED / "file-manifest.json")
    mismatches = [entry["path"] for entry in original_manifest["files"]
                  if not (ROOT / entry["path"]).is_file() or sha(ROOT / entry["path"]) != entry["sha256"]]
    check("Original prepared snapshot retains all original hashes", not mismatches,
          {"files": len(original_manifest["files"]), "mismatches": mismatches})
    daily = csv_rows(PREPARED / "climate/daily.csv")
    numeric_columns = list(read(PREPARED / "climate/data-dictionary.json"))
    climate_coverage = {}
    for name, start, end in (("baseline", "1991-01-01", "2020-12-31"),
                             ("historical_comparison", "2021-01-01", "2025-12-31"),
                             ("recent_partial", "2026-01-01", "2026-11-07")):
        rows = [r for r in daily if start <= r["date"] <= end]
        climate_coverage[name] = {"start": start, "end_inclusive": end, "dates": len(rows),
                                 "missing_by_metric": {column: sum(r[column] == "" for r in rows)
                                                       for column in numeric_columns}}
    check("Climate baseline is complete for every numeric metric",
          climate_coverage["baseline"]["dates"] == 10958 and
          not any(climate_coverage["baseline"]["missing_by_metric"].values()))
    check("Comparison history is complete for every numeric metric",
          climate_coverage["historical_comparison"]["dates"] == 1826 and
          not any(climate_coverage["historical_comparison"]["missing_by_metric"].values()))
    original_soil = csv_rows(PREPARED / "soil-terrain/processed/soil-cells.csv")
    original_soil_qa = dict(Counter(r["qa_status"] for r in original_soil))
    primary_ph = [r for r in original_soil if r["property"] == "phh2o" and r["row"] == "4" and r["col"] == "6"]
    check("Primary pH covers all five depths and three source statistics",
          len(primary_ph) == 15 and all(r["value"] and r["qa_status"] == "usable_prediction" for r in primary_ph))
    terrain = read(PREPARED / "soil-terrain/manifest-terrain.json")["records"][0]
    check("Elevation and slope have numeric valid cells",
          terrain["elevation_m"]["valid_cells"] > 0 and terrain["slope_degrees"]["valid_cells"] > 0)
    vegetation = read(PREPARED / "vegetation/summary.json")
    check("Both example pixels have quality-screened vegetation context",
          len(vegetation["points"]) == 2 and all(p["quality_counts"]["good_strict"] > 0 for p in vegetation["points"]))
    crop_refs = read(PREPARED / "agronomy/crop-reference.json")["crops"]
    check("All three crops have traceable numeric pH, temperature and seasonal ET references",
          {c["crop_id"] for c in crop_refs} == {"padi", "jagung", "kedelai"} and
          all(all(c[key]["min"] is not None and c[key]["max"] is not None and c[key]["source_id"]
                  for key in ("species_soil_ph_optimum", "species_temperature_optimum_c", "seasonal_crop_water_need_indicative_mm"))
              for c in crop_refs))
    gaez = read(PREPARED / "agronomy/gaez-baseline-point.json")["rows"]
    check("Extracted GAEZ classes and bounds are present",
          len(gaez) == 12 and all(r["raw_value"] is not None and r["class_label"] and r["pixel_bounds"] for r in gaez))
    contract = read(SUPPLEMENT / "agronomy/farm-input-contract.json")
    rule_map = read(SUPPLEMENT / "agronomy/method-rule-input-map.json")
    method = read(ROOT / "specs/rotation-method-v1.json")
    check("Complete typed input definitions and twelve rule mappings are present",
          len(contract["fields"]) == 119 and rule_map["rule_count"] == 12 and
          not rule_map["unmapped_active_fields"] and
          {r["rule_id"] for r in rule_map["rules"]} == {r["id"] for r in method["rules"]})
    for name in MODULES:
        validation = summaries[name].get("validation", {})
        if name == "agronomy":
            schema_cases = validation.get("schema_checks", [])
            passed = (validation.get("prepared_immutable") is True and
                      validation.get("claim_source_links_valid") is True and
                      validation.get("all_template_field_values_null") is True and
                      validation.get("json_schema_validation") == "passed_draft202012_schema_null_template_and_boundaries" and
                      validation.get("schema_check_count", 0) == len(schema_cases) >= 19 and
                      all(case.get("passed") is True for case in schema_cases))
        else:
            passed = validation.get("pass") is True
        check(f"{name} supplemental validation passed", passed, validation)

    # Verify module inventories written by the collectors before making a new
    # global inventory. Rehashing modified data alone would hide corruption.
    for relative in ("agronomy/manifest.json", "soil-terrain/file-manifest.json"):
        inventory = read(SUPPLEMENT / relative)["files"]
        bad = [entry["path"] for entry in inventory
               if not (ROOT / entry["path"]).is_file() or sha(ROOT / entry["path"]) != entry["sha256"]
               or (ROOT / entry["path"]).stat().st_size != entry["bytes"]]
        check(f"Collector inventory remains intact: {relative}", not bad, {"files": len(inventory), "mismatches": bad})
    environment_manifest = read(SUPPLEMENT / "environment/manifest.json")
    environment_sources = environment_manifest["sources"] + environment_manifest["derived_files"]
    bad_environment = [entry["file"] for entry in environment_sources
                       if sha(SUPPLEMENT / "environment" / entry["file"]) != entry["sha256"]]
    check("Environment source and derived inventories remain intact", not bad_environment,
          {"files": len(environment_sources), "mismatches": bad_environment})
    for name in ("regional-context", "crop-water"):
        sources = read(SUPPLEMENT / name / "source-evidence.json")["sources"]
        bad = [entry["path"] for entry in sources if sha(SUPPLEMENT / name / entry["path"]) != entry["sha256"]]
        check(f"Official source snapshots remain intact: {name}", not bad, {"files": len(sources), "mismatches": bad})

    requirements = [
        {"id": "daily_climate_baseline", "status": "available_complete", "required_for_mvp": True,
         "path": "data/prepared/climate/daily.csv", "limit": "Regional grid context; recent publication latency is separate from the complete baseline/history."},
        {"id": "quality_screened_vegetation", "status": "available_with_source_qa_gaps", "required_for_mvp": True,
         "path": "data/supplemental/environment/summary.json", "limit": "Terra and Aqua retain source/QA identity; missing good observations do not become invented crop/fallow records."},
        {"id": "soil_properties_and_uncertainty", "status": "available_predictions_with_documented_masks", "required_for_mvp": True,
         "path": "data/supplemental/soil-terrain/summary.json", "limit": "Native verification is separate from the original WCS snapshot; valid model zeros are distinguished from nodata. Neither is a soil laboratory result."},
        {"id": "terrain_and_landcover", "status": "available_historical_context", "required_for_mvp": True,
         "path": "data/prepared/soil-terrain/manifest.json", "limit": "Copernicus DSM and WorldCover 2021 do not establish current farm microtopography or crop species."},
        {"id": "crop_references", "status": "available_references", "required_for_mvp": True,
         "path": "data/supplemental/agronomy/source-evidence.json", "limit": "Cultivar descriptors are alternatives; no actual cultivar or duration is selected for the unknown farm."},
        {"id": "gaez", "status": "available_historical_categories", "required_for_mvp": True,
         "path": "data/prepared/agronomy/gaez-baseline-point.json", "limit": "Historical 2001–2020, five arc-minute categorical model; management assumptions remain separate."},
        {"id": "input_definitions_and_rule_requirements", "status": "complete_definitions_actuals_unknown", "required_for_mvp": True,
         "path": "data/supplemental/agronomy/farm-input-contract.json", "limit": "119 typed definitions, units and record structures; actual values are not fabricated."},
        {"id": "repeatable_comparison_case", "status": "available_explicit_synthetic_fixture", "required_for_mvp": True,
         "path": "specs/fixtures/rotation-demo.json", "limit": "The fixture is not farm history; it uses real environmental inputs and explicit calendar assumptions."},
        {"id": "short_term_weather", "status": "available_expiring_snapshot", "required_for_mvp": False,
         "path": "data/supplemental/regional-context/summary.json", "limit": "Official Klaten administrative forecast context. Re-fetch before use; not a seasonal forecast or assigned field observation."},
        {"id": "future_crop_water_parameters", "status": "available_generic_reference_only", "required_for_mvp": False,
         "path": "data/supplemental/crop-water/crop-water-reference.json", "limit": "FAO56 Kc/root/depletion references do not close the local water balance or enable water-savings claims."},
        {"id": "actual_farm_and_management", "status": "unknown_no_actual_farm_data", "required_for_mvp": False,
         "needed_for": "field_specific_advice", "path": "data/supplemental/agronomy/farm-input-complete-template.json",
         "limit": "User confirmed no farm data; geometry, crop dates, cultivar, irrigation and management require field information."},
        {"id": "local_model_validation", "status": "not_available_from_public_context_alone", "required_for_mvp": False,
         "needed_for": "validated_field_recommendations", "limit": "Local agronomic review, measurements and calibration remain necessary."},
        {"id": "economics", "status": "deferred_no_comparable_farm_inputs", "required_for_mvp": False,
         "needed_for": "economic_comparison", "limit": "Farm-relevant yield, sale price, quality/moisture, date and costs are not provided. Generic statistics are not substituted for farm profit."},
        {"id": "seasonal_forecast", "status": "not_acquired_or_validated", "required_for_mvp": False,
         "needed_for": "operational_season_planning", "limit": "Historical analogues and a three-day weather forecast do not supply a seasonal forecast."},
        {"id": "optional_nasa_missions", "status": "metadata_only_not_required_for_current_mvp", "required_for_mvp": False,
         "path": "data/prepared/optional-sources.json", "limit": "HLS/SMAP/GPM/ECOSTRESS/NASADEM/GRACE require a justified bounded extraction, QA and access before future use."},
    ]
    for requirement in requirements:
        if "path" in requirement:
            check(f"Requirement {requirement['id']} resolves to a real file", (ROOT / requirement["path"]).is_file())
    policies = {
        "prepared_snapshot": "Keep the original data/prepared and its 390-file manifest immutable; use supplemental sources explicitly.",
        "input_contract": "The supplemental typed contract corrects the original generic dictionary for future use; retained legacy priority weights are unused.",
        "soil": "Use native-verified supplemental data with its CRS/mask/provenance when selected; do not patch zeros into the old WCS grid. The actual primary anchor native pH Q95 is 7.9; the legacy WCS containing-cell centre Q95 is 7.8. These are different sampling supports. Preserve the stage-2 historical fixture and do not reuse legacy row/column indexes in the native grid.",
        "vegetation": "Preserve sensor/product/selected observation date/QA and native footprint. Do not silently blend sensors or interpolate gaps.",
        "climate": "Use complete baseline/history for comparisons; recent missing source values remain null. Do not replace observations with forecast values.",
        "forecast": "The BMKG snapshot is optional and time limited. Check issue/valid times and attribution, and refetch before operational use.",
        "farmer_inputs": "No actual farmer data exists in this task; use public example context and explicitly labelled comparison assumptions.",
        "unavailable_outputs": "Yield/ranking/profit/N credit/soil-health gain/irrigation/savings remain null under method v0.1.0.",
    }
    audit = {"audited_at_utc": datetime.now(timezone.utc).isoformat(), "user_decision": "No actual farm data; retrieve available public sources.",
             "status": "public_demo_data_ready_with_explicit_source_and_field_gaps", "backend_implemented": False,
             "public_context_ready": True, "all_possible_data_complete": False,
             "actual_farm_dataset_complete": False, "local_agronomic_validation": False,
             "prepared_snapshot": {"files_verified": len(original_manifest["files"]), "unchanged": True,
                                   "manifest_sha256": sha(PREPARED / "file-manifest.json")},
             "original_missingness": {"climate": climate_coverage, "soil_qa_counts": original_soil_qa,
                                      "vegetation": [{"point_id": p["id"], "good_months": p["months_with_primary_data"],
                                                      "months_without_good_data": p["months_without_primary_data"]} for p in vegetation["points"]]},
             "requirements": requirements, "use_policy": policies,
             "module_summary_paths": {name: f"data/supplemental/{name}/summary.json" for name in MODULES},
             "checks": checks}
    write(SUPPLEMENT / "readiness-audit.json", audit)
    (SUPPLEMENT / "README.md").write_text(
        "# FieldShift — tambahan data sebelum backend\n\n"
        "Indeks terbaru adalah [readiness-audit.json](readiness-audit.json). Paket ini menambah sumber numerik, "
        "verifikasi dan definisi input tanpa mengubah snapshot `data/prepared`. Kelengkapan publik untuk contoh MVP "
        "berbeda dari kelengkapan informasi lahan nyata. Pengguna mengonfirmasi belum ada data petani.\n\n"
        "- `environment/`: tambahan Terra/Aqua dan pemeriksaan batas publikasi POWER.\n"
        "- `soil-terrain/`: verifikasi raster asli dan perbedaan nol prediksi dengan nodata.\n"
        "- `agronomy/`: descriptor resmi, kontrak input bertipe, satuan, skema dan kebutuhan 12 aturan.\n"
        "- `regional-context/`: snapshot prakiraan cuaca BMKG yang punya masa berlaku.\n"
        "- `crop-water/`: FAO56 Tabel 12/22 untuk riset model air berikutnya; bukan kalibrasi lokal.\n\n"
        "Sebelum menggunakan data, ikuti `use_policy` pada indeks. Sumber, waktu, QA dan hash tersimpan per modul. "
        "Nilai publik tidak dipindahkan ke kolom observasi petani. Tidak ada backend atau proses refresh otomatis.\n\n"
        "Audit offline dan kemas ulang: `py -3.11 scripts/data/audit_data_completeness.py`. "
        "Skrip mengharuskan semua modul tambahan telah selesai; tidak mengunduh data.\n", encoding="utf-8")

    manifest_entries = []
    for path in sorted(SUPPLEMENT.rglob("*")):
        if not path.is_file() or path in {SUPPLEMENT / "file-manifest.json", SUPPLEMENT / "validation-report.json"}:
            continue
        if path.suffix in {".json", ".geojson"}:
            read(path)
        manifest_entries.append({"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
    write(SUPPLEMENT / "file-manifest.json", {"created_at_utc": datetime.now(timezone.utc).isoformat(), "files": manifest_entries})
    check("Every supplemental file matches the final checksum inventory",
          all(sha(ROOT / entry["path"]) == entry["sha256"] for entry in manifest_entries), {"files": len(manifest_entries)})
    write(SUPPLEMENT / "validation-report.json", {"validated_at_utc": datetime.now(timezone.utc).isoformat(),
          "pass": True, "checks": checks, "supplemental_files": len(manifest_entries),
          "local_agronomic_validation": False,
          "archive_verification_sidecar": "outputs/data-package-verification.json",
          "scope": "Data/source integrity and current-MVP public context coverage; not field/model accuracy. Archive CRC/digest is recorded separately to avoid a self-referential archive hash."})

    # A new version preserves both the original public snapshot and the additions.
    archive = OUTPUT / "fieldshift-data-publik-v2-2026-11-08.zip"
    package_paths = [p for directory in (ROOT / "data/prepared", SUPPLEMENT, ROOT / "specs", ROOT / "docs", ROOT / "scripts/data", ROOT / "scripts/method", ROOT / "tests/method")
                     for p in directory.rglob("*") if p.is_file() and
                     not any(part in {"_vendor", "__pycache__", "node_modules"} for part in p.parts) and p.suffix != ".pyc"]
    package_paths += [ROOT / "PROJECT_CONTEXT.md", OUTPUT / "audit-kelengkapan-data-fieldshift.md",
                      OUTPUT / "kesiapan-data-fieldshift.md", OUTPUT / "audit-data-field-shift.md", ROOT / "work/page-text.txt",
                      OUTPUT / "rotation-method-demo.json", OUTPUT / "rotation-method-demo.md", OUTPUT / "rotation-method-verification.json"]
    # The report is prepared after the agent modules settle and must exist before packaging.
    check("Final human-readable completeness report exists", (OUTPUT / "audit-kelengkapan-data-fieldshift.md").is_file())
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zipped:
        for path in sorted(set(package_paths)):
            zipped.write(path, path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as zipped:
        check("Version-two archive CRC and source snapshot integrity", zipped.testzip() is None)
        archive_files = len(zipped.infolist())
    archive_sha256 = sha(archive)
    archive.with_suffix(".zip.sha256").write_text(f"{archive_sha256}  {archive.name}\n", encoding="ascii")
    write(OUTPUT / "data-package-verification.json", {"verified_at_utc": datetime.now(timezone.utc).isoformat(),
          "archive": archive.relative_to(ROOT).as_posix(), "files": archive_files, "bytes": archive.stat().st_size,
          "crc_pass": True, "sha256": archive_sha256,
          "prepared_files_unchanged": len(original_manifest["files"]), "supplemental_files_hashed": len(manifest_entries)})
    print(json.dumps({"public_context_ready": True, "actual_farm_dataset_complete": False,
                      "prepared_unchanged_files": len(original_manifest["files"]), "supplemental_files": len(manifest_entries),
                      "archive": str(archive), "archive_bytes": archive.stat().st_size,
                      "archive_sha256": archive_sha256}, indent=2))


if __name__ == "__main__":
    main()
