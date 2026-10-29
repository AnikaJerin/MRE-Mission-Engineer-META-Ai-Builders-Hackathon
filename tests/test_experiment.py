"""Owner-run tests for new user-input contracts; no real API calls."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from mre_engineer.evidence import EvidenceError
from mre_engineer.experiment_input import validate_input,readiness
from mre_engineer.experiment_math import accounting
from mre_engineer.experiment_agent import run,load,example,save_review


def sample():return {'experiment_name':'Constructed software control','current_A':0.5,'duration_s':3600,'collected_o2_g':0.07,'time_alignment':'reported_same_interval'}


class FakeClient:
    def __init__(self,root,record):self.calls=0
    def request(self,body):
        self.calls+=1;assert self.calls<=5
        content=json.loads(body['input']);refs=content['allowed_evidence_refs'];name=body['tools'][0]['name']
        assert 'ground_truth_answer' not in body['input']
        h={'explanation':'Unconfirmed measurement interpretation','discriminating_observation':'Applicable calibrated records','unresolved_limit':'No causal ground truth','evidence_refs':[refs[0]]}
        if name=='propose_and_choose_check':value={'hypotheses':[h,dict(h)],'tool':body['tools'][0]['parameters']['properties']['tool']['enum'][0],'reason':'Inspect requested check','evidence_refs':[refs[0]]}
        elif name=='choose_critic_check':value={'tool':body['tools'][0]['parameters']['properties']['tool']['enum'][0],'reason':'Inspect a permitted additional check','evidence_refs':[refs[0]]}
        elif name=='submit_experiment_critique':value={'weakness':'Calibration is not independently confirmed','rival_explanation':'Collection and generation differ','requested_revision':'Retain conditional accounting and request records','evidence_refs':[refs[-1]],'comments':[{'dimension':'measurement_integrity','position':'evidence_gap','comment':'Constructed offline critic response','basis':'The supplied control does not identify a calibration record.','input_fields':['calibration_reference'],'metric_ids':[],'evidence_refs':[refs[-1]]}]}
        else:value={'summary':'Conditional evidence review, not a reactor health diagnosis','judgement':'conditional_review','findings':[{'text':'Inputs are user-reported','basis':'The control was supplied as manual data.','kind':'reported_observation','evidence_refs':[refs[0]]}],
          'hypotheses':[h,dict(h)],'next_test':{'candidate_id':'gas_accounting_review','question':'Which gas records are missing?','measurement_or_record':'Applicable calibration and window records','rival_outcomes':'Different records could support different interpretations; not observed outcomes','prerequisites':'Engineer review of records','reason':'Avoid unsupported diagnosis','evidence_refs':[refs[-1]]},
          'limitations':['New input has no reference engineering answer','No hardware approval'],'review_scope':'document_review_only','evidence_refs':[refs[-1]],
          'assessments':[{'dimension':dimension,'status':'insufficient_evidence','finding':'Constructed offline response; not a reactor conclusion','basis':'Input fields are supplied, but no independent measurement validation is provided.','improvement_or_next_evidence':'Review applicable records','metric_ids':[],'input_fields':['current_A'],'evidence_refs':[refs[-1]]} for dimension in ('production','electrical','energy','materials','endurance','measurement_integrity')]}
        return {'id':'offline','output':[{'type':'function_call','name':name,'arguments':json.dumps(value)}]}


class InputTests(unittest.TestCase):
    def test_missing_optional_oxygen_is_not_zero(self):
        value=sample();del value['collected_o2_g'];data=validate_input(value)
        self.assertIsNone(data['collected_o2_g']);self.assertIsNone(accounting(data)['apparent_collected_to_charge_ratio'])
    def test_measured_zero_is_preserved(self):
        value=sample();value['collected_o2_g']=0;self.assertEqual(accounting(validate_input(value))['apparent_collected_to_charge_ratio'],0)
    def test_invalid_units_are_not_guessed_from_numeric_strings(self):
        value=sample();value['current_A']='500 mA'
        with self.assertRaises(EvidenceError):validate_input(value)
    def test_negative_nonfinite_and_boolean_inputs_are_rejected(self):
        for v in (-1,float('inf'),True):
            value=sample();value['current_A']=v
            with self.assertRaises(EvidenceError):validate_input(value)
    def test_unknown_process_is_outside_this_adapter(self):
        value=sample();value['process']='water_electrolysis'
        with self.assertRaises(EvidenceError):validate_input(value)
    def test_current_and_trace_cannot_be_mixed(self):
        value=sample();value['trace']=[{'time_s':0,'current_A':0.5},{'time_s':3600,'current_A':0.5}]
        with self.assertRaises(EvidenceError):validate_input(value)
    def test_trace_must_cover_declared_window_and_not_be_resorted(self):
        for points in ([0,1800],[3600,0],[0,0]):
            value=sample();value['current_A']=None;value['trace']=[{'time_s':t,'current_A':0.5} for t in points]
            with self.assertRaises(EvidenceError):validate_input(value)
    def test_partial_voltage_trace_is_rejected(self):
        value=sample();value['current_A']=None;value['trace']=[{'time_s':0,'current_A':0.5,'voltage_V':2},{'time_s':3600,'current_A':0.5}]
        with self.assertRaises(EvidenceError):validate_input(value)
    def test_zero_current_trace_has_no_charge_budget(self):
        value=sample();value['current_A']=None;value['trace']=[{'time_s':0,'current_A':0},{'time_s':3600,'current_A':0}]
        with self.assertRaises(EvidenceError):validate_input(value)
    def test_composition_is_one_analysis_without_normalization(self):
        value=sample();value['composition']={'analysis_id':'control','source':'constructed reference','rows':[{'oxide':'SiO2','wt_percent':90},{'oxide':'FeO','wt_percent':20}]}
        with self.assertRaises(EvidenceError):validate_input(value)
    def test_ambiguous_or_duplicate_oxides_are_not_inferred(self):
        for rows in ([{'oxide':'Fe_total','wt_percent':4}],[{'oxide':'FeO','wt_percent':4},{'oxide':'FeO','wt_percent':2}]):
            value=sample();value['composition']={'analysis_id':'control','source':'constructed','rows':rows}
            with self.assertRaises(EvidenceError):validate_input(value)
    def test_unknown_metadata_remains_readiness_gap(self):
        ready=readiness(validate_input(sample()));self.assertIn('gas_calibration',{g['id'] for g in ready['gaps']});self.assertEqual(ready['status'],'evidence_needed')


class ArithmeticTests(unittest.TestCase):
    def test_historical_nominal_accounting_has_independent_reference(self):
        result=accounting(validate_input(example()));self.assertAlmostEqual(result['charge_C'],1800);self.assertAlmostEqual(result['ideal_o2_g'],0.14923615520748468)
        self.assertTrue(all(c['passed'] for c in result['independent_checks'].values()))
    def test_new_input_changes_accounting_and_does_not_replay_old_result(self):
        first=accounting(validate_input(sample()));value=sample();value['current_A']=1;second=accounting(validate_input(value))
        self.assertAlmostEqual(second['ideal_o2_g'],2*first['ideal_o2_g'])
    def test_trapezoid_integrates_whole_trace_with_aligned_power(self):
        value=sample();value['current_A']=None;value['trace']=[{'time_s':0,'current_A':0.2,'voltage_V':2},{'time_s':1800,'current_A':0.8,'voltage_V':3},{'time_s':3600,'current_A':0.2,'voltage_V':2}]
        result=accounting(validate_input(value));self.assertAlmostEqual(result['charge_C'],1800);self.assertAlmostEqual(result['electrical_energy_Wh'],1.4)
        self.assertTrue(all(c['passed'] for c in result['independent_checks'].values()))
    def test_different_windows_do_not_produce_a_ratio(self):
        value=sample();value['time_alignment']='different_interval';self.assertIsNone(accounting(validate_input(value))['apparent_collected_to_charge_ratio'])
    def test_ratio_above_one_is_flagged_not_clipped(self):
        value=sample();value['collected_o2_g']=1;result=accounting(validate_input(value));self.assertGreater(result['apparent_collected_to_charge_ratio'],1);self.assertTrue(result['ratio_above_one'])
    def test_composition_inventory_has_separate_reference(self):
        value=sample();value['sample_mass_g']=100;value['composition']={'analysis_id':'pure-silica-control','source':'Constructed stoichiometric control','rows':[{'oxide':'SiO2','wt_percent':100}]}
        result=accounting(validate_input(value));self.assertAlmostEqual(result['inventory']['represented_oxygen_g'],100*31.998/(28.085+31.998));self.assertTrue(result['independent_checks']['inventory_o2_g']['passed'])
    def test_partial_uncertainty_is_not_full_propagation(self):
        value=sample();value['oxygen_uncertainty_g']=0.001;self.assertIsNone(accounting(validate_input(value))['sensitivity'])
    def test_full_absolute_bounds_have_independently_checked_sensitivity(self):
        value=sample();value.update(current_uncertainty_A=0.01,duration_uncertainty_s=1,oxygen_uncertainty_g=0.002)
        result=accounting(validate_input(value));self.assertIsNotNone(result['sensitivity']);self.assertTrue(result['independent_checks']['bound_ratio_max']['passed'])


class AgentTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def test_no_paid_work_without_flag(self):
        with self.assertRaises(EvidenceError):run(self.root,sample(),client_factory=FakeClient)
    def test_complete_input_driven_loop_has_five_calls_two_actual_checks(self):
        with patch('urllib.request.build_opener',side_effect=AssertionError('No network')):r=run(self.root,sample(),True,client_factory=FakeClient)
        saved=load(self.root,r['assessment_id']);self.assertEqual(r['api_attempts'],5);self.assertEqual(saved['status'],'completed');self.assertEqual(len(saved['report']['tools']),2);self.assertEqual(saved['report']['execution_mode'],'test-double')
        self.assertEqual(saved['report']['validation']['engineering_ground_truth'],'not available for new user input')
    def test_input_gate_does_not_rewrite_raw_model_judgement(self):
        r=run(self.root,sample(),True,client_factory=FakeClient);report=load(self.root,r['assessment_id'])['report']
        self.assertEqual(report['final_review']['judgement'],'conditional_review');self.assertEqual(report['effective_review_status'],'evidence_needed')
    def test_hardware_authorization_is_code_policy_not_model_boolean(self):
        from mre_engineer.experiment_agent import PLAN
        self.assertNotIn('ready_for_hardware_operation',PLAN['properties'])
        self.assertEqual(PLAN['properties']['review_scope'],{'type':'string','enum':['document_review_only']})
        r=run(self.root,sample(),True,client_factory=FakeClient);report=load(self.root,r['assessment_id'])['report']
        self.assertIs(report['ready_for_hardware_operation'],False)
        self.assertEqual(report['final_review']['review_scope'],'document_review_only')
    def test_wrong_review_scope_is_rejected_without_coercion_or_retry(self):
        class BadScope(FakeClient):
            def request(self,body):
                response=super().request(body)
                if body['tools'][0]['name']=='submit_experiment_review':
                    args=json.loads(response['output'][0]['arguments']);args['review_scope']=False;response['output'][0]['arguments']=json.dumps(args)
                return response
        r=run(self.root,sample(),True,client_factory=BadScope)
        self.assertEqual(r['api_attempts'],2);self.assertEqual(r['status'],'failed');self.assertIsNone(load(self.root,r['assessment_id'])['report']['final_review'])
    def test_unknown_model_citation_stops_without_fabricated_final(self):
        class Bad(FakeClient):
            def request(self,body):
                value=super().request(body)
                args=json.loads(value['output'][0]['arguments']);args['evidence_refs']=['not-returned'];value['output'][0]['arguments']=json.dumps(args);return value
        r=run(self.root,sample(),True,client_factory=Bad);self.assertEqual(r['api_attempts'],1);self.assertEqual(r['status'],'failed');self.assertIsNone(load(self.root,r['assessment_id'])['report']['final_review'])
    def test_independent_math_failure_blocks_before_client(self):
        with patch('mre_engineer.experiment_agent.accounting',side_effect=EvidenceError('Mismatch')):
            with self.assertRaises(EvidenceError):run(self.root,sample(),True,client_factory=lambda *a:self.fail('Must not call model'))
    def test_stop_prevents_the_next_request(self):
        r=run(self.root,sample(),True,client_factory=FakeClient,stop=lambda:True);self.assertEqual(r['api_attempts'],0);self.assertEqual(r['status'],'failed')
    def test_tampered_report_is_not_replayed_as_valid(self):
        r=run(self.root,sample(),True,client_factory=FakeClient);p=self.root/'outputs/assessments'/r['assessment_id']/'report.json';data=json.loads(p.read_text());data['input']['current_A']=99;p.write_text(json.dumps(data));self.assertEqual(load(self.root,r['assessment_id'])['status'],'needs-review')
    def test_review_is_recorded_separately_without_overwriting_model(self):
        r=run(self.root,sample(),True,client_factory=FakeClient);id=r['assessment_id'];before=load(self.root,id)['report']['sha256'];save_review(self.root,id,'changes_requested','Owner','Need original calibration records')
        after=load(self.root,id);self.assertEqual(after['report']['sha256'],before);self.assertEqual(after['review']['state'],'changes_requested')
        with self.assertRaises(EvidenceError):save_review(self.root,id,'accepted_draft','Owner','Second overwrite is not allowed')
    def test_edited_example_is_not_labelled_an_unchanged_published_case(self):
        data=example();data['collected_o2_g']=0.08;r=run(self.root,data,True,example_id='yu2025-one-hour',client_factory=FakeClient)
        provenance=load(self.root,r['assessment_id'])['report']['provenance'];self.assertEqual(provenance['kind'],'edited_published_example');self.assertIn('collected_o2_g',provenance['changed_fields'])


class CommentEvidenceTests(unittest.TestCase):
    def test_critic_cannot_cite_a_fabricated_measurement_field(self):
        from mre_engineer.experiment_agent import verify_critic_comments,tool
        data=validate_input(sample());receipt=tool(data,'performance_assessment')
        critic={'comments':[{'input_fields':['fabricated_sensor'],'metric_ids':[],'evidence_refs':[receipt['evidence_id']]}]}
        with self.assertRaises(EvidenceError):verify_critic_comments(critic,data,receipt['result'],[receipt['evidence_id']],[receipt])
    def test_critic_numbers_need_their_executed_performance_receipt(self):
        from mre_engineer.experiment_agent import verify_critic_comments,tool
        data=validate_input(sample());receipt=tool(data,'performance_assessment')
        critic={'comments':[{'input_fields':['collected_o2_g'],'metric_ids':['oxygen_rate_g_h'],'evidence_refs':['input-record']}]}
        with self.assertRaises(EvidenceError):verify_critic_comments(critic,data,receipt['result'],['input-record',receipt['evidence_id']],[receipt])
    def test_comment_evidence_resolves_real_receipt_and_input(self):
        from mre_engineer.experiment_agent import critic_evidence,verify_critic_comments,tool,source_context
        data=validate_input(sample());receipt=tool(data,'performance_assessment')
        critic={'comments':[{'dimension':'production','position':'retain_original','comment':'Constructed review','basis':'The executed calculation uses the declared aligned interval.','input_fields':['collected_o2_g'],'metric_ids':['oxygen_rate_g_h'],'evidence_refs':[receipt['evidence_id']]}]}
        verify_critic_comments(critic,data,receipt['result'],[receipt['evidence_id']],[receipt])
        proof=critic_evidence(critic,data,receipt['result'],[receipt],source_context(data))
        self.assertEqual(proof[0]['inputs']['collected_o2_g'],0.07);self.assertEqual(proof[0]['references'][0]['tool'],'performance_assessment')
        self.assertEqual(proof[0]['basis'],critic['comments'][0]['basis'])
    def test_uploaded_record_locator_does_not_impersonate_gas_calibration(self):
        data=validate_input(sample());provenance={'kind':'excel','filename':'Constructed.xlsx','import_id':'a'*32}
        gaps={g['id'] for g in readiness(data,provenance)['gaps']}
        self.assertNotIn('original_records',gaps);self.assertIn('gas_calibration',gaps)
        gaps={g['id'] for g in readiness(data,{**provenance,'kind':'edited_excel'})['gaps']}
        self.assertIn('original_records',gaps)
    def test_critic_schema_requires_basis_for_each_comment(self):
        from mre_engineer.experiment_agent import CRITIC
        from mre_engineer.agent_contracts import validate
        value={'weakness':'Constructed','rival_explanation':'Constructed','requested_revision':'Constructed','evidence_refs':['input-record'],'comments':[{'dimension':'production','position':'retain_original','comment':'Constructed','input_fields':[],'metric_ids':[],'evidence_refs':['input-record']}]}
        with self.assertRaises(EvidenceError):validate(value,CRITIC)
