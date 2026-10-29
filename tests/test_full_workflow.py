"""Owner-run regression controls. Synthetic values are not reactor ground truth."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_experiment import FakeClient
from mre_engineer.experiment_agent import preview,run,load,model_tool,tool,verify_assessments
from mre_engineer.experiment_input import validate_input
from mre_engineer.evidence import EvidenceError
from mre_engineer.meta_client import MAX_CONTEXT_BYTES,MODEL,MAX_OUTPUT_TOKENS,MetaClient
from mre_engineer.workspace_actions import Actions

FIXTURE=Path(__file__).parent/'fixtures/full_workflow_synthetic.json'
def fixture():return json.loads(FIXTURE.read_text())

class FullWorkflowTests(unittest.TestCase):
    def test_full_input_has_useful_comparisons_without_paid_calls(self):
        with tempfile.TemporaryDirectory() as root,patch('urllib.request.build_opener',side_effect=AssertionError('No network')):
            r=preview(root,fixture())
        self.assertEqual(r['api_calls'],0)
        self.assertAlmostEqual(r['accounting']['charge_C'],172800)
        self.assertAlmostEqual(r['accounting']['ideal_o2_g'],14.326670899918527)
        self.assertAlmostEqual(r['performance']['metrics']['reported_specific_energy_kWh_kg']['value'],12000/7)
        self.assertAlmostEqual(r['performance']['metrics']['wall_loss_rate_um_h']['value'],.25)
        self.assertAlmostEqual(r['performance']['metrics']['resistance_change_percent']['value'],10)
        self.assertAlmostEqual(r['performance']['metrics']['conditional_remaining_wall_life_h']['value'],352)
        results={c['target_field']:c['status'] for c in r['performance']['target_checks']}
        self.assertEqual(results['target_oxygen_rate_g_h'],'within_declared_target')
        for key in ['target_max_specific_energy_kWh_kg','target_min_oxygen_purity_percent','target_max_wall_loss_um','target_max_abs_resistance_change_percent']:
            self.assertEqual(results[key],'outside_declared_target')
        self.assertEqual(len(r['performance']['official_profile_checks']),5)
        pub=r['performance']['publication_comparisons']
        self.assertEqual(pub['status'],'no_condition_matched_publication')
        self.assertEqual(len(pub['reference_cases']),3)
        self.assertEqual(pub['comparisons'],[])

    def test_missing_one_basis_does_not_erase_other_dimensions(self):
        value=fixture();value['energy_scope']='unknown'
        with tempfile.TemporaryDirectory() as root:r=preview(root,value)
        checks={c['target_field']:c for c in r['performance']['target_checks']}
        self.assertEqual(checks['target_max_specific_energy_kWh_kg']['status'],'insufficient_evidence')
        self.assertEqual(checks['target_max_wall_loss_um']['status'],'outside_declared_target')
        self.assertAlmostEqual(r['performance']['metrics']['current_density_A_cm2']['value'],.1)

    def test_stale_preview_rejected_before_thread_or_spending(self):
        with tempfile.TemporaryDirectory() as root,patch('threading.Thread') as thread:
            with self.assertRaisesRegex(EvidenceError,'Inputs changed'):
                Actions(root).start({'action':'assess','input':fixture(),'consent':True,'preview_sha256':'stale'})
            thread.assert_not_called()

    def test_all_five_requests_fit_and_saved_receipts_are_complete(self):
        sizes=[]
        class Sized(FakeClient):
            def request(self,body):
                selftest.assertNotIn('local_output_contract',body['input'])
                payload={**body,'model':MODEL,'max_output_tokens':MAX_OUTPUT_TOKENS,'reasoning':{'effort':'minimal'},'tool_choice':'auto','parallel_tool_calls':False}
                size=len(json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode());sizes.append(size)
                selftest.assertLessEqual(size,MAX_CONTEXT_BYTES)
                response=super().request(body)
                name=body['tools'][0]['name'];content=json.loads(body['input'])
                if name=='submit_experiment_review':
                    value=json.loads(response['output'][0]['arguments'])
                    perf=next(t for t in content['tool_results'] if t['tool']=='performance_assessment')
                    refs=[perf['evidence_id']]
                    specs={'production':('conditional_target_missed','oxygen_purity_percent','oxygen_purity_percent'),
                           'electrical':('conditional_target_missed','resistance_change_percent','resistance_comparability'),
                           'energy':('conditional_target_missed','reported_specific_energy_kWh_kg','energy_scope'),
                           'materials':('conditional_target_missed','wall_loss_um','wall_loss_um'),
                           'endurance':('conditional_target_met','endurance_test_h','endurance_test_h'),
                           'measurement_integrity':('supported_observation',None,'trace')}
                    for a in value['assessments']:
                        status,metric,field=specs[a['dimension']]
                        a.update(status=status,metric_ids=[metric] if metric else [],input_fields=[field],evidence_refs=refs,
                                 finding='Synthetic contract control; conditional numerical comparison, not real reactor validation',
                                 basis='The supplied synthetic requirement and returned numerical comparison establish only this conditional result.')
                    response['output'][0]['arguments']=json.dumps(value)
                return response
        selftest=self
        with tempfile.TemporaryDirectory() as root,patch('urllib.request.build_opener',side_effect=AssertionError('No network')):
            result=run(root,fixture(),True,client_factory=Sized)
            self.assertEqual(result['status'],'completed',result)
            saved=load(root,result['assessment_id'])
        self.assertEqual(len(sizes),5)
        self.assertIsNotNone(saved['report']['original_review'])
        self.assertIsNotNone(saved['report']['critique'])
        self.assertIsNotNone(saved['report']['final_review'])
        self.assertTrue(saved['report']['critic_comments_validated'])
        first=saved['report']['tools'][0]
        self.assertEqual(first['tool'],'performance_assessment')
        self.assertIn('independent_check',first['result']['metrics']['wall_loss_um'])
        compact=model_tool(first)
        self.assertNotIn('independent_check',compact['result']['metrics']['wall_loss_um'])
        self.assertEqual(compact['result']['target_checks'][0]['actual'],first['result']['target_checks'][0]['actual'])

    def test_huge_request_is_rejected_before_transport_or_reservation(self):
        with tempfile.TemporaryDirectory() as root,patch.dict('os.environ',{'MODEL_API_KEY':'offline'}),patch('mre_engineer.meta_client.api_budget.reserve') as reserve,patch('urllib.request.build_opener') as opener:
            with self.assertRaisesRegex(EvidenceError,'not sent or charged'):
                MetaClient(root,lambda *args:None).request({'input':'x'*(MAX_CONTEXT_BYTES+1)})
            reserve.assert_not_called();opener.assert_not_called()

    def test_matching_publication_uses_trace_resistance_endpoints(self):
        value=fixture();value.update(configuration='hollow_ysz_pt',feedstock='LHS-1',duration_s=43200,thermal_exposure_h=14,trace=[{'time_s':0,'current_A':.5},{'time_s':43200,'current_A':.5}],resistance_trace=[{'time_s':0,'resistance_ohm':1.46},{'time_s':43200,'resistance_ohm':.78}],collected_o2_g=.749,wall_loss_um=85)
        # Unrelated synthetic system/endurance settings must not imply experimental equivalence.
        value.update(endurance_test_h=12,system_operating_h=12,reported_projected_lifetime_h=None)
        with tempfile.TemporaryDirectory() as root:r=preview(root,value)
        pub=r['performance']['publication_comparisons']
        self.assertEqual(pub['status'],'declared_context_matched_not_experimental_equivalence')
        rows={c['field']:c for c in pub['comparisons']}
        self.assertAlmostEqual(rows['final_resistance_ohm']['difference'],0)
        self.assertAlmostEqual(rows['wall_loss_um']['difference'],0)
        self.assertAlmostEqual(rows['collected_o2_g']['difference'],0)
