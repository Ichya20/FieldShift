"""Exercise the stage-2 method with real source data and labelled scenario inputs.

This is a reference calculation, not an application service or farm advice.
Run from repository root: py -3.11 scripts/method/build_rotation_demo.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

from climate_reference import historical_analogue, load_daily, modis_window, window_summary
from rotation_reference import calendar_cycle, check_transition, generate_candidates

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/prepared"
OUTPUT = ROOT / "outputs"


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def verify_prepared_sources():
    manifest = load(DATA / "file-manifest.json")
    for entry in manifest["files"]:
        path = ROOT / entry["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"], entry["path"]
    return {"manifest": "data/prepared/file-manifest.json", "sha256_files_verified": len(manifest["files"]),
            "all_match_preparation_manifest": True}


def soil_ph_at_point(longitude, latitude):
    west, south, east, north = load(DATA / "soil-terrain/summary.json")["bbox_soil_terrain_wgs84"]
    if not west <= longitude < east or not south < latitude <= north:
        return {"status": "outside_coverage", "value": None}
    # The extraction has 9 columns and 8 rows; derive the containing cell,
    # never the nearest centre. This is a small-grid reference, not a GIS API.
    col = math.floor((longitude - west) / ((east - west) / 9))
    row = math.floor((north - latitude) / ((north - south) / 8))
    with (DATA / "soil-terrain/processed/soil-cells.csv").open(newline="", encoding="utf-8") as stream:
        selected = [r for r in csv.DictReader(stream) if r["property"] == "phh2o"
                    and r["depth"] == "0-5cm" and int(r["row"]) == row and int(r["col"]) == col]
    values = {r["statistic"]: float(r["value"]) if r["qa_status"] == "usable_prediction" and r["value"] else None for r in selected}
    return {"status": "evidence_available" if values.get("mean") is not None else "needs_input",
            "origin": "SoilGrids_prediction_not_laboratory", "depth": "0-5cm", "row": row, "column": col,
            "value": values.get("mean"), "q05": values.get("Q0.05"), "q95": values.get("Q0.95"),
            "unit": "pH", "source": "data/prepared/soil-terrain/processed/soil-cells.csv"}


def gaez_at_point(longitude, latitude):
    rows = []
    for record in load(DATA / "agronomy/gaez-baseline-point.json")["rows"]:
        b = record["pixel_bounds"]
        if b["west"] <= longitude < b["east"] and b["south"] < latitude <= b["north"]:
            rows.append({"layer_code": record["layer_code"], "raw_class": record["raw_value"],
                         "class_label": record["class_label"], "bounds": b, "source_url": record["url"]})
    return {"status": "historical_reference_only", "rows": rows, "period": "2001-2020",
            "management_regime_selected": None,
            "note": "Regimes remain separate; RCW represents wetland rice, which is not confirmed for this scenario. No suitability score is inferred."}


def relationship(value, low, high):
    if value is None:
        return "unknown"
    return "within_reference_optimum" if low <= value <= high else "outside_reference_optimum_requires_review"


def finding(rule_id, status, explanation, inputs_used, source_refs, missing_inputs=None, next_action=None):
    return {"rule_id": rule_id, "status": status, "scope": "labelled_synthetic_scenario_at_example_location",
            "inputs_used": inputs_used, "source_refs": source_refs,
            "assumptions": ["Calendar and farming inputs are fixture assumptions; environmental values are source data."],
            "explanation": explanation, "missing_inputs": missing_inputs or [], "next_action": next_action}


def build_report():
    integrity = verify_prepared_sources()
    spec = load(ROOT / "specs/rotation-method-v1.json")
    fixture = load(ROOT / "specs/fixtures/rotation-demo.json")
    crops = {c["crop_id"]: c for c in load(DATA / "agronomy/crop-reference.json")["crops"]}
    daily = load_daily(DATA / "climate/daily.csv")
    generated = generate_candidates(fixture)
    assert generated["generation_status"] == "complete", generated
    assert generated["strategies"] == {"existing": ["padi", "padi"],
        "candidate_1": ["padi", "jagung"], "candidate_2": ["padi", "kedelai"]}, generated
    horizon = fixture["horizon"]
    point = fixture["coordinate"]
    ph = soil_ph_at_point(point["longitude"], point["latitude"])
    context = {"location_id": fixture["location_id"], "coordinate": point,
        "is_verified_farm": False, "climate_context_id": fixture["climate_context_id"],
        "climate_context_role": fixture["climate_context_role"],
        "soil_ph_0_5cm": ph, "gaez": gaez_at_point(point["longitude"], point["latitude"]),
        "whole_horizon_environment": window_summary(daily, horizon["start_date"], horizon["end_exclusive"]),
        "whole_horizon_historical_analogue": historical_analogue(daily, horizon["start_date"], horizon["end_exclusive"]),
        "vegetation_context": modis_window(DATA / "vegetation/modis_16day_qa.csv", fixture["location_id"],
                                           horizon["start_date"], horizon["end_exclusive"])}
    strategies = []
    for strategy_id, sequence in generated["strategies"].items():
        cycles, findings = [], []
        for i, crop_id in enumerate(sequence):
            plan = {"crop_id": crop_id, "production_method": fixture["production_method_assumption"],
                "sowing_date": fixture["slot_start_dates"][i], "transplanting_date": None,
                "duration": fixture["duration_assumptions"][crop_id], "nursery_off_main_field": None}
            calendar = calendar_cycle(plan)
            assert calendar["status"] == "calendar_computed", calendar
            start = max(calendar["field_start"], horizon["start_date"])
            end = min(calendar["latest_release_date"], horizon["end_exclusive"])
            assert start < end, "An ongoing crop must have actual occupation overlap; do not fabricate it."
            # Fixture durations are exact. General uncertain-duration summaries
            # must keep separate endpoint windows, as specified by the method.
            assert calendar["earliest_release_date"] == calendar["latest_release_date"]
            environment = window_summary(daily, start, end)
            crop = crops[crop_id]
            temp = crop["species_temperature_optimum_c"]
            optimum = crop["species_soil_ph_optimum"]
            cycle = {"crop_id": crop_id, "calendar_inputs": plan, "calendar": calendar,
                "environment_window": environment,
                "temperature_reference": {"optimum_c": [temp["min"], temp["max"]],
                    "mean_relation": relationship(environment["temperature_mean_c"], temp["min"], temp["max"]),
                    "note": "Historical species optimum, not a Tmax stress threshold or yield model"},
                "ph_reference": {"optimum": [optimum["min"], optimum["max"]],
                    "mean_relation": relationship(ph["value"], optimum["min"], optimum["max"]),
                    "prediction_interval_extends_beyond_optimum": (ph["q05"] < optimum["min"] or ph["q95"] > optimum["max"])
                        if ph["q05"] is not None and ph["q95"] is not None else None},
                "seasonal_et_reference": crop["seasonal_crop_water_need_indicative_mm"]}
            cycles.append(cycle)
            findings.append(finding("climate_exposure", "evidence_available",
                "Paparan historis regional pada jendela kalender yang diisi; bukan konsumsi atau kebutuhan irigasi tanaman.",
                {"crop_id": crop_id, "window": [start, end], "climate_context_id": fixture["climate_context_id"]},
                ["nasa-power", "fao56", "climate-manifest"]))
            findings.append(finding("ph_reference", "review_required",
                "Mean prediksi pH berada dalam optimum referensi, tetapi kuantil prediksi melintasi batasnya. Kedalaman 0–5 cm dan peta model tidak membuktikan kondisi seluruh zona akar.",
                {"crop_id": crop_id, "soil": ph, "reference": [optimum["min"], optimum["max"]]},
                [optimum["source_id"], "soil-manifest"], ["soil_lab_or_local_review"], "Tinjau metode/kedalaman dan hasil uji tanah bila tersedia."))
            findings.append(finding("temperature_reference", "evidence_available",
                "Rerata T2M historis dibandingkan dengan optimum spesies; bukan ambang stres, kegagalan atau kehilangan hasil.",
                {"crop_id": crop_id, "mean_temperature_c": environment["temperature_mean_c"],
                 "reference": [temp["min"], temp["max"]]}, [temp["source_id"], "nasa-power"]))
            findings.append(finding("seasonal_et_reference", "evidence_available",
                "Rentang ET seluruh musim adalah referensi umum. Tidak diskalakan menjadi konsumsi lokal, kebutuhan irigasi atau ranking hemat air.",
                {"crop_id": crop_id, "reference": cycle["seasonal_et_reference"]}, ["fao-seasonal-water"]))
        transitions = [check_transition(cycles[i-1]["calendar"], cycles[i]["calendar"], fixture["preparation_gap_days"])
                       for i in range(1, len(cycles))]
        findings.append(finding("calendar", "evidence_available",
            "Tidak ditemukan konflik pada kalender asumsi yang diisi; hasil ini bukan sertifikat kelayakan agronomi.",
            {"transitions": transitions, "preparation_gap_days": fixture["preparation_gap_days"]}, ["method-calendar-policy"]))
        if any(a == "padi" and b in {"jagung", "kedelai"} for a, b in zip(sequence, sequence[1:])):
            findings.append(finding("paddy_upland_transition", "needs_input",
                "Rezim air padi belum diketahui. Tanam langsung tidak membuktikan sawah tergenang; relevansi transisi ke upland perlu ditinjau.",
                {"sequence": sequence, "rice_water_regime": fixture["rice_water_regime"]},
                ["fao-paddy-irrigation", "fao-aquacrop-inputs"],
                ["rice_water_regime", "drainage", "water_control", "soil_management"], "Lengkapi sistem air dan tinjau pengelolaan bersama penyuluh."))
        else:
            findings.append(finding("paddy_upland_transition", "not_applicable",
                "Urutan ini tidak memuat transisi padi ke jagung/kedelai. Rezim air padi sendiri tetap belum diketahui.",
                {"sequence": sequence, "rice_water_regime": fixture["rice_water_regime"]},
                ["fao-paddy-irrigation", "fao-aquacrop-inputs"]))
        if "kedelai" in sequence:
            findings.append(finding("legume_mechanism", "needs_input",
                "Kedelai memberi alasan meninjau potensi fiksasi nitrogen; besar kredit N/penghematan pupuk belum dapat dihitung.",
                {"sequence": sequence}, ["fao-crop-rotation"],
                ["nodulation", "inoculation", "residue_fate", "nutrient_balance"], "Periksa kondisi nodulasi, residu dan neraca hara lokal."))
        else:
            findings.append(finding("legume_mechanism", "not_applicable",
                "Urutan tidak memuat kedelai; kredit nitrogen tidak dihitung.",
                {"sequence": sequence}, ["fao-crop-rotation"]))
        findings.append(finding("pest_break", "needs_input",
            "Urutan tanaman saja belum membuktikan pemutusan hama/penyakit.", {"sequence": sequence},
            ["fao-crop-rotation"], ["local_pest_or_pathogen", "host_range", "management_history"], "Identifikasi masalah dan tanaman inangnya."))
        findings.append(finding("coverage", "review_required",
            "Titik contoh belum merupakan lahan terverifikasi; POWER memakai konteks regional eksplisit dan layer lain memakai dukungan yang diekstrak.",
            {"location_id": fixture["location_id"], "coordinate": point, "climate_context_id": fixture["climate_context_id"],
             "is_verified_farm": False}, ["analysis-profile"], ["verified_farm_geometry"], "Verifikasi batas dan lokasi lahan sebelum analisis petani."))
        findings.append(finding("vegetation_context", "review_required",
            "Ringkasan MODIS memakai observasi strict-good dan mempertahankan gap; piksel campuran tidak mengidentifikasi tanaman atau tanggal tanam.",
            context["vegetation_context"], ["modis-manifest"], ["field_observations"], "Gunakan hanya sebagai konteks historis piksel."))
        findings.append(finding("gaez_context", "review_required",
            "Kategori model historis disajikan terpisah menurut rezim. Belum ada rezim yang dipilih dan RCW hanya merepresentasikan wetland rice.",
            context["gaez"], ["gaez-six-legend", "gaez-user-guide"], ["rice_water_regime", "management_regime"], "Tinjau kecocokan definisi tanaman dan pengelolaan."))
        findings.append(finding("economics", "needs_input",
            "Perbandingan ekonomi belum termasuk MVP dan tidak dihitung dari referensi tanaman atau citra satelit.",
            {"crop_yield": fixture["crop_yield"], "farm_prices": fixture["farm_prices"], "costs": fixture["costs"]},
            ["method-accounting-boundary"], ["marketable_yield", "farm_gate_price", "costs", "units", "time_and_location_basis"],
            "Tetap kosong; metode ekonomi memerlukan perluasan cakupan dan data lokal."))
        strategies.append({"strategy_id": strategy_id, "sequence": sequence,
            "calendar_source": "explicit_synthetic_fixture", "cycles": cycles,
            "transitions": transitions, "findings": findings,
            "whole_horizon_environment": window_summary(daily, horizon["start_date"], horizon["end_exclusive"]),
            "analysis_status": "partial", "local_agronomic_validation": False,
            **{name: None for name in spec["unavailable_outputs"]}})
    assert all(s["whole_horizon_environment"] == context["whole_horizon_environment"] for s in strategies)
    assert len({tuple(s["sequence"]) for s in strategies}) == 3
    assert all(t["status"] == "no_calendar_conflict" for s in strategies for t in s["transitions"])
    rule_ids = {r["id"] for r in spec["rules"]}
    source_ids = {s["id"] for s in load(DATA / "agronomy/source-evidence.json")["sources"]}
    source_ids.update(spec["additional_source_refs"])
    for strategy in strategies:
        assert {result["rule_id"] for result in strategy["findings"]} == rule_ids
        for result in strategy["findings"]:
            assert result["rule_id"] in rule_ids
            assert result["status"] in spec["check_statuses"]
            assert set(result["source_refs"]) <= source_ids
            assert all(field in result for field in spec["finding_fields"])
    numerical_checks = [window_summary(daily, f"{year}-05-01", f"{year}-09-01") for year in [2023,2025]]
    numerical_checks.append(window_summary(daily, "2026-11-01", "2026-11-06"))
    report = {"method_id": spec["method_id"], "method_version": spec["method_version"],
        "is_synthetic_scenario": True, "is_verified_farm": False, "application_implemented": False,
        "fixture_path": "specs/fixtures/rotation-demo.json", "assumptions": fixture["assumptions"],
        "generation": generated, "comparison_context": context, "strategies": strategies,
        "numerical_examples": numerical_checks,
        "checks_passed": ["three_filled_distinct_strategies", "same_horizon_and_context", "calendar_no_conflict_for_explicit_fixture",
            "whole_horizon_environment_invariant", "finding_rule_status_and_sources_resolve", "prepared_sources_match_sha256"],
        "source_integrity": verify_prepared_sources()}
    assert report["source_integrity"] == integrity
    return report


def write_report(report):
    generated = report["generation"]
    context = report["comparison_context"]
    strategies = report["strategies"]
    integrity = report["source_integrity"]
    ph = context["soil_ph_0_5cm"]
    OUTPUT.mkdir(exist_ok=True)
    (OUTPUT / "rotation-method-demo.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    def number(value):
        return "belum tersedia" if value is None else f"{value:.4f}".rstrip("0").rstrip(".").replace(".", ",")
    lines = []
    for strategy in strategies:
        second = strategy["cycles"][1]
        env = second["environment_window"]
        lines.append(f"| {strategy['strategy_id']} | {' → '.join(strategy['sequence'])} | {second['calendar']['latest_harvest_date']} | {env['days_expected']} | {number(env['rainfall_total_mm'])} | {number(env['reference_eto_total_mm'])} | {number(env['rain_minus_reference_eto_total_mm'])} |")
    whole = context["whole_horizon_environment"]
    text = f"""# Latihan metode rotasi FieldShift

Versi {report['method_version']} · 8 November 2026. **Seluruh informasi petani, urutan dan kalender di contoh ini adalah asumsi sintetis.** Lingkungan menggunakan data nyata yang sudah disiapkan. Ini replay historis 2025, bukan prediksi atau rekomendasi lahan.

## Tiga strategi terisi

Horizon bersama 1 Januari 2025–1 Januari 2026 (akhir eksklusif). Semai pertama 1 Januari dan kedua 1 Juni; tanam langsung, durasi elapsed 120/100/90 hari untuk padi/jagung/kedelai dan jeda 14 hari merupakan asumsi latihan. Hari panen masih menempati petak. Semua strategi lolos pemeriksaan konflik kalender untuk isian tersebut; status agronomi tetap parsial.

Tabel berikut menunjukkan **paparan lingkungan pada okupansi tanaman kedua**, bukan kebutuhan air tanaman:

| Strategi | Urutan | Panen kedua (asumsi) | Hari okupansi | Hujan (mm) | ETo referensi (mm) | P−ETo (mm) |
|---|---|---|---:|---:|---:|---:|
{chr(10).join(lines)}

Konteks POWER adalah regional, bukan pengukuran cuaca pada piksel Klaten. Selisih pada jendela tanaman di atas berasal dari panjang okupansi yang diasumsikan, bukan bukti tanaman lebih hemat air.

**Sepanjang horizon 365 hari yang sama, ketiganya identik:** hujan {number(whole['rainfall_total_mm'])} mm; ETo {number(whole['reference_eto_total_mm'])} mm; P−ETo {number(whole['rain_minus_reference_eto_total_mm'])} mm. Hari jeda tidak dihapus dari horizon.

## Bukti dan informasi yang kurang

- Sel SoilGrids yang memuat titik primary adalah row {ph['row']}, col {ph['column']}; prediksi pH kedalaman 0–5 cm mean {number(ph['value'])}, q05 {number(ph['q05'])}, q95 {number(ph['q95'])}. Mean berada dalam referensi ketiga tanaman, tetapi rentang prediksi melewati batas optimum. Ini bukan bukti kesesuaian zona akar atau uji laboratorium.
- Rezim air padi, drainase, kontrol air dan pengelolaan belum diketahui. Tanam langsung tidak menetapkan sawah tergenang atau gogo.
- Potensi mekanisme legum dan pergantian tanaman perlu bukti nodulasi, residu, neraca hara, organisme hama dan host range lokal.
- GAEZ tetap kategori model historis dengan rezim terpisah. MODIS tetap konteks vegetasi piksel campuran dengan QA/gap; bukan identifikasi tanaman.
- Ranking, skor, hasil, keuntungan, kredit N dan penghematan/kebutuhan irigasi tetap kosong.

Analog historis disimpan terpisah, bukan forecast. Horizon 365 hari ini memiliki 22 tahun referensi lengkap karena kebijakan tidak menambah/menghapus 29 Februari. Daftar tahun dan alasan yang dilewati ada di JSON. Perbandingan selisih antarjendela harus memakai kohort berpasangan yang sama.

## Pemeriksaan

Tiga strategi berbeda, horizon sama, konflik kalender, invariansi lingkungan dan resolusi sumber temuan diperiksa. Seluruh {integrity['sha256_files_verified']} berkas data prepared tetap cocok dengan manifest SHA-256; template petani sumber tetap kosong.

Reproduksi: `py -3.11 scripts/method/build_rotation_demo.py`. Hasil lengkap: [rotation-method-demo.json](rotation-method-demo.json). Metode: [rotation-method.md](../docs/rotation-method.md). Fixture: [rotation-demo.json](../specs/fixtures/rotation-demo.json).
"""
    (OUTPUT / "rotation-method-demo.md").write_text(text, encoding="utf-8")


def main():
    report = build_report()
    write_report(report)
    print(json.dumps({"strategies": report["generation"]["strategies"],
        "whole_horizon": report["comparison_context"]["whole_horizon_environment"],
        "source_integrity": report["source_integrity"], "analysis_status": "partial_not_locally_validated",
        "report": "outputs/rotation-method-demo.md"}, indent=2))


if __name__ == "__main__":
    main()
