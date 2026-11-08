"""Bounded checks of source nodata and native-CRS SoilGrids extractions."""
from __future__ import annotations
import csv,datetime as dt,hashlib,json,pathlib,re,sys,urllib.parse,urllib.request

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'scripts/data/soil-terrain/_vendor'))
import rasterio
from rasterio.warp import transform_bounds

OUT=ROOT/'data/supplemental/soil-terrain'
RAW=OUT/'raw'
RAW.mkdir(parents=True,exist_ok=True)
NOW=dt.datetime.now(dt.timezone.utc).isoformat()
records=[]
BBOX=[110.54,-7.73,110.56,-7.71]

def write_json(path,obj):path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')

def download(url,name,cap=200_000,byte_range=None):
    p=RAW/name
    if p.exists():
        body=p.read_bytes();status='cached';headers={}
    else:
        head={'User-Agent':'FieldShift-supplemental-data-audit/1.0'}
        if byte_range:head['Range']=byte_range
        with urllib.request.urlopen(urllib.request.Request(url,headers=head),timeout=40) as response:
            body=response.read(cap+1);status=response.status;headers=dict(response.headers)
        if len(body)>cap:raise ValueError('Bounded response limit exceeded')
        p.write_bytes(body)
    records.append({'url':url,'path':str(p.relative_to(OUT)).replace('\\','/'),'accessed_at_utc':NOW,
        'http_status':status,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'range_requested':byte_range,
        'content_type':headers.get('Content-Type'),'content_range':headers.get('Content-Range')})
    return body,p

def coverage_url(prop,depth,stat,native):
    crs='http://www.opengis.net/def/crs/EPSG/0/'+('152160' if native else '4326')
    return 'https://maps.isric.org/mapserv?'+urllib.parse.urlencode([
        ('map',f'/map/{prop}.map'),('SERVICE','WCS'),('VERSION','2.0.1'),('REQUEST','GetCoverage'),
        ('COVERAGEID',f'{prop}_{depth}_{stat}'),('FORMAT','GEOTIFF_INT16'),
        ('SUBSET',f'X({BBOX[0]},{BBOX[2]})'),('SUBSET',f'Y({BBOX[1]},{BBOX[3]})'),
        ('SUBSETTINGCRS','http://www.opengis.net/def/crs/EPSG/0/4326'),('OUTPUTCRS',crs),
        ('INTERPOLATION','NEAREST')])

def main():
    observations=[]
    sources=[
        ('cfvo-Q05-head.xml','https://files.isric.org/soilgrids/latest/data/cfvo/cfvo_0-5cm_Q05.vrt'),
        ('cfvo-Q0.05-head.xml','https://files.isric.org/soilgrids/latest/data/cfvo/cfvo_0-5cm_Q0.05.vrt'),
        ('cfvo-index.html','https://files.isric.org/soilgrids/latest/data/cfvo/'),
    ]
    for name,url in sources:
        try:
            body,path=download(url,name,cap=100_000,byte_range='bytes=0-8191' if name.endswith('.xml') else None)
            text=body.decode(errors='replace')
            observations.append({'source':name,'nodata':re.findall(r'<NoDataValue>(.*?)</NoDataValue>',text),
                'statistics_min':re.findall(r'<MDI key="STATISTICS_MINIMUM">(.*?)</MDI>',text),
                'depth_0_5_links':[v for v in re.findall(r'href="([^"]+)"',text) if '0-5cm' in v][:20]})
        except Exception as e: observations.append({'source':name,'error':str(e)})
    for prop,depth,stat in [('phh2o','0-5cm','mean'),('cfvo','0-5cm','Q0.05'),('wv0033','0-5cm','mean')]:
        name=f'{prop}_{depth}_{stat}-native.tif'
        try:
            body,path=download(coverage_url(prop,depth,stat,True),name)
            with rasterio.open(path) as ds:
                a=ds.read(1)
                observations.append({'source':name,'shape':list(a.shape),'crs':str(ds.crs),'crs_wkt':ds.crs.to_wkt(),
                    'transform':list(ds.transform),'bounds':list(ds.bounds),'nodata_tag':ds.nodata,
                    'min':int(a.min()),'max':int(a.max()),'zeros':int((a==0).sum()),
                    'negative_sentinel':int((a==-32768).sum()),'values':a.tolist()})
        except Exception as e:observations.append({'source':name,'error':str(e)})
    rows=list(csv.DictReader((ROOT/'data/prepared/soil-terrain/processed/soil-cells.csv').open(encoding='utf-8')))
    observations.append({'legacy_negative_records':[{k:r[k] for k in ['property','depth','statistic','row','col','raw_value']} for r in rows if r['raw_value']=='-32768']})
    write_json(OUT/'probe-observations.json',observations)
    write_json(OUT/'probe-source-manifest.json',{'prepared_at_utc':NOW,'records':records})
    print(json.dumps(observations,indent=2),flush=True)

if __name__=='__main__':main()
