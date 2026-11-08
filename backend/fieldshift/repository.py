"""Read-only access to the frozen public evidence package.

Spatial queries use containing source support. They never choose a nearest
sample or turn an unverified example into a farmer observation.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import csv
from datetime import date, timedelta
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path

import rasterio
from rasterio.transform import rowcol
from rasterio.warp import transform as project

from scripts.method.climate_reference import historical_analogue, load_daily, window_summary


class DataUnavailableError(Exception):
    """A required local evidence file is missing, corrupt, or inconsistent."""


TIME_MODES = {"historical_replay", "recent_partial", "historical_analogue_not_forecast"}
CLIMATE_ID = "power_regional_yogyakarta"
SINUSOIDAL = "+proj=sinu +R=6371007.181 +nadgrids=@null +wktext"


def _number(value):
    if value in (None, ""):
        return None
    parsed = float(value)
    return parsed if math.isfinite(parsed) else None


def _contains(lon, lat, bounds):
    """Raster convention: west/north included, east/south excluded."""
    return bounds["west"] <= lon < bounds["east"] and bounds["south"] < lat <= bounds["north"]


class DataRepository:
    def __init__(self, root: Path | None = None):
        self.root = (root or Path(__file__).resolve().parents[2]).resolve()
        self._manifests = {}
        for name in ("data/prepared/file-manifest.json", "data/supplemental/file-manifest.json"):
            manifest = self._json(name)
            if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list) or not manifest["files"]:
                raise DataUnavailableError(f"Invalid evidence manifest: {name}")
            for entry in manifest["files"]:
                if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or not isinstance(entry.get("sha256"), str) or len(entry["sha256"]) != 64:
                    raise DataUnavailableError(f"Invalid evidence manifest entry: {name}")
                path = self._path(entry["path"])
                if not path.is_file() or self._sha(path) != entry["sha256"].lower():
                    raise DataUnavailableError(f"Evidence checksum failed: {entry['path']}")
            self._manifests[name] = {"sha256": self._sha(self._path(name)), "files": len(manifest["files"])}
        self.method = self._json("specs/rotation-method-v1.json")
        self.crops = self._json("data/prepared/agronomy/crop-reference.json")["crops"]
        public_refs = self._json("data/supplemental/agronomy/agronomy-reference-supplement.json")["public_references"]
        for crop in self.crops:
            crop["supplemental_public_references"] = [ref for ref in public_refs if ref.get("fact", {}).get("crop_id") == crop["crop_id"]]
        try:
            self.daily = load_daily(self._path("data/prepared/climate/daily.csv"))
        except (OSError, ValueError) as exc:
            raise DataUnavailableError("Invalid prepared daily climate") from exc
        self._features = self._json("data/prepared/locations.geojson")["features"]
        self._examples = {f["properties"]["id"]: f for f in self._features if f["properties"]["id"].startswith("klaten_cropland_")}
        self._soil = self._json("data/supplemental/soil-terrain/grid-catalog.json")
        self._soil_summary = self._json("data/supplemental/soil-terrain/summary.json")
        if self._soil_summary["validation"]["pass"] is not True:
            raise DataUnavailableError("Native soil evidence has not passed validation")
        self._terrain = self._json("data/prepared/soil-terrain/summary.json")["terrain"]
        self._gaez = self._json("data/prepared/agronomy/gaez-baseline-point.json")
        self._landcover = {
            "klaten_cropland_primary": self._json("data/prepared/soil-terrain/modis-primary-footprint-landcover-summary.json"),
            "klaten_cropland_candidate": self._json("data/prepared/soil-terrain/modis-footprint-landcover-summary.json"),
        }
        self._footprints = {}
        for row in self._json("data/supplemental/environment/footprint-comparison.json")["records"]:
            key = (row["product"], row["point_id"])
            grid = {k: float(row[k]) for k in ("xllcorner", "yllcorner", "cellsize", "nrows", "ncols")}
            if key in self._footprints and self._footprints[key] != grid:
                raise DataUnavailableError(f"Inconsistent product footprint: {key}")
            self._footprints[key] = grid
        self._vegetation = defaultdict(list)
        seen = set()
        for name, product, platform in (
            ("data/prepared/vegetation/modis_16day_qa.csv", "MOD13Q1", "Terra"),
            ("data/supplemental/environment/MOD13Q1-supplemental-qa.csv", "MOD13Q1", "Terra"),
            ("data/supplemental/environment/MYD13Q1-supplemental-qa.csv", "MYD13Q1", "Aqua"),
        ):
            for raw in self._csv(name):
                row = dict(raw, product=product, platform=platform)
                key = (product, row["point_id"], row["modis_date"])
                if key in seen:
                    raise DataUnavailableError(f"Duplicate vegetation observation: {key}")
                seen.add(key)
                for field in ("ndvi", "evi", "ndvi_raw", "evi_raw", "pixel_reliability", "vi_quality_raw", "modland_qa", "vi_usefulness", "aerosol_quantity", "adjacent_cloud", "mixed_cloud", "possible_shadow", "possible_snow_ice"):
                    if field in row:
                        row[field] = _number(row[field])
                row["source_file"] = (Path(name).parent / row["source_file"]).as_posix()
                self._vegetation[(product, row["point_id"])].append(row)
        for rows in self._vegetation.values():
            rows.sort(key=lambda row: row["modis_date"])
        self._source_catalog = self._build_sources()

    def _path(self, name: str) -> Path:
        path = (self.root / name).resolve()
        if not path.is_relative_to(self.root):
            raise DataUnavailableError("Evidence path escapes project root")
        return path

    @staticmethod
    def _sha(path: Path) -> str:
        try:
            with path.open("rb") as stream:
                return hashlib.file_digest(stream, "sha256").hexdigest()
        except OSError as exc:
            raise DataUnavailableError("Required evidence file cannot be read") from exc

    def _json(self, name):
        try:
            return json.loads(self._path(name).read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise DataUnavailableError(f"Required JSON evidence unavailable: {name}") from exc

    def _csv(self, name):
        try:
            with self._path(name).open(encoding="utf-8-sig", newline="") as stream:
                return list(csv.DictReader(stream))
        except OSError as exc:
            raise DataUnavailableError(f"Required CSV evidence unavailable: {name}") from exc

    def locations(self) -> list[dict]:
        return [self._resolve({"example_id": example}) for example in self._examples]

    def resolve_location(self, location: dict) -> dict:
        """Resolve the declared example or explicit coordinate without data fusion."""
        return self._resolve(location)

    def _resolve(self, location: dict) -> dict:
        example = location.get("example_id")
        lon, lat = location.get("longitude"), location.get("latitude")
        if (lon is None) != (lat is None):
            raise ValueError("longitude and latitude must be supplied together")
        if example is not None:
            if example not in self._examples:
                raise ValueError("Unknown example_id")
            feature = self._examples[example]
            x, y = feature["geometry"]["coordinates"]
            if lon is not None and (float(lon) != x or float(lat) != y):
                raise ValueError("Example and supplied coordinates contradict each other")
            lon, lat = x, y
        if lon is not None:
            if isinstance(lon, bool) or isinstance(lat, bool) or not math.isfinite(float(lon)) or not math.isfinite(float(lat)) or not -180 <= float(lon) <= 180 or not -90 <= float(lat) <= 90:
                raise ValueError("Coordinates must be finite longitude/latitude")
            lon, lat = float(lon), float(lat)
        climate_id = location.get("climate_context_id")
        if climate_id is None and example:
            climate_id = CLIMATE_ID
        if climate_id not in (None, CLIMATE_ID):
            raise ValueError("Unknown climate_context_id")
        return {"id": example or ("custom_coordinate" if lon is not None else None),
                "example_id": example, "coordinate": {"longitude": lon, "latitude": lat},
                "is_verified_farm": False, "climate_context_id": climate_id,
                "climate_context_assignment": "declared_example_regional_context" if example else "explicit_user_context" if climate_id else None,
                "role": self._examples[example]["properties"]["role"] if example else "unverified_query"}

    def _build_sources(self):
        result = deepcopy(self.method["additional_source_refs"])
        for package in ("data/prepared/agronomy", "data/supplemental/agronomy", "data/supplemental/crop-water", "data/supplemental/regional-context"):
            for source in self._json(package + "/source-evidence.json")["sources"]:
                row = deepcopy(source)
                if row.get("path") and not row["path"].startswith("data/"):
                    row["path"] = (Path(package) / row["path"]).as_posix()
                result[row["id"]] = row
        known = {
            "soilgrids-native": ("data/supplemental/soil-terrain/native-source-manifest.json", "Original ISRIC native 250m model predictions with explicit nodata"),
            "copernicus-dem": ("data/prepared/soil-terrain/manifest.json", "Copernicus DEM GLO-30 DSM and derived slope"),
            "modis-terra": ("data/prepared/vegetation/manifest.json", "Terra MOD13Q1; collection version unverified in REST subset"),
            "modis-aqua": ("data/supplemental/environment/manifest.json", "Aqua MYD13Q1; collection version unverified in REST subset"),
            "modis-supplement": ("data/supplemental/environment/manifest.json", "Terra 2026 and Aqua 2021-2026 source snapshots"),
            "esa-worldcover-2021": ("data/prepared/soil-terrain/manifest.json", "ESA WorldCover 2021 v200 historical land cover"),
            "gaez-v5": ("data/prepared/agronomy/gaez-baseline-point.json", "GAEZ V5 2001-2020 categorical historical baseline"),
        }
        for key, (path, description) in known.items():
            result[key] = {"path": path, "description": description, "sha256": self._sha(self._path(path))}
        # Preserve the provider reference while adding its actual local snapshot.
        result["nasa-power"].update({"manifest_path": "data/prepared/climate/manifest.json", "daily_path": "data/prepared/climate/daily.csv", "daily_sha256": self._sha(self._path("data/prepared/climate/daily.csv"))})
        for source in result.values():
            path = source.get("path")
            if path and self._path(path).is_file():
                source.setdefault("sha256", self._sha(self._path(path)))
        return result

    def sources(self) -> dict:
        return deepcopy(self._source_catalog)

    def catalog(self) -> dict:
        return {"project": "FieldShift", "data_status": "public_example_evidence_not_verified_farm", "time_modes": sorted(TIME_MODES),
                "examples": self.locations(), "critical_manifests": deepcopy(self._manifests),
                "layers": {"climate": {"context_id": CLIMATE_ID, "available_start": min(self.daily), "available_end_inclusive": max(self.daily), "source_refs": ["nasa-power", "fao56"]},
                           "soil": {"native_layers": len(self._soil["native_soil_layers"]), "grid_resolution_m": 250, "source_refs": ["soilgrids-native"]},
                           "terrain": {"source_product": self._terrain["source_product"], "source_refs": ["copernicus-dem"]},
                           "vegetation": {"products": ["MOD13Q1", "MYD13Q1"], "interpolated": False, "source_refs": ["modis-terra", "modis-aqua", "modis-supplement"]},
                           "gaez": {"period": self._gaez["period"], "source_refs": ["gaez-v5"]},
                           "landcover": {"epoch": 2021, "source_refs": ["esa-worldcover-2021"]}},
                "missing_farm_inputs": self._json("data/prepared/analysis-profile.json")["farm_specific_outputs_require"],
                "forecast_policy": "Forecast snapshots are separate; historical context never substitutes a forecast."}

    @staticmethod
    def _window(window):
        if window is None:
            return None
        start, end = window["start_date"], window["end_exclusive"]
        first, last = date.fromisoformat(start), date.fromisoformat(end)
        if first.isoformat() != start or last.isoformat() != end or first >= last:
            raise ValueError("Window must be canonical ISO dates with end_exclusive after start_date")
        return {"start_date": start, "end_exclusive": end}

    def climate_window(self, location: dict, start: str, end_exclusive: str, time_mode: str) -> dict:
        return self._climate(self._resolve(location), self._window({"start_date": start, "end_exclusive": end_exclusive}), time_mode)

    def _climate(self, location, window, time_mode):
        if time_mode not in TIME_MODES:
            raise ValueError("Unsupported time_mode")
        support = {"context_id": location["climate_context_id"], "coordinate": {"longitude": 110.37, "latitude": -7.8},
                   "spatial_support": "Regional POWER meteorological grid spanning tens of kilometres; not field weather", "time_standard": "LST", "available_start": min(self.daily), "available_end_inclusive": max(self.daily), "assignment": location["climate_context_assignment"]}
        result = {"status": "needs_input" if not location["climate_context_id"] else "evidence_available", "summary": None,
                  "source_refs": ["nasa-power", "fao56", "climate-manifest"], "support": support, "time_mode": time_mode, "warnings": []}
        if not location["climate_context_id"]:
            result["missing_inputs"] = ["location.climate_context_id"]
            return result
        if window is None:
            return result
        if time_mode == "historical_analogue_not_forecast":
            result["summary"] = historical_analogue(self.daily, window["start_date"], window["end_exclusive"])
            if any(count == 0 for count in result["summary"]["counts_by_metric"].values()):
                result["status"] = "review_required"
                result["warnings"].append("No complete historical analogue windows for one or more metrics.")
        else:
            summary = window_summary(self.daily, window["start_date"], window["end_exclusive"])
            result["summary"] = summary
            if any(value != summary["days_expected"] for value in summary["valid_days"].values()):
                result["status"] = "review_required"
                result["warnings"].append("Incomplete metric coverage; full-window totals remain null.")
            if time_mode == "recent_partial":
                result["warnings"].append("Recent observations retain provider latency and partial coverage; this is not a forecast.")
        return result

    def monthly_climate(self, location: dict, window: dict, time_mode: str = "historical_replay") -> dict:
        """Calendar-month slices of the same climate layer; no new metric or gap filling.

        Each slice uses the context complete-day rule, so a month with missing
        days keeps null totals. Analogue slices keep their statistics only.
        """
        resolved = self._resolve(location)
        window = self._window(window)
        if window is None:
            raise ValueError("A window is required for a monthly series")
        layer = self._climate(resolved, None, time_mode)
        first = date.fromisoformat(window["start_date"])
        end = date.fromisoformat(window["end_exclusive"])
        months, cursor = [], first
        while cursor < end:
            following = date(cursor.year + (cursor.month == 12), cursor.month % 12 + 1, 1)
            stop = min(following, end)
            part = self._climate(resolved, {"start_date": cursor.isoformat(), "end_exclusive": stop.isoformat()}, time_mode)
            summary = part["summary"]
            if summary and summary.get("mode") == "historical_analogue_not_forecast":
                summary = {key: summary[key] for key in (
                    "mode", "start", "end_exclusive", "days_expected", "baseline_start_year",
                    "baseline_end_year", "counts_by_metric", "statistics", "mapping_policy")}
            months.append({"month": cursor.strftime("%Y-%m"), "start": cursor.isoformat(), "end_exclusive": stop.isoformat(),
                           "whole_calendar_month": cursor.day == 1 and stop == following,
                           "status": part["status"], "summary": summary, "warnings": part["warnings"]})
            cursor = stop
        statuses = {month["status"] for month in months}
        latest = None
        if resolved["climate_context_id"] and time_mode != "historical_analogue_not_forecast":
            fields = {"rainfall_total_mm": ("PRECTOTCORR",), "reference_eto_total_mm": ("eto_fao56_mm_day",),
                      "rain_minus_reference_eto_total_mm": ("PRECTOTCORR", "eto_fao56_mm_day"), "temperature_mean_c": ("T2M",)}
            latest = {}
            for metric, keys in fields.items():
                latest[metric], day = None, end
                while day > first:
                    day -= timedelta(days=1)
                    row = self.daily.get(day.isoformat()) or {}
                    if all(row.get(key) is not None for key in keys):
                        latest[metric] = day.isoformat()
                        break
        return {"location": resolved, "window": window, "time_mode": time_mode,
                "status": layer["status"] if layer["status"] != "evidence_available" else "review_required" if "review_required" in statuses else "evidence_available",
                "support": layer["support"], "source_refs": layer["source_refs"], "months": months,
                "latest_valid_dates": latest,
                "interpretation": "Monthly slices use the context complete-day rule; months with missing days keep null totals. Not a forecast or irrigation demand."}

    @lru_cache(maxsize=192)
    def _raster(self, name):
        try:
            with rasterio.open(self._path(name)) as ds:
                return {"values": ds.read(1), "mask": ds.read_masks(1), "crs": ds.crs, "transform": ds.transform,
                        "width": ds.width, "height": ds.height, "nodata": ds.nodata, "bounds": list(ds.bounds)}
        except (OSError, rasterio.errors.RasterioError) as exc:
            raise DataUnavailableError(f"Required raster unavailable: {name}") from exc

    def _raster_at(self, name, coordinate):
        lon, lat = coordinate["longitude"], coordinate["latitude"]
        if lon is None:
            return {"value": None, "status": "needs_input", "reason": "coordinate_required"}
        ds = self._raster(name)
        x, y = project("EPSG:4326", ds["crs"], [lon], [lat])
        row, column = rowcol(ds["transform"], x[0], y[0], op=math.floor)
        row, column = int(row), int(column)
        support = {"path": name, "crs_wkt": ds["crs"].to_wkt(), "transform": list(ds["transform"]), "row": row, "column": column, "resolution_in_crs": [abs(ds["transform"].a), abs(ds["transform"].e)], "query_policy": "containing_cell_no_nearest_fallback"}
        if not 0 <= row < ds["height"] or not 0 <= column < ds["width"]:
            return {"value": None, "status": "outside_coverage", "reason": "outside_stored_grid", "support": support}
        value = float(ds["values"][row, column])
        if not ds["mask"][row, column] or not math.isfinite(value):
            return {"value": None, "status": "review_required", "reason": "source_nodata", "support": support}
        return {"value": value, "status": "evidence_available", "reason": "source_valid", "support": support}

    def _soil_layer(self, coordinate):
        properties = []
        for layer in self._soil["native_soil_layers"]:
            query = self._raster_at(layer["path"], coordinate)
            value = query["value"] / layer["scale_divisor"] if query["value"] is not None else None
            properties.append({"property": layer["property"], "depth": layer["depth"], "statistic": layer["statistic"],
                               "value": value, "raw_value": query["value"], "unit": layer["unit"], "status": query["status"],
                               "qa_status": "valid_model_quantile_zero" if value == 0 else query["reason"],
                               "support": query.get("support", {}), "source_refs": ["soilgrids-native"]})
        ph = {row["statistic"]: row for row in properties if row["property"] == "phh2o" and row["depth"] == "0-5cm"}
        status = self._combined_status(properties)
        return {"status": status, "source_refs": ["soilgrids-native", "soil-manifest"],
                "support": {"resolution_m": 250, "product": "SoilGrids spatial model predictions", "is_measured_soil_test": False, "query_policy": "native_containing_cell_with_explicit_mask", "retention_phase": "pre-release"},
                "ph_0_5cm": {"value": ph["mean"]["value"], "q05": ph["Q0.05"]["value"], "q95": ph["Q0.95"]["value"], "unit": "pH", "depth": "0-5cm", "status": ph["mean"]["status"], "support": ph["mean"]["support"], "source_refs": ["soilgrids-native"]},
                "properties": properties,
                "warnings": ["Prediction quantiles are not measured field variation. Total nitrogen is not plant-available nitrogen; retention is not current soil moisture."]}

    @staticmethod
    def _combined_status(rows):
        statuses = {row["status"] for row in rows}
        if "evidence_available" in statuses:
            return "evidence_available" if statuses == {"evidence_available"} else "review_required"
        return "needs_input" if statuses == {"needs_input"} else "outside_coverage" if statuses == {"outside_coverage"} else "review_required"

    def _terrain_layer(self, coordinate):
        elevation = self._raster_at("data/prepared/soil-terrain/processed/elevation-utm49s.tif", coordinate)
        slope = self._raster_at("data/prepared/soil-terrain/processed/slope-degrees-utm49s.tif", coordinate)
        return {"status": self._combined_status([elevation, slope]), "source_refs": ["copernicus-dem"],
                "support": {"source_product": self._terrain["source_product"], "resolution_m": 30, "is_surveyed_microtopography": False},
                "elevation_m": elevation, "slope_degrees": slope,
                "warnings": ["DSM includes buildings and vegetation; derived slopes omit edge cells."]}

    def _footprint_contains(self, coordinate, grid):
        if coordinate["longitude"] is None:
            return False
        x, y = project("EPSG:4326", SINUSOIDAL, [coordinate["longitude"]], [coordinate["latitude"]])
        return _contains(x[0], y[0], {"west": grid["xllcorner"], "east": grid["xllcorner"] + grid["cellsize"] * grid["ncols"], "south": grid["yllcorner"], "north": grid["yllcorner"] + grid["cellsize"] * grid["nrows"]})

    @staticmethod
    def _modis_summary(rows, point_id, window):
        selected = [row for row in rows if row["selected_observation_date"]]
        good = [row for row in selected if row["quality_status"] == "good_strict"]
        counts = Counter(row["quality_status"] for row in selected)
        summary = {"mode": "historical_vegetation_context", "point_id": point_id,
                   "n_selected_observations": len(selected), "n_good_strict": len(good),
                   "n_marginal_review": counts["marginal_review"], "n_excluded": counts["excluded"],
                   "good_observation_dates": sorted(row["selected_observation_date"] for row in good),
                   "coverage_status": "has_good_observations" if good else "no_good_observations" if selected else "no_selected_observations", "interpolated": False,
                   "interpretation": "Mixed-pixel context; no crop species, planting, harvest or fallow inference", "valid_good_observations": {}}
        for index in ("ndvi", "evi"):
            values = [row[index] for row in good if row[index] is not None]
            summary["valid_good_observations"][index] = len(values)
            summary[index + "_good_mean"] = math.fsum(values) / len(good) if good and len(values) == len(good) else None
        if window:
            summary.update(start=window["start_date"], end_exclusive=window["end_exclusive"], days_expected=(date.fromisoformat(window["end_exclusive"]) - date.fromisoformat(window["start_date"])).days)
        return summary

    def _vegetation_layer(self, coordinate, window):
        series = []
        for (product, point_id), grid in self._footprints.items():
            if not self._footprint_contains(coordinate, grid):
                continue
            rows = self._vegetation[(product, point_id)]
            selected = [row for row in rows if row["selected_observation_date"] and (window is None or window["start_date"] <= row["selected_observation_date"] < window["end_exclusive"])]
            summary = self._modis_summary(selected, point_id, window)
            if window:
                first = date.fromisoformat(window["start_date"]).replace(day=1)
                end = date.fromisoformat(window["end_exclusive"])
            else:
                first = date.fromisoformat(min(row["composite_start_date"] for row in rows)).replace(day=1)
                latest = date.fromisoformat(max(row["selected_observation_date"] or row["composite_start_date"] for row in rows))
                end = date(latest.year + (latest.month == 12), latest.month % 12 + 1, 1)
            monthly = []
            while first < end:
                month_rows = [row for row in selected if row["selected_observation_date"].startswith(first.strftime("%Y-%m"))]
                monthly.append({"month": first.strftime("%Y-%m"), **self._modis_summary(month_rows, point_id, None)})
                first = date(first.year + (first.month == 12), first.month % 12 + 1, 1)
            refs = ["modis-terra" if product == "MOD13Q1" else "modis-aqua", "modis-supplement"]
            series.append({"product": product, "platform": "Terra" if product == "MOD13Q1" else "Aqua", "point_id": point_id,
                           "status": "evidence_available" if summary["n_good_strict"] else "review_required", "summary": summary,
                           "observations": deepcopy(rows if window is None else selected), "monthly": monthly, "source_refs": refs,
                           "support": {"crs": SINUSOIDAL, **grid, "nominal_resolution_m": 250, "collection_version": None, "mixed_pixel": True, "query_policy": "exact_product_footprint_contains"},
                           "unassigned_observations_count": sum(not row["selected_observation_date"] for row in rows)})
        return {"status": "needs_input" if coordinate["longitude"] is None else self._combined_status(series) if series else "outside_coverage",
                "source_refs": ["modis-terra", "modis-aqua", "modis-supplement"], "support": {"products_kept_separate": True, "interpolated": False}, "series": series,
                "warnings": ["QA excludes cloudy and marginal samples from strict-good means. Collection version is unverified in subset responses."]}

    def _gaez_layer(self, coordinate):
        rows = []
        if coordinate["longitude"] is not None:
            for row in self._gaez["rows"]:
                if _contains(coordinate["longitude"], coordinate["latitude"], row["pixel_bounds"]):
                    parts = row["layer_code"].split(".")
                    rows.append({"layer_code": row["layer_code"], "crop_code": parts[-2], "regime": parts[-1], "class_code": row["raw_value"], "class_label": row["class_label"], "continuous_suitability_score": None, "pixel_bounds": row["pixel_bounds"], "source_url": row["url"]})
        return {"status": "needs_input" if coordinate["longitude"] is None else "evidence_available" if rows else "outside_coverage", "source_refs": ["gaez-v5"],
                "support": {"period": self._gaez["period"], "scenario": self._gaez["scenario"], "climate": self._gaez["climate"], "resolution_degrees": self._gaez["spatial_resolution_degrees"], "regimes_kept_separate": True}, "rows": rows,
                "warnings": ["Historical coarse categorical model classes are not current field suitability or a continuous score."]}

    def _landcover_layer(self, coordinate):
        footprints = []
        for point_id, evidence in self._landcover.items():
            if self._footprint_contains(coordinate, self._footprints[("MOD13Q1", point_id)]):
                footprints.append({"point_id": point_id, "epoch": 2021, "stats": evidence["worldcover_stats_within_modis_pixel"], "sinusoidal_bounds_m": evidence["sinusoidal_bounds_m"], "meaning": "Historical context within this exact Terra footprint; not a farm boundary or current point classification"})
        return {"status": "needs_input" if coordinate["longitude"] is None else "evidence_available" if footprints else "outside_coverage", "source_refs": ["esa-worldcover-2021"], "support": {"epoch": 2021, "product": "ESA WorldCover 2021 v200", "query_policy": "query_inside_exact_historical_footprint"}, "footprints": footprints}

    def context(self, location: dict, window: dict | None = None, time_mode: str = "historical_replay") -> dict:
        resolved = self._resolve(location)
        window = self._window(window)
        coordinate = resolved["coordinate"]
        layers = {"climate": self._climate(resolved, window, time_mode), "soil": self._soil_layer(coordinate),
                  "terrain": self._terrain_layer(coordinate), "vegetation": self._vegetation_layer(coordinate, window),
                  "gaez": self._gaez_layer(coordinate), "landcover": self._landcover_layer(coordinate)}
        missing = []
        if coordinate["longitude"] is None:
            missing.append("location.coordinate")
        if not resolved["climate_context_id"]:
            missing.append("location.climate_context_id")
        return {"location": resolved, "window": window, "time_mode": time_mode, "layers": layers, "missing_inputs": missing,
                "warnings": ["Public example evidence is not a verified farmer field. Source resolutions and dates differ; no nearest-point fallback or imputation is used."]}
