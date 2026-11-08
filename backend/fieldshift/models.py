"""Small HTTP transport models; domain inputs use the audited JSON Schema."""
from __future__ import annotations

from datetime import date
import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

TimeMode = Literal["historical_replay", "historical_analogue_not_forecast", "recent_partial"]
ExampleId = Literal["klaten_cropland_primary", "klaten_cropland_candidate"]


class TransportModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class Location(TransportModel):
    example_id: ExampleId | None = None
    longitude: float | None = Field(default=None, ge=-180, le=180)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    climate_context_id: Literal["power_regional_yogyakarta"] | None = None

    @model_validator(mode="after")
    def paired_coordinates(self):
        if (self.longitude is None) != (self.latitude is None):
            raise ValueError("Bujur dan lintang harus diisi bersama.")
        if self.example_id is None and self.longitude is None:
            raise ValueError("Pilih lokasi contoh atau isi koordinat.")
        return self


def parse_date(value: str) -> date:
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value or not 1900 <= parsed.year <= 2100:
        raise ValueError("Tanggal harus YYYY-MM-DD dalam rentang 1900–2100.")
    return parsed


class Window(TransportModel):
    start_date: str
    end_exclusive: str

    @model_validator(mode="after")
    def valid_range(self):
        start, end = parse_date(self.start_date), parse_date(self.end_exclusive)
        if not 0 < (end - start).days <= 3660:
            raise ValueError("Periode harus berurutan dan paling panjang 3.660 hari.")
        return self


class ContextRequest(TransportModel):
    location: Location
    window: Window | None = None
    time_mode: TimeMode = "historical_replay"


class SlotInput(TransportModel):
    production_method: Literal["direct_seeded", "transplanted"] | None = None
    sowing_date: str | None = None
    transplanting_date: str | None = None
    nursery_off_main_field: bool | None = None

    @model_validator(mode="after")
    def dates(self):
        for value in (self.sowing_date, self.transplanting_date):
            if value is not None:
                parse_date(value)
        return self


class CompareRequest(TransportModel):
    location: Location
    document: dict = Field(default_factory=dict)
    input_kind: Literal["scenario_assumption", "user_reported"]
    assumptions: list[str] = Field(default_factory=list, max_length=30)
    slot_inputs: list[SlotInput] | None = Field(default=None, max_length=3)

    @model_validator(mode="after")
    def declared_assumptions(self):
        if any(not value.strip() or len(value) > 1000 for value in self.assumptions):
            raise ValueError("Asumsi harus berupa teks terisi, paling panjang 1.000 karakter.")
        if self.input_kind == "scenario_assumption" and not self.assumptions:
            raise ValueError("Skenario asumsi harus menyebutkan asumsi yang digunakan.")
        return self


def finite_json(value, depth=0):
    if depth > 30:
        raise ValueError("Struktur input terlalu dalam.")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("NaN dan Infinity tidak dapat digunakan sebagai data.")
    if isinstance(value, dict):
        for child in value.values():
            finite_json(child, depth + 1)
    elif isinstance(value, list):
        if len(value) > 1000:
            raise ValueError("Daftar input melebihi batas 1.000 catatan.")
        for child in value:
            finite_json(child, depth + 1)
