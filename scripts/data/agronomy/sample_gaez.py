"""Extract a single historical-model GAEZ pixel using bounded HTTP ranges.
Only metadata/header and one compressed TIFF tile per layer are requested.
"""
from pathlib import Path
import urllib.request, urllib.parse, json, io, datetime, zlib, math, struct
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'data/prepared/agronomy'
SRC=OUT/'sources'

def get(url,limit=500000):
 with urllib.request.urlopen(url,timeout=25) as r:
  b=r.read(limit+1)
  if len(b)>limit: raise ValueError('response exceeded bound')
  return b

def rangeget(url,start,end):
 req=urllib.request.Request(url,headers={'Range':f'bytes={start}-{end}'})
 with urllib.request.urlopen(req,timeout=25) as r:
  if r.status!=206: raise ValueError('server did not honor Range; full file not downloaded')
  b=r.read(end-start+2)
  if len(b)!=end-start+1: raise ValueError('unexpected range size')
  return b,dict(r.headers)

def metadata():
 for name,url in {
 'gaez-crop-dimension':'https://io.apps.fao.org/gismgr/api/v2/catalog/workspaces/GAEZ-V5/mapsets/RES05-SIX/dimensions/CROP-RES05/members',
 'gaez-mapset':'https://io.apps.fao.org/gismgr/api/v2/catalog/workspaces/GAEZ-V5/mapsets/RES05-SIX',
 }.items():
  try:
   d=get(url); (SRC/(name+'.json')).write_bytes(d); print(name,d.decode()[:12000])
  except Exception as e: print(name,'ERROR',str(e))

def sample(crop,management,lon=110.37,lat=-7.8):
 code=f'GAEZ-V5.RES05-SIX.HP0120.AGERA5.HIST.{crop}.{management}'
 base='https://storage.googleapis.com/fao-gismgr-gaez-v5-data/DATA/GAEZ-V5/MAPSET/RES05-SIX/'+code
 row={'layer_code':code,'url':base+'.tif','requested_point':{'longitude':lon,'latitude':lat,'crs':'EPSG:4326'},'processed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'download_mode':'HTTP Range: TIFF header and one tile only; cached source subsets reused when present','status':'failed'}
 try:
  meta_path=SRC/(code+'.json')
  raw=meta_path.read_bytes() if meta_path.exists() else get(base+'.json',3000); meta_path.write_bytes(raw)
  row['layer_metadata']=json.loads(raw)
  head_path=SRC/(code+'.header.bin')
  if head_path.exists(): head,headers=head_path.read_bytes(),{'Content-Range':'cached bytes 0-65535'}
  else: head,headers=rangeget(base+'.tif',0,65535); head_path.write_bytes(head)
  img=Image.open(io.BytesIO(head)); tags={int(k):v for k,v in img.tag_v2.items()}
  row['tiff_metadata']={str(k):v for k,v in tags.items() if k not in [320,324,325]}
  scale=tags[33550]; tie=tags[33922]
  col=math.floor((lon-tie[3])/scale[0]+tie[0]); y=math.floor((tie[4]-lat)/scale[1]+tie[1])
  tw,th=tags[322],tags[323]; nx=math.ceil(tags[256]/tw)
  tileidx=(y//th)*nx+(col//tw); offset=tags[324][tileidx]; length=tags[325][tileidx]
  tile_path=SRC/(code+f'.tile-{tileidx}.bin')
  legacy_tile_path=SRC/(code+'.tile.bin')
  reference_tileidx=(math.floor((tie[4]-(-7.8))/scale[1])//th)*nx+(math.floor((110.37-tie[3])/scale[0])//tw)
  if not tile_path.exists() and legacy_tile_path.exists() and tileidx==reference_tileidx:
   tile_path.write_bytes(legacy_tile_path.read_bytes())
  if tile_path.exists(): tile,tileheaders=tile_path.read_bytes(),{'Content-Range':f'cached bytes {offset}-{offset+length-1}'}
  else: tile,tileheaders=rangeget(base+'.tif',offset,offset+length-1); tile_path.write_bytes(tile)
  row['source_snapshot_written_at_utc']={'header':datetime.datetime.fromtimestamp(head_path.stat().st_mtime,datetime.timezone.utc).isoformat(),'tile':datetime.datetime.fromtimestamp(legacy_tile_path.stat().st_mtime if legacy_tile_path.exists() and tileidx==reference_tileidx else tile_path.stat().st_mtime,datetime.timezone.utc).isoformat()}
  row['retrieval_timing_note']='Snapshot file-write times locate initial bounded retrieval; processed_at is local extraction time and is not a claim of a fresh network request.'
  compression=tags.get(259,1)
  decoded=zlib.decompress(tile) if compression in [8,32946] else tile if compression==1 else None
  if compression==5:
   # Wrap the one LZW tile as a standalone strip TIFF. Pillow/libtiff decodes it.
   entries={256:(4,tw),257:(4,th),258:(3,8),259:(3,5),262:(3,1),273:(4,0),277:(3,1),278:(4,th),279:(4,len(tile)),284:(3,1),317:(3,tags.get(317,1))}
   entries[273]=(4,8+2+12*len(entries)+4)
   ifd=struct.pack('<H',len(entries))
   for tag,(typ,val) in sorted(entries.items()): ifd+=struct.pack('<HHI',tag,typ,1)+(struct.pack('<H',val)+b'\0\0' if typ==3 else struct.pack('<I',val))
   wrapped=b'II'+struct.pack('<HI',42,8)+ifd+struct.pack('<I',0)+tile
   decoded=Image.open(io.BytesIO(wrapped)).tobytes()
  if decoded is None: raise ValueError(f'unsupported compression {compression}')
  bits=tags[258][0] if isinstance(tags[258],tuple) else tags[258]
  dtype={8:'u1',16:'<u2' if head[:2]==b'II' else '>u2',32:'<u4' if head[:2]==b'II' else '>u4'}[bits]
  arr=np.frombuffer(decoded,dtype=dtype).reshape(th,tw)
  if tags.get(317,1)==2 and compression!=5: arr=np.cumsum(arr,axis=1,dtype=arr.dtype)
  elif tags.get(317,1)!=1: raise ValueError('unsupported predictor')
  value=int(arr[y%th,col%tw]); nodata=tags.get(42113)
  legend_path=SRC/'gaez-six-legend.json'
  labels={int(x['quantity']):x['label'] for x in json.loads(legend_path.read_text())['colorMap']['items']} if legend_path.exists() else {}
  row.update(status='pixel_extracted',raw_value=value,class_label=labels.get(value),continuous_suitability_score=None,legend_source='https://storage.googleapis.com/fao-gismgr-gaez-v5-data/DATA/GAEZ-V5/STYLE/GAEZ-V5.SIX.json',nodata_tag=nodata,pixel_index={'column':col,'row':y},pixel_bounds={'west':tie[3]+col*scale[0],'east':tie[3]+(col+1)*scale[0],'north':tie[4]-y*scale[1],'south':tie[4]-(y+1)*scale[1]},bytes_in_source_subset=len(head)+len(tile)+len(raw),range_headers={'header':headers.get('Content-Range'),'tile':tileheaders.get('Content-Range')},units='categorical_GAEZ_SIX_legend_code',interpretation_status='historical_model_class_only; not observed or recommended farm suitability')
 except Exception as e: row['error']=str(e)
 return row

if __name__=='__main__':
 import sys
 if '--metadata' in sys.argv: metadata()
 else:
  import concurrent.futures
  jobs=[(c,m,lon,lat) for lon,lat in [(110.37,-7.8),(110.55,-7.72)] for c in ['RCW','MZE','SOY'] for m in ['HRLM','HILM']]
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
   rows=list(pool.map(lambda args:sample(*args),jobs))
  (OUT/'gaez-baseline-point.json').write_text(json.dumps({'schema_version':'1.0','sample_is_verified_farm':False,'period':'2001-2020','climate':'AgERA5','scenario':'HIST','spatial_resolution_degrees':1/12,'use':'historical coarse-grid reference only; never current field recommendation','rows':rows},indent=2),encoding='utf-8')
  print(json.dumps([{k:v for k,v in r.items() if k in ['layer_code','status','raw_value','error','bytes_downloaded','pixel_index','pixel_bounds']} for r in rows],indent=2))
