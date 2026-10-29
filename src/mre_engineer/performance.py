"""Input-derived metric ledger. No publication numbers used as universal cutoffs."""
import math
from .evidence import EvidenceError
from .performance_reference import reference
from .performance_contract import load_profile

# Display/derivation metadata, never a prewritten case verdict.
DEFINITIONS={
 'oxygen_per_processed_regolith_kg_kg':('System output oxygen / processed regolith','kg/kg','matched system-output O2 mass / measured processed-regolith mass',['collected_o2_g','processed_regolith_g','feedstock_mass_basis','feedstock_mass_reference','measurement_window_scope','oxygen_measurement_location']),
 'oxygen_extraction_yield_percent':('System collected O2 / documented available oxygen','%','100 * matched system-output O2 / available oxygen in processed feedstock',['collected_o2_g','available_oxygen_g','available_oxygen_reference','available_oxygen_basis','measurement_window_scope','oxygen_measurement_location']),
 'system_oxygen_rate_kg_h':('Full-system output oxygen rate','kg/h','system-output O2 kg / full operations-window hours',['collected_o2_g','system_operating_h','measurement_window_scope','oxygen_measurement_location']),
 'oxygen_per_energy_kg_kWh':('Full-system oxygen per energy input','kg/kWh','system-output O2 kg / matched total-system kWh',['collected_o2_g','total_energy_kWh','energy_scope','energy_time_alignment','measurement_window_scope','oxygen_measurement_location']),
 'consumables_kg_per_kg_o2':('Other consumables per output oxygen','kg/kg O2','matched-window other consumables / system-output O2',['consumables_g','collected_o2_g','measurement_window_scope','oxygen_measurement_location']),
 'oxygen_rate_g_h':('Reported collected oxygen rate','g/h','m / electrolysis hours',['collected_o2_g','duration_s','time_alignment']),
 'collected_mass_fraction_percent':('Reported O2 / feedstock mass','%','100 * reported O2 / batch mass',['collected_o2_g','sample_mass_g']),
 'current_density_A_cm2':('Average current density','A/cm²','integrated charge / duration / active area',['trace','current_A','duration_s','active_anode_area_cm2']),
 'cell_specific_energy_kWh_kg':('Cell electrical energy / collected O2','kWh/kg','integrated cell IV energy / reported O2 kg',['trace','current_A','voltage_V','duration_s','collected_o2_g','time_alignment']),
 'reported_specific_energy_kWh_kg':('Metered energy / collected O2','kWh/kg','reported matched-window energy / reported O2 kg',['total_energy_kWh','energy_scope','energy_time_alignment','collected_o2_g','time_alignment']),
 'resistance_change_percent':('Measured resistance endpoint change','%','100 * (Rfinal - Rinitial) / Rinitial',['resistance_trace','initial_resistance_ohm','final_resistance_ohm','resistance_comparability']),
 'resistance_slope_ohm_h':('Resistance history linear slope','Ω/h','OLS slope across all supplied R(t) points',['resistance_trace','resistance_comparability']),
 'wall_loss_um':('Reported measured wall loss','µm','direct user-supplied measurement',['wall_loss_um','wall_measurement_reference']),
 'wall_loss_rate_um_h':('Wall-loss exposure-average rate','µm/h','measured wall loss / declared exposure-time basis',['wall_loss_um','wall_rate_basis','thermal_exposure_h','duration_s']),
 'wall_loss_fraction_percent':('Wall loss / initial thickness','%','100 * wall loss / initial thickness',['wall_loss_um','initial_wall_thickness_um']),
 'conditional_remaining_wall_life_h':('Conditional remaining wall-life projection','h','max(0, declared retirement loss - measured loss) / exposure-average rate',['projection_model','retirement_wall_loss_um','wall_loss_um','wall_rate_basis','wall_measurement_reference']),
 'temperature_span_C':('Reported operating temperature span','°C','reported maximum - minimum',['temperature_min_C','temperature_max_C']),
 'thermal_cycles':('Reported completed thermal cycles','count','direct reported count; no endurance extrapolation',['thermal_cycles','thermal_reference']),
 'endurance_test_h':('Observed continuous endurance duration','h','direct observed test duration',['endurance_test_h','endurance_outcome','endurance_reference']),
 'reported_projected_lifetime_h':('External lifetime projection','h','reported external model estimate, not measured endurance',['reported_projected_lifetime_h','projection_reference']),
 'endurance_target_coverage_percent':('Observed test duration / duration requirement','%','100 * observed duration / declared required duration',['endurance_test_h','target_endurance_h','endurance_outcome']),
 'oxygen_purity_percent':('Reported gas oxygen purity','%','reported measurement; dry/wet basis retained',['oxygen_purity_percent','purity_basis','purity_reference']),
}

def assess(data,calc,profile=None):
    h=data['duration_s']/3600;mass=data['collected_o2_g'];aligned=data['time_alignment']=='reported_same_interval';rt=data['resistance_trace']
    initial=rt[0]['resistance_ohm'] if rt else data['initial_resistance_ohm'];final=rt[-1]['resistance_ohm'] if rt else data['final_resistance_ohm']
    slope=None
    if rt:
        xs=[r['time_s']/3600 for r in rt];ys=[r['resistance_ohm'] for r in rt];mx=math.fsum(xs)/len(xs);my=math.fsum(ys)/len(ys)
        slope=math.fsum((x-mx)*(y-my) for x,y in zip(xs,ys))/math.fsum((x-mx)**2 for x in xs)
    exposure=data['thermal_exposure_h'] if data['wall_rate_basis']=='thermal_exposure' else h if data['wall_rate_basis']=='electrolysis' else None
    rate=data['wall_loss_um']/exposure if data['wall_loss_um'] is not None and exposure is not None else None
    full_system=data['measurement_window_scope']=='full_system_operation' and data['oxygen_measurement_location']=='system_output'
    v={
      'oxygen_per_processed_regolith_kg_kg':mass/data['processed_regolith_g'] if mass is not None and data['processed_regolith_g'] is not None and data['processed_regolith_g']>0 and data['feedstock_mass_basis']=='processed_in_window' and data['feedstock_mass_reference'] and full_system else None,
      'oxygen_extraction_yield_percent':100*mass/data['available_oxygen_g'] if mass is not None and data['available_oxygen_g'] is not None and data['available_oxygen_g']>0 and data['available_oxygen_basis']=='matched_processed_feedstock' and data['available_oxygen_reference'] and full_system else None,
      'system_oxygen_rate_kg_h':mass/1000/data['system_operating_h'] if mass is not None and data['system_operating_h'] is not None and data['measurement_window_scope']=='full_system_operation' and data['oxygen_measurement_location']=='system_output' else None,
      'oxygen_per_energy_kg_kWh':mass/1000/data['total_energy_kWh'] if mass is not None and data['total_energy_kWh'] is not None and data['total_energy_kWh']>0 and data['energy_scope']=='total_system' and data['energy_time_alignment']=='reported_same_interval' and data['measurement_window_scope']=='full_system_operation' and data['oxygen_measurement_location']=='system_output' else None,
      'consumables_kg_per_kg_o2':data['consumables_g']/mass if mass is not None and mass>0 and data['consumables_g'] is not None and data['measurement_window_scope']=='full_system_operation' and data['oxygen_measurement_location']=='system_output' else None,
      'oxygen_rate_g_h':mass/h if mass is not None and aligned else None,
      'collected_mass_fraction_percent':100*mass/data['sample_mass_g'] if mass is not None and data['sample_mass_g'] is not None else None,
      'current_density_A_cm2':calc['charge_C']/data['duration_s']/data['active_anode_area_cm2'] if data['active_anode_area_cm2'] is not None else None,
      'cell_specific_energy_kWh_kg':calc['electrical_energy_Wh']/mass if calc['electrical_energy_Wh'] is not None and mass is not None and mass>0 and aligned else None,
      'reported_specific_energy_kWh_kg':data['total_energy_kWh']*1000/mass if data['total_energy_kWh'] is not None and mass is not None and mass>0 and aligned and data['energy_time_alignment']=='reported_same_interval' and data['energy_scope']!='unknown' else None,
      'resistance_change_percent':100*(final-initial)/initial if initial is not None and final is not None else None,
      'resistance_slope_ohm_h':slope,'wall_loss_um':data['wall_loss_um'],'wall_loss_rate_um_h':rate,
      'wall_loss_fraction_percent':100*data['wall_loss_um']/data['initial_wall_thickness_um'] if data['wall_loss_um'] is not None and data['initial_wall_thickness_um'] is not None else None,
      'conditional_remaining_wall_life_h':max(0,(data['retirement_wall_loss_um']-data['wall_loss_um'])/rate) if data['projection_model']=='constant_wall_loss' and rate is not None and rate>0 and data['retirement_wall_loss_um'] is not None and data['wall_measurement_reference'] else None,
      'temperature_span_C':data['temperature_max_C']-data['temperature_min_C'] if data['temperature_max_C'] is not None and data['temperature_min_C'] is not None else None,
      'thermal_cycles':data['thermal_cycles'],'endurance_test_h':data['endurance_test_h'],'reported_projected_lifetime_h':data['reported_projected_lifetime_h'],
      'endurance_target_coverage_percent':100*data['endurance_test_h']/data['target_endurance_h'] if data['endurance_test_h'] is not None and data['target_endurance_h'] is not None and data['target_endurance_h']>0 else None,
      'oxygen_purity_percent':data['oxygen_purity_percent']}
    expected=reference(data);checks={}
    for key,value in v.items():
        other=expected[key];tolerance=max(1e-10,abs(other or 0)*1e-10)
        passed=value is None and other is None or value is not None and other is not None and math.isfinite(value) and math.isfinite(other) and abs(value-other)<=tolerance
        checks[key]={'production':value,'independent':other,'tolerance':tolerance,'passed':passed}
    if not all(c['passed'] for c in checks.values()):raise EvidenceError('Performance arithmetic disagreement; paid work not started')
    metrics={k:{'value':v[k],'label':spec[0],'unit':spec[1],'formula':spec[2],'input_fields':spec[3],'independent_check':checks[k],
      'availability':'calculated_or_reported' if v[k] is not None else 'missing_input_or_inapplicable_basis'} for k,spec in DEFINITIONS.items()}
    target_checks=compare_targets(data,v)
    flags=[]
    if v['oxygen_extraction_yield_percent'] is not None and v['oxygen_extraction_yield_percent']>100:flags.append('reported_system_oxygen_exceeds_declared_available_oxygen')
    if data['available_oxygen_g'] is not None and data['processed_regolith_g'] is not None and data['available_oxygen_g']>data['processed_regolith_g']:flags.append('declared_available_oxygen_exceeds_processed_feedstock_mass')
    if data['wall_loss_um'] is not None and data['initial_wall_thickness_um'] is not None and data['wall_loss_um']>data['initial_wall_thickness_um']:flags.append('reported_wall_loss_exceeds_initial_thickness')
    if data['total_energy_kWh'] is not None and data['energy_scope']=='total_system' and data['energy_time_alignment']=='reported_same_interval' and calc['electrical_energy_Wh'] is not None and data['total_energy_kWh']*1000<calc['electrical_energy_Wh']-1e-8:flags.append('reported_total_energy_below_computed_cell_energy')
    return {'version':'mre-performance-v2','charge_accounting':{k:calc[k] for k in ('charge_C','ideal_o2_g','reported_collected_o2_g','apparent_collected_to_charge_ratio','basis')},'metrics':metrics,'target_checks':target_checks,'official_profile_checks':profile_checks(data,v,profile),'input_consistency_flags':flags,
      'resistance_basis':'full_history_OLS' if rt else 'two_endpoints_only','resistance_comparable':data['resistance_comparability']=='same_conditions' and bool(data['resistance_reference']),
      'wall_rate_time_basis':data['wall_rate_basis'],'energy_boundary':data['energy_scope'],'independent_checks_passed':True,
      'scope':'Input-derived calculations and declared-target checks. No universal grade, NASA qualification, measured reliability or causal failure probability. Reported values are not independently authenticated.'}

def compare_targets(data,v):
    specs=[('target_oxygen_rate_g_h','oxygen_rate_g_h','minimum'),('target_max_specific_energy_kWh_kg','reported_specific_energy_kWh_kg','maximum'),('target_min_oxygen_purity_percent','oxygen_purity_percent','minimum'),('target_max_wall_loss_um','wall_loss_um','maximum'),('target_max_abs_resistance_change_percent','resistance_change_percent','maximum_absolute'),('target_endurance_h','endurance_test_h','minimum'),('target_max_temperature_C','reported_peak_temperature_C','maximum')]
    out=[]
    for field,key,direction in specs:
        target=data[field]
        if target is None:continue
        actual=data['temperature_max_C'] if key=='reported_peak_temperature_C' else v[key];missing=[]
        if not data['target_reference']:missing.append('target_reference')
        if actual is None:missing.append('metric_value')
        if field=='target_oxygen_rate_g_h' and (not data['calibration_reference'] or data['calibration_status']!='reported_available' or not data['gas_measurement_method']):missing.append('documented_oxygen_measurement')
        if field=='target_max_specific_energy_kWh_kg' and (not data['energy_reference'] or data['target_energy_scope']=='unknown' or data['energy_scope']!=data['target_energy_scope']):missing.append('matching_energy_boundary_and_record')
        if field=='target_min_oxygen_purity_percent' and (not data['purity_reference'] or data['purity_basis']=='unknown' or data['purity_quantity_basis']=='unknown' or data['purity_quantity_basis']!=data['target_purity_quantity_basis']):missing.append('purity_record_and_matching_quantity_basis')
        if field=='target_max_temperature_C' and not data['thermal_reference']:missing.append('measured_temperature_record')
        if field=='target_max_wall_loss_um' and not data['wall_measurement_reference']:missing.append('wall_measurement_reference')
        if field=='target_max_abs_resistance_change_percent' and (data['resistance_comparability']!='same_conditions' or not data['resistance_reference']):missing.append('comparable_resistance_record')
        if field=='target_endurance_h' and (not data['endurance_reference'] or data['endurance_outcome']!='no_failure_reported' or data['endurance_run_alignment']!='same_demonstration'):missing.append('documented_no_failure_continuous_run')
        compared=abs(actual) if actual is not None and direction=='maximum_absolute' else actual
        met=None if compared is None else compared>=target if direction=='minimum' else compared<=target
        uncertain=field=='target_max_wall_loss_um' and actual is not None and data['wall_loss_uncertainty_um'] is not None and actual-data['wall_loss_uncertainty_um']<=target<actual+data['wall_loss_uncertainty_um']
        if uncertain:missing.append('wall_bound_straddles_target')
        out.append({'target_field':field,'metric_id':key,'actual':actual,'target':target,'direction':direction,'nominal_relation_met':met,
          'status':'insufficient_evidence' if missing else 'within_declared_target' if met else 'outside_declared_target','missing_prerequisites':missing,'target_reference':data['target_reference'],
          'scope':'Nominal conditional comparison with a user-declared requirement, not a NASA acceptance limit or reliability qualification. Except the explicitly supplied wall-loss bound, measurement uncertainty is not propagated into these target comparisons.'})
    return out


def profile_checks(data,values,profile=None):
    if data['comparison_profile']=='none':return []
    profile=profile or load_profile();out=[]
    for criterion in profile['criteria']:
        result={**criterion,'source_id':profile['source_id'],'actual':None,'status':'evidence_needed','missing':[],'scope':profile['scope']}
        if criterion['kind']=='required_demo':
            result['actual']=values['endurance_test_h']
            for key in ('integration_reference','endurance_reference','repair_reference'):
                if not data[key]:result['missing'].append(key)
            if data['measurement_window_scope']!='full_system_operation':result['missing'].append('full_system_operation_window')
            if data['integrated_flow_status']!='demonstrated':result['missing'].append('demonstrated_integrated_flow')
            if data['endurance_run_alignment']!='same_demonstration':result['missing'].append('same_demonstration_endurance_record')
            if data['system_operating_h'] is None or (result['actual'] is not None and result['actual']>data['system_operating_h']):result['missing'].append('matching_full_system_duration')
            if data['continuous_operation_status']!='reported_continuous':result['missing'].append('documented_continuous_system_operation')
            if data['repairs_count'] is None:result['missing'].append('repairs_count')
            if data['consumables_g'] is None or not data['consumables_reference']:result['missing'].append('consumables_records')
            if result['actual'] is None:result['missing'].append('observed_continuous_hours')
            if not result['missing']:result['status']='duration_criterion_numerically_met' if result['actual']>=criterion['value'] else 'duration_below_selected_requirement'
        elif criterion['kind']=='encouraged_pilot':
            result['actual']=values['system_oxygen_rate_kg_h']
            if result['actual'] is None or not data['records_reference']:result['missing'].append('full_window_system_output_measurement')
            if data['calibration_status']!='reported_available' or not data['calibration_reference']:result['missing'].append('gas_calibration_record')
            if not result['missing']:result['status']='at_or_above_encouraged_reference' if result['actual']>=criterion['value'] else 'below_encouraged_reference_not_a_required_failure'
        elif criterion['kind']=='notional_cleanliness':
            result['actual']=data['noncondensables_percent' if criterion['id'].endswith('NC') else 'condensables_percent']
            result['status']='context_only_notional_target';result['missing']=['matched_liquefaction_specification_and_abundance_basis_review']
        else:
            result['status']='scaling_evidence_requires_review';result['record']=data['scalability_reference']
        out.append(result)
    return out
