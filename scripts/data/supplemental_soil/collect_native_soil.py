"""Audit legacy values against bounded reads of original native SoilGrids tiles.

No prepared file is changed. This does not impute or rewrite the earlier WCS
product: the output is a separate native-grid source with explicit nodata.
"""
from __future__ import annotations
import concurrent.futures as futures
import csv,hashlib,json,math,pathlib,sys
import xml.etree.ElementTree as ET
from probe_soil_sources import ROOT,OUT,RAW,NOW,write_json
import numpy as np
import rasterio
from rasterio.warp import transform,transform_bounds
from rasterio.windows import Window,from_bounds

PROPERTIES={'phh2o':(10,'pH'),'sand':(10,'% mass'),'silt':(10,'% mass'),
    'clay':(10,'% mass'),'soc':(10,'g/kg'),'nitrogen':(100,'g/kg'),
    'cec':(10,'cmol(c)/kg'),'bdod':(100,'g/cm3'),'cfvo':(10,'% volume'),
    'wv0010':(10,'% volume'),'wv0033':(10,'% volume'),'wv1500':(10,'% volume')}
DEPTHS=['0-5cm','5-15cm','15-30cm','30-60cm','60-100cm']
STATISTICS=['mean','Q0.05','Q0.95']
BASE=ROOT/'data/prepared/soil-terrain'
LEGACY=list(csv.DictReader((BASE/'processed/soil-cells.csv').open(encoding='utf-8')))
SUMMARY=json.loads((BASE/'summary.json').read_text(encoding='utf-8'))
BBOX=SUMMARY['bbox_soil_terrain_wgs84']
ANCHORS=SUMMARY['frozen_observation_anchors']
PROC=OUT/'processed';PROC.mkdir(exist_ok=True)
TILES=RAW/'native';TILES.mkdir(exist_ok=True)

def original_hashes():
    manifest=json.loads((ROOT/'data/prepared/file-manifest.json').read_text(encoding='utf-8-sig'))
    mismatches=[]
    for entry in manifest['files']:
        if hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest()!=entry['sha256']:
            mismatches.append(entry['path'])
    return {'files':len(manifest['files']),'mismatches':mismatches,
        'manifest_sha256':hashlib.sha256((ROOT/'data/prepared/file-manifest.json').read_bytes()).hexdigest()}

def compare_status(old,native,nodata):
    source_missing=nodata is not None and native==nodata
    if old['qa_status']=='usable_prediction':
        return 'legacy_usable_native_nodata' if source_missing else (
            'legacy_usable_matches_native' if int(old['raw_value'])==native else 'legacy_usable_differs_native_do_not_substitute')
    if old['raw_value']=='0':
        return 'legacy_zero_source_nodata_at_coordinate' if source_missing else (
            'legacy_zero_native_zero_verified' if native==0 else 'legacy_zero_native_nonzero_at_coordinate')
    return 'legacy_sentinel_source_nodata_confirmed' if source_missing else 'legacy_sentinel_native_valid_at_coordinate'

def task(spec):
    prop,depth,stat=spec
    coverage=f'{prop}_{depth}_{stat}'
    # Source directory snapshots show a different file subdivision for these
    # two properties; retain each source transform instead of assuming a grid.
    tile_part='1-3' if prop in {'phh2o','bdod'} else '1-4'
    url=f'https://files.isric.org/soilgrids/latest/data/{prop}/{coverage}/tileSG-021-071/tileSG-021-071_{tile_part}.tif'
    if prop.startswith('wv'):
        metadata=ET.fromstring((RAW/f'retention-{prop}-iso.xml').read_bytes())
        urls=[node.text for node in metadata.iter() if node.tag.endswith('}URL') and node.text and node.text.endswith(f'/{coverage}.tif')]
        if len(urls)!=1:raise ValueError(f'Expected exactly one official native URL for {coverage}')
        url=urls[0]
    path=TILES/f'{coverage}.tif'
    rec={'property':prop,'depth':depth,'statistic':stat,'source_url':url,'accessed_at_utc':NOW,
        'subset_file':str(path.relative_to(OUT)).replace('\\','/')}
    try:
        meta_path=path.with_suffix('.source.json')
        if path.exists() and meta_path.exists():
            source=json.loads(meta_path.read_text(encoding='utf-8'))
        else:
            with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif',GDAL_HTTP_TIMEOUT='40',GDAL_HTTP_MAX_RETRY='1'):
                with rasterio.open(url) as ds:
                    b=transform_bounds('EPSG:4326',ds.crs,*BBOX,densify_pts=21)
                    win=from_bounds(*b,ds.transform)
                    left,top=math.floor(win.col_off),math.floor(win.row_off)
                    right,bottom=math.ceil(win.col_off+win.width),math.ceil(win.row_off+win.height)
                    win=Window(left,top,right-left,bottom-top)
                    if left<0 or top<0 or right>ds.width or bottom>ds.height:
                        raise ValueError('Requested bbox crosses native source file coverage; no silent nearest fallback')
                    a=ds.read(1,window=win)
                    profile=ds.profile.copy();profile.update(width=a.shape[1],height=a.shape[0],
                        transform=ds.window_transform(win),driver='GTiff',tiled=False,compress='deflate')
                    profile.pop('blockxsize',None);profile.pop('blockysize',None)
                    with rasterio.open(path,'w',**profile) as target:target.write(a,1)
                    source={'url':url,'accessed_at_utc':NOW,'source_shape':[ds.height,ds.width],
                        'source_transform':list(ds.transform),'source_bounds':list(ds.bounds),
                        'source_crs_wkt':ds.crs.to_wkt(),'source_nodata_tag':ds.nodata,
                        'source_tags':ds.tags(),'window_native_pixels':[left,top,right-left,bottom-top],
                        'read_method':'Original TIFF window read, no reprojection/interpolation; output retains source grid and nodata tag.',
                        'remote_full_file_sha256':None,
                        'checksum_note':'Subset bytes are hashed; complete remote source raster was not downloaded or hashed.'}
            write_json(meta_path,source)
        rows=[];anchor_rows=[]
        selected=[r for r in LEGACY if (r['property'],r['depth'],r['statistic'])==spec]
        with rasterio.open(path) as ds:
            a=ds.read(1);mask=ds.read_masks(1)
            points=[(float(r['longitude']),float(r['latitude'])) for r in selected]
            coordinates=transform('EPSG:4326',ds.crs,[p[0] for p in points],[p[1] for p in points])
            divisor,unit=PROPERTIES[prop]
            for old,x,y in zip(selected,*coordinates):
                row,col=ds.index(x,y)
                if not 0<=row<ds.height or not 0<=col<ds.width:raise ValueError('legacy center outside native subset')
                native=int(a[row,col]);valid=bool(mask[row,col])
                rows.append({'property':prop,'depth':depth,'statistic':stat,
                    'legacy_row':old['row'],'legacy_col':old['col'],'longitude':old['longitude'],'latitude':old['latitude'],
                    'legacy_raw_value':old['raw_value'],'legacy_qa_status':old['qa_status'],
                    'native_subset_row':row,'native_subset_col':col,'native_raw_value':native,
                    'native_mask_valid':valid,'native_value':native/divisor if valid else '',
                    'unit':unit,'comparison_status':compare_status(old,native,ds.nodata),'source_url':url})
            for role,anchor in ANCHORS.items():
                point=anchor['sample_coordinate'];lon,lat=point['longitude'],point['latitude']
                x,y=transform('EPSG:4326',ds.crs,[lon],[lat]);row,col=ds.index(x[0],y[0]);v=int(a[row,col]);valid=bool(mask[row,col])
                anchor_rows.append({'location_role':role,'longitude':lon,'latitude':lat,'property':prop,'depth':depth,
                    'statistic':stat,'native_subset_row':row,'native_subset_col':col,'native_raw_value':v,
                    'native_mask_valid':valid,'value':v/divisor if valid else '', 'unit':unit,
                    'qa_status':'source_valid_model_quantile_zero' if valid and v==0 else ('source_valid_prediction' if valid else 'source_nodata'),
                    'source_url':url,'source_support':'native250m_model_cell_not_farm_measurement'})
            rec.update(status='retrieved',nodata_tag=ds.nodata,shape=[ds.height,ds.width],
                transform=list(ds.transform),crs_wkt=ds.crs.to_wkt(),bounds=list(ds.bounds),
                native_grid_250m=bool(ds.transform.a==250 and ds.transform.e==-250),
                valid_cells=int((mask>0).sum()),nodata_cells=int((mask==0).sum()),
                valid_zero_cells=int(((a==0)&(mask>0)).sum()),subset_bytes=path.stat().st_size,
                subset_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        return rec,rows,anchor_rows
    except Exception as e:
        rec.update(status='failed',error=str(e));return rec,[],[]

def write_csv(name,rows):
    if rows:
        with (PROC/name).open('w',newline='',encoding='utf-8') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def main():
    before=original_hashes();assert not before['mismatches'],before
    specs=[(p,d,s) for p in PROPERTIES for d in DEPTHS for s in STATISTICS]
    records=[];rows=[];anchors=[]
    with futures.ThreadPoolExecutor(max_workers=3) as pool:
        for rec,points,point_anchors in pool.map(task,specs):
            records.append(rec);rows.extend(points);anchors.extend(point_anchors)
            print(rec['property'],rec['depth'],rec['statistic'],rec['status'],flush=True)
            write_json(OUT/'native-progress.json',records)
    write_csv('legacy-centers-native-audit.csv',rows)
    write_csv('anchor-native-profiles.csv',anchors)
    after=original_hashes();assert before==after,(before,after)
    write_json(OUT/'native-source-manifest.json',{'prepared_at_utc':NOW,'records':records,
        'prepared_integrity_before':before,'prepared_integrity_after':after})
    print(json.dumps({'requested':len(specs),'retrieved':sum(r['status']=='retrieved' for r in records),
        'center_audit_rows':len(rows),'anchor_rows':len(anchors),'integrity':after},indent=2),flush=True)

if __name__=='__main__':main()
