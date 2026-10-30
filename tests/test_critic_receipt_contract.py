import unittest
from jsonschema import Draft202012Validator
from mre_engineer.experiment_agent import critic_submission_schema, CRITIC, TOOL_REASON, TEXT
from mre_engineer.evaluation import provider_output_schema
class CriticReceiptContractTests(unittest.TestCase):
 def test_wrong_tool_cannot_replace_selected_check(self):
  schema=critic_submission_schema('actual-second-check')['properties']['evidence_refs']
  validator=Draft202012Validator(schema)
  self.assertTrue(validator.is_valid(['actual-second-check']))
  self.assertFalse(validator.is_valid(['original-performance-check']))
  self.assertFalse(validator.is_valid([]))
 def test_provider_receives_exact_receipt_enum(self):
  schema=provider_output_schema(critic_submission_schema('actual-second-check'))
  self.assertEqual(schema['properties']['evidence_refs']['items']['enum'],['actual-second-check'])
 def test_shared_schema_not_mutated(self):
  original=CRITIC['properties']['evidence_refs']
  critic_submission_schema('actual-second-check')
  self.assertIs(CRITIC['properties']['evidence_refs'],original)
  self.assertNotIn('enum',original['items'])

 def test_recorded_reason_lengths_fit_without_changing_review_limits(self):
  v=Draft202012Validator(TOOL_REASON)
  self.assertTrue(v.is_valid('x'*474))
  self.assertTrue(v.is_valid('x'*740))
  self.assertFalse(v.is_valid('x'*1201))
  self.assertEqual(TEXT['maxLength'],450)
