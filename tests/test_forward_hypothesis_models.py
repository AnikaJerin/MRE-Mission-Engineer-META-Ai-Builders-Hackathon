import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from mre_engineer.hypothesis_tests import validate_assumptions,calculate,run
from mre_engineer.evidence import EvidenceError

def inputs():
 return dict(scenario=dict(inner_radius_mm=3,outer_radius_mm=12,height_mm=25,conductivity_S_m=10,thermal_conductivity_W_mK=2,current_A=.5,inner_temperature_C=1600,outer_temperature_C=1500),conductivity_factor=.5,thermal_factor=.5,generation_g=.12,recovery=.8,recovery_change=-.2,duration_s=3600,oxygen_current_fraction=.8,allocation_change=-.2,resistance_factor=1.1,references=[])
def item(n,model):return dict(hypothesis_number=n,rank=n,support='plausible',basis='Synthetic sensitivity',model=model,model_applicability='Forward effect only, not causal diagnosis',evidence_refs=['input-record'])
class FakeClient:
 def __init__(self,root,record):self.calls=0
 def request(self,body):
  self.calls+=1;name=body['tools'][0]['name']
  if name=='rank_hypothesis_tests':value={'ranked':[item(1,'current_allocation'),item(2,'equivalent_resistance')],'ranking_limit':'Constructed example; not causal truth','evidence_refs':['input-record']}
  else:value=dict(experiment='Measure matched recovery and electrical response',measurement='Independent generated and collected mass, bulk voltage',why_distinguishes='Compare effects rather than infer a cause',expected_patterns=[dict(hypothesis_number=1,pattern='Lower generated mass under the allocation assumption'),dict(hypothesis_number=2,pattern='Higher bulk voltage under the resistance assumption')],prerequisites='Matched calibrated measurements',validation_limit='Not real reactor validation',evidence_refs=['simulation-1','simulation-2'])
  return {'output':[{'type':'function_call','name':name,'arguments':json.dumps(value)}]}
class ForwardHypothesisTests(unittest.TestCase):
 def test_allocation_reduction_reduces_generated_and_collected_mass(self):
  c=calculate(validate_assumptions(inputs()),[item(1,'current_allocation')])['cases'][0]
  self.assertEqual(c['status'],'computed')
  self.assertAlmostEqual(c['predicted']['generated_o2_g']/c['baseline']['generated_o2_g'],.75)
  self.assertAlmostEqual(c['predicted']['collected_o2_g']/c['baseline']['collected_o2_g'],.75)
  self.assertIsNone(c['field'])
 def test_resistance_multiplier_applies_to_voltage_and_heating_at_fixed_current(self):
  c=calculate(validate_assumptions(inputs()),[item(1,'equivalent_resistance')])['cases'][0]
  self.assertAlmostEqual(c['predicted']['bulk_voltage_V']/c['baseline']['bulk_voltage_V'],1.1)
  self.assertAlmostEqual(c['predicted']['joule_power_W']/c['baseline']['joule_power_W'],1.1)
  self.assertIsNotNone(c['field'])
 def test_allocation_over_one_is_rejected(self):
  a=inputs();a['allocation_change']=.3
  with self.assertRaises(EvidenceError):validate_assumptions(a)
 def test_two_request_extension_preserves_input_and_computes_before_recommendation(self):
  scene={'status':'completed','assessment_id':'original','sha256':'scene-hash','result':{'hypotheses':[{'explanation':'Allocation rival'},{'explanation':'Resistance rival'}]}}
  original={'input':{'trace':[{'time_s':0,'current_A':.5,'voltage_V':3.2}],'resistance_trace':[{'time_s':0,'resistance_ohm':1.54}]},'original_review':{},'critique':{'weakness':'Synthetic test'},'final_review':{},'sources':[],'tools':[]}
  before=copy.deepcopy(original)
  with tempfile.TemporaryDirectory() as root,patch('mre_engineer.hypothesis_tests.load_scene',return_value=scene),patch('mre_engineer.hypothesis_tests.assessment',return_value=original):
   result=run(root,'scene',inputs(),True,client_factory=FakeClient)
   self.assertEqual(result['status'],'completed');self.assertEqual(result['api_attempts'],2)
   saved=json.loads((Path(root)/'outputs/hypothesis-tests'/result['test_id']/'report.json').read_text())
   pairs=saved['measurement_basis_checks']['electrical_pairs']
   self.assertEqual(len(pairs),1);self.assertEqual(pairs[0]['dc_apparent_V_over_I_ohm'],6.4);self.assertEqual(pairs[0]['separate_resistance_ohm'],1.54)
  self.assertEqual(original,before)
