"""Classify WorldCover cell centers within the reported MODIS sinusoidal pixel."""
from __future__ import annotations
import hashlib,json,pathlib,sys
from prepare_soil_terrain import ROOT,RAW,PROC,OUT,dump,ACCESSED
from prepare_landcover import CLASSES,stats
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import transform_geom

def main():
    primary=len(sys.argv)>1 and sys.argv[1]=='primary'
    primary_raw=ROOT/'data/prepared/vegetation/raw/klaten_cropland_primary-A2021001-A2021145.json'
    raw=(primary_raw if primary_raw.exists() else RAW/'modis-primary-grid-check.json') if primary else ROOT/'data/prepared/vegetation/raw/klaten_cropland_candidate-A2021001-A2021145.json'
    meta=json.loads(raw.read_text(encoding='utf-8'))
    x=float(meta['xllcorner']);y=float(meta['yllcorner']);s=float(meta['cellsize'])
    assert meta['ncols']==1 and meta['nrows']==1,'Expected exactly one pixel'
    # Densify before projection to retain curved sinusoidal geographic edges.
    xy=[]
    corners=[(x,y),(x+s,y),(x+s,y+s),(x,y+s),(x,y)]
    for a,b in zip(corners[:-1],corners[1:]):
        for t in np.linspace(0,1,17)[:-1]:xy.append([a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])])
    xy.append(xy[0])
    sinu='+proj=sinu +R=6371007.181 +nadgrids=@null +wktext'
    geo=transform_geom(sinu,'EPSG:4326',{'type':'Polygon','coordinates':[xy]},precision=10)
    with rasterio.open(RAW/'worldcover-2021-klaten.tif') as ds:
        a=ds.read(1)
        mask=geometry_mask([geo],out_shape=a.shape,transform=ds.transform,invert=True,all_touched=False)
        vals=a[mask]
        result=stats(vals)
        point_code=int(list(ds.sample([(meta['longitude'],meta['latitude'])]))[0][0])
        # Raw landcover values within pixel, with zero outside, not new resampling.
        profile=ds.profile.copy();profile.update(nodata=0)
        masked_name='worldcover-2021-modis-primary-footprint.tif' if primary else 'worldcover-2021-modis-candidate-footprint.tif'
        with rasterio.open(PROC/masked_name,'w',**profile) as dst:
            dst.write(np.where(mask,a,0).astype(a.dtype),1)
    report={'prepared_utc':ACCESSED,'location_role':('primary' if primary else 'comparison')+' demonstration pixel, not a farm boundary',
        'sample_coordinate':{'latitude':meta['latitude'],'longitude':meta['longitude']},
        'worldcover_point_class_code':point_code,'worldcover_point_class_label':CLASSES[point_code],
        'modis_metadata_file':str(raw.relative_to(ROOT)).replace('\\','/'),
        'modis_metadata_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),
        'modis_source_url':meta['header'],
        'sinusoidal_crs':sinu,'sinusoidal_bounds_m':[x,y,x+s,y+s],
        'sinusoidal_cellsize_m':s,'nominal_product_resolution_m':250,
        'worldcover_epoch':2021,'worldcover_stats_within_modis_pixel':result,
        'method':'Densify 1x1 REST-reported sinusoidal pixel edges (16 segments/edge), project to WGS84 sphere R=6371007.181, then count native WorldCover cells whose centers lie inside polygon; no all-touched expansion.',
        'limitations':'WorldCover2021 classification is uncertain and land use may have changed. Class fractions use native grid cell counts; geographic cell areas vary negligibly across this small pixel. This is no claim of farm ownership, field extent, current crop species, or collection version of REST MODIS service.'}
    dump(OUT/('modis-primary-footprint-landcover-summary.json' if primary else 'modis-footprint-landcover-summary.json'),report)
    dump(PROC/('modis-primary-pixel-footprint.geojson' if primary else 'modis-candidate-pixel-footprint.geojson'),{'type':'FeatureCollection','features':[
        {'type':'Feature','geometry':geo,'properties':{'role':'MODIS observation pixel footprint; not farm boundary','source':meta['header'],
            'cropland_fraction_worldcover2021':result['cropland_fraction_valid_cells']}}]})
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
