"""Bounded ESA WorldCover 2021 context for unverified sample coordinates."""
from __future__ import annotations
import json, math, pathlib, sys, urllib.parse, urllib.request
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'_vendor'))
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform, transform_bounds
from prepare_soil_terrain import RAW, PROC, OUT, dump, ACCESSED, fetch, records

CLASSES={10:'Tree cover',20:'Shrubland',30:'Grassland',40:'Cropland',50:'Built-up',
    60:'Bare / sparse vegetation',70:'Snow and ice',80:'Permanent water bodies',
    90:'Herbaceous wetland',95:'Mangroves',100:'Moss and lichen',0:'No data'}
SITES=[{'id':'klaten','lat':-7.72,'lon':110.55,'bbox':[110.54,-7.73,110.56,-7.71]},
    {'id':'yogyakarta','lat':-7.8,'lon':110.37,'bbox':[110.36,-7.81,110.38,-7.79]}]

def stats(arr):
    vals,c=np.unique(arr,return_counts=True)
    hist={str(int(v)):{'label':CLASSES.get(int(v),'unknown'),'cells':int(n)} for v,n in zip(vals,c)}
    valid=int(np.count_nonzero(arr!=0))
    return {'grid_cells':int(arr.size),'valid_cells':valid,'class_histogram':hist,
        'cropland_fraction_valid_cells':float(np.count_nonzero(arr==40)/valid) if valid else None,
        'built_up_fraction_valid_cells':float(np.count_nonzero(arr==50)/valid) if valid else None}

def main():
    url='https://planetarycomputer.microsoft.com/api/stac/v1/search?'+urllib.parse.urlencode({
        'collections':'esa-worldcover','bbox':'110.36,-7.81,110.56,-7.71',
        'datetime':'2021-01-01T00:00:00Z/2021-12-31T23:59:59Z','limit':3})
    b,_=fetch(url,RAW/'worldcover-stac.json')
    obj=json.loads(b)
    if not obj.get('features'):raise RuntimeError('No WorldCover 2021 STAC record')
    item=obj['features'][0]
    # Public AWS distribution is documented by the ESA WorldCover team.
    tile='S09E108'
    aws=f'https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{tile}_Map.tif'
    rec={'status':'downloaded','product':'ESA WorldCover 2021 v200','epoch':2021,
        'source_url':aws,'stac_source_url':url,'stac_id':item['id'],'accessed_utc':ACCESSED,
        'license':'CC BY 4.0','attribution':'ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium',
        'class_codes':CLASSES,'sites':[],
        'caveat':'2021 classified land cover, with classification error and possible subsequent land-use change; not verified farm boundaries or actual crop species. Centered 250m square is contextual, not the exact MODIS footprint.'}
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif',GDAL_HTTP_TIMEOUT='45'):
        with rasterio.open(aws) as src:
            for site in SITES:
                b=transform_bounds('EPSG:4326',src.crs,*site['bbox'])
                win=from_bounds(*b,src.transform).round_offsets().round_lengths()
                a=src.read(1,window=win)
                profile=src.profile.copy();profile.update(width=a.shape[1],height=a.shape[0],
                    transform=src.window_transform(win),driver='GTiff',tiled=False,compress='deflate')
                profile.pop('blockxsize',None);profile.pop('blockysize',None)
                with rasterio.open(RAW/f"worldcover-2021-{site['id']}.tif",'w',**profile) as dst:dst.write(a,1)
                x,y=transform('EPSG:4326',src.crs,[site['lon']],[site['lat']])
                code=int(list(src.sample([(x[0],y[0])]))[0][0])
                ux,uy=transform('EPSG:4326','EPSG:32749',[site['lon']],[site['lat']])
                sq=transform_bounds('EPSG:32749',src.crs,ux[0]-125,uy[0]-125,ux[0]+125,uy[0]+125)
                small=src.read(1,window=from_bounds(*sq,src.transform).round_offsets().round_lengths())
                site_rec={**site,'point_class_code':code,'point_class_label':CLASSES[code],
                    'bbox_stats':stats(a),'centered_250m_square_stats':stats(small)}
                if site['id']=='klaten':
                    # Pick a crop-dominant contextual sample, never a user farm boundary.
                    mask=(a==40).astype(int)
                    integral=np.pad(mask,((1,0),(1,0))).cumsum(0).cumsum(1)
                    n=27
                    sums=integral[n:,n:]-integral[:-n,n:]-integral[n:,:-n]+integral[:-n,:-n]
                    candidates=np.argwhere(sums==sums.max())
                    row,col=min(candidates.tolist(),key=lambda rc:(rc[0]+n//2-a.shape[0]/2)**2+(rc[1]+n//2-a.shape[1]/2)**2)
                    lon,lat=rasterio.transform.xy(src.window_transform(win),row+n//2,col+n//2)
                    ux,uy=transform('EPSG:4326','EPSG:32749',[lon],[lat])
                    bounds=transform_bounds('EPSG:32749',src.crs,ux[0]-125,uy[0]-125,ux[0]+125,uy[0]+125)
                    cw=from_bounds(*bounds,src.transform).round_offsets().round_lengths()
                    ca=src.read(1,window=cw)
                    cp=profile.copy();cp.update(width=ca.shape[1],height=ca.shape[0],transform=src.window_transform(cw))
                    with rasterio.open(RAW/'worldcover-2021-klaten-candidate250m.tif','w',**cp) as dst:dst.write(ca,1)
                    candidate_code=int(list(src.sample([(lon,lat)]))[0][0])
                    site_rec['cropland_context_candidate']={'latitude':lat,'longitude':lon,
                        'selection':'Highest WorldCover2021 crop count in a 27x27-cell window inside Klaten bbox; tie nearest bbox center. This is a candidate demonstration sample, not a verified farm.',
                        'nominal_square_size_m':250,'class_code':candidate_code,'square_stats':stats(ca)}
                rec['sites'].append(site_rec)
    dump(OUT/'landcover-summary.json',rec)
    print(json.dumps(rec,indent=2),flush=True)

if __name__=='__main__':main()
