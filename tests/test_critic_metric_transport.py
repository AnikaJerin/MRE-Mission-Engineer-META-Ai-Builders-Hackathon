import copy,unittest
from jsonschema import Draft202012Validator
from mre_engineer.experiment_agent import CRITIC,critic_submission_schema
from mre_engineer.evaluation import provider_output_schema
class CriticMetricTransportTests(unittest.TestCase):
 def test_performance_receipt_is_required_on_each_comment(self):
  schema=critic_submission_schema('second-check','performance-check')
  refs=schema['properties']['comments']['items']['properties']['evidence_refs'];v=Draft202012Validator(refs)
  self.assertTrue(v.is_valid(['performance-check']));self.assertFalse(v.is_valid(['second-check']));self.assertFalse(v.is_valid([]))
 def test_both_constraints_reach_provider_without_mutating_shared_schema(self):
  before=copy.deepcopy(CRITIC);wire=provider_output_schema(critic_submission_schema('second-check','performance-check'))
  self.assertEqual(wire['properties']['evidence_refs']['items']['enum'],['second-check'])
  self.assertEqual(wire['properties']['comments']['items']['properties']['evidence_refs']['items']['enum'],['performance-check']);self.assertEqual(CRITIC,before)
