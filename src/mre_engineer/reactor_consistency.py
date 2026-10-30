"""Advisory measurement-basis checks; never edits measurements or old reviews."""
import math

def inspect(data,scenario=None):
 trace=data.get('trace') or [];rt=data.get('resistance_trace') or []
 rows=[]
 for point in trace:
  t,I,V=point.get('time_s'),point.get('current_A'),point.get('voltage_V')
  if not all(type(x) in (int,float) and math.isfinite(x) for x in (t,I,V)) or I==0:continue
  matches=[x for x in rt if x.get('time_s')==t]
  if not matches:continue
  R=matches[0].get('resistance_ohm')
  if type(R) not in (int,float) or not math.isfinite(R):continue
  apparent=V/I
  rows.append({'time_s':t,'dc_apparent_V_over_I_ohm':apparent,'separate_resistance_ohm':R,'difference_ohm':apparent-R})
 return {'electrical_pairs':rows,'interpretation':'V/I includes full-cell voltage contributions. A separate resistance may be impedance, differential or ohmic resistance. Different values are not automatically contradictory. Define measurement method, temperature and time window before treating them as the same quantity. No measurement has been changed.',
 'scenario_boundary':'Scenario temperatures are imposed boundaries. A single submitted temperature does not establish a spatial field.',
 'bulk_voltage_scope':'The annular model excludes interfaces and reaction overpotential. Its bulk voltage must not be validated against full-cell voltage without separating those contributions.',
 'scenario_current_A':scenario.get('current_A') if scenario else None}
