# Agronomy supplement

Additive public evidence and input contract for FieldShift; prepared files remain unchanged. No farm observations, backend, recommendations or quantitative benefits were created.

- `summary.json`: integration entry point and counts.
- `agronomy-reference-supplement.json`: Anjasmoro duration alternatives, rice vocabulary and management prerequisites.
- `source-evidence.json`: precise quotes, source paths, timestamps, SHA256 and PDF locators; source snapshots and three visual-QA pages in `sources/`.
- `farm-input-contract.json`: typed/nullable definitions for every original 91 field plus required additions; units and records explicit.
- `farm-input-complete.schema.json`: JSON Schema 2020-12; `farm-input-complete-template.json`: all field values null.
- `method-rule-input-map.json`: all 12 method rules, exact prerequisites and original/supplemental field links.
- `gap-register.json`: public-reference, farmer-only, scenario-configuration and local-validation needs.
- `validation.json`: invariant/source/schema verification; `manifest.json`: output/script hashes.

The official BRMP catalog reports Anjasmoro maturity 82–93 days after planting; separate official sources report 82.5–92.5 days/HST. Preserve these source alternatives. Do not silently rewrite the prepared 82–92 reference, round fractional days, choose a farmer cultivar or claim a calibrated harvest date.

Rice ecosystem, establishment and actual water regime are separate. Rainfed lowland can flood; direct seeding alone does not identify upland. Drainage and paddy-to-upland management require actual local review. Operational water-regime terms are project vocabulary, not direct FAO category codes.

Legacy weights are inactive. The MVP uses explicit priority labels with no weighting/ranking. Negative latitude is valid. Area units are hectares. Histories/market records have explicit shapes; monetary and yield data stay deferred.

Every supplied actual value remains null. Empty array, zero, false and unknown are distinct. Public soil predictions belong to context, never laboratory results. Geometry-derived area requires a real farmer boundary and geodesic calculation. The JSON Schema covers structural types; semantic geometry/calendar/source-support validations are documented and remain future implementation requirements.

Rebuild offline with `scripts/data/supplemental_agronomy/build_supplement.py`. Full schema QA uses Python 3.11 with the isolated `work/validation-deps` installation of `jsonschema==4.26.0`; the compiled dependency must match the Python version. The build records the validator version and 19 ephemeral boundary checks. Fetching and PDF extraction use the bundled Python with `pypdf`. `fetch_sources.py` caches official sources, records failures, and bounds each download to 8 MB and total snapshots to 20 MB. Source PDFs are read-only; no PDF authored.
