"""Acquire bounded public SoilGrids and Copernicus DEM samples (no app code)."""
from __future__ import annotations
import concurrent.futures as futures
import csv, datetime as dt, hashlib, json, math, pathlib, sys, time
import urllib.parse, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
if (HERE / '_vendor').exists():
    sys.path.insert(0, str(HERE / '_vendor'))
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling, transform_bounds
from rasterio.windows import from_bounds

ROOT = HERE.parents[2]
OUT = ROOT / 'data/prepared/soil-terrain'
RAW = OUT / 'raw'
PROC = OUT / 'processed'
for p in (RAW, PROC): p.mkdir(parents=True, exist_ok=True)
BBOX = [110.54, -7.73, 110.56, -7.71]
DEPTHS = ['0-5cm', '5-15cm', '15-30cm', '30-60cm', '60-100cm']
# SoilGrids FAQ table: mapped integer / conversion factor = conventional unit.
PROPERTIES = {
    'phh2o': (10, 'pH', 'pH in water'),
    'sand': (10, '% mass', 'sand fraction'),
    'silt': (10, '% mass', 'silt fraction'),
    'clay': (10, '% mass', 'clay fraction'),
    'soc': (10, 'g/kg', 'soil organic carbon concentration'),
    'nitrogen': (100, 'g/kg', 'total nitrogen concentration; not plant-available N'),
    'cec': (10, 'cmol(c)/kg', 'cation exchange capacity'),
    'bdod': (100, 'g/cm3', 'bulk density of fine earth'),
    'cfvo': (10, '% volume', 'coarse fragments'),
    'wv0010': (10, '% volume', 'predicted volumetric water content at 10 kPa suction'),
    'wv0033': (10, '% volume', 'predicted volumetric water content at 33 kPa suction'),
    'wv1500': (10, '% volume', 'predicted volumetric water content at 1500 kPa suction'),
}
DOCS = {
    'soilgrids-faq.html': 'https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html',
    'soilgrids-wcs.html': 'https://docs.isric.org/globaldata/soilgrids/wcs.html',
}
ACCESSED = dt.datetime.now(dt.timezone.utc).isoformat()
records = []

def dump(path, obj): path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding='utf-8')

def fetch(url, target, cap=10_000_000):
    if target.exists(): return target.read_bytes(), 'cached'
    error = None
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'FieldShift-data-preparation/1.0'})
            with urllib.request.urlopen(req, timeout=45) as r:
                content = r.read(cap + 1)
                if len(content) > cap: raise ValueError('bounded download limit exceeded')
            target.write_bytes(content)
            return content, 'downloaded'
        except Exception as e:
            error = e
            if attempt == 0: time.sleep(2)
    raise error

def soil_task(spec):
    prop, depth, stat = spec
    coverage = f'{prop}_{depth}_{stat}'
    url = ('https://maps.isric.org/mapserv?' + urllib.parse.urlencode([
        ('map', f'/map/{prop}.map'), ('SERVICE','WCS'),('VERSION','2.0.1'),
        ('REQUEST','GetCoverage'),('COVERAGEID',coverage),('FORMAT','GEOTIFF_INT16'),
        ('SUBSET', f'X({BBOX[0]},{BBOX[2]})'),('SUBSET', f'Y({BBOX[1]},{BBOX[3]})'),
        ('SUBSETTINGCRS','http://www.opengis.net/def/crs/EPSG/0/4326'),
        ('OUTPUTCRS','http://www.opengis.net/def/crs/EPSG/0/4326'),
        ('INTERPOLATION','NEAREST')]))
    path = RAW / f'{coverage}.tif'
    rec = {'property':prop,'depth':depth,'statistic':stat,'source_url':url,
           'accessed_utc':ACCESSED,'file':str(path.relative_to(OUT)).replace('\\','/')}
    try:
        content, status = fetch(url, path, 100_000)
        if content[:2] not in (b'II',b'MM'):
            raise ValueError('response is not a TIFF: '+content[:200].decode(errors='replace'))
        with rasterio.open(path) as ds:
            arr = ds.read(1)
            nodata = ds.nodata
            # Output lacks nodata on older endpoint examples. Do not silently call zero nodata.
            mask = np.isfinite(arr) & (arr != -32768)
            if nodata is not None: mask &= arr != nodata
            unresolved_zero = int(np.count_nonzero(mask & (arr == 0)))
            # Conservatively omit all ambiguous zeros from interpretation, preserve raw values.
            usable = mask & (arr != 0)
            scale, unit, desc = PROPERTIES[prop]
            vals = arr[usable].astype(float) / scale
            sample_rows=[]
            for row in range(ds.height):
                for col in range(ds.width):
                    lon, lat = ds.xy(row,col)
                    v=int(arr[row,col]); good=bool(usable[row,col])
                    sample_rows.append({'property':prop,'depth':depth,'statistic':stat,
                        'row':row,'col':col,'longitude':lon,'latitude':lat,
                        'raw_value':v,'value':v/scale if good else '',
                        'unit':unit,'qa_status':'usable_prediction' if good else ('zero_unresolved' if v==0 else 'nodata')})
            rec.update(status='usable_subset' if vals.size else 'downloaded_zero_only_unresolved',download_status=status,bytes=len(content),
                sha256=hashlib.sha256(content).hexdigest(),width=ds.width,height=ds.height,
                crs=str(ds.crs),transform=list(ds.transform),nodata_tag=nodata,
                grid_cells=int(arr.size),usable_cells=int(usable.sum()),zero_unresolved=unresolved_zero,
                scale_divisor=scale,unit=unit,description=desc,
                min=float(vals.min()) if vals.size else None,
                max=float(vals.max()) if vals.size else None,
                mean=float(vals.mean()) if vals.size else None)
        return rec,sample_rows
    except Exception as e:
        rec.update(status='failed',error=str(e))
        return rec,[]

def prepare_soil():
    for name,url in DOCS.items():
        try:
            body, _ = fetch(url, RAW / name)
            print('docs',name,len(body),flush=True)
        except Exception as e: print('docs failed',name,str(e),flush=True)
    specs=[(p,d,s) for s in ['mean','Q0.05','Q0.95'] for p in PROPERTIES for d in DEPTHS]
    rows=[]
    with futures.ThreadPoolExecutor(max_workers=3) as pool:
        for rec, sample_rows in pool.map(soil_task,specs):
            records.append(rec);rows.extend(sample_rows)
            print('soil',rec['property'],rec['depth'],rec['statistic'],rec['status'],flush=True)
            dump(OUT/'soil-download-progress.json',records)
    if rows:
        with (PROC/'soil-cells.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    valid=[r for r in records if r['status'] in ['usable_subset','downloaded_zero_only_unresolved']]
    if valid:
        cols=['property','depth','statistic','unit','scale_divisor','grid_cells','usable_cells',
            'zero_unresolved','min','mean','max','file']
        with (PROC/'soil-summary.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(valid)
    return {'status':'downloaded' if len(valid)==len(specs) else 'partial',
        'properties':list(PROPERTIES),'depths':DEPTHS,'statistics':['mean','Q0.05','Q0.95'],
        'successful_rasters':len(valid),'requested_rasters':len(specs),
        'interpretable_nonzero_rasters':sum(r['status']=='usable_subset' for r in valid),
        'zero_only_unresolved_rasters':sum(r['status']=='downloaded_zero_only_unresolved' for r in valid),
        'cell_records':len(rows),'numeric_cells':sum(r['usable_cells'] for r in valid),
        'unresolved_zeros':sum(r['zero_unresolved'] for r in valid),
        'download_bytes':sum(r['bytes'] for r in valid)}

def prepare_terrain():
    stac_url='https://planetarycomputer.microsoft.com/api/stac/v1/search?'+urllib.parse.urlencode({
        'collections':'cop-dem-glo-30','bbox':','.join(map(str,BBOX)),'limit':3})
    data,_=fetch(stac_url,RAW/'cop-dem-stac.json')
    obj=json.loads(data)
    features=obj.get('features',[])
    if not features: raise ValueError('no Copernicus DEM STAC features found')
    item=features[0]
    asset=item['assets']['data']['href']
    # Public AWS mirror: same Copernicus DSM COG tile; obtain exact tile id from STAC metadata.
    tile=item['id']
    if not tile.startswith('Copernicus_DSM_COG_'):
        tile=pathlib.PurePosixPath(urllib.parse.urlparse(asset).path).parent.name
    aws=f'https://copernicus-dem-30m.s3.amazonaws.com/{tile}/{tile}.tif'
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',
        CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif',GDAL_HTTP_TIMEOUT='45',
        GDAL_HTTP_MAX_RETRY='1',VSI_CACHE='TRUE'):
        with rasterio.open(aws) as src:
            b=transform_bounds('EPSG:4326',src.crs,*BBOX)
            win=from_bounds(*b,transform=src.transform).round_offsets().round_lengths()
            # One cell padding allows metric slope derivation near requested boundary.
            win=rasterio.windows.Window(max(win.col_off-1,0),max(win.row_off-1,0),win.width+2,win.height+2)
            arr=src.read(1,window=win,masked=True)
            trans=src.window_transform(win)
            profile=src.profile.copy();profile.update(width=arr.shape[1],height=arr.shape[0],transform=trans,
                tiled=False,compress='deflate',driver='GTiff')
            profile.pop('blockxsize',None);profile.pop('blockysize',None)
            with rasterio.open(RAW/'copernicus-dem-subset.tif','w',**profile) as dst: dst.write(arr.filled(src.nodata or -32767),1)
            dst_crs='EPSG:32749' # WGS84 / UTM zone 49S, local metre grid.
            t,w,h=calculate_default_transform(src.crs,dst_crs,arr.shape[1],arr.shape[0],
                *rasterio.transform.array_bounds(arr.shape[0],arr.shape[1],trans),resolution=30)
            dem=np.full((h,w),np.nan,dtype=np.float32)
            reproject(arr.filled(np.nan).astype(np.float32),dem,src_transform=trans,src_crs=src.crs,
                src_nodata=np.nan,dst_transform=t,dst_crs=dst_crs,dst_nodata=np.nan,
                resampling=Resampling.bilinear)
    dy,dx=np.gradient(dem,30.0,30.0)
    slope=np.degrees(np.arctan(np.hypot(dx,dy)))
    # Do not retain one-sided finite-difference slopes at exterior edges.
    slope[[0,-1],:]=np.nan;slope[:,[0,-1]]=np.nan
    metric={'driver':'GTiff','width':w,'height':h,'count':1,'dtype':'float32','crs':dst_crs,
        'transform':t,'nodata':np.nan,'compress':'deflate'}
    for name,a in [('elevation-utm49s.tif',dem),('slope-degrees-utm49s.tif',slope)]:
        with rasterio.open(PROC/name,'w',**metric) as dst:dst.write(a.astype('float32'),1)
    out={'status':'downloaded','source_product':'Copernicus DEM GLO-30 DSM (not NASADEM)',
        'source_url':aws,'stac_source_url':stac_url,'stac_id':item['id'],
        'accessed_utc':ACCESSED,'license':'Copernicus DEM license; attribution required',
        'native_crs':str(profile['crs']),'analysis_crs':dst_crs,'analysis_resolution_m':30,
        'subset_shape':list(arr.shape),'analysis_shape':[h,w],
        'elevation_m':{'min':float(np.nanmin(dem)),'mean':float(np.nanmean(dem)),'max':float(np.nanmax(dem)),
            'valid_cells':int(np.isfinite(dem).sum())},
        'slope_degrees':{'min':float(np.nanmin(slope)),'mean':float(np.nanmean(slope)),
            'max':float(np.nanmax(slope)),'valid_cells':int(np.isfinite(slope).sum())},
        'method':'Windowed COG read; bilinear reprojection of elevation to UTM49S 30m; slope atan(sqrt((dz/dx)^2+(dz/dy)^2)) with centered finite differences; edge slopes omitted.',
        'caveat':'DSM includes vegetation/buildings; not a surveyed bare-earth farm elevation. Sample bbox is not a verified farm boundary. No resampling creates extra independent detail.'}
    records.append({'kind':'terrain',**out})
    return out

def main():
    mode=sys.argv[1] if len(sys.argv)>1 else 'all'
    summary={'prepared_utc':ACCESSED,'bbox_wgs84':BBOX,'sample_location':'Rural Klaten; not verified user farm'}
    if mode in ['all','soil']:
        summary['soil']=prepare_soil()
    if mode in ['all','terrain']:
        try:summary['terrain']=prepare_terrain()
        except Exception as e:
            summary['terrain']={'status':'failed','error':str(e)}
            print('terrain failed',str(e),flush=True)
    dump(OUT/('summary-'+mode+'.json'),summary)
    dump(OUT/('manifest-'+mode+'.json'),{'prepared_utc':ACCESSED,'records':records})
    print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__': main()
