"""Independent Decimal/Fraction reference, no production physics import."""
from decimal import Decimal,localcontext
from fractions import Fraction

def calculations(data):
    f=lambda v:Fraction(str(v))
    trace=data['trace']
    if trace:
        q=sum((f(b['time_s'])-f(a['time_s']))*(f(a['current_A'])+f(b['current_A']))/2 for a,b in zip(trace,trace[1:]))
        energy=sum((f(b['time_s'])-f(a['time_s']))*(f(a['current_A'])*f(a['voltage_V'])+f(b['current_A'])*f(b['voltage_V']))/2 for a,b in zip(trace,trace[1:]))/3600 if trace[0]['voltage_V'] is not None else None
    else:q=f(data['current_A'])*f(data['duration_s']);energy=q*f(data['voltage_V'])/3600 if data['voltage_V'] is not None else None
    with localcontext() as c:
        c.prec=50
        mass=Decimal(q.numerator)/Decimal(q.denominator)*Decimal('31.998')/(4*Decimal('6.02214076e23')*Decimal('1.602176634e-19'))
    return {'charge_C':float(q),'ideal_o2_g':float(mass),'electrical_energy_Wh':float(energy) if energy is not None else None}


def inventory(data):
    if not data['composition'] or data['sample_mass_g'] is None:return None
    import re
    weights={'O':'15.999','Si':'28.085','Fe':'55.845','Mg':'24.305','Ca':'40.078','Al':'26.982','Ti':'47.867','Na':'22.990','K':'39.098','Mn':'54.938','P':'30.974'}
    with localcontext() as ctx:
        ctx.prec=50;result=Decimal(0)
        for row in data['composition']['rows']:
            symbol,n,m=re.fullmatch(r'([A-Z][a-z]?)([0-9]*)O([0-9]*)',row['oxide']).groups();n=int(n or 1);m=int(m or 1)
            oxygen=Decimal(weights['O'])*m;oxide=Decimal(weights[symbol])*n+oxygen
            result+=Decimal(str(data['sample_mass_g']))*Decimal(str(row['wt_percent']))/100*oxygen/oxide
    return float(result)


def sensitivity(data):
    if data['trace'] or data['time_alignment']!='reported_same_interval' or data['collected_o2_g'] is None or any(data[k] is None for k in ('current_uncertainty_A','duration_uncertainty_s','oxygen_uncertainty_g')):return None
    with localcontext() as ctx:
        ctx.prec=50
        d=lambda k:Decimal(str(data[k]))
        factor=Decimal('31.998')/(4*Decimal('6.02214076e23')*Decimal('1.602176634e-19'))
        low=(d('current_A')-d('current_uncertainty_A'))*(d('duration_s')-d('duration_uncertainty_s'))*factor
        high=(d('current_A')+d('current_uncertainty_A'))*(d('duration_s')+d('duration_uncertainty_s'))*factor
        rlow=max(Decimal(0),d('collected_o2_g')-d('oxygen_uncertainty_g'))/high
        rhigh=(d('collected_o2_g')+d('oxygen_uncertainty_g'))/low
    return {'bound_ideal_min':float(low),'bound_ideal_max':float(high),'bound_ratio_min':float(rlow),'bound_ratio_max':float(rhigh)}
