"""Explicit synthetic calendar over the real historical public context."""
from copy import deepcopy


DEMO_REQUEST = {
    "location": {"example_id": "klaten_cropland_primary"},
    "input_kind": "scenario_assumption",
    "assumptions": [
        "Kalender sintetis untuk demonstrasi historis 2025, bukan riwayat petani.",
        "Padi ditanam langsung; umur padi 120, jagung 100, kedelai 90 hari sejak semai (hari nol).",
        "Tanggal mulai 1 Januari dan 1 Juni; jeda persiapan 14 hari merupakan asumsi.",
    ],
    "slot_inputs": [{"production_method": "direct_seeded", "sowing_date": start}
                    for start in ("2025-01-01", "2025-06-01")],
    "document": {
        "planning": {
            "horizon": {"start_date": "2025-01-01", "end_exclusive": "2026-01-01"},
            "allowed_crop_ids": ["padi", "jagung", "kedelai"],
            "excluded_crop_ids": [],
            "existing_sequence": [
                {"crop_id": "padi", "date_status": "scenario_assumption",
                 "establishment_method": "direct_seeded", "sowing_date": start}
                for start in ("2025-01-01", "2025-06-01")
            ],
            "slot_start_dates": ["2025-01-01", "2025-06-01"],
            "locked_prefix_length": 1,
            "continuation_confirmed": True,
            "duration_by_crop": [
                {"crop_id": crop, "minimum_days": days, "maximum_days": days,
                 "basis_event": "sowing", "counting_convention": "elapsed_day_zero",
                 "source_ref": "demo-assumed-duration-" + crop,
                 "normalization_policy": "no_rounding_needed"}
                for crop, days in (("padi", 120), ("jagung", 100), ("kedelai", 90))
            ],
            "preparation_gap_days": 14,
            "selected_priorities": [],
        },
        "context": {"time_mode": "historical_replay"},
    },
}


def demo_request():
    return deepcopy(DEMO_REQUEST)
