import unittest
from mre_engineer.hypothesis_tests import validate_assumptions,calculate,compare,verify_ranking,run
from mre_engineer.evidence import EvidenceError

def assumptions():
 return {'scenario':dict(inner_radius_mm=3,outer_radius_mm=12,height_mm=25,conductivity_S_m=10,thermal_conductivity_W_mK=2,current_A=.5,inner_temperature_C=1600,outer_temperature_C=1500),'conductivity_factor':.5,'thermal_factor':.5,'generation_g':.12,'recovery':.8,'recovery_change':-.2,'references':[]}
def item(number,model):return dict(hypothesis_number=number,model=model,model_applicability='Constructed sensitivity assumption, not confirmed cause')
class HypothesisPhysicsTests(unittest.TestCase):
 def test_fixed_current_conductivity_reduction_doubles_bulk_voltage_and_power(self):
  a=validate_assumptions(assumptions());r=calculate(a,[item(1,'bulk_electrical')]);c=r['cases'][0]
  self.assertAlmostEqual(c['predicted']['bulk_voltage_V'],2*c['baseline']['bulk_voltage_V'])
  self.assertAlmostEqual(c['predicted']['joule_power_W'],2*c['baseline']['joule_power_W'])
 def test_thermal_change_does_not_invent_electrical_change(self):
  c=calculate(validate_assumptions(assumptions()),[item(1,'heat_transfer')])['cases'][0]
  self.assertEqual(c['predicted']['bulk_voltage_V'],c['baseline']['bulk_voltage_V'])
  self.assertEqual(c['predicted']['joule_power_W'],c['baseline']['joule_power_W'])
 def test_collection_scenario_closes_mass_and_does_not_generate_temperature(self):
  c=calculate(validate_assumptions(assumptions()),[item(1,'collection_accounting')])['cases'][0]
  self.assertAlmostEqual(sum(c['predicted'].values()),.12)
  self.assertIsNone(c['field'])
 def test_missing_recovery_cannot_be_used_as_a_modelled_result(self):
  a=assumptions();a.update(generation_g=None,recovery=None,recovery_change=None)
  c=calculate(validate_assumptions(a),[item(1,'collection_accounting')])['cases'][0]
  self.assertEqual(c['status'],'not_modelled');self.assertEqual(c['predicted'],{})
 def test_unmatched_reference_cannot_receive_validation_pass(self):
  refs=[dict(quantity='bulk_voltage_V',value=1,absolute_tolerance=.01,source='Different boundary',comparable=False)]
  self.assertIsNone(compare({'bulk_voltage_V':1},refs)[0]['within_declared_tolerance'])
 def test_wrong_reference_exposes_error(self):
  refs=[dict(quantity='bulk_voltage_V',value=1,absolute_tolerance=.01,source='Matched constructed reference',comparable=True)]
  self.assertFalse(compare({'bulk_voltage_V':2},refs)[0]['within_declared_tolerance'])
 def test_out_of_range_perturbation_rejected_before_model_call(self):
  a=assumptions();a['scenario']['conductivity_S_m']=100000;a['conductivity_factor']=20
  with self.assertRaises(EvidenceError):validate_assumptions(a)
 def test_rank_must_cover_every_hypothesis(self):
  with self.assertRaises(EvidenceError):verify_ranking({'ranked':[{'hypothesis_number':1,'rank':1},{'hypothesis_number':1,'rank':2}]},2)
 def test_no_api_work_without_consent(self):
  with self.assertRaises(EvidenceError):run('.', 'unused',assumptions())
