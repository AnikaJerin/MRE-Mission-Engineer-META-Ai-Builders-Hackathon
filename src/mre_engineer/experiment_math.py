"""Bounded input-driven accounting; no kinetic or failure prediction model."""
import math
from .physics import charge_oxygen_bound,oxygen_inventory,FARADAY_C_PER_MOL
from .experiment_reference import calculations as independent_calculations,inventory as independent_inventory,sensitivity as independent_sensitivity
from .evidence import EvidenceError


def accounting(data):
    trace=data['trace'];dt=data['duration_s']
    if trace:
        charge=math.fsum((b['time_s']-a['time_s'])*(a['current_A']+b['current_A'])/2 for a,b in zip(trace,trace[1:]))
        ideal=charge/(4*FARADAY_C_PER_MOL)*31.998
        energy=math.fsum((b['time_s']-a['time_s'])*(a['current_A']*a['voltage_V']+b['current_A']*b['voltage_V'])/2 for a,b in zip(trace,trace[1:]))/3600 if trace[0]['voltage_V'] is not None else None
    else:
        out=charge_oxygen_bound(data['current_A'],dt);charge=out['charge_c'];ideal=out['ideal_oxygen_g'];energy=charge*data['voltage_V']/3600 if data['voltage_V'] is not None else None
    mass=data['collected_o2_g'];ratio=mass/ideal if mass is not None and data['time_alignment']=='reported_same_interval' else None
    if ratio is not None and not math.isfinite(ratio):raise EvidenceError('Oxygen/charge ratio exceeds numerical range')
    bounds=None
    if not trace and all(data[k] is not None for k in ('current_uncertainty_A','duration_uncertainty_s','oxygen_uncertainty_g')) and ratio is not None:
        low=(data['current_A']-data['current_uncertainty_A'])*(dt-data['duration_uncertainty_s'])/(4*FARADAY_C_PER_MOL)*31.998
        high=(data['current_A']+data['current_uncertainty_A'])*(dt+data['duration_uncertainty_s'])/(4*FARADAY_C_PER_MOL)*31.998
        bounds={'ideal_o2_g':[low,high],'apparent_ratio':[max(0,mass-data['oxygen_uncertainty_g'])/high,(mass+data['oxygen_uncertainty_g'])/low],
          'scope':'Sensitivity to supplied absolute +/- bounds, not statistical confidence or complete measurement uncertainty.'}
    inventory=None
    if data['composition'] and data['sample_mass_g'] is not None:
        c=data['composition'];rows=[{'analysis_id':c['analysis_id'],'oxide':r['oxide'],'value':r['wt_percent'],'unit':'wt_percent','source_id':'input-composition','locator':c['source']} for r in c['rows']]
        inventory=oxygen_inventory(rows,data['sample_mass_g'])
        inventory['mass_basis']='User-reported batch mass; authenticity and measurement uncertainty unverified.'
    values={'charge_C':charge,'ideal_o2_g':ideal,'electrical_energy_Wh':energy}
    reference=independent_calculations(data)
    reference['apparent_ratio']=data['collected_o2_g']/reference['ideal_o2_g'] if ratio is not None else None
    reference['inventory_o2_g']=independent_inventory(data)
    compared={**values,'apparent_ratio':ratio,'inventory_o2_g':inventory['represented_oxygen_g'] if inventory else None}
    if bounds:
        reference.update(independent_sensitivity(data))
        compared.update(dict(zip(('bound_ideal_min','bound_ideal_max','bound_ratio_min','bound_ratio_max'),bounds['ideal_o2_g']+bounds['apparent_ratio'])))
    checks={k:{'production':v,'independent':reference[k],'passed':v is None and reference[k] is None or v is not None and reference[k] is not None and math.isfinite(v) and abs(v-reference[k])<=max(1e-10,abs(reference[k])*1e-12)} for k,v in compared.items()}
    if not all(c['passed'] for c in checks.values()):raise EvidenceError('Independent arithmetic disagreement; no API run started')
    return {**values,'reported_collected_o2_g':mass,'apparent_collected_to_charge_ratio':ratio,'ratio_above_one':ratio is not None and ratio>1,'inventory':inventory,'sensitivity':bounds,'independent_checks':checks,
      'basis':'Trapezoidal integration of supplied I(t) and P(t)=I(t)V(t)' if trace else 'Declared constant current over the entered duration',
      'limitations':['Four-electron ideal oxygen accounting; collected gas need not equal total generated oxygen.','Electrical energy excludes unmeasured furnace and auxiliary energy; no thermal efficiency.','An apparent ratio is not validated Faradaic efficiency or a fault diagnosis.','Independent arithmetic checks algorithms, not input authenticity or a new-case ground-truth answer.']}
