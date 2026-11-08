"""Validate acquired sample rasters and produce combined metadata catalog."""
from __future__ import annotations
import csv, hashlib, json, pathlib, sys, urllib.request
from prepare_soil_terrain import OUT, RAW, PROC, PROPERTIES, DEPTHS, dump, ACCESSED
import numpy as np
import rasterio

def load(name):return json.loads((OUT/name).read_text(encoding='utf-8'))

def main():
    soil=load('summary-soil.json');terrain=load('summary-terrain.json')
    soil_manifest=load('manifest-soil.json')
    arrays={};grids=[];bounds_issues=[];quantile=[];texture=[];water=[]
    for rec in soil_manifest['records']:
        if rec['status'] not in ['usable_subset','downloaded_zero_only_unresolved']:continue
        with rasterio.open(OUT/rec['file']) as ds:
            a=ds.read(1);scale=rec['scale_divisor']
            # Preserve ambiguous zeros as NaN for interpretation, raw file remains unchanged.
            x=np.where((a>0)&(a!=-32768),a.astype(float)/scale,np.nan)
            arrays[(rec['property'],rec['depth'],rec['statistic'])]=x
            grids.append((ds.width,ds.height,str(ds.crs),tuple(ds.transform)))
            if rec['property'] in ['phh2o','sand','silt','clay','cfvo','wv0010','wv0033','wv1500']:
                upper=14 if rec['property']=='phh2o' else 100
                invalid=np.isfinite(x)&((x<0)|(x>upper))
                if invalid.any():bounds_issues.append({'file':rec['file'],'out_of_range_cells':int(invalid.sum())})
    for prop in PROPERTIES:
        for depth in DEPTHS:
            lo=arrays[(prop,depth,'Q0.05')];hi=arrays[(prop,depth,'Q0.95')]
            valid=np.isfinite(lo)&np.isfinite(hi)
            quantile.append({'property':prop,'depth':depth,'comparable_cells':int(valid.sum()),
                'q05_greater_than_q95':int((valid&(lo>hi)).sum())})
    for depth in DEPTHS:
        a=[arrays[(p,depth,'mean')] for p in ['sand','silt','clay']]
        valid=np.logical_and.reduce([np.isfinite(x) for x in a]);s=sum(a)
        texture.append({'depth':depth,'comparable_cells':int(valid.sum()),
            'sum_percent_min':float(np.nanmin(s[valid])),'sum_percent_max':float(np.nanmax(s[valid])),
            'sum_percent_mean':float(np.nanmean(s[valid])),
            'outside_99_5_to_100_5_percent':int((valid&((s<99.5)|(s>100.5))).sum())})
        a10=arrays[('wv0010',depth,'mean')];a33=arrays[('wv0033',depth,'mean')];a1500=arrays[('wv1500',depth,'mean')]
        valid=np.isfinite(a10)&np.isfinite(a33)&np.isfinite(a1500)
        water.append({'depth':depth,'comparable_cells':int(valid.sum()),
            'nonmonotonic_retention_cells':int((valid&((a10<a33)|(a33<a1500))).sum())})
    lc=load('landcover-summary.json')
    primary=load('modis-primary-footprint-landcover-summary.json')
    comparison=load('modis-footprint-landcover-summary.json')
    anchors={}
    for role,report in [('primary',primary),('comparison',comparison)]:
        anchors[role]={'sample_coordinate':report['sample_coordinate'],
            'worldcover_epoch':2021,'modis_reported_grid_footprint':True,
            'worldcover_stats':report['worldcover_stats_within_modis_pixel'],
            'footprint_report_file':'modis-primary-footprint-landcover-summary.json' if role=='primary' else 'modis-footprint-landcover-summary.json',
            'status':'crop-dominant mixed observation pixel; not a verified user farm'}
    lc['frozen_modis_anchors']=anchors
    dump(OUT/'landcover-summary.json',lc)
    with rasterio.open(RAW/'copernicus-dem-subset.tif') as ds:
        terrain['terrain']['downloaded_window_bbox_wgs84']=list(ds.bounds)
    with rasterio.open(PROC/'elevation-utm49s.tif') as ds:
        terrain['terrain']['analysis_bbox_utm49s_m']=list(ds.bounds)
    qa={'soil_grid_alignment':len(set(grids))==1,'raster_count':len(grids),
        'out_of_range_issues':bounds_issues,'quantile_ordering':quantile,
        'quantile_inversion_cells':sum(x['q05_greater_than_q95'] for x in quantile),
        'quantile_pairs_without_comparable_cells':[{'property':x['property'],'depth':x['depth']} for x in quantile if x['comparable_cells']==0],
        'texture_mean_closure':texture,'retention_mean_monotonicity':water,
        'zero_policy':'Zero values remain in raw files and raw_value CSV, but converted value is blank and qa_status=zero_unresolved. This conservative exclusion does not assert that every zero is source nodata.',
        'water_capacity_policy':'No volumetric-to-mass conversion or profile available-water storage computed. Retention estimates are not actual current moisture or an irrigation prescription.',
        'terrain':'Slope in degrees from metre-based UTM49S finite differences; outer edges excluded.',
        'landcover':'2021 epoch; classification uncertainty and subsequent changes; 250m square is a proxy, not exact MODIS footprint.'}
    dump(OUT/'quality-report.json',qa)
    combined={'prepared_utc':ACCESSED,'sample_region':'Yogyakarta–Klaten, Indonesia; unverified demonstration locations',
        'bbox_soil_terrain_wgs84':soil['bbox_wgs84'],'soil':soil['soil'],
        'terrain':terrain['terrain'],'landcover':lc,'frozen_observation_anchors':anchors,
        'qa':{'aligned_soil_grids':qa['soil_grid_alignment'],'quantile_inversion_cells':qa['quantile_inversion_cells'],
            'out_of_range_issues':len(bounds_issues),'retention_nonmonotonic_cells':sum(x['nonmonotonic_retention_cells'] for x in water)},
        'limitations':['SoilGrids predictions, not laboratory soil tests or live nutrient availability.',
            'Separate property predictions are not guaranteed to be jointly physically consistent; raw means retained without forced normalization.',
            'Predicted retention at fixed suctions is not measured irrigation capacity.',
            'Copernicus DSM includes canopy/buildings; NASADEM remains metadata-only in the earlier audit.',
            'Land-cover classification shows original Yogyakarta point is urban and original Klaten point tree-cover; use crop-dominant candidate only as labeled contextual sample.']}
    dump(OUT/'summary.json',combined)
    inv=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name!='manifest.json':
            b=p.read_bytes();inv.append({'path':str(p.relative_to(OUT)).replace('\\','/'),'bytes':len(b),
                'sha256':hashlib.sha256(b).hexdigest()})
    manifest={'prepared_utc':ACCESSED,'soil_sources':soil_manifest['records'],
        'terrain_source':load('manifest-terrain.json')['records'],
        'landcover_source':{'url':lc['source_url'],'epoch':2021,'stac_url':lc['stac_source_url']},
        'documentation_sources':[
            {'url':'https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html','file':'raw/soilgrids-faq.html'},
            {'url':'https://docs.isric.org/globaldata/soilgrids/wcs.html','file':'raw/soilgrids-wcs.html'},
            {'url':'https://planetarycomputer.microsoft.com/api/stac/v1/collections/cop-dem-glo-30','file':'raw/cop-dem-collection.json'},
            *load('documentation-manifest.json')['sources']],
        'runtime':{'python':sys.version,'rasterio':rasterio.__version__,'numpy':np.__version__},
        'inventory':inv,'inventory_bytes':sum(r['bytes'] for r in inv),
        'network_note':'Only small WCS GeoTIFF subsets and windowed COG reads. Total remote COG range-transfer bytes were not measured; no global raster archive was downloaded.'}
    dump(OUT/'manifest.json',manifest)
    print(json.dumps({'soil':soil['soil'],'qa':combined['qa'],'texture':texture,'water':water,
        'inventory_files':len(inv),'inventory_bytes':manifest['inventory_bytes']},indent=2),flush=True)

if __name__=='__main__':main()
