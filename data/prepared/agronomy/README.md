# Agronomy data readiness — FieldShift

Prepared 8 November 2026 (Asia/Jakarta). This package contains reference data and missing-input definitions. No application, farm recommendation, yield/profit prediction or nitrogen credit has been implemented.

## Available

- `crop-reference.json` and CSV: padi, jagung and kedelai. Historical FAO ECOCROP temperature/pH/annual-rainfall ranges; clearly separate FAO indicative seasonal ET ranges; Indonesian variety examples (Inpari 32 HDB, Jakarin, Anjasmoro) with source and duration basis. Variety examples are not farmer selections.
- `agronomy-rules.json`: conditional mechanisms and required inputs for rotation, water balance, pests, nitrogen and economics. No invented effect sizes.
- `gaez-baseline-point.json` and CSV: actual pixels for twelve combinations: 2 test points × wetland rice/maize/soybean × rain-fed/irrigated high-input management. Exact crop, period, climate and management dimensions plus official SIX legend are saved in sources.
- `farm-input-template.json` and dictionary: no invented farm; all unknown user values are null.
- `strategy-comparison-template.json`: three empty strategy slots (existing, candidate_1, candidate_2); rotation sequence, outcomes, yield, price, costs and priorities stay null; economics unavailable.
- `source-evidence.json` and source snapshots: URLs, access timestamps where known, hashes, failed access attempts and short evidence locators.

## GAEZ result and interpretation

HP0120 = 2001–2020, AGERA5, HIST. Grid: EPSG:4326 at 0.0833333333° (5 arc-minutes, approximately 9 km), not 30 m field data. HRLM = rain-fed/high inputs; HILM = irrigation/high inputs. These assumed management scenarios do not describe the user's actual management.

At Yogyakarta test point 110.37,-7.8, all six samples have categorical value 7: official legend `SI >0 : Very marginal`. At Klaten test point 110.55,-7.72, wetland rice has class 4 (`SI >40 : Medium`); maize and soybean have class 5 (`SI >25 : Moderate`) under both management scenarios. Class 7 is not a score 7/100. A continuous score cannot be recovered from these categorical rasters. Neither point is a verified farm and no recommendation is inferred.

Only a 65,536-byte TIFF header plus the one relevant compressed tile per layer was retrieved using HTTP 206 byte ranges, then decoded with Pillow/libtiff as a standalone LZW tile. Both points fall in the same retrieved tile. Six source subsets total about 425 KB; no complete global raster/archive was downloaded. `gaez-baseline-point.json` records pixel indexes, exact bounds, nodata, URLs and extraction status. Original generic palette is not used as the class definition; the official SIX JSON and SLD are the interpretation evidence.

## Limits and remaining work

Annual ECOCROP rainfall is a climate descriptor; FAO seasonal water need is indicative crop ET; irrigation additionally depends on effective rainfall, soil storage, field losses and efficiency. Paddy ET excludes the full scheme's land preparation, seepage/percolation and conveyance losses. Do not compare the table ranges as guaranteed farm water savings.

Local stage dates, cultivar calibration, seed availability, drainage, irrigation allocation, pest host ranges, measured soil fertility, costs and farm-gate prices remain missing. SIAP TANAM is a documented Indonesian reference service; its machine API and location-specific current recommendations were not tested here. The public FAO crop-information maize/soybean URLs returned 404; the official GAEZ API endpoints returned 502. Downloading the linked GAEZ XLSX lookup files failed with timeout/certificate errors; public bucket dimension JSON and legend were obtained instead. No account access is required for the completed bounded GAEZ extraction.

Public reference data are ready for a demo that exposes provenance and coarse-grid limitations. Validated farm recommendations and economics are unavailable until actual farmer inputs, model choices and local validation are supplied. No cultivar listed in this reference is assumed selected by the farmer.

## Reproduce

Use the bundled Python runtime with numpy and Pillow. `scripts/data/agronomy/fetch_sources.py` captures bounded public source snapshots; `sample_gaez.py` extracts the two historical anchor pixels; `prepare_agronomy.py` writes the structured reference and template. The refresh scripts never create or modify an application. The CSV files are simple machine-readable exports of JSON; JSON is authoritative for nulls, units and nested limitations.
