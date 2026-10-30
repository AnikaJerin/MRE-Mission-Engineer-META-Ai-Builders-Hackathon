"""Researcher-supplied MRE records. Missing is not zero; provenance is not authentication."""
import math
from copy import deepcopy
from .evidence import EvidenceError
from .physics import OXIDES
from .performance_contract import EXTRA_NUMERIC,EXTRA_TEXT,EXTRA_UNITS,CHOICES,TARGET_FIELDS

CANDIDATES=('gas_accounting_review','current_record_review','material_characterization_review','repeat_run_comparison')
NUMERIC_FIELDS=('temperature_C','current_A','duration_s','collected_o2_g','voltage_V','sample_mass_g','oxygen_uncertainty_g','current_uncertainty_A','duration_uncertainty_s','available_hours','budget_usd')
NUMERIC_FIELDS+=EXTRA_NUMERIC
TEXT_FIELDS=('experiment_name','question','feedstock','anode_material','cathode_material','calibration_reference','gas_measurement_method','records_reference','observations','source_label')
TEXT_FIELDS+=EXTRA_TEXT
ENUMS={'process':['molten_regolith_electrolysis'],'configuration':['unknown','hollow_ysz_pt','other_mre'],
 'calibration_status':['unknown','reported_available','not_available'],'time_alignment':['unknown','reported_same_interval','different_interval']}
DEFAULTS={'process':'molten_regolith_electrolysis','configuration':'unknown','calibration_status':'unknown','time_alignment':'unknown',
 'question':'What does the oxygen accounting support, what remains uncertain, and which evidence should be checked next?'}
ENUMS.update({k:[v[0] for v in choices] for k,choices in CHOICES.items()})
DEFAULTS.update({k:choices[0][0] for k,choices in CHOICES.items()})
ALLOWED=set(NUMERIC_FIELDS)|set(TEXT_FIELDS)|set(ENUMS)|{'trace','composition','test_estimates','resistance_trace','reactor_scenario'}
UNITS={'temperature_C':'degC','current_A':'A','duration_s':'s','collected_o2_g':'g','voltage_V':'V','sample_mass_g':'g','oxygen_uncertainty_g':'g','current_uncertainty_A':'A','duration_uncertainty_s':'s','available_hours':'h','budget_usd':'USD'}
UNITS.update(EXTRA_UNITS)


def finite(value,label,positive=False):
    try:valid=type(value) in (int,float) and math.isfinite(value) and value>=0 and (not positive or value>0)
    except OverflowError:valid=False
    if not valid:raise EvidenceError(f'{label}: enter a finite {"positive" if positive else "nonnegative"} number, or leave an optional field blank')
    return float(value)


def validate_input(value):
    if not isinstance(value,dict) or set(value)-ALLOWED:raise EvidenceError('Unexpected experiment fields; use the input form or current Excel template')
    data={**deepcopy(DEFAULTS),**deepcopy(value)}
    if data.get('reactor_scenario') is not None:
        from .reactor_field import validate_scenario
        data['reactor_scenario']=validate_scenario(data['reactor_scenario'])
    for key in TEXT_FIELDS:
        v=data.get(key)
        if v is None or v=='':data[key]=None;continue
        if not isinstance(v,str) or len(v)> (1000 if key=='observations' else 500):raise EvidenceError(f'{key}: text is too long or not text')
        data[key]=v.strip() or None
    if not data.get('experiment_name'):raise EvidenceError('Enter an experiment name')
    if not data.get('question'):data['question']=DEFAULTS['question']
    for key,allowed in ENUMS.items():
        if data.get(key) not in allowed:raise EvidenceError(f'{key}: unsupported selection')
    for key in NUMERIC_FIELDS:
        v=data.get(key)
        data[key]=None if v is None or v=='' else finite(v,key,positive=key in ('current_A','duration_s','sample_mass_g'))
    if data['duration_s'] is None:raise EvidenceError('Electrolysis duration in seconds is required')
    trace=data.get('trace') or []
    if not isinstance(trace,list) or len(trace)>1000 or (trace and len(trace)<2):raise EvidenceError('Current trace requires 2–1000 data rows')
    clean=[]
    for row in trace:
        if not isinstance(row,dict) or set(row)-{'time_s','current_A','voltage_V','source'}:raise EvidenceError('Unknown current-trace columns')
        t=finite(row.get('time_s'),'Trace time');current=finite(row.get('current_A'),'Trace current')
        voltage=row.get('voltage_V');voltage=None if voltage is None or voltage=='' else finite(voltage,'Trace voltage')
        source=row.get('source') or None
        if source is not None and (not isinstance(source,str) or len(source)>300):raise EvidenceError('Invalid trace source')
        if clean and t<=clean[-1]['time_s']:raise EvidenceError('Trace time must strictly increase; duplicate/reversed rows are not sorted silently')
        clean.append({'time_s':t,'current_A':current,'voltage_V':voltage,'source':source})
    if clean:
        if data['current_A'] is not None:raise EvidenceError('Supply either a constant current or a current trace, not both')
        if clean[0]['time_s']!=0 or abs(clean[-1]['time_s']-data['duration_s'])>1e-6:raise EvidenceError('Trace must start at 0 and end at the declared duration; no extrapolation')
        if any(r['voltage_V'] is None for r in clean) and any(r['voltage_V'] is not None for r in clean):raise EvidenceError('Trace voltage must be complete or entirely blank')
        if data['voltage_V'] is not None:raise EvidenceError('Do not mix scalar voltage with a current trace; use a complete aligned voltage column')
        if not any(r['current_A']>0 for r in clean):raise EvidenceError('A zero-current trace has no positive charge budget')
        if any(data[k] is not None for k in ('current_uncertainty_A','duration_uncertainty_s')):raise EvidenceError('Scalar current/time uncertainty bounds are not supported for traces; retain them in observations')
    elif data['current_A'] is None:raise EvidenceError('Enter constant current in A, or upload a current trace')
    data['trace']=clean
    for uncertainty,target in (('current_uncertainty_A','current_A'),('duration_uncertainty_s','duration_s')):
        if data[uncertainty] is not None and data[target] is not None and data[uncertainty]>=data[target]:raise EvidenceError(f'{uncertainty} must leave a positive lower bound')
    composition=data.get('composition')
    if composition:
        if not isinstance(composition,dict) or set(composition)!={'analysis_id','source','rows'}:raise EvidenceError('Composition requires one analysis ID, source and oxide rows')
        if any(not isinstance(composition[k],str) or not composition[k].strip() or len(composition[k])>300 for k in ('analysis_id','source')):raise EvidenceError('Composition analysis ID and source are required')
        rows=composition['rows']
        if not isinstance(rows,list) or not 1<=len(rows)<=len(OXIDES):raise EvidenceError('Use one supported oxide analysis')
        seen=set()
        for row in rows:
            if not isinstance(row,dict) or set(row)!={'oxide','wt_percent'}:raise EvidenceError('Composition rows require oxide and wt_percent')
            if not isinstance(row['oxide'],str) or row['oxide'] not in OXIDES or row['oxide'] in seen:raise EvidenceError('Unsupported or duplicate oxide; total Fe is not silently speciated')
            seen.add(row['oxide']);row['wt_percent']=finite(row['wt_percent'],'Oxide wt%')
        total=math.fsum(r['wt_percent'] for r in rows)
        if not 0<total<=100+1e-8:raise EvidenceError('Oxide wt% total must be above zero and no more than 100; no normalization')
    data['composition']=composition or None
    estimates=data.get('test_estimates') or {}
    if not isinstance(estimates,dict) or set(estimates)-set(CANDIDATES):raise EvidenceError('Unknown diagnostic estimate')
    for name,row in list(estimates.items()):
        if not isinstance(row,dict) or set(row)-{'hours','cost_usd'}:raise EvidenceError('Diagnostic estimates use hours and cost_usd only')
        for k in ('hours','cost_usd'):
            row[k]=None if row.get(k) in (None,'') else finite(row[k],name+' '+k)
        if row['hours'] is None and row['cost_usd'] is None:del estimates[name]
    data['test_estimates']=estimates
    validate_performance(data)
    return data


def validate_performance(data):
    for key in ('initial_resistance_ohm','final_resistance_ohm','active_anode_area_cm2','initial_wall_thickness_um','thermal_exposure_h','endurance_test_h','target_endurance_h','system_operating_h'):
        if data[key] is not None and data[key]<=0:raise EvidenceError(key+': must be positive if supplied')
    for key in ('oxygen_purity_percent','target_min_oxygen_purity_percent','noncondensables_percent','condensables_percent'):
        if data[key] is not None and data[key]>100:raise EvidenceError(key+': percent must not exceed 100')
    if data['thermal_cycles'] is not None and not data['thermal_cycles'].is_integer():raise EvidenceError('Thermal cycles must be a whole count')
    if data['repairs_count'] is not None and not data['repairs_count'].is_integer():raise EvidenceError('Repairs must be a whole count')
    if data['system_operating_h'] is not None and data['system_operating_h']+1e-10<data['duration_s']/3600:raise EvidenceError('Full-system window cannot be shorter than its electrolysis interval')
    if data['thermal_exposure_h'] is not None and data['thermal_exposure_h']+1e-10<data['duration_s']/3600:raise EvidenceError('Total hot-melt exposure cannot be shorter than its electrolysis duration')
    if all(data[k] is not None for k in ('temperature_min_C','temperature_max_C')) and data['temperature_min_C']>data['temperature_max_C']:raise EvidenceError('Minimum temperature exceeds maximum')
    if data['endurance_run_alignment']=='same_demonstration' and data['endurance_test_h'] is not None and data['system_operating_h'] is not None and data['endurance_test_h']>data['system_operating_h']:raise EvidenceError('Observed endurance exceeds the full window of the same system demonstration')
    if data['failure_time_h'] is not None:
        if data['endurance_outcome']!='failure_observed' or data['endurance_test_h'] is None or data['failure_time_h']>data['endurance_test_h']:raise EvidenceError('Failure time requires an observed failure within a declared endurance run')
    if data['retirement_wall_loss_um'] is not None and data['initial_wall_thickness_um'] is not None and data['retirement_wall_loss_um']>data['initial_wall_thickness_um']:raise EvidenceError('Declared retirement wall loss exceeds initial wall thickness')
    trace=data.get('resistance_trace') or []
    if not isinstance(trace,list) or len(trace)>1000 or (trace and len(trace)<2):raise EvidenceError('Resistance history requires 2–1000 rows')
    clean=[]
    for row in trace:
        if not isinstance(row,dict) or set(row)-{'time_s','resistance_ohm','source'}:raise EvidenceError('Resistance rows require time_s, resistance_ohm, optional source')
        t=finite(row.get('time_s'),'Resistance time');r=finite(row.get('resistance_ohm'),'Measured resistance',positive=True)
        source=row.get('source')
        if source is not None and (not isinstance(source,str) or len(source)>300):raise EvidenceError('Invalid resistance record source')
        if t>data['duration_s'] or (clean and t<=clean[-1]['time_s']):raise EvidenceError('Resistance timestamps must increase within the electrolysis interval')
        clean.append({'time_s':t,'resistance_ohm':r,'source':source})
    if clean and any(data[k] is not None for k in ('initial_resistance_ohm','final_resistance_ohm')):raise EvidenceError('Use resistance history or scalar endpoints, not both')
    data['resistance_trace']=clean


def readiness(data,provenance=None):
    gaps=[]
    if not data['trace']:gaps.append({'id':'measured_current_trace','message':'Current is a declared constant, not a measured current history.'})
    if data['collected_o2_g'] is None:gaps.append({'id':'oxygen_mass','message':'Collected oxygen mass is not supplied; no collected-to-charge comparison.'})
    if data['time_alignment']!='reported_same_interval':gaps.append({'id':'time_alignment','message':'The gas and electrical measurement windows are not declared aligned.'})
    if data['calibration_status']!='reported_available' or not data['calibration_reference']:gaps.append({'id':'gas_calibration','message':'Applicable gas calibration documentation is not identified.'})
    if not data['gas_measurement_method']:gaps.append({'id':'measurement_method','message':'The oxygen measurement/conversion method is not identified.'})
    if data['oxygen_uncertainty_g'] is None:gaps.append({'id':'oxygen_uncertainty','message':'Oxygen measurement uncertainty/bounds are unknown.'})
    identified_upload=bool(provenance and provenance.get('kind')=='excel' and provenance.get('filename') and provenance.get('import_id'))
    if not data['records_reference'] and not identified_upload:gaps.append({'id':'original_records','message':'Your measurement record is not identified. Backend scientific references are already provided; the provenance of this new measurement is separate.'})
    if not data['feedstock']:gaps.append({'id':'feedstock','message':'Feedstock identity is unknown.'})
    if data['configuration']=='unknown' or not data['anode_material'] or not data['cathode_material']:gaps.append({'id':'configuration','message':'Configuration/electrode context is incomplete; material mechanisms cannot be transferred.'})
    if data['temperature_C'] is None:gaps.append({'id':'temperature_context','message':'Operating temperature is not identified; thermal/material interpretation is limited.'})
    if data['composition'] and data['sample_mass_g'] is None:gaps.append({'id':'inventory_mass','message':'Oxide analysis is supplied without sample mass; oxygen inventory cannot be calculated.'})
    if not ((data['observations'] and data['records_reference']) or (data['post_test_method'] and data['post_test_findings'] and data['post_test_reference'])):gaps.append({'id':'material_records','message':'Applicable post-test material observations/records are not identified.'})
    if any(data[k] is not None for k in TARGET_FIELDS) and not data['target_reference']:gaps.append({'id':'target_reference','message':'Target values have no requirement/source locator; no target verdict is released.'})
    if (data['resistance_trace'] or any(data[k] is not None for k in ('initial_resistance_ohm','final_resistance_ohm'))) and (data['resistance_comparability']!='same_conditions' or not data['resistance_reference']):gaps.append({'id':'resistance_context','message':'Resistance comparison needs comparable measurement conditions and a record locator.'})
    if data['wall_loss_um'] is not None and (not data['wall_measurement_reference'] or data['wall_rate_basis']=='unknown'):gaps.append({'id':'wall_context','message':'Wall loss needs its measurement record and declared exposure-time basis.'})
    if data['crack_observation']!='not_assessed' and not data['crack_reference']:gaps.append({'id':'crack_context','message':'Inspection outcome lacks its method/record locator.'})
    if data['endurance_test_h'] is not None and (not data['endurance_reference'] or data['endurance_outcome']=='not_supplied'):gaps.append({'id':'endurance_context','message':'Endurance duration needs its outcome and matching conditions/record.'})
    if data['thermal_cycles'] is not None and not data['thermal_reference']:gaps.append({'id':'thermal_context','message':'Cycle count lacks a cycle definition and thermal-history record.'})
    if data['reported_projected_lifetime_h'] is not None and not data['projection_reference']:gaps.append({'id':'projection_context','message':'External lifetime projection has no identified model or assumptions.'})
    if data['total_energy_kWh'] is not None and (data['energy_scope']=='unknown' or data['energy_time_alignment']!='reported_same_interval' or not data['energy_reference']):gaps.append({'id':'energy_context','message':'Energy comparison needs a documented system boundary and matched oxygen/time interval.'})
    if data['oxygen_purity_percent'] is not None and (not data['purity_reference'] or data['purity_basis']=='unknown' or data['purity_quantity_basis']=='unknown'):gaps.append({'id':'purity_context','message':'Reported purity needs its method, record and dry/wet reference basis.'})
    if data['processed_regolith_g'] is not None and (data['feedstock_mass_basis']!='processed_in_window' or not data['feedstock_mass_reference']):gaps.append({'id':'processed_mass_context','message':'Processed-regolith mass needs a matching window and method record; loaded batch mass is different.'})
    if data['available_oxygen_g'] is not None and (data['available_oxygen_basis']!='matched_processed_feedstock' or not data['available_oxygen_reference']):gaps.append({'id':'available_oxygen_context','message':'Extraction yield needs documented available oxygen in matching processed feedstock.'})
    return {'gaps':gaps,'status':'evidence_needed' if gaps else 'records_identified_for_review',
      'scope':'User declarations and record locators are not independent calibration or raw-data authenticity checks.'}
