"""Independent decimal arithmetic for performance metrics, without production imports."""
from decimal import Decimal,localcontext

def reference(data):
    with localcontext() as ctx:
        ctx.prec=50
        d=lambda k:None if data.get(k) is None else Decimal(str(data[k]))
        h=d('duration_s')/3600;mass=d('collected_o2_g');aligned=data['time_alignment']=='reported_same_interval'
        trace=data['trace'];q=sum((Decimal(str(b['time_s']))-Decimal(str(a['time_s'])))*(Decimal(str(a['current_A']))+Decimal(str(b['current_A'])))/2 for a,b in zip(trace,trace[1:])) if trace else d('current_A')*d('duration_s')
        cell=sum((Decimal(str(b['time_s']))-Decimal(str(a['time_s'])))*(Decimal(str(a['current_A']))*Decimal(str(a['voltage_V']))+Decimal(str(b['current_A']))*Decimal(str(b['voltage_V'])))/2 for a,b in zip(trace,trace[1:]))/Decimal(3600000) if trace and trace[0]['voltage_V'] is not None else q*d('voltage_V')/Decimal(3600000) if not trace and d('voltage_V') is not None else None
        full_system=data['measurement_window_scope']=='full_system_operation' and data['oxygen_measurement_location']=='system_output'
        result={'oxygen_per_processed_regolith_kg_kg':mass/d('processed_regolith_g') if mass is not None and d('processed_regolith_g') is not None and d('processed_regolith_g')>0 and data['feedstock_mass_basis']=='processed_in_window' and data['feedstock_mass_reference'] and full_system else None,
          'oxygen_extraction_yield_percent':100*mass/d('available_oxygen_g') if mass is not None and d('available_oxygen_g') is not None and d('available_oxygen_g')>0 and data['available_oxygen_basis']=='matched_processed_feedstock' and data['available_oxygen_reference'] and full_system else None,
          'oxygen_rate_g_h':mass/h if mass is not None and aligned else None,
          'system_oxygen_rate_kg_h':mass/1000/d('system_operating_h') if mass is not None and d('system_operating_h') is not None and data['measurement_window_scope']=='full_system_operation' and data['oxygen_measurement_location']=='system_output' else None,
          'oxygen_per_energy_kg_kWh':mass/1000/d('total_energy_kWh') if mass is not None and d('total_energy_kWh') is not None and d('total_energy_kWh')>0 and data['energy_scope']=='total_system' and data['energy_time_alignment']=='reported_same_interval' and data['measurement_window_scope']=='full_system_operation' and data['oxygen_measurement_location']=='system_output' else None,
          'consumables_kg_per_kg_o2':d('consumables_g')/mass if mass is not None and mass>0 and d('consumables_g') is not None and data['measurement_window_scope']=='full_system_operation' and data['oxygen_measurement_location']=='system_output' else None,
          'collected_mass_fraction_percent':100*mass/d('sample_mass_g') if mass is not None and d('sample_mass_g') is not None else None,
          'current_density_A_cm2':q/d('duration_s')/d('active_anode_area_cm2') if d('active_anode_area_cm2') is not None else None,
          'cell_specific_energy_kWh_kg':cell/(mass/1000) if cell is not None and mass is not None and mass>0 and aligned else None,
          'reported_specific_energy_kWh_kg':d('total_energy_kWh')/(mass/1000) if d('total_energy_kWh') is not None and mass is not None and mass>0 and aligned and data['energy_time_alignment']=='reported_same_interval' and data['energy_scope']!='unknown' else None,
          'oxygen_purity_percent':d('oxygen_purity_percent'),'thermal_cycles':d('thermal_cycles'),'endurance_test_h':d('endurance_test_h'),'reported_projected_lifetime_h':d('reported_projected_lifetime_h'),
          'temperature_span_C':d('temperature_max_C')-d('temperature_min_C') if d('temperature_max_C') is not None and d('temperature_min_C') is not None else None,
          'wall_loss_um':d('wall_loss_um'),'wall_loss_fraction_percent':100*d('wall_loss_um')/d('initial_wall_thickness_um') if d('wall_loss_um') is not None and d('initial_wall_thickness_um') is not None else None}
        rt=data['resistance_trace'];initial=Decimal(str(rt[0]['resistance_ohm'])) if rt else d('initial_resistance_ohm');final=Decimal(str(rt[-1]['resistance_ohm'])) if rt else d('final_resistance_ohm')
        result['resistance_change_percent']=100*(final-initial)/initial if initial is not None and final is not None else None
        slope=None
        if rt:
            xs=[Decimal(str(r['time_s']))/3600 for r in rt];ys=[Decimal(str(r['resistance_ohm'])) for r in rt];n=Decimal(len(xs))
            slope=(n*sum(x*y for x,y in zip(xs,ys))-sum(xs)*sum(ys))/(n*sum(x*x for x in xs)-sum(xs)**2)
        result['resistance_slope_ohm_h']=slope
        exposure=d('thermal_exposure_h') if data['wall_rate_basis']=='thermal_exposure' else h if data['wall_rate_basis']=='electrolysis' else None
        rate=d('wall_loss_um')/exposure if d('wall_loss_um') is not None and exposure is not None else None
        result['wall_loss_rate_um_h']=rate
        result['endurance_target_coverage_percent']=100*d('endurance_test_h')/d('target_endurance_h') if d('endurance_test_h') is not None and d('target_endurance_h') is not None and d('target_endurance_h')>0 else None
        result['conditional_remaining_wall_life_h']=max(Decimal(0),(d('retirement_wall_loss_um')-d('wall_loss_um'))/rate) if data['projection_model']=='constant_wall_loss' and rate is not None and rate>0 and d('retirement_wall_loss_um') is not None and data['wall_measurement_reference'] else None
        return {k:float(v) if v is not None else None for k,v in result.items()}
