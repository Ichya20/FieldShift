"""Snapshot public directory/service metadata relevant to missing-value semantics."""
import json,re,urllib.parse
from probe_soil_sources import OUT,RAW,download,write_json,NOW,records

def main():
    obs=[]
    urls={
        'soilgrids-data-index.html':'https://files.isric.org/soilgrids/latest/data/',
        'soilgrids-root-index.html':'https://files.isric.org/soilgrids/',
        'soilgrids-latest-index.html':'https://files.isric.org/soilgrids/latest/',
        'phh2o-tile-index.html':'https://files.isric.org/soilgrids/latest/data/phh2o/phh2o_0-5cm_mean/',
        'phh2o-local-tile-index.html':'https://files.isric.org/soilgrids/latest/data/phh2o/phh2o_0-5cm_mean/tileSG-021-071/',
        'retention-map-describe.xml':'https://maps.isric.org/mapserv?'+urllib.parse.urlencode({
            'map':'/map/wv0033.map','SERVICE':'WCS','VERSION':'2.0.1','REQUEST':'DescribeCoverage','COVERAGEID':'wv0033_0-5cm_mean'}),
        'soilgrids-properties.html':'https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html',
        'wcs-docs.html':'https://docs.isric.org/globaldata/soilgrids/wcs.html',
        'retention-wv0033-page.html':'https://maps.isric.org/generated/soilgrids/wv0033.html',
        'retention-wv0033-iso.xml':'https://data.isric.org/geonetwork/srv/api/records/14e7c761-6f87-4f4c-9035-adb282439a44/formatters/xml',
        'retention-wv0010-iso.xml':'https://data.isric.org/geonetwork/srv/api/records/c6cb5073-78dd-4d8d-be81-9d546a1c004f/formatters/xml',
        'retention-wv1500-iso.xml':'https://data.isric.org/geonetwork/srv/api/records/f5a1188a-09f8-4ef6-b841-93f08e3903f4/formatters/xml',
    }
    for name,url in urls.items():
        try:
            body,path=download(url,name,cap=250_000)
            text=body.decode(errors='replace')
            obs.append({'file':name,'hrefs':re.findall(r'href="([^"]+)"',text) if 'index' in name else [],
                'text_excerpt':re.sub(r'<[^>]*>',' ',text)[:1000] if name.endswith('.xml') else None})
        except Exception as e:obs.append({'url':url,'error':str(e)})
    write_json(OUT/'catalog-observations.json',obs)
    write_json(OUT/'catalog-source-manifest.json',{'prepared_at_utc':NOW,'records':records})
    print(json.dumps(obs,indent=2),flush=True)

if __name__=='__main__':main()
