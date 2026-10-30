import copy,unittest
from jsonschema import Draft202012Validator
from mre_engineer.experiment_agent import PLAN,evidence_catalogue_schema,critic_submission_schema
from mre_engineer.evaluation import provider_output_schema
class EvidenceCatalogueContractTests(unittest.TestCase):
 def test_seven_known_citations_are_retained_not_truncated(self):
  refs=['input-record','performance','si','yu','materials','electrical','endurance'];before=copy.deepcopy(PLAN)
  schema=evidence_catalogue_schema(PLAN,refs);v=Draft202012Validator(schema['properties']['evidence_refs'])
  self.assertTrue(v.is_valid(refs));self.assertEqual(PLAN,before)
 def test_unknown_and_duplicate_citations_still_fail(self):
  v=Draft202012Validator(evidence_catalogue_schema(PLAN,['input-record','tool'])['properties']['evidence_refs'])
  self.assertFalse(v.is_valid(['invented']));self.assertFalse(v.is_valid(['tool','tool']))
 def test_nested_citations_use_same_available_catalogue(self):
  refs=['input-record','tool','research','materials','energy']
  schema=evidence_catalogue_schema(PLAN,refs)['properties']['assessments']['items']['properties']['evidence_refs']
  self.assertTrue(Draft202012Validator(schema).is_valid(refs))
 def test_receipt_specific_restrictions_are_preserved_in_provider_schema(self):
  schema=evidence_catalogue_schema(critic_submission_schema('second','performance'),['input-record','second','performance','research']);wire=provider_output_schema(schema)
  self.assertEqual(wire['properties']['evidence_refs']['items']['enum'],['second']);self.assertEqual(wire['properties']['comments']['items']['properties']['evidence_refs']['items']['enum'],['performance'])
