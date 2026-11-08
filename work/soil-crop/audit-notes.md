# Non-NASA dataset audit — 2026-11-08

## Soil properties: ISRIC SoilGrids

- Official docs: https://docs.isric.org/globaldata/soilgrids/
- WCS docs: https://docs.isric.org/globaldata/soilgrids/wcs.html
- Layer units and uncertainty: https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html
- Global predicted maps, native 250 m, six depth intervals 0–5, 5–15, 15–30, 30–60, 60–100, 100–200 cm. Includes pH, organic carbon, texture fractions, bulk density, total nitrogen, CEC. Mean and 5/50/95% quantiles. CC BY 4.0.
- Model predictions are not a laboratory measurement or current nutrient availability. Total nitrogen must not be relabeled as plant-available nitrogen. These maps alone do not establish a fertilizer prescription or guaranteed soil-health improvement.
- Official notice currently states REST API paused, beta, no guaranteed uptime. One REST query at 110.37,-7.8 returned HTTP 200 with mean:null; rural query 110.55,-7.72 timed out after 20 s. An HTTP 200 does not establish usable numeric data.
- WCS GetCapabilities and DescribeCoverage succeeded HTTP 200. Tiny pH 0–5 cm mean subset succeeded HTTP 200, 648 bytes, image/tiff. File ph-rural-subset.tif.
- WGS84 output raster: width 9, height 8; west=110.54000000000002; east≈110.56; north=-7.71; south≈-7.73; dx=0.0022222222222207932 degrees; dy=0.002500000000000137 degrees. This is a reprojected grid; 250 m refers to the native Homolosine product.
- Integer values are pH×10. Decoded raster has 5 cells=56, 24 cells=57, 39 cells=58, 4 cells=0. Therefore 68 plausible nonzero values represent predicted pH 5.6–5.8. The four zeros are unvalidated/invalid for interpretation and must not be presented as measured pH 0.
- Caveat: output TIFF has no GDAL_NODATA tag, DescribeCoverage nilValues is empty and its uom is a generic wrong value. Partial official source VRT (HTTP Range first 8192 bytes) declares source nodata=-32768. Therefore zero is NOT confirmed source nodata; avoid claiming that it is.
- Official VRT URL: https://files.isric.org/soilgrids/latest/data/phh2o/phh2o_0-5cm_mean.vrt . Only first 8192 bytes retrieved, file ph-source-vrt-head.xml.

## Crop reference: FAO ECOCROP / AquaCrop

- Official ECOCROP overview: https://www.fao.org/geospatial/data-and-tools/data-portals/ecocrop/
- ~2,568 species; temperature, annual rainfall, pH, ecology, uses and cycle descriptors. Official overview says original database discontinued around 2015 and now accessible through GAEZ. It is a historical species-level reference, not a current local variety database.
- Actual FAO profile HTML downloads all succeeded without login: rice id1574 (6144 bytes), maize id2175 (6393 bytes), soybean id1150 (7274 bytes). Corresponding curated numerical facts are in crop-reference.csv. Missing fields and very broad ranges exist. These values do not validate rotation sequences.
- AquaCrop inputs: https://www.fao.org/aquacrop/overview/input-requirements/ . Requires climate, calibrated crop parameters, soil profile and groundwater, plus field and irrigation management. Local cultivar adjustment is explicitly needed. Available model inputs are not a ready-made locally validated rotation recommender.

## Local calendars and market data

- Kementan SIAP TANAM official description: https://brmp.pertanian.go.id/index.php/layanan/layanan-elektronik/siap-tanam . Recommends timing, pattern, and planted area for rice, maize, soybean using BMKG rainfall predictions and water balance; supports national through kecamatan use. Public documented machine API was not confirmed. Do not claim live integration is ready.
- FAO GIEWS Indonesia country brief: https://www.fao.org/giews/countrybrief/country.jsp?code=IDN&lang=en . Current accessible reference dated 29 January 2026, contains national rice/maize seasonal context, not individual farm history.
- BPS producer-price publication found in official indexed result: https://www.bps.go.id/id/publication/2026/04/24/ab557ad3c44be1254c87c5aa/statistik-harga-produsen-pertanian-subsektor-tanaman-pangan-hortikultura-dan-tanaman-perkebunan-rakyat-2025.html . Search result says monthly producer prices across 37 provinces, excluding Jakarta. Direct web tool received403. Download/API and exact relevant crop coverage not tested. Provincial producer-price averages are not farmer-specific sale prices or profit.

## Still requires farmer/local expert input

- Field boundary/area, existing rotation and planting/harvest dates, cultivar, irrigation source/limits and drainage, measured soil results if available, pest history and management.
- Priorities and constraints: water saving vs income vs soil improvement; access to machinery, labor, inputs, buyers, budget and crop market preferences.
- Comparing three candidate rotations is a designed analytical output, not an existing NASA dataset. Nitrogen fixation, pest interruption and soil-health benefits require crop/management logic with evidence and local validation, and should not be presented as directly observed satellite values.
