"""Bounded official-source snapshots; never changes prepared data."""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
from urllib.request import Request, urlopen
import json, re
from html import unescape

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'data/supplemental/agronomy'
SOURCES = [
 ('kementan-anjasmoro-descriptor', 'https://applypvt.pertanian.go.id/storage/deskripsi_varietas_yang_sama/DESKRIPSI_VARIETAS_YANG_SAMA_B933907B-97F0-4BE7-AAF5-6AABC732CE2C.pdf', 'pdf'),
 ('kementan-lakin-2023', 'https://ppid.pertanian.go.id/doc/108/LAKIN%202023%20FINAL%20ir.pdf', 'pdf'),
 ('kementan-variety-catalog', 'https://tanamanpangan.bsip.pertanian.go.id/storage/assets/uploads/publikasi/c9a6fj01bn2mX7D8LXFss08241GY6qw5J7tPJS2F.pdf', 'pdf'),
 ('kementan-variety-catalog-brmp', 'https://tanamanpangan.brmp.pertanian.go.id/storage/assets/uploads/publikasi/c9a6fj01bn2mX7D8LXFss08241GY6qw5J7tPJS2F.pdf', 'pdf'),
 ('fao-rice-ecosystems', 'https://www.fao.org/4/ai408e/ai408e05.htm', 'html'),
 ('fao-rice-phase-water-regimes', 'https://www.fao.org/4/ac800e/ac800e05.htm', 'html'),
]
def main():
    target = OUT / 'sources'
    target.mkdir(parents=True, exist_ok=True)
    records, total = [], 0
    for sid, url, ext in SOURCES:
        path = target / f'{sid}.{ext}'
        rec = dict(id=sid, url=url, accessed_at_utc=datetime.now(timezone.utc).isoformat(), path=path.relative_to(ROOT).as_posix())
        try:
            if path.exists():
                data = path.read_bytes()
                rec.update(status='cached_snapshot', final_url=url)
            else:
                with urlopen(Request(url, headers={'User-Agent':'FieldShift-reference-audit/0.1'}), timeout=45) as response:
                    data = response.read(8_000_001)
                    if len(data)>8_000_000 or total+len(data)>20_000_000:
                        raise ValueError('bounded download limit exceeded')
                    rec.update(status='downloaded', http_status=response.status, final_url=response.url)
                path.write_bytes(data)
            total += len(data)
            rec.update(bytes=len(data), sha256=sha256(data).hexdigest())
            if ext=='pdf':
                from pypdf import PdfReader
                reader=PdfReader(path)
                rec['pages']=len(reader.pages)
                hits=[]
                for i,page in enumerate(reader.pages):
                    t=page.extract_text() or ''
                    if 'anjasmoro' in t.lower():
                        hits.append({'page_1_based':i+1,'text':t})
                text_path=target/f'{sid}-relevant-pages.json'
                text_path.write_text(json.dumps(hits,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
                rec['text_extraction_path']=text_path.relative_to(ROOT).as_posix()
            else:
                t=data.decode('utf8',errors='replace')
                t=re.sub(r'<(script|style)\b[^>]*>.*?</\1>',' ',t,flags=re.I|re.S)
                t=unescape(re.sub(r'<[^>]+>',' ',t))
                t=re.sub(r'\s+',' ',t).strip()
                (target/f'{sid}.txt').write_text(t+'\n',encoding='utf8')
        except Exception as exc:
            rec.update(status='failed',error=str(exc))
        records.append(rec)
        print(sid,rec['status'],rec.get('bytes'),rec.get('pages'))
    (OUT/'source-snapshots.json').write_text(json.dumps({'download_budget_bytes':20_000_000,'downloaded_or_cached_bytes':total,'sources':records},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
if __name__=='__main__': main()
