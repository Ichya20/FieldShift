"""Extract bounded FAO56 reference rows without computing local crop water use."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from html import unescape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/supplemental/crop-water"


def main():
    evidence = json.loads((DATA / "source-evidence.json").read_text(encoding="utf-8-sig"))
    documents = {}
    for source in evidence["sources"]:
        raw = (DATA / source["path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == source["sha256"]
        documents[source["id"]] = raw.decode("cp1252")
    table_rows = {}
    for source_id, html in documents.items():
        table_rows[source_id] = [re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]*>", " ", row))).strip()
                                 for row in re.findall(r"<tr\b[^>]*>.*?</tr>", html, re.I | re.S)]

    def exact_row(source_id, expected):
        assert expected in table_rows[source_id], (source_id, expected)
        return {"source_id": source_id, "row_text": expected}

    crops = [
        {"crop_id": "padi", "source_crop_label": "Rice",
         "kc_initial": 1.05, "kc_initial_basis": "crop-specific Table 12 row",
         "kc_mid": 1.20, "kc_end": {"min": 0.60, "max": 0.90, "source_order": "0.90-0.60"},
         "mean_maximum_crop_height_m": {"min": 1.0, "max": 1.0},
         "maximum_effective_root_depth_m": {"min": 0.5, "max": 1.0},
         "source_depletion_fraction": {"value": 0.20, "basis": "0.20 of saturation, Table 22 footnote 4; do not treat as ordinary upland p times TAW"},
         "evidence": [exact_row("fao56-table12", "Rice 1.05 1.20 0.90-0.60 1"),
                      exact_row("fao56-table22", "Rice 0.5-1.0 0.20 4")],
         "crop_specific_limits": ["Flooded rice water regime is not established by selecting the species.",
                                  "Paddy preparation, standing water, seepage and percolation need separate accounting."]},
        {"crop_id": "jagung", "source_crop_label": "Maize, Field (grain) (field corn)",
         "kc_initial": 0.3, "kc_initial_basis": "cereals group row; not a separately calibrated maize measurement",
         "kc_mid": 1.20, "kc_end": {"min": 0.35, "max": 0.60, "source_order": "0.60-0.35"},
         "mean_maximum_crop_height_m": {"min": 2.0, "max": 2.0},
         "maximum_effective_root_depth_m": {"min": 1.0, "max": 1.7},
         "source_depletion_fraction": {"value": 0.55, "basis": "p at crop ET about 5 mm/day, Table 22"},
         "evidence": [exact_row("fao56-table12", "i. Cereals 0.3 1.15 0.4"),
                      exact_row("fao56-table12", "Maize, Field (grain) (field corn) 1.20 0.60-0.35 11 2"),
                      exact_row("fao56-table22", "Maize, Field (grain) (field corn) 1.0-1.7 0.55")],
         "crop_specific_limits": ["Grain maize reference does not represent sweet corn.",
                                  "The two end coefficients reflect different harvest moisture/maturity conditions; no midpoint is selected."]},
        {"crop_id": "kedelai", "source_crop_label": "Soybeans",
         "kc_initial": 0.4, "kc_initial_basis": "legumes group row; not a separately calibrated soybean measurement",
         "kc_mid": 1.15, "kc_end": {"min": 0.50, "max": 0.50, "source_order": "0.50"},
         "mean_maximum_crop_height_m": {"min": 0.5, "max": 1.0},
         "maximum_effective_root_depth_m": {"min": 0.6, "max": 1.3},
         "source_depletion_fraction": {"value": 0.50, "basis": "p at crop ET about 5 mm/day, Table 22"},
         "evidence": [exact_row("fao56-table12", "e. Legumes (Leguminosae) 0.4 1.15 0.55"),
                      exact_row("fao56-table12", "Soybeans 1.15 0.50 0.5-1.0"),
                      exact_row("fao56-table22", "Soybeans 0.6-1.3 0.50")],
         "crop_specific_limits": ["Reference coefficients are not a local cultivar or nodulation model."]},
    ]
    flat8 = re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]*>", " ", documents["fao56-table22"])))
    assert "The value for p for rice is 0.20 of saturation." in flat8
    notes = {
        "status": "generic_published_reference_not_local_calibration",
        "source_tables": [12, 22], "coefficient_units": "dimensionless", "root_depth_units": "m",
        "table12_conditions": "Non-stressed, well-managed crops in subhumid climates, minimum RH about 45% and wind at 2 m about 2 m/s.",
        "initial_stage_caveat": "Initial Kc is strongly affected by wetting frequency and exposed wet soil; source group values are not automatic local defaults.",
        "later_stage_caveat": "Mid/end coefficients can require local humidity, wind, crop-height and management adjustment; harvest condition matters.",
        "root_depth_caveat": "Ranges are maximum effective rooting depths, not an observed root-depth trajectory. Restrict to actual soil/rootable profile when developing a validated model.",
        "depletion_caveat": "Table 22 depletion values depend on ET and crop/soil; the rice saturation footnote must remain separate.",
        "not_provided": ["Local growth-stage dates", "Actual soil-water initial conditions", "Effective rain/runoff",
                         "Paddy water control/losses", "Actual irrigation allocation/efficiency", "Local model validation"],
        "enabled_for_current_mvp_local_water_outputs": False,
        "local_etc_mm": None, "net_irrigation_mm": None, "water_savings_percent": None,
    }
    content = {"reference_notes": notes, "crops": crops}
    (DATA / "crop-water-reference.json").write_text(json.dumps(content, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    summary = {"prepared_at_utc": datetime.now(timezone.utc).isoformat(), "module": "crop-water",
               "crops": [c["crop_id"] for c in crops], "source_tables": [12, 22],
               "what_filled": ["Published stage coefficients with initial-group provenance", "Maximum effective root-depth ranges",
                               "ET-dependent depletion references including the special rice saturation footnote"],
               "remaining_gaps": notes["not_provided"], "local_irrigation_ready": False,
               "validation": {"pass": True, "exact_source_rows_checked": sum(len(c["evidence"]) for c in crops),
                              "source_hashes": len(evidence["sources"]), "rice_special_footnote_checked": True}}
    (DATA / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (DATA / "README.md").write_text(
        "# Referensi air tanaman untuk pengembangan berikutnya\n\n"
        "FAO56 Tabel 12 dan 22 menyediakan referensi generik koefisien tanaman, kedalaman akar maksimum dan fraksi deplesi "
        "untuk padi, jagung biji dan kedelai. Setiap nilai ditautkan ke baris sumber. Nilai awal jagung/kedelai berasal dari "
        "baris kelompok tanaman; bukan hasil kalibrasi lokal. Footnote padi memakai 0,20 dari kondisi jenuh dan tidak "
        "disamakan dengan deplesi tanaman upland. Rentang dipertahankan.\n\n"
        "Paket ini belum mengaktifkan perhitungan ET tanaman atau irigasi dalam MVP. Tanggal fase, kondisi awal air tanah, "
        "hujan efektif, pengelolaan padi, alokasi air dan validasi lokal tetap diperlukan. Sumber primer: "
        "[FAO56 Bab 6](https://www.fao.org/4/x0490e/x0490e0b.htm) dan "
        "[Bab 8](https://www.fao.org/4/x0490e/x0490e0e.htm).\n\n"
        "Unduh/katalog: `pwsh -File scripts/data/supplemental_regional/fetch_crop_water.ps1`. "
        "Validasi/olah: `py -3.11 scripts/data/supplemental_regional/prepare_crop_water.py`.\n", encoding="utf-8")
    print(json.dumps(summary["validation"], indent=2))


if __name__ == "__main__":
    main()
