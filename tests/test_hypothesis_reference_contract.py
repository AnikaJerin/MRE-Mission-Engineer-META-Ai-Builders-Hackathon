import unittest
from jsonschema import Draft202012Validator
from mre_engineer.hypothesis_tests import submission_schema,REC_SCHEMA
class HypothesisReferenceContractTests(unittest.TestCase):
 def test_nine_known_citations_are_accepted(self):
  ids=['evidence-'+str(i) for i in range(9)]
  v=Draft202012Validator(submission_schema(REC_SCHEMA,ids)['properties']['evidence_refs'])
  self.assertTrue(v.is_valid(ids))
  self.assertFalse(v.is_valid(ids+['invented']))
  self.assertFalse(v.is_valid([ids[0],ids[0]]))
 def test_base_schema_is_not_mutated(self):
  submission_schema(REC_SCHEMA,['a','b'])
  self.assertEqual(REC_SCHEMA['properties']['evidence_refs']['maxItems'],6)
