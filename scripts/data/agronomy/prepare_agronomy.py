"""Prepare cited agronomy reference and deliberately empty farm-input templates.

The CSV is a machine-readable reference table, not a formatted workbook.
This script does not generate agronomic recommendations or invent a farm.
"""
from pathlib import Path
import csv, json, hashlib, shutil, datetime, re, html
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'data/prepared/agronomy'
SRC=OUT/'sources'
NOW=datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

logs=[]
for f in SRC.glob('*download-log.json'): logs.extend(json.loads(f.read_text(encoding='utf-8')))
sources={}
for row in logs:
 key=row['id']+('-sld' if row['path'].endswith('.sld') else '')
 row['id']=key
 if key not in sources or row['status']=='downloaded': sources[key]=row

quotes={
 'fao-water-needs':'The water need of a crop thus consists of transpiration plus evaporation.',
 'fao-seasonal-water':'The values indicated in the table provide a rough estimate',
 'fao-paddy-irrigation':'from panicle initiation to flowering; duration approximately one month.',
 'fao-crop-rotation':'Crop rotation also has an important phytosanitary function',
 'kementan-inpari32':'masa panen sekitar 120 hari setelah semai',
 'kementan-anjasmoro':'sekitar 82 – 92 hari',
 'kementan-jakarin':'memiliki umur tanam 100 hst',
 'gaez-user-guide':'HP0120 for 2001-2020',
}
for key,q in quotes.items():
 if key in sources: sources[key]['evidence_excerpt']=q

for name,crop in [('rice','padi'),('maize','jagung'),('soybean','kedelai')]:
 source=ROOT/f'work/soil-crop/ecocrop-{name}.html'
 target=SRC/f'ecocrop-{name}.html'
 shutil.copyfile(source,target)
 ids={'rice':1574,'maize':2175,'soybean':1150}
 sources['ecocrop-'+name]={'id':'ecocrop-'+name,'url':f'https://ecocrop.apps.fao.org/ecocrop/srv/en/dataSheet?id={ids[name]}','path':'sources/'+target.name,'status':'inherited_local_snapshot','access_date':'2026-11-08','accessed_at_utc':None,'access_note':'Original audit snapshot; exact download timestamp not recorded. Copied without new network access.','sha256':digest(target),'bytes':target.stat().st_size,'provider':'FAO ECOCROP','limitations':['Historical species-level reference, original development discontinued around 2015.','Not a current local cultivar database.']}

old=list(csv.DictReader((ROOT/'work/soil-crop/crop-reference.csv').open(encoding='utf-8')))
mapping=[('padi','rice','RCW','Inpari 32 HDB',120,120,'sowing/semai','kementan-inpari32',(450,700)),('jagung','maize','MZE','Jakarin',100,100,'planting/HST','kementan-jakarin',(500,800)),('kedelai','soybean','SOY','Anjasmoro',82,92,'not_explicit_in_source','kementan-anjasmoro',(450,700))]
crops=[]
for row,info in zip(old,mapping):
 cid,eng,gaez,variety,dmin,dmax,start,vid,water=info
 ref='ecocrop-'+eng
 crops.append({
  'crop_id':cid,'common_name_id':row['crop'],'scientific_name':row['species'],'gaez_crop_code':gaez,
  'reference_status':'documented_generic_reference; local calibration required',
  'species_temperature_optimum_c':{'min':float(row['temp_opt_min_c']),'max':float(row['temp_opt_max_c']),'source_id':ref,'meaning':'historical ECOCROP species optimum; not a cultivar-specific heat threshold'},
  'species_soil_ph_optimum':{'min':float(row['soil_ph_opt_min']),'max':float(row['soil_ph_opt_max']),'source_id':ref,'measurement_basis':'source species reference; compare laboratory/SoilGrids pH only with method/depth caveats'},
  'species_annual_rainfall_optimum_mm_year':{'min':int(row['annual_rain_opt_min_mm']),'max':int(row['annual_rain_opt_max_mm']),'source_id':ref,'meaning':'ANNUAL rainfall climate descriptor; never seasonal irrigation demand'},
  'species_crop_cycle_reference_days':{'min':int(row['crop_cycle_min_days']),'max':int(row['crop_cycle_max_days']),'source_id':ref,'limitations':'Very broad historical species range; cannot schedule a local cultivar from this alone.'},
  'seasonal_crop_water_need_indicative_mm':{'min':water[0],'max':water[1],'source_id':'fao-seasonal-water','source_locator':'Section 3.3.4, Table 14','meaning':'Indicative crop evapotranspiration over total growing period; not gross irrigation, rainfall requirement, or field-specific prediction','status':'rough_planning_reference_only','local_seasonal_etc_mm':None,'local_net_irrigation_mm':None,'local_gross_irrigation_mm':None},
  'local_variety_reference':{'name':variety,'duration_days_min':dmin,'duration_days_max':dmax,'duration_start_event':start,'source_id':vid,'status':'illustrative_indonesian_variety_reference; not farmer-selected cultivar','limitations':'Approximate duration depends on location/environment/management. Obtain actual seed description and local advice; HST must not be conflated with rice transplanting or sowing dates.'},
  'phenology':{'source_id':'fao-paddy-irrigation' if cid=='padi' else 'fao-seasonal-water','stages':([{'id':'vegetative','description':'Sowing/germination to panicle initiation. Direct-seeded rice has no separate nursery. Transplanted rice includes a nursery phase before transplanting; record both sowing and transplant dates and preserve the origin date of any duration. The FAO irrigation manual lists nursery separately from its post-transplant vegetative stage.','duration_days':None},{'id':'reproductive','description':'Panicle initiation to flowering','duration_days':None},{'id':'ripening','description':'Flowering to maturity; includes grain growth','duration_days':None}] if cid=='padi' else [{'id':x,'duration_days':None} for x in ['initial','crop_development','mid_season_flowering_and_grain_setting','late_season_ripening']]),'local_stage_dates':None,'status':'stage_definition_only; no local phenology model calibrated'},
  'limitations':['No recommendation, expected yield, nitrogen credit, profit, or soil-health gain is inferred from these generic references.','Farmer dates/cultivar, irrigation capacity, soil profile and local validation remain necessary.']
 })
save('crop-reference.json',{'schema_version':'1.0','prepared_at_utc':NOW,'crops':crops})
fields=['crop_id','common_name_id','scientific_name','gaez_crop_code','temp_opt_min_c','temp_opt_max_c','ph_opt_min','ph_opt_max','annual_rainfall_opt_min_mm_year','annual_rainfall_opt_max_mm_year','seasonal_etc_indicative_min_mm','seasonal_etc_indicative_max_mm','variety_reference','duration_days_min','duration_days_max','duration_start_event','species_source_url','water_source_url','variety_source_url','status','caveat']
with (OUT/'crop-reference.csv').open('w',newline='',encoding='utf-8') as stream:
 writer=csv.DictWriter(stream,fieldnames=fields); writer.writeheader()
 for r in crops:
  e=r['species_temperature_optimum_c']; p=r['species_soil_ph_optimum']; a=r['species_annual_rainfall_optimum_mm_year']; w=r['seasonal_crop_water_need_indicative_mm']; v=r['local_variety_reference']
  writer.writerow(dict(crop_id=r['crop_id'],common_name_id=r['common_name_id'],scientific_name=r['scientific_name'],gaez_crop_code=r['gaez_crop_code'],temp_opt_min_c=e['min'],temp_opt_max_c=e['max'],ph_opt_min=p['min'],ph_opt_max=p['max'],annual_rainfall_opt_min_mm_year=a['min'],annual_rainfall_opt_max_mm_year=a['max'],seasonal_etc_indicative_min_mm=w['min'],seasonal_etc_indicative_max_mm=w['max'],variety_reference=v['name'],duration_days_min=v['duration_days_min'],duration_days_max=v['duration_days_max'],duration_start_event=v['duration_start_event'],species_source_url=sources[e['source_id']]['url'],water_source_url=sources[w['source_id']]['url'],variety_source_url=sources[v['source_id']]['url'],status='reference_only_not_farm_recommendation',caveat='Annual rain != seasonal ET != irrigation; historic species ranges and illustrative cultivar durations need local validation.'))

rules=[
 {'id':'water_balance','statement':'Distinguish crop ET, effective rainfall, soil storage, net irrigation and gross irrigation. Paddy accounting additionally needs land preparation/saturation, percolation/seepage and water-layer management.','source_ids':['fao-water-needs','fao-paddy-irrigation'],'requires':['planting dates and cultivar','daily climate and validated ETo','soil profile/available water','effective rainfall method','irrigation efficiency/capacity','paddy losses where applicable'],'status':'concept_documented_model_not_implemented','numeric_effect':None},
 {'id':'rotation_pest_break','statement':'Crop diversity can interrupt crop-specific pest and disease carry-over. Benefit requires the next crop to be a non-host for the identified local problem.','source_ids':['fao-crop-rotation'],'requires':['pest/pathogen identification','host range','history','local extension validation'],'status':'qualitative_conditional_evidence','numeric_effect':None},
 {'id':'legume_nitrogen','statement':'Symbiotic nitrogen fixation is a possible mechanism. Do not assign soybean a fixed nitrogen credit or fertilizer saving without nodulation, inoculation, biomass/residue fate and nutrient-balance evidence.','source_ids':['fao-crop-rotation'],'requires':['soil tests','nodulation/inoculation','residue retention/removal','grain/biomass N removal','fertilizer management'],'status':'qualitative_conditional_evidence','nitrogen_credit_kg_ha':None,'numeric_effect':None},
 {'id':'soil_health','statement':'Diversified rooting/residue inputs may affect soil processes; satellite greenness or a crop label does not measure improvement in soil organic carbon.','source_ids':['fao-crop-rotation'],'requires':['baseline soil tests','repeat sampling at matched depth/method','residue and tillage history','time horizon'],'status':'mechanism_only_no_local_effect_size','numeric_effect':None},
 {'id':'season_fit','statement':'Candidate crop sequences must fit observed sowing/harvest dates, cultivar durations, field preparation and water windows. Reference duration is not the farm calendar.','source_ids':['fao-water-needs','kementan-siap-tanam'],'requires':['farm rotation history','sowing/transplant/harvest dates','cultivar and management','irrigation availability','local calendar advice'],'status':'required_constraint_not_evaluated','numeric_effect':None},
 {'id':'rice_upland_transition','statement':'Paddy irrigation management cannot be carried unchanged to an upland crop. Check drainage and the ability to prepare/manage the next crop under local conditions.','source_ids':['fao-paddy-irrigation','fao-aquacrop-inputs'],'requires':['field drainage','soil profile','water table','irrigation control','locally validated non-rice management'],'status':'design_constraint_pending_local_validation','numeric_effect':None},
 {'id':'economic_comparison','statement':'Calculate net returns only from crop-specific expected marketable yield, farm-gate price, actual costs, labor/transport/storage and timing. Generic suitability and potential yield are not realized profit.','source_ids':[],'evidence_type':'application_accounting_requirement_not_empirical_agronomic_effect','requires':['price and buyer','marketable yield basis','cost records','currency/date','labor and sales constraints'],'status':'blocked_missing_farmer_and_market_inputs','profit_difference_idr_ha':None,'numeric_effect':None},
 {'id':'gaez_scale','statement':'GAEZ HIST suitability classes are long-term model/grid context, not live observations or a per-field recommendation. Never label class code 7 as 7/100.','source_ids':['gaez-user-guide','gaez-period','gaez-crop-res05','gaez-wsim-res05','gaez-six-legend'],'requires':['exact dimensions and legend','grid footprint','farmer field geometry','current conditions and local validation'],'status':'historical_context_available','numeric_effect':None},
 {'id':'crop_model_inputs','statement':'AquaCrop simulation needs climate, crop, soil profile/groundwater and management inputs; locally adapted crop parameters are still required.','source_ids':['fao-aquacrop-inputs'],'requires':['climate','crop parameters','soil profile','groundwater','irrigation and field management'],'status':'input_inventory_only_model_not_run','numeric_effect':None},
]
save('agronomy-rules.json',{'schema_version':'1.0','prepared_at_utc':NOW,'purpose':'Evidence and input requirements for a future analytical model; these are not computed recommendations.','automatic_rotation_ranking_ready':False,'rules':rules})

# Unknown farmer values are null, including missing history arrays. No fake farm.
template={
 'farm_id':None,'field_id':None,
 'location':{'geometry_geojson':None,'representative_longitude':None,'representative_latitude':None,'area_ha_reported':None,'area_ha_geometry':None,'village':None,'district':None,'province':None,'country_code':None,'boundary_recorded_at':None,'boundary_source':None},
 'current_crop':{'crop_id':None,'cultivar':None,'seed_source':None,'production_system':None,'sowing_date':None,'transplanting_date':None,'expected_harvest_date':None,'observed_growth_stage':None,'stage_observed_at':None},
 'rotation_history':None,
 'irrigation':{'system':None,'source':None,'rainfed':None,'availability_window_start':None,'availability_window_end':None,'capacity_m3_day':None,'allocation_m3_season':None,'application_efficiency_fraction':None,'water_cost_idr_m3':None,'drainage_condition':None,'water_table_depth_m':None,'flooding_history':None},
 'soil_lab':{'sampling_date':None,'laboratory':None,'method':None,'depth_top_cm':None,'depth_bottom_cm':None,'ph_h2o':None,'organic_carbon_percent':None,'total_n_percent':None,'available_p_mg_kg':None,'exchangeable_k_cmolc_kg':None,'ec_ds_m':None,'texture_class':None,'bulk_density_g_cm3':None,'field_capacity_fraction':None,'wilting_point_fraction':None,'rootable_depth_cm':None,'report_file':None},
 'management':{'tillage':None,'residue_fate':None,'fertilizer_history':None,'organic_amendments':None,'legume_inoculation':None,'nodulation_observations':None,'pest_disease_weed_history':None,'pesticide_history':None},
 'resources':{'labor_available_days_season':None,'machinery_access':None,'seed_access':None,'budget_idr_season':None},
 'market':{'buyer_access':None,'crop_preferences':None,'contract_constraints':None,'farm_gate_prices':None,'expected_marketable_yield_kg_ha':None,'transport_storage_costs':None,'currency':None,'price_observed_at':None},
 'costs':{'seed_idr_ha':None,'fertilizer_idr_ha':None,'pest_management_idr_ha':None,'labor_idr_ha':None,'machinery_idr_ha':None,'irrigation_idr_ha':None,'other_idr_ha':None,'reference_season':None},
 'priorities':{'water_saving_weight':None,'net_income_weight':None,'soil_health_weight':None,'risk_tolerance':None,'planning_horizon_start':None,'planning_horizon_end':None,'excluded_crops':None},
 'provenance':{'respondent_role':None,'recorded_at':None,'information_source':None,'local_extension_reviewed_at':None}
}
save('farm-input-template.json',{'schema_version':'1.0','is_template':True,'farm':template})
strategy_slot=lambda sid,role:{'strategy_id':sid,'role':role,'rotation_sequence':None,'crop_seasons':None,'source_history':None,'farmer_selected':None,'agronomy_reviewed_at':None,'water_outcome_mm':None,'soil_health_outcome':None,'expected_marketable_yield_kg_ha':None,'farm_gate_price_idr_kg':None,'costs_idr_ha':None,'net_income_idr_ha':None,'farmer_priority_weights':None,'economics_status':'unavailable_missing_farm_inputs','recommendation_status':'not_evaluated'}
save('strategy-comparison-template.json',{'schema_version':'1.0','is_template':True,'purpose':'Empty slots for comparison design; no actual or candidate rotation has been invented.','farm_id':None,'field_id':None,'strategies':[strategy_slot('existing','farmer_existing_rotation'),strategy_slot('candidate_1','candidate_pending_design_and_local_validation'),strategy_slot('candidate_2','candidate_pending_design_and_local_validation')],'ranking':None,'economics_available':False,'validated_farm_recommendation_available':False})
dictionary=[]
def walk(obj,prefix='farm'):
 for key,value in obj.items():
  path=prefix+'.'+key
  if isinstance(value,dict): walk(value,path)
  else:
   typ='number' if any(s in key for s in ['_ha','_m3','_percent','_fraction','_cm','_kg','_ds_','_weight','longitude','latitude','_m_','_days_','_idr_']) or key=='ph_h2o' or key.endswith('_m') else 'date_iso8601' if any(s in key for s in ['_date','_at','_start','_end']) else 'string_or_documented_array'
   if key=='rainfed': typ='boolean'
   if key=='geometry_geojson': typ='GeoJSON Polygon or MultiPolygon in WGS84 longitude,latitude order'
   units=next((unit for suffix,unit in [('_m3_day','m3/day'),('_m3_season','m3/season'),('_idr_m3','IDR/m3'),('_idr_ha','IDR/ha'),('_idr_season','IDR/season'),('_kg_ha','kg/ha'),('_mg_kg','mg/kg'),('_cmolc_kg','cmol(+)/kg'),('_g_cm3','g/cm3'),('_ds_m','dS/m'),('_ha','ha'),('_percent','percent'),('_cm','cm'),('_fraction','fraction 0..1'),('_weight','fraction 0..1'),('_m','m')] if key.endswith(suffix)),None)
   if key=='ph_h2o': units='pH measured in water (method required)'
   if key in ['representative_longitude','representative_latitude']: units='decimal degrees WGS84'
   dictionary.append({'path':path,'type_when_known':typ,'units':units,'missing_value':None,'zero_meaning':'Known zero only; never use zero for unknown','meaning':key.replace('_',' '),'source_required':'farmer record / measurement / named local adviser with observation date','validation':'Nonnegative where a quantity; weights/efficiency/fractions 0..1; date meaning and units must be preserved.'})
walk(template)
save('farm-input-data-dictionary.json',{'schema_version':'1.0','crs':'EPSG:4326; GeoJSON coordinates [longitude,latitude]','null_semantics':'unknown or not yet collected; never assumed zero, false, empty history, or nonexistent irrigation','history_record_shape':{'crop_id':None,'cultivar':None,'sowing_date':None,'transplanting_date':None,'harvest_date':None,'yield_kg_ha':None,'yield_moisture_basis':None,'irrigation_system':None,'pests':None,'residue_fate':None,'source':None},'validation_rules':['Closed non-self-intersecting polygon within supported AOI; compute geodesic area rather than trusting reported area.','Sowing <= transplant <= harvest when events apply; distinguish planned from observed dates.','pH 0..14 and laboratory method/depth/date required; total N is not available N.','Null history means unknown; [] may mean no records only when respondent explicitly confirms this.','Farm-gate prices require crop, unit, quality, currency, location and date; costs require area/time basis.','Weights 0..1 and sum to 1 only after user selection; do not assume priorities.','SoilGrids/GAEZ values must be stored as model-derived layers, never inserted into soil_lab as measured values.'],'fields':dictionary})
save('source-evidence.json',{'schema_version':'1.0','prepared_at_utc':NOW,'timezone_for_user_dates':'Asia/Jakarta','sources':list(sources.values()),'notes':['Excerpts are short locators; quantitative facts are curated in crop-reference.json.','Downloaded source HTML is a provenance snapshot, not an endorsement of unrelated page claims.','Two historical GAEZ point samples are data-access anchors, not verified farmer fields.']})

gaez=json.loads((OUT/'gaez-baseline-point.json').read_text())
with (OUT/'gaez-baseline-point.csv').open('w',newline='',encoding='utf-8') as stream:
 fields=['longitude','latitude','layer_code','class_code','class_label','continuous_suitability_score','period','scenario','resolution_degrees','status','source_url']
 writer=csv.DictWriter(stream,fieldnames=fields); writer.writeheader()
 for r in gaez['rows']:
  writer.writerow({'longitude':r['requested_point']['longitude'],'latitude':r['requested_point']['latitude'],'layer_code':r['layer_code'],'class_code':r.get('raw_value'),'class_label':r.get('class_label'),'continuous_suitability_score':'','period':'2001-2020','scenario':'HIST','resolution_degrees':1/12,'status':r['status'],'source_url':r['url']})

readme='''# Agronomy data readiness — FieldShift

Prepared 8 November 2026 (Asia/Jakarta). This package contains reference data and missing-input definitions. No application, farm recommendation, yield/profit prediction or nitrogen credit has been implemented.

## Available

- `crop-reference.json` and CSV: padi, jagung and kedelai. Historical FAO ECOCROP temperature/pH/annual-rainfall ranges; clearly separate FAO indicative seasonal ET ranges; Indonesian variety examples (Inpari 32 HDB, Jakarin, Anjasmoro) with source and duration basis. Variety examples are not farmer selections.
- `agronomy-rules.json`: conditional mechanisms and required inputs for rotation, water balance, pests, nitrogen and economics. No invented effect sizes.
- `gaez-baseline-point.json` and CSV: actual pixels for twelve combinations: 2 test points × wetland rice/maize/soybean × rain-fed/irrigated high-input management. Exact crop, period, climate and management dimensions plus official SIX legend are saved in sources.
- `farm-input-template.json` and dictionary: no invented farm; all unknown user values are null.
- `strategy-comparison-template.json`: three empty strategy slots (existing, candidate_1, candidate_2); rotation sequence, outcomes, yield, price, costs and priorities stay null; economics unavailable.
- `source-evidence.json` and source snapshots: URLs, access timestamps where known, hashes, failed access attempts and short evidence locators.

## GAEZ result and interpretation

HP0120 = 2001–2020, AGERA5, HIST. Grid: EPSG:4326 at 0.0833333333° (5 arc-minutes, approximately 9 km), not 30 m field data. HRLM = rain-fed/high inputs; HILM = irrigation/high inputs. These assumed management scenarios do not describe the user's actual management.

At Yogyakarta test point 110.37,-7.8, all six samples have categorical value 7: official legend `SI >0 : Very marginal`. At Klaten test point 110.55,-7.72, wetland rice has class 4 (`SI >40 : Medium`); maize and soybean have class 5 (`SI >25 : Moderate`) under both management scenarios. Class 7 is not a score 7/100. A continuous score cannot be recovered from these categorical rasters. Neither point is a verified farm and no recommendation is inferred.

Only a 65,536-byte TIFF header plus the one relevant compressed tile per layer was retrieved using HTTP 206 byte ranges, then decoded with Pillow/libtiff as a standalone LZW tile. Both points fall in the same retrieved tile. Six source subsets total about 425 KB; no complete global raster/archive was downloaded. `gaez-baseline-point.json` records pixel indexes, exact bounds, nodata, URLs and extraction status. Original generic palette is not used as the class definition; the official SIX JSON and SLD are the interpretation evidence.

## Limits and remaining work

Annual ECOCROP rainfall is a climate descriptor; FAO seasonal water need is indicative crop ET; irrigation additionally depends on effective rainfall, soil storage, field losses and efficiency. Paddy ET excludes the full scheme's land preparation, seepage/percolation and conveyance losses. Do not compare the table ranges as guaranteed farm water savings.

Local stage dates, cultivar calibration, seed availability, drainage, irrigation allocation, pest host ranges, measured soil fertility, costs and farm-gate prices remain missing. SIAP TANAM is a documented Indonesian reference service; its machine API and location-specific current recommendations were not tested here. The public FAO crop-information maize/soybean URLs returned 404; the official GAEZ API endpoints returned 502. Downloading the linked GAEZ XLSX lookup files failed with timeout/certificate errors; public bucket dimension JSON and legend were obtained instead. No account access is required for the completed bounded GAEZ extraction.

Public reference data are ready for a demo that exposes provenance and coarse-grid limitations. Validated farm recommendations and economics are unavailable until actual farmer inputs, model choices and local validation are supplied. No cultivar listed in this reference is assumed selected by the farmer.

## Reproduce

Use the bundled Python runtime with numpy and Pillow. `scripts/data/agronomy/fetch_sources.py` captures bounded public source snapshots; `sample_gaez.py` extracts the two historical anchor pixels; `prepare_agronomy.py` writes the structured reference and template. The refresh scripts never create or modify an application. The CSV files are simple machine-readable exports of JSON; JSON is authoritative for nulls, units and nested limitations.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
save('summary.json',{
 'schema_version':'1.0','prepared_at_utc':NOW,'checked_date':'2026-11-08','timezone':'Asia/Jakarta',
 'scope':'Public agronomy reference and two historical coarse-grid GAEZ anchors; no verified farm',
 'numeric_status':'reference_values_and_gaez_pixels_prepared_and_checked',
 'records':{'crop_references':len(crops),'conditional_rules':len(rules),'farm_input_fields':len(dictionary),'empty_strategy_slots':3,'gaez_point_layer_samples':len(gaez['rows'])},
 'public_reference_ready_for_demo':True,'farm_recommendation_ready':False,'economics_available':False,
 'gaez':{'version':5,'period':'2001-2020','period_code':'HP0120','climate':'AGERA5','scenario':'HIST','resolution_degrees':1/12,'crop_codes':['RCW','MZE','SOY'],'management_codes':['HRLM','HILM'],'values_are_categorical':True,'continuous_score_available':False,'sample_points_are_verified_farms':False,'global_archive_downloaded':False},
 'validation':{'script':'scripts/data/agronomy/validate_prepared.py','checks':['JSON parse','file sizes and SHA256 manifest','all 91 farmer values null','source IDs unique and references resolved','evidence excerpts present in snapshots','GAEZ dimensions/legend/pixel bounds','no inferred continuous suitability score']},
 'gaps':['Actual farmer boundary, area and records','Farmer-selected cultivar, sowing/transplant/harvest dates and local phenology calibration','Irrigation capacity/allocations, drainage and soil profile/laboratory results','Local pest host ranges, residue fate and nitrogen balance evidence','Farm-gate prices, marketable yields, costs and farmer priorities','Locally validated crop-sequence model and recommendation review'],
 'access_limits':['FAO crop-information maize/soybean URLs returned 404','Direct GAEZ catalogue API returned 502; public bucket dimensions and legend succeeded','Linked GAEZ XLSX lookups unavailable by attempted routes; equivalent public dimension JSON verified','SIAP TANAM current location-specific output and public machine API not tested'],
 'authoritative_files':['crop-reference.json','agronomy-rules.json','farm-input-template.json','farm-input-data-dictionary.json','strategy-comparison-template.json','gaez-baseline-point.json','source-evidence.json']
})
files=[]
for p in sorted(OUT.rglob('*')):
 if p.is_file() and p.name!='manifest.json': files.append({'path':str(p.relative_to(OUT)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':digest(p)})
save('manifest.json',{'schema_version':'1.0','prepared_at_utc':NOW,'purpose':'Agronomy reference and input readiness; not an application or agronomic advice','records':{'crops':len(crops),'rules':len(rules),'farm_dictionary_fields':len(dictionary),'gaez_point_layer_samples':len(gaez['rows'])},'storage_bytes_excluding_manifest':sum(x['bytes'] for x in files),'download_limit_bytes':20000000,'global_archive_downloaded':False,'files':files})
print(json.dumps({'crops':len(crops),'rules':len(rules),'dictionary_fields':len(dictionary),'gaez_samples':len(gaez['rows']),'bytes':sum(x['bytes'] for x in files)},indent=2))
