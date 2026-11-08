# FieldShift

FieldShift is a web tool that helps farmers and extension workers think through a change in crop rotation. It puts the rotation a farmer uses now next to two alternatives over the same planning period, and shows the environmental evidence, crop constraints, and missing information behind each one.

It is built for the NASA Space Apps Challenge 2026 challenge [Field Shift: Adapting Farms with NASA Data](https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/).

The question it tries to answer: **"What should I consider if I change the crop rotation at this location?"**

## Scope of version 0.1.0

| Aspect | Current scope |
|---|---|
| Demo area | Yogyakarta–Klaten, Indonesia (two sample points in rural Klaten) |
| Crops | Rice, maize, soybean |
| Comparison | One location, one planning horizon, three strategies: `existing`, `candidate_1`, `candidate_2` |
| Checks | 12 agronomic and calendar checks per strategy (method v0.1.0) |
| Interface language | Indonesian |
| Accounts and storage | None. Inputs live only in the browser session; the API stores nothing. |

### What it deliberately does not do

- No ranking, scores, yield prediction, water-saving percentages, nitrogen credits, or profit. The method has not been calibrated for those claims, so the API returns them as `null`.
- No local agronomic validation yet. Every result carries `local_agronomic_validation: false`.
- No silent nearest-neighbour fallback. If a data layer has no value for a location, the app says so instead of borrowing a nearby value.
- Historical climate is never labelled as a forecast, and P−ETo is never labelled as irrigation demand.
- Analysis is point-based. Field polygons are not supported yet.

## Data sources

| Layer | Source | Coverage in this repo |
|---|---|---|
| Climate (daily, monthly, 1991–2020 baseline) | [NASA POWER](https://power.larc.nasa.gov/) | One regional point, 1991–2025 plus partial 2026 |
| Vegetation (NDVI/EVI with QA) | [NASA MODIS via ORNL DAAC](https://modis.ornl.gov/data/modis_webservice.html), Terra and Aqua kept separate | Two Klaten pixels, 2021–2026 |
| Soil (12 properties × 5 depths × mean/Q05/Q95) | [ISRIC SoilGrids](https://docs.isric.org/globaldata/soilgrids/) (CC BY 4.0) | About 2 × 2 km subset |
| Elevation and slope | [Copernicus DEM GLO-30](https://registry.opendata.aws/copernicus-dem/) | Same subset |
| Land cover | [ESA WorldCover 2021](https://esa-worldcover.org/) (CC BY 4.0) | Same subset and MODIS footprints |
| Crop suitability categories | [FAO GAEZ v5](https://gaez.fao.org/) | Two points × three crops × two water regimes |
| Crop water references | [FAO-56](https://www.fao.org/4/x0490e/x0490e00.htm) | Reference tables only |
| Indonesian varieties | Kementan / BRMP catalogues | Reference durations, not farmer defaults |
| Short-range weather snapshot | BMKG | Reference only, expires quickly |

Each layer keeps its own attribution, access time, and checksums in the `manifest.json` next to it. See [data/prepared/README.md](data/prepared/README.md) and [data/supplemental/readiness-audit.json](data/supplemental/readiness-audit.json) for coverage, gaps, and QA details.

## Tech stack

- **Backend:** Python 3.11, FastAPI, Uvicorn, rasterio, jsonschema
- **Frontend:** React 19, TypeScript, Vite, three.js (3D field diorama), Leaflet (map)

## Repository layout

| Path | Contents |
|---|---|
| `backend/fieldshift/` | FastAPI app: data repository, context layers, rotation analysis, input validation |
| `frontend/` | Single-page landing site and exploration tool |
| `data/prepared/` | Initial public data package (390 files with SHA-256 manifest) |
| `data/supplemental/` | Additional public data and the 119-field typed input contract (526 files with manifest) |
| `scripts/data/` | Data download, preparation, QA, and packaging scripts |
| `scripts/method/` | Reference implementation of the rotation method |
| `specs/` | Rotation method spec (`rotation-method-v1.json`) and demo fixture |
| `tests/` | Method and backend tests |
| `docs/` | MVP spec, roadmap, rotation method, design briefs (Indonesian) |
| `outputs/` | Audit reports, demo request/response, OpenAPI contract, verification reports, data package ZIPs |
| `work/` | Early research samples and challenge page snapshot |

## Getting started

Requirements: Python 3.11 and Node.js with npm.

### 1. Backend

From the repository root (PowerShell):

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
.venv\Scripts\python.exe -m uvicorn backend.fieldshift.app:app --host 127.0.0.1 --port 8000
```

On macOS or Linux, use `python3.11 -m venv .venv` and `.venv/bin/python` instead.

Interactive API docs are at http://127.0.0.1:8000/docs. On startup the backend checks the SHA-256 hash of every file in both data manifests and returns `503` if any file is missing or changed.

### 2. Frontend (development)

With the backend running:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The dev server proxies `/api` and `/health` to the backend.

### 3. Single server

Run `npm run build` in `frontend/`, then restart the backend. FastAPI serves the built app at http://127.0.0.1:8000/ alongside the API.

## API overview

| Endpoint | Purpose |
|---|---|
| `GET /health` | Readiness and data integrity status |
| `GET /api/v1/catalog` | Coverage, manifests, time modes, sources |
| `GET /api/v1/locations` | The two Klaten sample points |
| `GET /api/v1/crops` | Rice, maize, soybean references |
| `GET /api/v1/input-contract` | JSON Schema for partial farm input documents |
| `POST /api/v1/context` | Climate, soil, terrain, vegetation, GAEZ, and land cover for a point and time window |
| `POST /api/v1/climate/monthly` | Monthly climate slices for charts |
| `POST /api/v1/compare` | Three strategies with 12 checks, status, missing inputs, and sources |
| `GET /api/v1/demo` | A labelled 2025 historical demo request and its recomputed result |

Full request rules and error formats are in [backend/README.md](backend/README.md). The OpenAPI contract is in [outputs/backend-openapi.json](outputs/backend-openapi.json).

## Verification

```powershell
# Method and backend tests, real HTTP checks, manifest checks
.venv\Scripts\python.exe scripts/verify_backend.py

# Rotation method reference checks
.venv\Scripts\python.exe scripts/method/verify_rotation_method.py

# Offline data package checks
.venv\Scripts\python.exe scripts/data/validate_prepared_data.py
.venv\Scripts\python.exe scripts/data/audit_data_completeness.py
```

The latest recorded run ([outputs/backend-verification.json](outputs/backend-verification.json)) passed 55 method tests, 79 backend tests, and 5 real HTTP checks, with all 916 data file hashes verified.

## Notes for contributors

- **Do not edit files under `data/` by hand.** The backend refuses to start if a hash no longer matches its manifest. `.gitattributes` marks `data/` as binary so git does not change line endings on checkout.
- **Vendored libraries are not in the repo.** Some data scripts look for local copies of numpy/rasterio and jsonschema. Recreate them if you need to rerun those scripts:

  ```powershell
  python -m pip install --target scripts/data/soil-terrain/_vendor -r scripts/data/soil-terrain/requirements.txt
  python -m pip install --target work/validation-deps jsonschema==4.26.0
  ```

  The backend itself only needs `backend/requirements-lock.txt`.
- Unknown values stay `null`. A known zero, an explicit "none", and "don't know" mean different things throughout the input contract.

## Project status

| Stage | Status |
|---|---|
| 0. Public data foundation | Done |
| 1. MVP definition | Done ([docs/mvp.md](docs/mvp.md)) |
| 2. Rotation analysis method | Done ([docs/rotation-method.md](docs/rotation-method.md)) |
| 3. Backend | Done |
| 4. Interface | Done |
| 5. Testing and local agronomic validation | Done |
| 6. Challenge demo | Done |

See [docs/roadmap.md](docs/roadmap.md) for details. The app is not deployed yet.
