"""Bounded radial conduction scenario, not a calibrated reactor digital twin.

Constant-property annulus, isothermal inner/outer boundaries, insulated ends.
Bulk ohmic conduction excludes YSZ, reaction overpotential and gas transport.
The finite-volume heat solve is checked against the independent closed form.
"""
import math
from .evidence import EvidenceError

FIELDS = {'inner_radius_mm':(0.1,500), 'outer_radius_mm':(0.2,1000),
          'height_mm':(1,2000), 'conductivity_S_m':(0.001,100000),
          'thermal_conductivity_W_mK':(0.01,1000), 'current_A':(0,10000),
          'inner_temperature_C':(0,2500), 'outer_temperature_C':(0,2500)}
SOURCE = {'title':'Yu et al. 2025, inverted YSZ/Pt hollow-anode configuration',
          'url':'https://ntrs.nasa.gov/citations/20250004626',
          'locator':'Figure 1(b), sections 2.2.1–2.2.2',
          'scope':'Component arrangement only. Scenario dimensions and constant properties are user assumptions, not values extracted from this paper.'}

def validate_scenario(raw):
    if not isinstance(raw,dict) or set(raw)!=set(FIELDS):
        raise EvidenceError('Scenario requires all eight named geometry, property, current and boundary inputs')
    clean={}
    for key,(low,high) in FIELDS.items():
        v=raw[key]
        if type(v) not in (int,float) or not math.isfinite(v) or not low<=v<=high:
            raise EvidenceError(f'{key}: enter a finite value from {low} to {high}')
        clean[key]=float(v)
    if clean['outer_radius_mm']<=clean['inner_radius_mm']*1.05:
        raise EvidenceError('Outer radius must exceed inner radius by at least five percent')
    return clean

def _solve(s,n):
    a,b,h=(s[k]/1000 for k in ('inner_radius_mm','outer_radius_mm','height_mm'))
    sigma,k,I=(s[x] for x in ('conductivity_S_m','thermal_conductivity_W_mK','current_A'))
    ti,to=s['inner_temperature_C'],s['outer_temperature_C']
    # Exact radial electrical solution; electrochemical interfaces excluded.
    L=math.log(b/a); coefficient=I/(2*math.pi*h)
    c=coefficient**2/(sigma*k)
    dx=L/n; g=2*math.pi*k*h/dx
    lower=[-g]*(n-1); upper=[-g]*(n-1); diag=[2*g]*n
    diag[0]=diag[-1]=3*g
    source=2*math.pi*h*coefficient**2/sigma*dx
    rhs=[source]*n;rhs[0]+=2*g*ti;rhs[-1]+=2*g*to
    # Tridiagonal finite-volume heat balance in x=ln(r/a).
    for i in range(1,n):
        factor=lower[i-1]/diag[i-1];diag[i]-=factor*upper[i-1];rhs[i]-=factor*rhs[i-1]
    T=[0.0]*n;T[-1]=rhs[-1]/diag[-1]
    for i in range(n-2,-1,-1):T[i]=(rhs[i]-upper[i]*T[i+1])/diag[i]
    samples=[];max_error=0.0
    for i,t in enumerate(T):
        x=(i+.5)*dx;r=a*math.exp(x)
        analytic=ti+(to-ti)*x/L+c*x*(L-x)/2
        max_error=max(max_error,abs(t-analytic))
        samples.append({'radius_mm':r*1000,'temperature_C':t,
                        'potential_V':coefficient/sigma*x,'current_density_A_m2':coefficient/r})
    power=I**2*L/(2*math.pi*h*sigma)
    heat_out=2*g*(T[0]-ti)+2*g*(T[-1]-to)
    resistance=L/(2*math.pi*h*sigma)
    return {'samples':samples,'bulk_resistance_ohm':resistance,'bulk_voltage_V':I*resistance,
            'joule_power_W':power,'peak_temperature_C':max(ti,to,*T),
            'heat_out_W':heat_out,'energy_balance_error_W':abs(heat_out-power),
            'analytic_max_error_C':max_error}

def simulate(raw):
    s=validate_scenario(raw);coarse=_solve(s,48);fine=_solve(s,96)
    result={**fine,'input':s,'model':'radial-annulus-steady-v1','source':SOURCE,
            'verification':{'analytic_max_error_C':fine['analytic_max_error_C'],
                'coarse_analytic_error_C':coarse['analytic_max_error_C'],
                'peak_mesh_change_C':abs(fine['peak_temperature_C']-coarse['peak_temperature_C']),
                'energy_balance_error_W':fine['energy_balance_error_W']},
            'assumptions':['Steady radial conduction; identical field at every height and azimuth.',
                'Constant bulk conductivity and thermal conductivity; both boundaries held at entered temperatures.',
                'No YSZ interface, electrolysis kinetics, convection, radiation, phase change or degradation model.',
                'Numerical consistency is not validation against a measured thermal field.'],
            'interpretation':'Scenario only; not a reconstruction of NASA COMSOL results or a hardware operating recommendation.'}
    if not all(math.isfinite(row['temperature_C']) for row in result['samples']):
        raise EvidenceError('Scenario solve produced a nonfinite field')
    return result
