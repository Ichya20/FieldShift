"""Snapshot official documentation and the frozen primary sample's grid header."""
import concurrent.futures as futures
import json,urllib.request,urllib.parse
from prepare_soil_terrain import OUT,RAW,PROPERTIES,fetch,dump,ACCESSED

def source_header(prop):
    url=f'https://files.isric.org/soilgrids/latest/data/{prop}/{prop}_0-5cm_mean.vrt'
    path=RAW/f'{prop}-source-vrt-head.xml'
    try:
        req=urllib.request.Request(url,headers={'Range':'bytes=0-8191','User-Agent':'FieldShift-data-preparation/1.0'})
        with urllib.request.urlopen(req,timeout=25) as r:
            b=r.read(8192);status=r.status
        path.write_bytes(b)
        return {'url':url,'file':str(path.relative_to(OUT)).replace('\\','/'),
            'accessed_utc':ACCESSED,'status':status,'bytes':len(b),'partial':True,
            'notes':'Only first8192bytes; source VRT may be incomplete XML. Range header requested.'}
    except Exception as e:return {'url':url,'status':'failed','error':str(e)}

def main():
    recs=list(futures.ThreadPoolExecutor(max_workers=3).map(source_header,PROPERTIES))
    docs={'copernicus-dem-aws-registry.html':'https://registry.opendata.aws/copernicus-dem/',
        'worldcover-data-access.html':'https://esa-worldcover.org/en/data-access',
        'worldcover-collection.json':'https://planetarycomputer.microsoft.com/api/stac/v1/collections/esa-worldcover'}
    for name,url in docs.items():
        try:
            b,status=fetch(url,RAW/name)
            recs.append({'url':url,'file':'raw/'+name,'accessed_utc':ACCESSED,'status':status,'bytes':len(b)})
        except Exception as e:recs.append({'url':url,'status':'failed','error':str(e)})
    url='https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset?'+urllib.parse.urlencode({
        'latitude':-7.721875031299882,'longitude':110.55354472008753,
        'startDate':'A2021001','endDate':'A2021001','kmAboveBelow':0,'kmLeftRight':0})
    b,status=fetch(url,RAW/'modis-primary-grid-check.json')
    d=json.loads(b)
    assert d.get('nrows')==1 and d.get('ncols')==1
    recs.append({'url':url,'file':'raw/modis-primary-grid-check.json','status':status,'accessed_utc':ACCESSED,'bytes':len(b)})
    dump(OUT/'documentation-manifest.json',{'prepared_utc':ACCESSED,'sources':recs})
    print(json.dumps(recs,indent=2),flush=True)

if __name__=='__main__':main()
