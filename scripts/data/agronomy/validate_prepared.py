"""Integrity and scientific-semantics checks for this prepared reference package."""
from pathlib import Path
import json, csv, hashlib, html, re
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'data/prepared/agronomy'
def read(name): return json.loads((OUT/name).read_text(encoding='utf-8'))
for f in OUT.rglob('*.json'): json.loads(f.read_text(encoding='utf-8'))
manifest=read('manifest.json')
summary=read('summary.json')
assert summary['farm_recommendation_ready'] is False and summary['economics_available'] is False
for item in manifest['files']:
 p=OUT/item['path']
 assert p.stat().st_size==item['bytes'],p
 assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],p

def leaves(value):
 if isinstance(value,dict):
  for v in value.values(): yield from leaves(v)
 elif isinstance(value,list):
  for v in value: yield from leaves(v)
 else: yield value
farm=read('farm-input-template.json')['farm']
assert all(v is None for v in leaves(farm)),'Invented farm value'
assert len(list(leaves(farm)))==len(read('farm-input-data-dictionary.json')['fields'])
strategies=read('strategy-comparison-template.json')
assert strategies['economics_available'] is False and strategies['ranking'] is None
assert [s['strategy_id'] for s in strategies['strategies']]==['existing','candidate_1','candidate_2']
assert all(s['rotation_sequence'] is None and s['net_income_idr_ha'] is None for s in strategies['strategies'])
evidence=read('source-evidence.json')
ids={s['id'] for s in evidence['sources']}
assert len(ids)==len(evidence['sources']),'Duplicate source identifiers'
sources={s['id']:s for s in evidence['sources']}
for source in evidence['sources']:
 if source.get('evidence_excerpt'):
  raw=(OUT/source['path']).read_text(encoding='utf-8',errors='replace')
  clean=html.unescape(re.sub('<[^>]+>',' ',raw))
  normalize=lambda s:re.sub(r'\s+',' ',s).strip().casefold()
  assert normalize(source['evidence_excerpt']) in normalize(clean),source['id']
crops=read('crop-reference.json')['crops']
assert {c['crop_id'] for c in crops}=={'padi','jagung','kedelai'}
for c in crops:
 for field in ['species_temperature_optimum_c','species_soil_ph_optimum','species_annual_rainfall_optimum_mm_year','seasonal_crop_water_need_indicative_mm']:
  assert c[field]['source_id'] in ids
  assert c[field]['min']<=c[field]['max']
 assert c['local_variety_reference']['source_id'] in ids
 assert c['seasonal_crop_water_need_indicative_mm']['local_gross_irrigation_mm'] is None
csvrows=list(csv.DictReader((OUT/'crop-reference.csv').open(encoding='utf-8')))
assert len(csvrows)==3
for c in read('agronomy-rules.json')['rules']:
 assert all(s in ids for s in c['source_ids']),c['id']
 assert c['numeric_effect'] is None
g=read('gaez-baseline-point.json')
legend={int(i['quantity']):i['label'] for i in read('sources/gaez-six-legend.json')['colorMap']['items']}
cropdim=read('sources/gaez-crop-res05.json')['members']
assert {k:cropdim[k]['caption'] for k in ['RCW','MZE','SOY']}=={'RCW':'Wetland rice','MZE':'Maize','SOY':'Soybean'}
assert len(g['rows'])==12
for r in g['rows']:
 assert r['status']=='pixel_extracted'
 assert '.HP0120.AGERA5.HIST.' in r['layer_code']
 assert r['class_label']==legend[r['raw_value']]
 assert r['continuous_suitability_score'] is None
 b=r['pixel_bounds']; p=r['requested_point']
 assert b['west']<=p['longitude']<b['east'] and b['south']<p['latitude']<=b['north']
 assert r['tiff_metadata']['33550'][:2]==[1/12,1/12]
assert {r['raw_value'] for r in g['rows'] if r['requested_point']['longitude']==110.37}=={7}
assert manifest['storage_bytes_excluding_manifest']<20_000_000
print(json.dumps({'status':'passed','manifest_files_checked':len(manifest['files']),'farm_unknown_fields_checked':len(list(leaves(farm))),'crop_rows':len(crops),'gaez_samples_checked':len(g['rows']),'continuous_scores_inferred':False},indent=2))
