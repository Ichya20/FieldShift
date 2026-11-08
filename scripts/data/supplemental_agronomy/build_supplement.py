"""Build an additive agronomy contract/evidence audit. No prepared writes."""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
from copy import deepcopy
import json, sys

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'data/supplemental/agronomy'
PREP=ROOT/'data/prepared/agronomy'
NOW=datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text(encoding='utf8'))
def write(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def digest(p): return sha256(Path(p).read_bytes()).hexdigest()
def num(lo=0,hi=None,integer=False):
    d={'type':'integer' if integer else 'number','minimum':lo}
    if hi is not None:d['maximum']=hi
    return d
def st(enum=None,fmt=None):
    d={'type':'string'}
    if enum is not None:d['enum']=enum
    else:d['minLength']=1
    if fmt:d['format']=fmt
    return d
def ref(name): return {'$ref':'#/$defs/'+name}
def arr(items):return {'type':'array','items':items}
def obj(props,required=None):
    return {'type':'object','properties':props,'required':required if required is not None else list(props),'additionalProperties':False}
def nullable(s):return {'anyOf':[deepcopy(s),{'type':'null'}]}
DATE=st(fmt='date');STAMP=st(fmt='date-time');TEXT=st();BOOL={'type':'boolean'}
CROPS=st(['padi','jagung','kedelai'])
RULES=[x['id'] for x in read(ROOT/'specs/rotation-method-v1.json')['rules']]
ALL=RULES.copy()
DEFS={}
def shape(name,props,required=None):
    DEFS[name]=obj({k:nullable(v) for k,v in props.items()},required)

shape('source_record',{'source_ref':TEXT,'observed_at':STAMP,'recorded_at':STAMP,'location_basis':TEXT,'notes':TEXT})
shape('dated_activity',{'start_date':DATE,'end_date':DATE,'description':TEXT,'source':ref('source_record')})
shape('crop_access',{'crop_id':CROPS,'cultivar':TEXT,'available':BOOL,'available_from':DATE,'available_until':DATE,'source':ref('source_record')})
shape('crop_constraint',{'crop_id':CROPS,'constraint':TEXT,'start_date':DATE,'end_date':DATE,'source':ref('source_record')})
shape('price_record',{'crop_id':CROPS,'cultivar':TEXT,'product_form':TEXT,'quality_grade':TEXT,'moisture_percent':num(0,100),'price_value':num(),'price_unit':st(['IDR/kg','IDR/t','IDR/quintal']),'currency':st(['IDR']),'buyer':TEXT,'market_location':TEXT,'observed_on':DATE,'source':ref('source_record')})
shape('cost_record',{'category':st(['transport','storage','seed','fertilizer','pest_management','labor','machinery','irrigation','other']),'value':num(),'currency':st(['IDR']),'basis':st(['per_ha_per_season','per_field_per_season','per_kg','per_trip','per_person_day','other_documented']),'basis_description':TEXT,'crop_id':CROPS,'season_start':DATE,'season_end':DATE,'observed_on':DATE,'source':ref('source_record')})
shape('fertilizer_record',{'application_date':DATE,'product_name':TEXT,'product_kg_ha':num(),'nitrogen_percent_by_mass':num(0,100),'p2o5_percent_by_mass':num(0,100),'k2o_percent_by_mass':num(0,100),'basis':st(['product_mass','elemental_nutrient_mass','oxide_mass','other_documented']),'source':ref('source_record')})
shape('amendment_record',{'application_date':DATE,'material':TEXT,'amount_kg_ha':num(),'moisture_percent':num(0,100),'dry_matter_basis':BOOL,'analysis_report_ref':TEXT,'source':ref('source_record')})
shape('inoculation_record',{'application_date':DATE,'crop_id':CROPS,'cultivar':TEXT,'inoculated':BOOL,'product':TEXT,'organism_or_strain':TEXT,'dose_value':num(),'dose_unit':TEXT,'method':TEXT,'source':ref('source_record')})
shape('nodulation_record',{'observation_date':DATE,'crop_id':CROPS,'growth_stage':TEXT,'plants_sampled':num(integer=True),'nodules_per_plant':num(),'nodule_internal_colour':TEXT,'observer':TEXT,'protocol':TEXT,'source':ref('source_record')})
shape('pest_record',{'organism_scientific_name':TEXT,'organism_local_name':TEXT,'identification_status':st(['unconfirmed_symptom','identified_by_farmer','identified_by_adviser','laboratory_confirmed']),'crop_id':CROPS,'first_observed_on':DATE,'last_observed_on':DATE,'severity_value':num(),'severity_unit_or_scale':TEXT,'identification_source':TEXT,'management':TEXT,'source':ref('source_record')})
shape('pesticide_record',{'application_date':DATE,'crop_id':CROPS,'target_organism':TEXT,'active_ingredient':TEXT,'product':TEXT,'dose_value':num(),'dose_unit':TEXT,'method':TEXT,'source':ref('source_record')})
shape('flood_record',{'start_date':DATE,'end_date':DATE,'maximum_water_depth_cm':num(),'cause':TEXT,'observed_or_reported':st(['observed','reported']),'source':ref('source_record')})
shape('residue_record',{'crop_id':CROPS,'date':DATE,'fate':st(['retained_surface','incorporated','removed','burned','fed_to_livestock','mixed','other_documented']),'fraction_of_aboveground_residue':num(0,1),'dry_mass_kg_ha':num(),'source':ref('source_record')})
shape('history_record',{'crop_id':CROPS,'cultivar':TEXT,'sowing_date':DATE,'transplanting_date':DATE,'harvest_date':DATE,'yield_kg_ha':num(),'yield_moisture_basis':TEXT,'irrigation_system':TEXT,'rice_ecosystem':st(['irrigated_lowland','rainfed_lowland','rainfed_upland','flood_prone']),'rice_water_regime':st(['flooded_paddy','intermittently_flooded_paddy','nonflooded_aerobic','mixed_or_variable','other_documented']),'pests':arr(ref('pest_record')),'residue_fate':arr(ref('residue_record')),'source':ref('source_record')})
shape('duration_record',{'crop_id':CROPS,'minimum_days':num(integer=True),'maximum_days':num(integer=True),'basis_event':st(['sowing','transplanting']),'counting_convention':st(['elapsed_day_zero']),'source_ref':TEXT,'source_origin_wording':TEXT,'source_minimum_days':num(),'source_maximum_days':num(),'normalization_policy':st(['no_rounding_needed','explicit_source_integer_alternative','documented_external_conversion']),'normalization_note':TEXT,'cultivar':TEXT})
shape('crop_slot',{'slot_id':TEXT,'crop_id':CROPS,'cultivar':TEXT,'date_status':st(['observed','planned','scenario_assumption']),'sowing_date':DATE,'transplanting_date':DATE,'harvest_date':DATE,'establishment_method':st(['direct_seeded','transplanted','other_documented']),'duration':ref('duration_record'),'preparation_gap_days':num(integer=True),'nursery_separate_from_main_field':BOOL,'nursery_location_ref':TEXT,'rice_ecosystem':st(['irrigated_lowland','rainfed_lowland','rainfed_upland','flood_prone']),'rice_water_regime':st(['flooded_paddy','intermittently_flooded_paddy','nonflooded_aerobic','mixed_or_variable','other_documented']),'source':ref('source_record')})
shape('nutrient_balance_record',{'crop_id':CROPS,'period_start':DATE,'period_end':DATE,'nutrient':st(['N','P','K']),'fertilizer_input_kg_element_ha':num(),'organic_input_kg_element_ha':num(),'measured_fixation_kg_n_ha':num(),'harvest_export_kg_element_ha':num(),'residue_export_kg_element_ha':num(),'other_input_kg_element_ha':num(),'losses_kg_element_ha':num(),'stock_change_kg_element_ha':{'type':'number'},'measurement_method':TEXT,'source':ref('source_record')})
shape('host_range_record',{'organism_scientific_name':TEXT,'crop_id':CROPS,'host_status':st(['host','non_host','uncertain']),'source_ref':TEXT,'local_reviewer':TEXT,'reviewed_on':DATE,'scope_and_limitations':TEXT})
shape('field_provenance_record',{'field_path':TEXT,'data_class':st(['farmer_reported','field_measured','local_adviser','derived_geometry','public_reference_context','scenario_assumption']),'source_ref':TEXT,'observed_at':STAMP,'recorded_at':STAMP,'uncertainty_note':TEXT})
shape('layer_support_record',{'layer_id':TEXT,'source_ref':TEXT,'support_identifier':TEXT,'support_geometry_ref':TEXT,'selection_basis':st(['containing_extracted_support','explicit_regional_context','explicit_demo_support','outside_coverage']),'period_start':DATE,'period_end':DATE,'valid_observations':num(integer=True),'expected_observations':num(integer=True),'qa_policy_ref':TEXT})
shape('ph_context_record',{'value':num(0,14),'origin':st(['laboratory_measurement','soilgrids_prediction']),'top_cm':num(),'bottom_cm':num(),'method':TEXT,'source_ref':TEXT,'sampled_on':DATE,'model_epoch':TEXT,'containing_cell_ref':TEXT})
shape('window_record',{'start_date':DATE,'end_exclusive':DATE})
shape('temperature_context_record',{'crop_id':CROPS,'mean_t2m_c':{'type':'number'},'window':ref('window_record'),'source_ref':TEXT,'complete_days':num(integer=True),'expected_days':num(integer=True)})
shape('vegetation_context_record',{'exact_pixel_id':TEXT,'source_ref':TEXT,'window':ref('window_record'),'qa_policy_ref':TEXT,'valid_observations':num(integer=True),'expected_observations':num(integer=True),'mixed_pixel_context_ref':TEXT})
shape('gaez_context_record',{'containing_cell_ref':TEXT,'crop_code':st(['RCW','MZE','SOY']),'management_regime':st(['HRLM','HILM','explicit_unknown']),'source_ref':TEXT,'legend_ref':TEXT,'model_period':TEXT,'category_code':num(integer=True)})

# Units for numeric values inside records are explicit, rather than inferred by consumers.
RECORD_UNITS={
 'price_record':{'moisture_percent':'percent_product_mass','price_value':'specified_by_price_unit'},
 'cost_record':{'value':'IDR_per_declared_basis'},
 'fertilizer_record':{'product_kg_ha':'kg_product/ha','nitrogen_percent_by_mass':'percent_product_mass','p2o5_percent_by_mass':'percent_product_mass','k2o_percent_by_mass':'percent_product_mass'},
 'amendment_record':{'amount_kg_ha':'kg_material/ha','moisture_percent':'percent_material_mass'},
 'inoculation_record':{'dose_value':'specified_by_dose_unit'},
 'nodulation_record':{'plants_sampled':'plant_count','nodules_per_plant':'nodule_count/plant'},
 'pest_record':{'severity_value':'specified_by_severity_unit_or_scale'},
 'pesticide_record':{'dose_value':'specified_by_dose_unit'},
 'flood_record':{'maximum_water_depth_cm':'cm_above_soil_surface'},
 'residue_record':{'fraction_of_aboveground_residue':'fraction_0_1','dry_mass_kg_ha':'kg_dry_residue/ha'},
 'history_record':{'yield_kg_ha':'kg_harvested_product/ha'},
 'duration_record':{x:'days' for x in ['minimum_days','maximum_days','source_minimum_days','source_maximum_days']},
 'crop_slot':{'preparation_gap_days':'days'},
 'nutrient_balance_record':{x:'kg_element/ha/declared_period' for x in ['fertilizer_input_kg_element_ha','organic_input_kg_element_ha','measured_fixation_kg_n_ha','harvest_export_kg_element_ha','residue_export_kg_element_ha','other_input_kg_element_ha','losses_kg_element_ha','stock_change_kg_element_ha']},
 'layer_support_record':{'valid_observations':'observation_count','expected_observations':'observation_count'},
 'ph_context_record':{'value':'pH_H2O_dimensionless','top_cm':'cm_below_soil_surface','bottom_cm':'cm_below_soil_surface'},
 'temperature_context_record':{'mean_t2m_c':'degree_C','complete_days':'days','expected_days':'days'},
 'vegetation_context_record':{'valid_observations':'observation_count','expected_observations':'observation_count'},
 'gaez_context_record':{'category_code':'categorical_code_not_numeric_score'},
}
for name,units in RECORD_UNITS.items():
    for prop,unit in units.items():DEFS[name]['properties'][prop]['x-unit']=unit

FIELDS=[]
def field(path,schema,units,meaning,rules,kind='farmer_reported',stage='conditional',notes='',original=True,record_shape=None):
    FIELDS.append({'path':path,'origin':'prepared_91' if original else 'supplemental_addition','schema':nullable(schema),'units':units,'unit_status':'not_applicable' if units is None else 'specified','meaning':meaning,'rule_ids':rules,'acquisition_class':kind,'requirement_stage':stage,'value':None,'validation_notes':notes,'record_shape':record_shape,'provenance_required':True,'public_source_may_replace_field_actual':False})
def f(path,schema=TEXT,units=None,meaning='',rules=None,**kw):
    field('farm.'+path,schema,units,meaning or path.replace('_',' '),rules or ['coverage'],**kw)

f('farm_id',meaning='Opaque farm identifier; no personal name required',rules=ALL,stage='optional')
f('field_id',meaning='Opaque field identifier; does not assert a mapped boundary',rules=ALL,stage='optional')
position={'type':'array','prefixItems':[num(-180,180),num(-90,90)],'items':{'type':'number'},'minItems':2,'maxItems':3}
ring={'type':'array','items':position,'minItems':4}
polygon_coords={'type':'array','items':ring,'minItems':1}
geometry={'oneOf':[obj({'type':{'const':'Polygon'},'coordinates':polygon_coords}),obj({'type':{'const':'MultiPolygon'},'coordinates':{'type':'array','items':polygon_coords,'minItems':1}})]}
f('location.geometry_geojson',geometry,'decimal degrees EPSG:4326 [longitude,latitude]','Farmer field boundary, if actually surveyed',ALL,kind='field_measured',notes='Requires semantic GeoJSON validation: finite coordinates, closed rings >=4 positions, longitude [-180,180], latitude [-90,90], nonzero area, no self-intersection. This schema checks structure only; do not use a satellite footprint as field boundary.')
f('location.representative_longitude',num(-180,180),'degree_east','Explicit point longitude',ALL,kind='field_measured',stage='initial',notes='Negative longitudes valid globally; supported AOI is checked separately.')
f('location.representative_latitude',num(-90,90),'degree_north','Explicit point latitude',ALL,kind='field_measured',stage='initial',notes='Negative latitude is valid and expected in Yogyakarta-Klaten. Never impose nonnegative latitude.')
f('location.area_ha_reported',num(0),'ha','Reported area', ['coverage','economics'],notes='Known zero can be stored but active farm area must be >0; never infer area from a MODIS pixel.')
f('location.area_ha_geometry',num(0),'ha','Geodesic area derived from a valid farmer boundary',['coverage','economics'],kind='derived_geometry',notes='Derived value with method and CRS provenance; never trusted as an independent measurement.')
for x in ['village','district','province']: f('location.'+x,rules=['coverage','economics'])
f('location.country_code',{'type':'string','pattern':'^[A-Z]{2}$'},meaning='ISO3166-1 alpha2 country code',rules=['coverage'])
f('location.boundary_recorded_at',STAMP,meaning='Boundary collection timestamp with offset',rules=['coverage'],kind='field_measured')
f('location.boundary_source',rules=['coverage'],kind='field_measured')
f('current_crop.crop_id',CROPS,meaning='Actual crop reported by farmer',rules=['calendar','temperature_reference','seasonal_et_reference','paddy_upland_transition','legume_mechanism','pest_break','gaez_context'],stage='initial')
for x in ['cultivar','seed_source']: f('current_crop.'+x,rules=['calendar','legume_mechanism'],notes='Public example varieties do not select this field.')
f('current_crop.production_system',meaning='Original free-text production description, retained without automatic ecological inference',rules=['paddy_upland_transition','gaez_context'],notes='Use supplemental establishment_method, rice_ecosystem and rice_water_regime separately.')
for x in ['sowing_date','transplanting_date','expected_harvest_date']: f('current_crop.'+x,DATE,meaning=x.replace('_',' '),rules=['calendar','climate_exposure'],stage='initial',notes='Date-only ISO8601; expected harvest is a plan and not an observed harvest.')
f('current_crop.observed_growth_stage',rules=['calendar'],kind='field_measured',notes='Record stage vocabulary and observation source; no growth stage inferred from MODIS.')
f('current_crop.stage_observed_at',STAMP,rules=['calendar'],kind='field_measured')
f('rotation_history',arr(ref('history_record')),meaning='Observed or explicitly reported past crops',rules=['calendar','paddy_upland_transition','legume_mechanism','pest_break'],record_shape='history_record',notes='Null means unknown; [] means explicitly confirmed no records. History alone never defines the future continuation.')
f('irrigation.system',st(['none','surface','sprinkler','drip','mixed','other_documented']),rules=['paddy_upland_transition','gaez_context'],notes='System type does not establish water reliability or continuous flooding.')
f('irrigation.source',rules=['paddy_upland_transition'])
f('irrigation.rainfed',BOOL,rules=['paddy_upland_transition','gaez_context'],stage='initial',notes='True means farmer reports rainfed; false does not prove assured irrigation; null is unknown.')
for x in ['availability_window_start','availability_window_end']: f('irrigation.'+x,DATE,rules=['calendar','paddy_upland_transition'])
for x,unit,rules in [('capacity_m3_day','m3/day',['paddy_upland_transition']),('allocation_m3_season','m3/season',['paddy_upland_transition']),('application_efficiency_fraction','fraction_0_1',['paddy_upland_transition']),('water_cost_idr_m3','IDR/m3',['economics']),('water_table_depth_m','m_below_soil_surface',['paddy_upland_transition'])]:
    f('irrigation.'+x,{'type':'number'} if x=='water_table_depth_m' else num(0,1 if x=='application_efficiency_fraction' else None),unit,rules=rules,notes='Depth positive below surface and negative above surface; datum and observation date required.' if x=='water_table_depth_m' else 'Measured/reported context only; does not enable irrigation-demand calculation.')
f('irrigation.drainage_condition',st(['good_reported','poor_reported','variable_reported','locally_verified','other_documented']),rules=['paddy_upland_transition'],stage='initial',notes='Good reported drainage is not locally verified crop suitability.')
f('irrigation.flooding_history',arr(ref('flood_record')),rules=['paddy_upland_transition'],record_shape='flood_record')
f('soil_lab.sampling_date',DATE,rules=['ph_reference','legume_mechanism'],kind='field_measured')
for x in ['laboratory','method']: f('soil_lab.'+x,rules=['ph_reference','legume_mechanism'],kind='field_measured',notes='Lab method must identify analyte-specific extraction or measurement method; one generic method label is insufficient for all analytes.')
for x in ['depth_top_cm','depth_bottom_cm']: f('soil_lab.'+x,num(),'cm_below_soil_surface',rules=['ph_reference','legume_mechanism'],kind='field_measured',notes='Bottom > top; retain each sampled horizon. Never average pH across depths.')
soil_fields=[('ph_h2o',num(0,14),'pH_H2O_dimensionless',['ph_reference']),('organic_carbon_percent',num(0,100),'percent_dry_soil_mass',['legume_mechanism']),('total_n_percent',num(0,100),'percent_dry_soil_mass',['legume_mechanism']),('available_p_mg_kg',num(),'mg_P/kg_dry_soil',['legume_mechanism']),('exchangeable_k_cmolc_kg',num(),'cmol_charge/kg_dry_soil',['legume_mechanism']),('ec_ds_m',num(),'dS/m',['paddy_upland_transition']),('texture_class',TEXT,None,['paddy_upland_transition']),('bulk_density_g_cm3',num(),'g/cm3',['paddy_upland_transition']),('field_capacity_fraction',num(0,1),'m3_water/m3_soil',['paddy_upland_transition']),('wilting_point_fraction',num(0,1),'m3_water/m3_soil',['paddy_upland_transition']),('rootable_depth_cm',num(),'cm',['paddy_upland_transition'])]
for x,sch,unit,rules in soil_fields: f('soil_lab.'+x,sch,unit,rules=rules,kind='field_measured',notes='Actual laboratory/profile observation only. Public soil prediction belongs in context, never here. Total N is not available N; field capacity >= wilting point; texture class must name its classification system.')
f('soil_lab.report_file',meaning='Local document reference; no public upload implied',rules=['ph_reference','legume_mechanism'],kind='field_measured')
f('management.tillage',arr(ref('dated_activity')),rules=['paddy_upland_transition','legume_mechanism'],record_shape='dated_activity')
f('management.residue_fate',arr(ref('residue_record')),rules=['legume_mechanism','pest_break'],record_shape='residue_record')
for x,shape_name,rules in [('fertilizer_history','fertilizer_record',['legume_mechanism','economics']),('organic_amendments','amendment_record',['legume_mechanism']),('legume_inoculation','inoculation_record',['legume_mechanism']),('nodulation_observations','nodulation_record',['legume_mechanism']),('pest_disease_weed_history','pest_record',['pest_break']),('pesticide_history','pesticide_record',['pest_break','economics'])]: f('management.'+x,arr(ref(shape_name)),rules=rules,record_shape=shape_name)
f('resources.labor_available_days_season',num(),'person_days/season',rules=['calendar','economics'],notes='One person-day basis and season dates required; clarify working hours per person-day in provenance.')
f('resources.machinery_access',arr(ref('dated_activity')),rules=['calendar','paddy_upland_transition','economics'],record_shape='dated_activity')
f('resources.seed_access',arr(ref('crop_access')),rules=['calendar'],record_shape='crop_access')
f('resources.budget_idr_season',num(),'IDR/season',rules=['economics'],stage='deferred_economics')
f('market.buyer_access',arr(ref('dated_activity')),rules=['economics'],stage='deferred_economics',record_shape='dated_activity')
f('market.crop_preferences',arr(CROPS),rules=['calendar','economics'],notes='Preference alone is not permission to generate a crop; planning.allowed_crop_ids must be explicit.')
f('market.contract_constraints',arr(ref('crop_constraint')),rules=['calendar','economics'],record_shape='crop_constraint')
f('market.farm_gate_prices',arr(ref('price_record')),rules=['economics'],stage='deferred_economics',record_shape='price_record')
f('market.expected_marketable_yield_kg_ha',num(),'kg_marketable_product/ha',rules=['economics'],stage='deferred_economics',notes='Crop, moisture, quality, location, season and empirical/assumed provenance required; never substitute catalog potential yield.')
f('market.transport_storage_costs',arr(ref('cost_record')),rules=['economics'],stage='deferred_economics',record_shape='cost_record')
f('market.currency',st(['IDR']),rules=['economics'],stage='deferred_economics')
f('market.price_observed_at',STAMP,rules=['economics'],stage='deferred_economics')
for x in ['seed','fertilizer','pest_management','labor','machinery','irrigation','other']: f('costs.'+x+'_idr_ha',num(),'IDR/ha/season',rules=['economics'],stage='deferred_economics',notes='Same crop, field-area basis and reference season; record actual/assumed status and avoid double counting transport/storage or irrigation water costs.')
f('costs.reference_season',ref('window_record'),rules=['economics'],stage='deferred_economics',record_shape='window_record',notes='Season start inclusive, end exclusive, matching each monetary cost; no free-text season conversion silently.')
for x in ['water_saving','net_income','soil_health']: f('priorities.'+x+'_weight',num(0,1),'fraction_0_1',rules=[],stage='legacy_unused',notes='Retained for compatibility only. MVP/spec uses explicit priority labels with no weights, weighting or composite score. Do not request, infer, sum, normalize or use these values.')
f('priorities.risk_tolerance',st(['low','moderate','high','other_documented']),rules=ALL,notes='Self-described preference, never converted into a numerical benefit ranking.')
for x in ['planning_horizon_start','planning_horizon_end']: f('priorities.'+x,DATE,rules=['calendar','climate_exposure','vegetation_context'],stage='initial',notes='Horizon [start,end_exclusive); label legacy end as exclusive. Reject disagreement with planning.horizon.')
f('priorities.excluded_crops',arr(CROPS),rules=['calendar'],stage='initial',notes='Unique crop IDs; [] is explicitly no exclusions; null is unknown. Reject disagreement with planning.excluded_crop_ids.')
for x in ['respondent_role','information_source']: f('provenance.'+x,rules=ALL)
for x in ['recorded_at','local_extension_reviewed_at']: f('provenance.'+x,STAMP,rules=ALL,notes='Timestamp alone is not agronomic approval. Review needs scope, reviewer identity/role, evidence and result.')

def add(path,schema,units=None,meaning='',rules=None,kind='farmer_reported',stage='conditional',notes='',record_shape=None):
    field(path,schema,units,meaning or path.replace('_',' '),rules if rules is not None else ['calendar'],kind,stage,notes,False,record_shape)
add('farm.current_crop.establishment_method',st(['direct_seeded','transplanted','other_documented']),rules=['calendar','paddy_upland_transition'],notes='Establishment is separate from ecosystem and water regime.')
add('farm.current_crop.rice_ecosystem',st(['irrigated_lowland','rainfed_lowland','rainfed_upland','flood_prone']),rules=['paddy_upland_transition','gaez_context'],notes='Reference vocabulary from FAO; field assignment requires farmer/adviser observation. Null for unknown; non-rice uses rule applicability, not fake rice value.')
add('farm.current_crop.rice_water_regime',st(['flooded_paddy','intermittently_flooded_paddy','nonflooded_aerobic','mixed_or_variable','other_documented']),rules=['paddy_upland_transition'],notes='Operational app vocabulary, not direct FAO/GAEZ category codes; record actual dates, water control and flooding observations.')
add('farm.irrigation.water_control',st(['can_supply_and_drain_reported','supply_only_reported','drain_only_reported','no_control_reported','locally_verified','other_documented']),rules=['paddy_upland_transition'],notes='No inference from irrigation system type. Capability and actual availability differ.')
add('farm.management.soil_management_for_transition',arr(ref('dated_activity')),rules=['paddy_upland_transition'],record_shape='dated_activity')
add('farm.management.nutrient_balance',arr(ref('nutrient_balance_record')),rules=['legume_mechanism'],record_shape='nutrient_balance_record',notes='Balance components remain unknown until measured/sourced; this schema does not calculate a fertilizer or nitrogen credit.')
add('farm.management.local_host_range_evidence',arr(ref('host_range_record')),rules=['pest_break'],kind='local_adviser',record_shape='host_range_record')
add('planning.horizon',ref('window_record'),rules=['calendar','climate_exposure','vegetation_context'],kind='scenario_configuration',stage='generator_required',record_shape='window_record')
for x in ['allowed_crop_ids','excluded_crop_ids']: add('planning.'+x,arr(CROPS),rules=['calendar'],kind='scenario_configuration',stage='generator_required',notes='Unique IDs. Explicit [] differs from null; future exclusions affect mutable slots and do not erase the existing continuation.')
add('planning.existing_sequence',arr(ref('crop_slot')),rules=['calendar','climate_exposure','paddy_upland_transition','legume_mechanism','pest_break'],kind='scenario_configuration',stage='generator_required',record_shape='crop_slot',notes='Explicit future continuation or confirmed phase-anchored repetition; historical records are not automatically a continuation.')
add('planning.slot_start_dates',arr(DATE),rules=['calendar','climate_exposure'],kind='scenario_configuration',stage='generator_required',notes='Ordered field-start dates; <=3 automatically generated slots; per-slot establishment determines which biological date is meant.')
add('planning.locked_prefix_length',num(0,3,integer=True),'slot_count',rules=['calendar'],kind='scenario_configuration',stage='generator_required',notes='Must be <=sequence length. Zero is explicit none locked; null is unknown.')
add('planning.continuation_confirmed',BOOL,rules=['calendar'],kind='scenario_configuration',stage='generator_required',notes='Must be true for a generated comparison of an existing continuation. False is an explicit rejection, not unknown.')
add('planning.duration_by_crop',arr(ref('duration_record')),'days',rules=['calendar'],kind='scenario_configuration',record_shape='duration_record',notes='Every selected crop/cultivar needs an explicit duration basis and source; a public example is never farmer-selected by default.')
add('planning.preparation_gap_days',num(integer=True),'days',rules=['calendar','paddy_upland_transition'],kind='scenario_configuration',notes='Null is not zero. Gap begins after field release (harvest+1day); per-slot overrides require provenance.')
add('planning.nursery_separate_from_main_field',BOOL,rules=['calendar'],kind='scenario_configuration',notes='Separate nursery must be explicit before allowing overlap with an earlier main-field crop.')
add('planning.nursery_location_ref',rules=['calendar'],schema=TEXT,kind='scenario_configuration',notes='Actual or explicit scenario resource reference; no fabricated farm geometry.')
add('planning.selected_priorities',arr(st(['water_context','soil_context','pest_management','calendar_constraints','economic_information'])),rules=ALL,kind='scenario_configuration',notes='Presentation highlights only; no default weights, scores, ranking or benefits.')
add('context.time_mode',st(['historical_replay','historical_analogue_not_forecast','recent_partial']),rules=['climate_exposure','temperature_reference','vegetation_context'],kind='scenario_configuration')
add('context.climate_window',ref('window_record'),rules=['climate_exposure','temperature_reference'],kind='scenario_configuration',record_shape='window_record')
add('context.explicit_climate_context',TEXT,rules=['coverage','climate_exposure','temperature_reference'],kind='public_reference_selection',notes='Select exact source/path and explicit regional/example support; never silently nearest-point fallback.')
add('context.layer_support',arr(ref('layer_support_record')),rules=['coverage','climate_exposure','vegetation_context','ph_reference','gaez_context'],kind='public_reference_selection',record_shape='layer_support_record')
add('context.ph_reference_input',ref('ph_context_record'),'pH_H2O_dimensionless',rules=['ph_reference'],kind='public_reference_selection',record_shape='ph_context_record',notes='Laboratory measurement and model prediction remain distinct; containing cell, depth, source/method/date or model epoch required.')
add('context.temperature_reference_input',ref('temperature_context_record'),'degree_C',rules=['temperature_reference'],kind='public_reference_selection',record_shape='temperature_context_record',notes='Historical window summary; never Tmax threshold/failure-day calculation.')
add('context.vegetation_reference_input',ref('vegetation_context_record'),rules=['vegetation_context'],kind='public_reference_selection',record_shape='vegetation_context_record',notes='Exact extracted pixel and strict-good QA; no inferred species, crop dates, history or fallow.')
add('context.gaez_reference_input',ref('gaez_context_record'),rules=['gaez_context'],kind='public_reference_selection',record_shape='gaez_context_record',notes='Historical categorical reference with HRLM and HILM separate; RCW is wetland rice and not confirmed farmer ecology.')
add('provenance.fields',arr(ref('field_provenance_record')),rules=ALL,kind='provenance_metadata',record_shape='field_provenance_record',notes='Per-field data class, source and observation/recording dates; public context never replaces field actuals.')

def nested_set(root,path,value):
    parts=path.split('.')
    for p in parts[:-1]:root=root.setdefault(p,{})
    root[parts[-1]]=value
def leaf_paths(d,prefix=''):
    result=[]
    for k,v in d.items():
        p=f'{prefix}.{k}' if prefix else k
        if isinstance(v,dict):result+=leaf_paths(v,p)
        else:result.append(p)
    return result

def build_contract():
    original=read(PREP/'farm-input-data-dictionary.json')
    old_paths={x['path'] for x in original['fields']}
    new_old={x['path'] for x in FIELDS if x['origin']=='prepared_91'}
    assert len(old_paths)==91 and old_paths==new_old,(old_paths-new_old,new_old-old_paths)
    # f() defaults to coverage for an empty list; weights must have no active rule.
    for x in FIELDS:
        if x['requirement_stage']=='legacy_unused':x['rule_ids']=[]
        if x['path'] in ['planning.allowed_crop_ids','planning.excluded_crop_ids','farm.priorities.excluded_crops','planning.selected_priorities']:
            x['schema']['anyOf'][0]['uniqueItems']=True
    template={'schema_version':'1.1-supplemental','is_template':True}
    schema={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'https://fieldshift.invalid/contracts/farm-input-supplement-1.1','title':'FieldShift additive input contract; no farm observations supplied','type':'object','properties':{'schema_version':{'const':'1.1-supplemental'},'is_template':{'type':'boolean'}},'required':['schema_version','is_template'],'additionalProperties':False,'$defs':DEFS}
    for x in FIELDS:
        nested_set(template,x['path'],None)
        node=schema
        parts=x['path'].split('.')
        for p in parts[:-1]:
            node=node.setdefault('properties',{}).setdefault(p,{'type':'object','properties':{},'additionalProperties':False})
        node['properties'][parts[-1]]={**x['schema'],'description':x['meaning'],'x-unit':x['units'],'x-rule-ids':x['rule_ids'],'x-acquisition-class':x['acquisition_class']}
    contract={'schema_version':'1.1-supplemental','status':'additive_contract_not_backend_implementation','prepared_base_path':'data/prepared/agronomy/farm-input-data-dictionary.json','method_spec':'specs/rotation-method-v1.json','original_fields':91,'supplemental_fields':len(FIELDS)-91,'null_policy':{'null':'unknown/not supplied','zero':'known numerical zero subject to semantic constraints','false':'explicit false, not unknown','empty_array':'explicitly confirmed none, not unknown','not_applicable':'rule applicability/status, never fabricated field value'},'precedence':{'prepared_data':'Immutable; supplements do not rewrite prepared values','contract':'Use this typed overlay together with base dictionary during future implementation','legacy_weights':'Unused in MVP; no sum-to-one validation, normalization, ranking or composite score','horizon_aliases':'Reject differences between legacy priorities horizon/excluded fields and canonical planning fields; no silent precedence'},'cross_field_validation':['Coordinates longitude [-180,180], latitude [-90,90]; negative latitude valid. Spatial support checked separately per layer.','Validate GeoJSON ring closure/self-intersections/finite coordinates and geodesic area outside structural JSON Schema.','Sowing <= transplanting <= harvest where events apply; dates are ISO8601 date-only. Timestamp fields require an offset.','Horizon start < end_exclusive. Keep biological crop dates beyond horizon; clip exposure only.','Duration minimum <= maximum; explicit source, crop/cultivar mapping, origin and elapsed day-zero convention; do not silently convert fractional source days.','Locked prefix <=actual sequence length; <=3 automatic slots; continuation must be explicitly confirmed; no inferred continuation.','Null preparation gap never means zero; release=harvest+1day; next field start>=release+declared gap.','Separate nursery resource must be explicit for any nursery/main-field overlap; total sowing-based duration already includes nursery.','Soil depth bottom>top; field capacity>=wilting point; analyte method/depth/date required; pH not averaged across depths.','Array histories/prices/costs/fertilizers/pests use named record shapes and per-record provenance; empty array needs explicit confirmation.','Economics remains deferred even when records exist. Match crop/units/moisture/season/location before any future comparison.','Legacy priority weights are retained unused; no weighting, ranking or fabricated priority.','All actual input values stay null in this supplement; source context and scenario assumptions require their own explicit data class.'],'fields':FIELDS,'$defs':DEFS}
    write('farm-input-contract.json',contract)
    write('farm-input-complete-template.json',template)
    write('farm-input-complete.schema.json',schema)
    return template,schema

def evidence():
    snapshots=read(OUT/'source-snapshots.json')
    sources=snapshots['sources']
    existing=read(PREP/'source-evidence.json')['sources']
    reuse_ids=['fao-crop-rotation','fao-water-needs','fao-seasonal-water','fao-paddy-irrigation','fao-aquacrop-inputs','kementan-inpari32','kementan-jakarin','kementan-anjasmoro','ecocrop-rice','ecocrop-maize','ecocrop-soybean']
    for sid in reuse_ids:
        r=next(x for x in existing if x['id']==sid)
        p=PREP/r['path']
        sources.append({**r,'path':p.relative_to(ROOT).as_posix(),'status':'reused_prepared_snapshot','sha256':digest(p),'bytes':p.stat().st_size})
    claims=[
      {'id':'anjasmoro-maturity-after-planting','source_id':'kementan-variety-catalog-brmp','locator':'PDF page87 (printed64), Lampiran27','quote':'Umur masak : 82–93 hari setelah tanam','fact':{'crop_id':'kedelai','cultivar':'Anjasmoro','minimum_days':82,'maximum_days':93,'origin_event_wording':'tanam (planting)','endpoint_wording':'masak (maturity)'},'interpretation':'Explicit public duration origin filled. For a declared direct-seeded scenario, source planting can be mapped to sowing only with an explicit establishment assumption. Method uses elapsed-day-zero by declared convention, not a source guarantee.','limits':['Reference cultivar only; farmer cultivar/date not supplied.','Different published range from original rounded82–92 and PVT82.5–92.5; preserve alternatives.','Maturity reference does not guarantee exact field harvest date.']},
      {'id':'anjasmoro-descriptor-maturity','source_id':'kementan-anjasmoro-descriptor','locator':'PDF page1','quote':'Umur polong masak : 82,5 - 92,5 hari','fact':{'minimum_days':82.5,'maximum_days':92.5,'endpoint_wording':'polong masak'},'interpretation':'Retain fractional descriptor; origin not explicit on this page.','limits':['Do not round into integer calendar silently.']},
      {'id':'anjasmoro-hst-corroboration','source_id':'kementan-lakin-2023','locator':'PDF page39 (printed40), item23','quote':'berumur 82,5-92,5 HST','fact':{'minimum_days':82.5,'maximum_days':92.5,'origin_abbreviation':'HST'},'interpretation':'Corroborating official HST reference; integer after-planting alternative is independently explicit in catalog.','limits':['No local duration calibration; no realized farm yield from the adjoining potential-yield text.']},
      {'id':'rice-ecosystem-taxonomy','source_id':'fao-rice-phase-water-regimes','locator':'Section2.1.1 Rice area and water regime','quote':'Irrigated, Rainfed Lowland, Floodprone/Swampland, and Rainfed Upland','fact':{'reference_categories':['irrigated','rainfed_lowland','floodprone_swampland','rainfed_upland']},'interpretation':'Public vocabulary; local field classification remains unknown.','limits':['Historical reference context, not a farm map or current classification.']},
      {'id':'rice-upland-definition','source_id':'fao-rice-ecosystems','locator':'Rice environment, preceding The rice plant','quote':'Upland rice is grown under dryland conditions without irrigation and without puddling','fact':{'no_irrigation':True,'no_puddling':True},'interpretation':'Reference ecological definition only; direct seeding alone is insufficient for assignment.','limits':['Never assign field ecosystem from seed-establishment method.']},
      {'id':'rice-lowland-and-transition','source_id':'fao-rice-ecosystems','locator':'Rice environment, preceding The rice plant','quote':'In such systems, the preferred cultural practices for rice are often antagonistic to the preferred practices for the non-rice crops, and vice versa.','fact':{'rice_nonrice_management_review_required':True},'interpretation':'Supports separate drainage, water control and soil-management review.','limits':['No locally quantified cost, transition duration, drainage threshold or benefit.']},
      {'id':'rice-rainfed-lowland-flooded','source_id':'fao-rice-ecosystems','locator':'Rice environment, preceding The rice plant','quote':'Rainfed lowland rice is grown in bunded fields that are flooded with rainwater for at least part of the cropping season','fact':{'rainfed_can_be_flooded':True},'interpretation':'Rainfed is not equivalent to upland or nonflooded.','limits':['Irrigation status alone does not determine actual water regime.']},
    ]
    record={'schema_version':'1.0','created_at_utc':NOW,'sources':sources,'claims':claims,'public_reference_only':True,'rendered_visual_checks':[{'path':'data/supplemental/agronomy/sources/kementan-anjasmoro-descriptor-page-1.png','pdf_page_1_based':1,'status':'inspected_value_label_alignment'},{'path':'data/supplemental/agronomy/sources/kementan-lakin-2023-page-39.png','pdf_page_1_based':39,'status':'inspected_item23_and_hst'},{'path':'data/supplemental/agronomy/sources/kementan-variety-catalog-brmp-page-87.png','pdf_page_1_based':87,'status':'inspected_82_93_hari_setelah_tanam'}]}
    write('source-evidence.json',record)
    write('agronomy-reference-supplement.json',{'schema_version':'1.0','public_references':claims,'rice_vocabulary':{'ecosystem':{'terms':['irrigated_lowland','rainfed_lowland','rainfed_upland','flood_prone'],'type':'normalized_FAO_reference_categories','source_ids':['fao-rice-phase-water-regimes','fao-rice-ecosystems']},'water_regime':{'terms':['flooded_paddy','intermittently_flooded_paddy','nonflooded_aerobic','mixed_or_variable','other_documented'],'type':'project_operational_vocabulary_not_FAO_codes','value':None},'establishment_method':{'terms':['direct_seeded','transplanted','other_documented'],'type':'separate_project_input','value':None}},'planting_duration_policy':{'selection':'No cultivar or duration is automatically assigned to an actual farm.','alternatives':'Keep 82–93 days after planting, 82.5–92.5 HST, 82.5–92.5 days unspecified, and existing rounded 82–92 days as separately sourced references.','calendar':'Calendar integer source alternatives require explicit source selection, establishment and elapsed-day-zero convention.','fractional_days':'No silent floor/ceil/midpoint conversion.','farmer_selected_cultivar':None,'local_duration_days':None},'management_prerequisites':{'paddy_upland_transition':['actual rice ecosystem','actual water regime','drainage and water-table evidence','ability to control supply and drainage','soil preparation and declared time gap','local agronomic review'],'legume_mechanism':['inoculation details','nodulation observations','residue fate','nutrient inputs/exports and measurement basis'],'pest_break':['identified local organism','documented crop-specific host range','management/occurrence history','local review']},'unavailable_effects':{k:None for k in ['crop_yield_prediction','nitrogen_credit_kg_ha','water_saving_percent','net_irrigation_mm','gross_irrigation_mm','profit_difference_idr_ha','soil_health_gain']}})
    return record

RULE_INPUTS={
 'coverage':{'location':['farm.location.geometry_geojson','farm.location.representative_longitude','farm.location.representative_latitude'],'layer_support':['context.layer_support']},
 'calendar':{'dates':['farm.current_crop.sowing_date','farm.current_crop.transplanting_date','farm.current_crop.expected_harvest_date','planning.horizon','planning.existing_sequence','planning.slot_start_dates'],'duration_basis':['planning.duration_by_crop'],'duration_range':['planning.duration_by_crop'],'preparation_gap':['planning.preparation_gap_days','planning.existing_sequence'],'nursery_resource_when_relevant':['planning.nursery_separate_from_main_field','planning.nursery_location_ref']},
 'climate_exposure':{'time_mode':['context.time_mode'],'window':['context.climate_window','planning.horizon','planning.existing_sequence'],'explicit_climate_context':['context.explicit_climate_context','context.layer_support']},
 'ph_reference':{'pH_origin':['context.ph_reference_input','farm.soil_lab.ph_h2o'],'depth':['context.ph_reference_input','farm.soil_lab.depth_top_cm','farm.soil_lab.depth_bottom_cm'],'method_or_prediction_source':['context.ph_reference_input','farm.soil_lab.method','farm.soil_lab.laboratory'],'date_or_model_epoch':['context.ph_reference_input','farm.soil_lab.sampling_date'],'valid_value':['context.ph_reference_input','farm.soil_lab.ph_h2o']},
 'temperature_reference':{'historical_temperature_summary':['context.temperature_reference_input'],'crop_id':['farm.current_crop.crop_id','planning.existing_sequence']},
 'seasonal_et_reference':{'crop_id':['farm.current_crop.crop_id','planning.existing_sequence']},
 'paddy_upland_transition':{'sequence':['planning.existing_sequence','farm.rotation_history'],'rice_water_regime':['farm.current_crop.rice_water_regime','farm.current_crop.rice_ecosystem','planning.existing_sequence'],'drainage':['farm.irrigation.drainage_condition','farm.irrigation.water_table_depth_m'],'water_control':['farm.irrigation.water_control','farm.irrigation.availability_window_start','farm.irrigation.availability_window_end'],'soil_management':['farm.management.soil_management_for_transition','farm.management.tillage']},
 'legume_mechanism':{'sequence':['planning.existing_sequence'],'nodulation':['farm.management.nodulation_observations'],'inoculation':['farm.management.legume_inoculation'],'residue_fate':['farm.management.residue_fate'],'nutrient_balance':['farm.management.nutrient_balance','farm.management.fertilizer_history','farm.management.organic_amendments','farm.soil_lab.total_n_percent']},
 'pest_break':{'local_pest_or_pathogen':['farm.management.pest_disease_weed_history'],'host_range':['farm.management.local_host_range_evidence'],'management_history':['farm.management.pesticide_history','farm.management.residue_fate','farm.rotation_history']},
 'vegetation_context':{'exact_extracted_pixel':['context.vegetation_reference_input','context.layer_support'],'window':['context.vegetation_reference_input','planning.horizon'],'qa':['context.vegetation_reference_input','context.layer_support']},
 'gaez_context':{'containing_extracted_cell':['context.gaez_reference_input','context.layer_support'],'crop_code':['context.gaez_reference_input'],'management_regime_or_explicit_unknown':['context.gaez_reference_input','farm.current_crop.rice_ecosystem','farm.irrigation.rainfed']},
 'economics':{'marketable_yield':['farm.market.expected_marketable_yield_kg_ha'],'farm_gate_price':['farm.market.farm_gate_prices'],'costs':['farm.costs.seed_idr_ha','farm.costs.fertilizer_idr_ha','farm.costs.pest_management_idr_ha','farm.costs.labor_idr_ha','farm.costs.machinery_idr_ha','farm.costs.irrigation_idr_ha','farm.costs.other_idr_ha','farm.market.transport_storage_costs'],'units':['farm.market.currency','farm.market.farm_gate_prices','farm.market.transport_storage_costs'],'time_and_location_basis':['farm.costs.reference_season','farm.market.price_observed_at','farm.location.representative_longitude','farm.location.representative_latitude']},
}
def build_rules_and_gaps():
    spec=read(ROOT/'specs/rotation-method-v1.json')
    rules=[]
    for r in spec['rules']:
        assert set(r['input_requirements'])==set(RULE_INPUTS[r['id']])
        rules.append({'rule_id':r['id'],'requirements':[{'requirement':k,'input_paths':v} for k,v in RULE_INPUTS[r['id']].items()],'source_refs':r['source_refs'],'output_limit':r['output'],'status_without_farmer_data':'deferred_from_MVP' if r['id']=='economics' else ('public_context_available_after_explicit_selection' if r['id'] in ['coverage','climate_exposure','ph_reference','temperature_reference','seasonal_et_reference','vegetation_context','gaez_context'] else 'needs_explicit_scenario_or_farmer_input'),'original_91_paths':[x['path'] for x in FIELDS if x['origin']=='prepared_91' and r['id'] in x['rule_ids']],'supplemental_paths':[x['path'] for x in FIELDS if x['origin']!='prepared_91' and r['id'] in x['rule_ids']]})
    write('method-rule-input-map.json',{'method_version':spec['method_version'],'rule_count':len(rules),'all_91_fields_classified':True,'unmapped_active_fields':[],'legacy_unused_paths':[x['path'] for x in FIELDS if x['requirement_stage']=='legacy_unused'],'rules':rules,'notes':['Field-to-rule associations include contextual prerequisites; they do not claim every field is mandatory in every check.','Exact requirements are listed separately; e.g. soil total N alone does not satisfy a nutrient balance.','GAEZ regime is a model selection; farmer irrigation state does not automatically select high-management HRLM/HILM.']})
    gaps=[]
    for x in FIELDS:
        if x['requirement_stage']=='legacy_unused':continue
        if x['acquisition_class'] in ['scenario_configuration','provenance_metadata']:cat='scenario_configuration'
        elif x['acquisition_class']=='public_reference_selection':cat='public_reference_gap'
        elif x['acquisition_class']=='local_adviser':cat='local_validation_gap'
        else:cat='farmer_only_input'
        gaps.append({'id':'input:'+x['path'],'category':cat,'status':'available_reference_requires_explicit_selection' if cat=='public_reference_gap' else 'unknown_no_actual_field_supplied','path':x['path'],'rule_ids':x['rule_ids'],'can_fill_actual_from_public_sources':False,'next_action':'Keep null; public data supplies context only. User has no actual farm data and this does not block reference/demo work.' if cat=='farmer_only_input' else 'Select a public reference or an explicitly labelled scenario; never record as observed farm actual.' if cat in ['public_reference_gap','scenario_configuration'] else 'Requires an actual qualified local review/measurement; leave null.'})
    extra=[
      ('public:anjasmoro-duration-origin','public_reference_gap','filled','calendar','Official catalog explicitly reports 82–93 days after planting; preserve source differences and do not auto-select cultivar.'),
      ('public:rice-ecosystem-vocabulary','public_reference_gap','filled','paddy_upland_transition','Official FAO ecosystem definitions and separate operational water-regime/establishment vocabulary now documented.'),
      ('public:typed-input-units','public_reference_gap','filled','coverage','All 91 original fields typed and unit applicability explicit; negative latitude, hectares, records and legacy weighting corrected in additive contract.'),
      ('public:all-method-requirements','public_reference_gap','filled','calendar','All 12 rules input requirements linked to concrete original/supplemental paths.'),
      ('public:legacy-bsip-catalog-url','public_reference_gap','filled_via_official_brmp_alternative','calendar','Old BSIP host DNS failure preserved; same resource retrieved from official BRMP host, hash and visual QA captured.'),
      ('local:duration-calendar-calibration','local_validation_gap','unresolved','calendar','Cultivar and site-specific maturity, actual field-harvest dates, integer calendar conventions and management gaps require explicit scenario choices or local validation.'),
      ('local:paddy-upland-transition','local_validation_gap','unresolved','paddy_upland_transition','Drainage, water control, soil preparation and feasibility for a real field are unknown.'),
      ('local:legume-effects','local_validation_gap','unresolved','legume_mechanism','No measured fixation, residue/nutrient balance or local fertilizer-credit calibration; benefits remain null.'),
      ('local:pest-host-evidence','local_validation_gap','unresolved','pest_break','No identified field organism, local host range or validated rotation effect.'),
      ('local:ph-temperature-effect','local_validation_gap','unresolved','ph_reference','Species optima are historical references; no locally calibrated failure thresholds, yield response or stress-day rules.'),
      ('local:water-accounting','local_validation_gap','out_of_MVP','seasonal_et_reference','No calibrated local Kc, effective rainfall, root-zone balance, paddy seepage/percolation or actual irrigation-accounting model.'),
      ('local:economics','local_validation_gap','deferred_from_MVP','economics','Actual prices, costs, marketable yields and validated economic method absent; generic catalog yields cannot substitute.'),
      ('local:agronomic-approval','local_validation_gap','unresolved','coverage','Method remains reference_method_not_locally_validated; schema/reference coverage is not field approval.'),
    ]
    for gid,cat,status,rid,note in extra:gaps.append({'id':gid,'category':cat,'status':status,'rule_ids':[rid],'explanation':note,'can_fill_actual_from_public_sources':False})
    write('gap-register.json',{'schema_version':'1.0','created_at_utc':NOW,'categories':{'public_reference_gap':'Can enrich references or select already available public supports; cannot create farm actuals.','farmer_only_input':'Actual farmer/field observation;public sources cannot fill it.','local_validation_gap':'Needs real field measurements, agronomic review or calibration.','scenario_configuration':'Explicit planning/model choice; labelled assumptions may support a demo, never farm history.'},'user_context':'No actual farmer/field data supplied; user authorized publicly available sources only. Proceed with public context without requesting invented farm records.','gaps':gaps})
    return gaps

def verify_immutable():
    base=read(ROOT/'data/prepared/file-manifest.json')['files']
    bad=[x['path'] for x in base if not (ROOT/x['path']).exists() or digest(ROOT/x['path'])!=x['sha256']]
    assert len(base)==390 and not bad,bad
    return {'prepared_files_checked':len(base),'mismatches':bad,'prepared_immutable':True,'manifest_sha256':digest(ROOT/'data/prepared/file-manifest.json')}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    imm=verify_immutable()
    template,schema=build_contract()
    ev=evidence()
    gaps=build_rules_and_gaps()
    paths={x['path'] for x in FIELDS}
    assert len(paths)==len(FIELDS) and len(FIELDS)==len(leaf_paths({k:v for k,v in template.items() if k not in ['schema_version','is_template']}))
    for x in FIELDS:
        assert x['value'] is None and set(x['rule_ids'])<=set(RULES)
        assert x['rule_ids'] or x['requirement_stage']=='legacy_unused'
    for reqs in RULE_INPUTS.values():
        for pths in reqs.values():assert set(pths)<=paths,set(pths)-paths
    ids={x['id'] for x in ev['sources']}
    assert all(x['source_id'] in ids for x in ev['claims'])
    verified_sources=0
    for x in ev['sources']:
        if x.get('sha256'):
            assert digest(ROOT/x['path'])==x['sha256'];verified_sources+=1
    validation={'created_at_utc':NOW,**imm,'original_fields_typed':91,'supplemental_fields':len(FIELDS)-91,'total_fields':len(FIELDS),'all_template_field_values_null':True,'all_fields_rule_mapped_or_legacy_unused':True,'legacy_unused_fields':3,'method_rules_mapped':12,'source_hashes_verified':verified_sources,'claim_source_links_valid':True,'outcomes_remain_null':True,'json_schema_validation':'not_run','cross_field_semantics':'Documented contract requirements; not implemented backend checks.'}
    local_validator=ROOT/'work/validation-deps'
    if local_validator.is_dir():sys.path.insert(0,str(local_validator))
    try:
        import jsonschema
        jsonschema.Draft202012Validator.check_schema(schema)
        validator=jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker())
        validator.validate(template)
        cases=[
          ('negative_latitude_valid','farm.location.representative_latitude',-7.72,True),
          ('latitude_south_boundary_valid','farm.location.representative_latitude',-90,True),
          ('latitude_north_boundary_valid','farm.location.representative_latitude',90,True),
          ('latitude_out_of_range_invalid','farm.location.representative_latitude',-91,False),
          ('longitude_out_of_range_invalid','farm.location.representative_longitude',181,False),
          ('negative_area_invalid','farm.location.area_ha_reported',-1,False),
          ('known_zero_area_structurally_valid','farm.location.area_ha_reported',0,True),
          ('irrigation_fraction_out_of_range_invalid','farm.irrigation.application_efficiency_fraction',1.1,False),
          ('explicit_false_is_valid','farm.irrigation.rainfed',False,True),
          ('string_not_boolean','farm.irrigation.rainfed','false',False),
          ('unknown_crop_invalid','farm.current_crop.crop_id','invented_crop',False),
          ('impossible_date_invalid','farm.current_crop.sowing_date','2026-02-30',False),
          ('empty_history_structurally_valid','farm.rotation_history',[],True),
          ('duplicate_crop_ids_invalid','planning.allowed_crop_ids',['padi','padi'],False),
          ('more_than_three_locked_slots_invalid','planning.locked_prefix_length',4,False),
          ('fractional_gap_invalid','planning.preparation_gap_days',2.5,False),
          ('malformed_polygon_invalid','farm.location.geometry_geojson',{'type':'Polygon','coordinates':[[110.55,-7.72]]},False),
        ]
        checks=[]
        for label,path,value,expected in cases:
            candidate=deepcopy(template)
            nested_set(candidate,path,value)
            actual=validator.is_valid(candidate)
            assert actual==expected,label
            checks.append({'check':label,'passed':True,'expected_structural_validity':expected})
        # A sourced duration record maps a crop explicitly; no field value is saved.
        duration={k:None for k in DEFS['duration_record']['properties']}
        duration.update(crop_id='kedelai',minimum_days=82,maximum_days=93,basis_event='sowing',counting_convention='elapsed_day_zero',source_ref='kementan-variety-catalog-brmp',normalization_policy='explicit_source_integer_alternative')
        candidate=deepcopy(template)
        nested_set(candidate,'planning.duration_by_crop',[duration])
        assert validator.is_valid(candidate)
        checks.append({'check':'explicit_scenario_duration_record_valid','passed':True,'expected_structural_validity':True})
        duration['minimum_days']=82.5
        assert not validator.is_valid(candidate)
        checks.append({'check':'fractional_calendar_duration_invalid','passed':True,'expected_structural_validity':False})
        validation.update(json_schema_validation='passed_draft202012_schema_null_template_and_boundaries',schema_checks=checks,schema_check_count=len(checks),validator={'package':'jsonschema','version':'4.26.0','python_version':sys.version.split()[0],'isolated_target':'work/validation-deps','reproduce':'python -m pip install --target work/validation-deps jsonschema==4.26.0','synthetic_checks_only':'Boundary checks are ephemeral validation values; no actual farm records or geometry were generated.'})
    except ImportError:validation['json_schema_validation']='jsonschema_library_unavailable;structural_checks_passed'
    write('validation.json',validation)
    counts={c:sum(g['category']==c for g in gaps) for c in ['public_reference_gap','farmer_only_input','local_validation_gap','scenario_configuration']}
    summary={'schema_version':'1.0','created_at_utc':NOW,'module':'agronomy_supplement','status':'public_reference_enrichment_and_input_contract_complete;farm_actuals_unknown;local_validation_pending','what_filled':[{'id':'anjasmoro_duration_origin','status':'filled_reference','detail':'Official BRMP catalog PDF page 87 (printed 64), Lampiran 27: 82–93 hari setelah tanam. PVT 82.5–92.5 days and LAKIN 82.5–92.5 HST retained as distinct evidence.'},{'id':'rice_ecosystems_and_management','status':'filled_reference','detail':'FAO taxonomy, upland/rainfed lowland definitions; separate ecosystem, establishment and water-regime inputs with local review prerequisites.'},{'id':'input_contract','status':'filled_contract','detail':f'91 original fields plus {len(FIELDS)-91} additions, nullable typed schemas, units, record shapes, valid negative coordinates and explicit legacy-weight exclusion.'},{'id':'rule_input_mapping','status':'filled_contract','detail':'All 12 method rules and each named input requirement mapped; farmer-only, public-selection, scenario and local-validation gaps separated.'}],'remaining_gaps':{'category_counts':counts,'farmer_values_supplied':0,'farmer_values_policy':'All actuals remain null; public context can be used without actual farm records.','unresolved':['actual field boundary/location, crop rotation, cultivar, dates, water regime, drainage, lab, management, prices/costs/yields','explicit selection of references, labelled scenarios and calendar assumptions','local agronomic validation and calibration','water saving, yield, N credit, profit and soil-health outcomes remain unavailable']},'references':{'index':'data/supplemental/agronomy/source-evidence.json','snapshot_index':'data/supplemental/agronomy/source-snapshots.json','new_snapshots':sum(x['status'] in ['downloaded','cached_snapshot'] for x in ev['sources']),'reused_prepared_snapshots':sum(x['status']=='reused_prepared_snapshot' for x in ev['sources']),'failed_legacy_url_attempts':sum(x['status']=='failed' for x in ev['sources']),'claims':len(ev['claims']),'source_manifest':'data/supplemental/agronomy/manifest.json'},'validation':validation,'backend_implemented':False,'local_agronomic_validation':False}
    write('summary.json',summary)
    (OUT/'README.md').write_text('''# Agronomy supplement\n\nAdditive public evidence and input contract for FieldShift; prepared files remain unchanged. No farm observations, backend, recommendations or quantitative benefits were created.\n\n- `summary.json`: integration entry point and counts.\n- `agronomy-reference-supplement.json`: Anjasmoro duration alternatives, rice vocabulary and management prerequisites.\n- `source-evidence.json`: precise quotes, source paths, timestamps, SHA256 and PDF locators; source snapshots and three visual-QA pages in `sources/`.\n- `farm-input-contract.json`: typed/nullable definitions for every original 91 field plus required additions; units and records explicit.\n- `farm-input-complete.schema.json`: JSON Schema 2020-12; `farm-input-complete-template.json`: all field values null.\n- `method-rule-input-map.json`: all 12 method rules, exact prerequisites and original/supplemental field links.\n- `gap-register.json`: public-reference, farmer-only, scenario-configuration and local-validation needs.\n- `validation.json`: invariant/source/schema verification; `manifest.json`: output/script hashes.\n\nThe official BRMP catalog reports Anjasmoro maturity 82–93 days after planting; separate official sources report 82.5–92.5 days/HST. Preserve these source alternatives. Do not silently rewrite the prepared 82–92 reference, round fractional days, choose a farmer cultivar or claim a calibrated harvest date.\n\nRice ecosystem, establishment and actual water regime are separate. Rainfed lowland can flood; direct seeding alone does not identify upland. Drainage and paddy-to-upland management require actual local review. Operational water-regime terms are project vocabulary, not direct FAO category codes.\n\nLegacy weights are inactive. The MVP uses explicit priority labels with no weighting/ranking. Negative latitude is valid. Area units are hectares. Histories/market records have explicit shapes; monetary and yield data stay deferred.\n\nEvery supplied actual value remains null. Empty array, zero, false and unknown are distinct. Public soil predictions belong to context, never laboratory results. Geometry-derived area requires a real farmer boundary and geodesic calculation. The JSON Schema covers structural types; semantic geometry/calendar/source-support validations are documented and remain future implementation requirements.\n\nRebuild offline with `scripts/data/supplemental_agronomy/build_supplement.py`. Full schema QA uses Python 3.11 with the isolated `work/validation-deps` installation of `jsonschema==4.26.0`; the compiled dependency must match the Python version. The build records the validator version and 19 ephemeral boundary checks. Fetching and PDF extraction use the bundled Python with `pypdf`. `fetch_sources.py` caches official sources, records failures, and bounds each download to 8 MB and total snapshots to 20 MB. Source PDFs are read-only; no PDF authored.\n''',encoding='utf8')
    files=[]
    for folder in [OUT,ROOT/'scripts/data/supplemental_agronomy']:
        for p in sorted(folder.rglob('*')):
            if p.is_file() and p.name!='manifest.json' and '__pycache__' not in p.parts:files.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)})
    write('manifest.json',{'created_at_utc':NOW,'file_count':len(files),'files':files,'excludes':['manifest.json(self)'],'prepared_invariance':imm})
    print(json.dumps({'fields':len(FIELDS),'gaps':len(gaps),'files_manifested':len(files),'validation':validation},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
