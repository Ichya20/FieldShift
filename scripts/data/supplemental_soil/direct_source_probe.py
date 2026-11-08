"""Locate one native SoilGrids tile using bounded remote header reads."""
from __future__ import annotations
import json,pathlib,re,sys,urllib.parse
from probe_soil_sources import ROOT,OUT,RAW,download,write_json,NOW,records
import rasterio
from rasterio.warp import transform

def main():
    results=[]
    url='https://files.isric.org/soilgrids/latest/data/cfvo/cfvo_0-5cm_Q0.05/tileSG-021-071/'
    try:
        body,path=download(url,'cfvo-Q05-tile-directory-021-071.html')
        names=[v for v in re.findall(r'href="([^"]+)"',body.decode(errors='replace')) if v.endswith('.tif')]
    except Exception as e:
        results.append({'url':url,'error':str(e)});names=['tileSG-021-071_1-4.tif']
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif',GDAL_HTTP_TIMEOUT='30'):
        for name in names:
            source=urllib.parse.urljoin(url,name)
            try:
                with rasterio.open(source) as ds:
                    x,y=transform('EPSG:4326',ds.crs,[110.55354472008753],[-7.721875031299882])
                    contains=ds.bounds.left<=x[0]<ds.bounds.right and ds.bounds.bottom<y[0]<=ds.bounds.top
                    result={'source_url':source,'shape':[ds.height,ds.width],'nodata_tag':ds.nodata,
                        'crs_wkt':ds.crs.to_wkt(),'transform':list(ds.transform),'bounds':list(ds.bounds),
                        'contains_primary':contains}
                    if contains:
                        result['primary_value']=float(list(ds.sample([(x[0],y[0])]))[0][0])
                    results.append(result)
                    if contains:break
            except Exception as e:results.append({'source_url':source,'error':str(e)})
    write_json(OUT/'direct-source-probe.json',{'prepared_at_utc':NOW,'results':results})
    write_json(OUT/'direct-probe-source-manifest.json',{'prepared_at_utc':NOW,'records':records})
    print(json.dumps(results,indent=2),flush=True)

if __name__=='__main__':main()
