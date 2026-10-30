import unittest
from mre_engineer.hypothesis_tests import recession, calculate, validate_assumptions
from mre_engineer.evidence import EvidenceError
S=dict(inner_radius_mm=3,outer_radius_mm=12,height_mm=25,conductivity_S_m=10,thermal_conductivity_W_mK=2,current_A=.5,inner_temperature_C=1600,outer_temperature_C=1500)
class ForwardMaterialTests(unittest.TestCase):
 def test_loss_forecast_and_correlated_bound(self):
  d=dict(component='anode',measured_loss_um=40,loss_bound_um=5,exposure_h=3,horizon_h=3,initial_thickness_um=1000,source='synthetic',comparable_conditions=True)
  r=recession(d);self.assertEqual(r['total_loss_um'],80);self.assertEqual(r['remaining_thickness_um'],920);self.assertEqual(r['total_loss_lower_um'],70);self.assertEqual(r['total_loss_upper_um'],90)
 def test_forecast_requires_matching_conditions(self):
  with self.assertRaises(EvidenceError):recession({'comparable_conditions':False})
 def test_identical_observable_preserves_ambiguity(self):
  from mre_engineer.physics import FARADAY_C_PER_MOL
  ideal=.5*3600*31.998/(4*FARADAY_C_PER_MOL)
  a=validate_assumptions(dict(scenario=S,conductivity_factor=.5,thermal_factor=.5,duration_s=3600,oxygen_current_fraction=.8,allocation_change=-.2,generation_g=ideal*.8,recovery=.8,recovery_change=-.2))
  r=calculate(a,[dict(hypothesis_number=1,model='collection_accounting',model_applicability='scenario'),dict(hypothesis_number=2,model='current_allocation',model_applicability='scenario')]);self.assertEqual(len(r['ambiguities']),1)
 def test_fixed_current_does_not_invent_current_density_change(self):
  a=validate_assumptions(dict(scenario=S,conductivity_factor=.5,thermal_factor=.5,resistance_factor=2))
  r=calculate(a,[dict(hypothesis_number=1,model='equivalent_resistance',model_applicability='scenario')]);c=r['cases'][0]
  self.assertEqual(c['deltas']['max_current_density_change_A_m2'],0);self.assertAlmostEqual(c['predicted']['bulk_voltage_V'],2*c['baseline']['bulk_voltage_V'])
