"""Verify the supplemental native-grid evidence and publish a bounded catalog."""
from __future__ import annotations
from collections import Counter,defaultdict
import csv,hashlib,json,math
from collect_native_soil import ROOT,OUT,RAW,PROC,LEGACY,BASE,PROPERTIES,DEPTHS,STATISTICS,ANCHORS,original_hashes,write_json,NOW
import numpy as np
import rasterio

def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def csv_rows(path):return list(csv.DictReader(path.open(encoding='utf-8')))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def grid_info(path):
    with rasterio.open(path) as ds:
        nodata=ds.nodata
        if nodata is not None and not math.isfinite(nodata):nodata='NaN'
        return {'path':str(path.relative_to(ROOT)).replace('\\','/'),'sha256':sha(path),
            'width':ds.width,'height':ds.height,'crs_wkt':ds.crs.to_wkt(),
            'transform':list(ds.transform),'bounds_in_crs':list(ds.bounds),'dtype':ds.dtypes[0],
            'nodata_tag':nodata,'valid_mask_cells':int((ds.read_masks(1)>0).sum()),
            'query_policy':'Use containing cell in this stored CRS/transform and check its mask; no nearest-cell fallback.'}

def main():
    source=load(OUT/'native-source-manifest.json')
    records=source['records'];retrieved=[r for r in records if r['status']=='retrieved']
    audit=csv_rows(PROC/'legacy-centers-native-audit.csv')
    anchors=csv_rows(PROC/'anchor-native-profiles.csv')
    counts=Counter(r['comparison_status'] for r in audit)
    old_counts=Counter(r['qa_status'] for r in LEGACY)
    unresolved={(r['property'],r['depth'],r['statistic'],r['row'],r['col']) for r in LEGACY if r['qa_status']!='usable_prediction'}
    audited={(r['property'],r['depth'],r['statistic'],r['legacy_row'],r['legacy_col']) for r in audit if r['legacy_qa_status']!='usable_prediction'}
    zero_verified=counts['legacy_zero_native_zero_verified']
    zero_nodata=counts['legacy_zero_source_nodata_at_coordinate']
    source_nodata=zero_nodata+counts['legacy_sentinel_source_nodata_confirmed']
    zero_nonzero=counts['legacy_zero_native_nonzero_at_coordinate']
    zero_still_unresolved=old_counts['zero_unresolved']-zero_verified-zero_nodata
    grid_catalog=[];masks=[];arrays={};raw_bad_hash=[];masked_values_bad=[]
    for record in retrieved:
        path=OUT/record['subset_file']
        if sha(path)!=record['subset_sha256']:raw_bad_hash.append(record['subset_file'])
        grid_catalog.append({'property':record['property'],'depth':record['depth'],'statistic':record['statistic'],
            'source_url':record['source_url'],'scale_divisor':PROPERTIES[record['property']][0],
            'unit':PROPERTIES[record['property']][1],**grid_info(path)})
        with rasterio.open(path) as ds:
            a=ds.read(1);mask=ds.read_masks(1)>0
            masks.append(mask)
            arrays[(record['property'],record['depth'],record['statistic'])]=(a,mask)
            if not np.array_equal(mask,a!=ds.nodata):masked_values_bad.append(record['subset_file'])
    mask_identical=bool(masks) and all(np.array_equal(mask,masks[0]) for mask in masks)
    if mask_identical:
        reference=OUT/retrieved[0]['subset_file']
        with rasterio.open(reference) as ds:
            profile=ds.profile.copy();profile.update(dtype='uint8',nodata=0)
            with rasterio.open(PROC/'native-common-valid-mask.tif','w',**profile) as target:
                target.write(masks[0].astype('uint8')*255,1)
        mask_meta=grid_info(PROC/'native-common-valid-mask.tif')
    else:mask_meta=None
    quantile_inversions=[];texture_checks=[];retention_checks=[]
    for prop in PROPERTIES:
        for depth in DEPTHS:
            keys=[(prop,depth,s) for s in ['Q0.05','Q0.95']]
            if not all(key in arrays for key in keys):continue
            (lo,lm),(hi,hm)=[arrays[key] for key in keys]
            invalid=(lm&hm)&(lo>hi)
            if invalid.any():quantile_inversions.append({'property':prop,'depth':depth,'cells':int(invalid.sum())})
    for depth in DEPTHS:
        texture_keys=[(p,depth,'mean') for p in ['sand','silt','clay']]
        if all(key in arrays for key in texture_keys):
            layers=[arrays[key] for key in texture_keys]
            valid=np.logical_and.reduce([m for a,m in layers]);total=sum(a.astype(int) for a,m in layers)
            texture_checks.append({'depth':depth,'valid_cells':int(valid.sum()),
                'sum_percent_min':float(total[valid].min()/10),'sum_percent_max':float(total[valid].max()/10),
                'outside_99_5_to_100_5_percent':int((valid&((total<995)|(total>1005))).sum())})
        water_keys=[(p,depth,'mean') for p in ['wv0010','wv0033','wv1500']]
        if all(key in arrays for key in water_keys):
            layers=[arrays[key] for key in water_keys];valid=np.logical_and.reduce([m for a,m in layers])
            a10,a33,a1500=[a for a,m in layers]
            retention_checks.append({'depth':depth,'valid_cells':int(valid.sum()),
                'nonmonotonic_cells':int((valid&((a10<a33)|(a33<a1500))).sum())})
    anchor_summary={}
    for role,anchor in ANCHORS.items():
        selected=[r for r in anchors if r['location_role']==role]
        actual={(r['property'],r['depth'],r['statistic']) for r in selected}
        missing=[{'property':p,'depth':d,'statistic':s} for p in PROPERTIES for d in DEPTHS for s in STATISTICS if (p,d,s) not in actual]
        anchor_summary[role]={'coordinate':anchor['sample_coordinate'],'expected_value_count':180,
            'available_value_count':sum(r['native_mask_valid']=='True' for r in selected),
            'verified_model_zero_count':sum(r['qa_status']=='source_valid_model_quantile_zero' for r in selected),
            'source_nodata_count':sum(r['native_mask_valid']!='True' for r in selected),'missing_extractions':missing,
            'properties':len({r['property'] for r in selected}),'depths':len({r['depth'] for r in selected}),
            'source_support':'Native 250m SoilGrids model cell, not a measured farmer field'}
    terrain_files=['raw/copernicus-dem-subset.tif','processed/elevation-utm49s.tif','processed/slope-degrees-utm49s.tif']
    terrain=[grid_info(BASE/name) for name in terrain_files]
    write_json(OUT/'grid-catalog.json',{'prepared_at_utc':NOW,
        'request_bbox_wgs84':[110.54,-7.73,110.56,-7.71],
        'native_window_note':'The aligned native 9-row by 11-column window slightly extends beyond the earlier geographic 8-row by 9-column request; consult the native bounds and valid mask. It does not imply complete values at every location in the bbox.',
        'native_soil_layers':grid_catalog,'native_common_mask':mask_meta,'terrain_existing_layers':terrain,
        'spatial_policy':'Transform coordinates into the exact stored CRS, use the containing cell, reject out-of-grid or masked cells, and never use nearest-point or nearest-valid substitution.'})
    integrity=original_hashes()
    checks={
        'all_180_native_rasters_retrieved':len(retrieved)==180,
        'all_12960_legacy_centers_audited':len(audit)==12960,
        'every_legacy_bad_record_has_an_audit':unresolved<=audited,
        'legacy_positive_values_all_match_native':counts['legacy_usable_matches_native']==11900,
        'no_legacy_positive_values_changed_or_disagreed':not any(counts[key] for key in ['legacy_usable_native_nodata','legacy_usable_differs_native_do_not_substitute']),
        'all_original_zeros_classified_without_imputation':zero_still_unresolved==0 and zero_nonzero==0,
        'all_four_negative_sentinels_confirmed_source_nodata':counts['legacy_sentinel_source_nodata_confirmed']==4,
        'native_subset_checksums_match':not raw_bad_hash,
        'all_native_layers250m':all(r['native_grid_250m'] for r in retrieved),
        'native_masks_match_explicit_nodata_tags':not masked_values_bad,
        'all_anchors_180_valid_values':all(r['available_value_count']==180 and not r['missing_extractions'] for r in anchor_summary.values()),
        'no_quantile_inversions':not quantile_inversions,
        'texture_mean_closure_pass':len(texture_checks)==5 and all(r['outside_99_5_to_100_5_percent']==0 for r in texture_checks),
        'retention_mean_monotonic':len(retention_checks)==5 and all(r['nonmonotonic_cells']==0 for r in retention_checks),
        'prepared390_files_still_match':integrity['files']==390 and not integrity['mismatches'],
    }
    validation={'pass':all(checks.values()),'checks':checks,'prepared_integrity':integrity,
        'quantile_inversions':quantile_inversions,'texture_checks':texture_checks,'retention_checks':retention_checks,
        'native_mask_identical_across_layers':mask_identical,'bad_subset_hashes':raw_bad_hash}
    write_json(OUT/'validation.json',validation)
    summary={'module_id':'soil-terrain-supplemental','prepared_at_utc':NOW,
        'status':'public_sample_evidence_audited_with_explicit_source_holes' if validation['pass'] else 'audit_needs_review',
        'before':{'prepared_rasters':180,'properties':12,'depths':5,'statistics':3,'legacy_cell_records':len(LEGACY),
            'usable_values':old_counts['usable_prediction'],'ambiguous_zeros':old_counts['zero_unresolved'],'negative_sentinels':old_counts['nodata']},
        'after':{'native_rasters_retrieved':len(retrieved),'native_properties':len(PROPERTIES),'native_depths':len(DEPTHS),
            'native_grid_shape':[9,11],'legacy_center_audit_records':len(audit),
            'original_zeros':{'valid_model_quantile_zero':zero_verified,'confirmed_source_nodata':zero_nodata,'still_unresolved':zero_still_unresolved},
            'original_negative_sentinels_confirmed_nodata':counts['legacy_sentinel_source_nodata_confirmed'],
            'legacy_center_interpretable_values_in_supplemental':counts['legacy_usable_matches_native']+zero_verified,
            'legacy_center_confirmed_nodata_records':source_nodata,
            'legacy_positive_values_matching_native':counts['legacy_usable_matches_native'],
            'prepared_files_modified':False,'comparison_status_counts':dict(counts),
            'native_subset_total_cells':sum(r['shape'][0]*r['shape'][1] for r in retrieved),
            'native_subset_valid_cells':sum(r['valid_cells'] for r in retrieved),
            'native_subset_nodata_cells':sum(r['nodata_cells'] for r in retrieved)},
        'anchors':anchor_summary,
        'zero_interpretation':'Valid cfvo Q0.05 zeros are lower prediction-quantile values with a valid native mask and source nodata=-32768; they are not observed absence of gravel. Other classified zero outputs correspond to explicit source nodata at the same coordinates.',
        'sources':{'core_properties':'Original public ISRIC GeoTIFF source tiles; bounded native-window reads.',
            'retention':'Public pre-release GeoTIFF URLs extracted from official ISRIC ISO records; source phase is retained.',
            'source_manifest':'native-source-manifest.json','catalog_evidence_manifest':'catalog-source-manifest.json',
            'direct_subset_checksums':'native-source-manifest.json records[].subset_sha256',
            'retention_metadata_records':{p:{'path':f'raw/retention-{p}-iso.xml','sha256':sha(RAW/f'retention-{p}-iso.xml')} for p in ['wv0010','wv0033','wv1500']},
            'full_global_raster_downloaded':False,'total_http_range_transfer_bytes':None,
            'range_transfer_note':'The window rasters are small; network range metadata/block bytes were not instrumented. No whole remote global TIFF was fetched.'},
        'gaps':[
            {'id':'native_source_holes','kind':'provider_nodata','status':'retained_not_imputed',
             'description':'The native grid has 7 masked cells per layer; the earlier geographic grid has 4 masked coordinate positions. Keep null/no-data for these locations; no nearest-valid or coarse fallback.'},
            {'id':'coverage_beyond_sample','kind':'public_extraction_not_performed','status':'not_acquired',
             'description':'This package covers only the bounded Klaten sample window; a new farm/location needs independent layer-specific extraction and QA.'},
            {'id':'retention_model_phase','kind':'source_limitation','status':'pre_release_label_retained',
             'description':'Retention source distribution is labelled pre-release; current field moisture, usable irrigation supply and calibrated profile water capacity are not inferred.'}],
        'needs_farmer':[
            'Verified field boundary/area and actual farm location',
            'Measured soil profile/test method/date, available P/K and salinity where relevant',
            'Rice water regime, drainage, irrigation availability and field management',
            'Actual crop/variety history and future planting/harvest dates',
            'Priorities, resource constraints, prices/costs/yields if later evaluating economics'],
        'validation':validation,
        'reproducibility':{'scripts_directory':'scripts/data/supplemental_soil',
            'order':['probe_soil_sources.py','direct_source_probe.py','inspect_source_catalog.py','collect_native_soil.py','finalize_soil_audit.py'],
            'runtime':'Python 3.12 with existing isolated rasterio/numpy vendor; no new packages installed',
            'read_only_prepared_manifest_sha256':integrity['manifest_sha256']}}
    write_json(OUT/'summary.json',summary)
    inventory=[]
    for path in sorted(OUT.rglob('*')):
        if path.is_file() and path.name!='file-manifest.json':
            inventory.append({'path':str(path.relative_to(ROOT)).replace('\\','/'),'bytes':path.stat().st_size,'sha256':sha(path)})
    write_json(OUT/'file-manifest.json',{'prepared_at_utc':NOW,'files':inventory,'total_bytes':sum(r['bytes'] for r in inventory)})
    print(json.dumps({'before':summary['before'],'after':summary['after'],'anchors':anchor_summary,
        'validation_pass':validation['pass'],'failed_checks':[k for k,v in checks.items() if not v],
        'files':len(inventory),'total_bytes':sum(r['bytes'] for r in inventory)},indent=2),flush=True)
    if not validation['pass']:raise SystemExit(1)

if __name__=='__main__':main()
