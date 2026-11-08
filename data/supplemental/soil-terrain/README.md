# Supplemental native soil evidence

This package audits the existing Klaten sample against original public ISRIC
SoilGrids rasters. It is a separate source package; all 390 files listed in the
prepared-data manifest retain their original SHA-256 hashes. No backend or
decision method is changed.

## Coverage and result

The requested WGS84 bounding box is west 110.54, south -7.73, east 110.56,
north -7.71. The package contains 180 native raster windows: 12 properties,
5 depths (0-5, 5-15, 15-30, 30-60, 60-100 cm), and mean, Q0.05 and Q0.95.
The source grid is 250m in Interrupted Goode Homolosine. Each aligned window
has 9 rows and 11 columns, with 92 valid cells and 7 source-nodata cells.
Native aligned bounds slightly extend outside the requested box. Per-layer
WKT, transforms, bounds, nodata and checksums are in `grid-catalog.json` and
`native-source-manifest.json`; retain them rather than assigning an invented
EPSG code or assuming that all WKT strings are identical.

The earlier geographic WCS output has 8 rows and 9 columns. Its 12,960
property/depth/statistic cell records were checked at their own coordinates:

| Earlier records | Result from original native source |
| --- | --- |
| 11,900 usable positive values | All match exactly |
| 1,056 ambiguous zeros | 340 valid model zeros; 716 explicit source nodata |
| 4 negative sentinel values | All confirmed as source nodata |
| Unresolved original zeros after this audit | 0 |

The 340 verified zeros belong to the lower prediction quantile of coarse
fragments (`cfvo`, Q0.05). A valid lower model quantile of zero does not establish
that a farmer's field contains no gravel. The other original zeros represent
source coverage holes, not measured zero soil properties. No values were
imputed. Native nodata remains -32768 and its mask must be checked before
scaling or using a value. The earlier grid has 4 masked coordinate positions
(row 7, columns 2-5); record counts across layers must not be mistaken for
additional independent geographic locations.

Both frozen example anchors contain all 180 valid values, including five valid
`cfvo` Q0.05 zeros each:

| Anchor | Latitude | Longitude | Available values |
| --- | --- | --- | --- |
| Primary | -7.721875031299882 | 110.55354472008753 | 180 / 180 |
| Comparison | -7.7240416666666665 | 110.546875 | 180 / 180 |

`processed/anchor-native-profiles.csv` records these extractions.
`processed/legacy-centers-native-audit.csv` records the complete comparison.
The actual primary coordinate and the old row 4, column 6 cell centre are
different points. For example, native 0-5cm pH at the primary anchor is mean
5.8, Q0.05 4.2, Q0.95 7.9; at the old cell centre it is 5.8, 4.2, 7.8.
Do not use the old cell centre as the actual anchor coordinate.
`processed/native-common-valid-mask.tif` stores the shared native mask; valid
cells are 255 and nodata cells are 0. Transform a query coordinate into the
exact layer CRS, use its containing cell and reject masked or out-of-grid
cells. Do not replace missing cells with a nearest valid cell.

## Sources and units

The nine basic properties use original GeoTIFF tiles under
<https://files.isric.org/soilgrids/latest/data/>. Official directory snapshots
identify the local tile subdivision. Water retention (`wv0010`, `wv0033`,
`wv1500`) uses public pre-release GeoTIFF URLs extracted from saved official
ISRIC ISO records. The XML records and source metadata are retained under
`raw/`. Source URLs, retrieval times and native subset SHA-256 hashes are in
`native-source-manifest.json`; documentation and directory hashes are in
`catalog-source-manifest.json`.

| Property | Divide raw integer by | Resulting unit |
| --- | --- | --- |
| phh2o | 10 | pH |
| sand, silt, clay | 10 | % mass |
| soc | 10 | g/kg organic carbon |
| nitrogen | 100 | g/kg total nitrogen |
| cec | 10 | cmol(c)/kg |
| bdod | 100 | g/cm3 |
| cfvo | 10 | % volume |
| wv0010, wv0033, wv1500 | 10 | % volume at 10, 33, 1500 kPa respectively |

These are spatial model predictions. Water retention is labelled pre-release
and is not current soil moisture, measured irrigation supply, or calibrated
farm water capacity. Total nitrogen is not plant-available nitrogen. Mean and
prediction quantiles are retained separately; quantiles are not confidence
intervals for a field measurement. Only bounded native windows were read; full
global remote rasters were not downloaded or hashed. Network range-transfer
bytes were not instrumented.

Initial unsuccessful native source attempts and diagnostic WCS probes remain
as evidence. A WCS request for native output CRS still produced a resampled
grid without explicit nodata, so it did not resolve the zero ambiguity. The
final original-source TIFF windows provide that evidence. Existing terrain
layers are catalogued by reference with their current hashes, CRS and grids;
they have not been overwritten.

## Validation and reproducibility

`summary.json` exposes before/after counts, source information, remaining gaps
and `validation.pass`. `validation.json` records all checks: 180 native windows,
12,960 legacy comparisons, source masks and hashes, two complete anchors,
quantile ordering, mean texture closure, mean water-retention ordering, and
the unchanged 390-file prepared manifest. Mean sand+silt+clay sums range from
99.9% to 100.1% on valid native cells at every depth. No tested water-retention
mean has a reversed 10/33/1500 kPa ordering. The checks pass.

Scripts live in `scripts/data/supplemental_soil/`, relative to the repository
root. The evidence acquisition sequence is `probe_soil_sources.py`,
`direct_source_probe.py`, `inspect_source_catalog.py`, `collect_native_soil.py`,
then `finalize_soil_audit.py`. The finalizer can be rerun against the saved
local package without downloading source rasters. Use the bundled Python 3.12
runtime with the existing isolated rasterio/numpy vendor paths configured by
the scripts. `file-manifest.json` hashes every file in this supplemental folder
except itself. Its hashes do not cover the external scripts.

## Remaining data gaps

Source coverage holes remain null. Coverage is limited to this sample window;
any new farm location needs its own extraction and checks. The example anchors
are not verified farmer fields. Farm boundaries and area, measured soil tests,
available P/K, salinity, irrigation and drainage, management and crop history,
actual planting dates, and costs/prices/yields remain unavailable. They must
stay missing until supplied; public model layers do not fill those gaps.
