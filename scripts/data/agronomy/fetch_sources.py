"""Bounded, public source snapshots for the agronomy reference. No account required."""
from pathlib import Path
import urllib.request, urllib.parse, json, datetime, hashlib, concurrent.futures

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'data/prepared/agronomy/sources'
OUT.mkdir(parents=True,exist_ok=True)
MAX_TOTAL=20_000_000
SOURCES={
 'gaez-user-guide.md':'https://raw.githubusercontent.com/wiki/un-fao/gaezv5/21.-GAEZ-v5-Platform-User-Guide.md',
 'gaez-theme4-mapping.xlsx':'https://github.com/user-attachments/files/21917536/_readme_RES05.xlsx',
 'gaez-crops.md':'https://raw.githubusercontent.com/wiki/un-fao/gaezv5/14.-Appendix-4%E2%80%901-Crops.md',
 'fao-water-needs.html':'https://www.fao.org/4/s2022e/s2022e02.htm',
 'fao-seasonal-water.html':'https://www.fao.org/4/s2022e/s2022e07.htm',
 'fao-paddy-irrigation.html':'https://www.fao.org/4/t7202e/t7202e07.htm',
 'fao-maize.html':'https://www.fao.org/land-water/databases-and-software/crop-information/maize/',
 'fao-soybean.html':'https://www.fao.org/land-water/databases-and-software/crop-information/soybean/',
 'kementan-inpari32.html':'https://sulbar.brmp.pertanian.go.id/berita/brmp-sulawesi-barat-dampingi-penanaman-varietas-unggul-inpari-32-hdb-di-desa-bumiayu',
 'kementan-anjasmoro.html':'https://pustaka.bppsdmp.pertanian.go.id/index-berita/varietas-anjasmoro-si-kedelai-biji-besar',
 'kementan-jakarin.html':'https://diy.brmp.pertanian.go.id/berita/kunjungan-kepala-bpsi-serealia-ke-ip2sip-banyakan',
 'kementan-siap-tanam.html':'https://brmp.pertanian.go.id/index.php/layanan/layanan-elektronik/siap-tanam',
 'fao-aquacrop-inputs.html':'https://www.fao.org/aquacrop/overview/input-requirements/',
 'fao-crop-rotation.html':'https://www.fao.org/conservation-agriculture/in-practice/species-diversification/en/',
 'gaez-crop-list.xlsx':'https://github.com/user-attachments/files/25523134/Appendix.4-1.List.of.Crops.xlsx',
}

def fetch(item):
 name,url=item
 when=datetime.datetime.now(datetime.timezone.utc).isoformat()
 row={'id':name.rsplit('.',1)[0],'url':url,'accessed_at_utc':when,'path':'sources/'+name}
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'FieldShift-data-audit/1.0'})
  with urllib.request.urlopen(req,timeout=35) as response:
   data=response.read(3_000_001)
   if len(data)>3_000_000: raise ValueError('individual-source limit 3MB')
   row.update(status='downloaded',http_status=response.status,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),final_url=response.url)
  (OUT/name).write_bytes(data)
 except Exception as exc: row.update(status='failed',error=str(exc))
 return row

if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool: rows=list(pool.map(fetch,SOURCES.items()))
 (OUT/'source-download-log.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
 print(json.dumps(rows,indent=2))
