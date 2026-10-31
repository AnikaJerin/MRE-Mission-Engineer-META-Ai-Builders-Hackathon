import copy,unittest
from mre_engineer.reactor_hypotheses import submission_schema,verify,SCHEMA
from mre_engineer.evidence import EvidenceError
from test_reactor_hypotheses import assessment,result
class HypothesisReceiptTests(unittest.TestCase):
 def test_runtime_schema_requires_real_receipt_without_mutation(self):
  original=copy.deepcopy(SCHEMA);r=assessment();schema=submission_schema(r)
  item=schema['properties']['hypotheses']['items']
  self.assertIn('calculation_receipt',item['required'])
  self.assertEqual(item['properties']['calculation_receipt']['enum'],['experiment-tool-test'])
  self.assertEqual(SCHEMA,original)
 def test_explicit_model_receipt_supports_metric_without_forging_refs(self):
  v=result();v['hypotheses'][0]['evidence_refs']=['input-record']
  for h in v['hypotheses']:h['calculation_receipt']='experiment-tool-test'
  original=copy.deepcopy(v);verify(v,assessment());self.assertEqual(v,original)
 def test_measurement_readiness_is_not_calculation_receipt(self):
  r=assessment();r['tools'].append({'tool':'measurement_readiness','evidence_id':'readiness'})
  v=result();v['hypotheses'][0]['calculation_receipt']='readiness'
  with self.assertRaises(EvidenceError):verify(v,r)
 def test_no_citation_still_rejected(self):
  v=result();v['hypotheses'][0]['evidence_refs']=['input-record']
  with self.assertRaises(EvidenceError):verify(v,assessment())

 def test_field_and_reference_catalogues_are_isolated(self):
  r=assessment();props=submission_schema(r)['properties']['hypotheses']['items']['properties']
  self.assertEqual(props['input_fields']['items']['enum'],list(r['input']))
  self.assertEqual(props['research_refs']['items']['enum'],['paper'])
  self.assertNotIn('input-record',props['input_fields']['items']['enum'])
  self.assertIsNot(props['input_fields'],props['evidence_refs'])
  self.assertIsNot(props['input_fields'],props['research_refs'])
  props['evidence_refs']['items']['enum'].append('other')
  self.assertNotIn('other',props['input_fields']['items']['enum'])
  self.assertNotIn('other',props['research_refs']['items']['enum'])
