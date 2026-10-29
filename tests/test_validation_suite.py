"""Offline T12 contracts; test doubles are never evidence of live model quality."""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from mre_engineer import validation_suite as suite
from mre_engineer.workspace_actions import Actions
from mre_engineer.evidence import EvidenceError

ROOT=Path(__file__).resolve().parents[1]


class FakeClient:
    def __init__(self,root,emit):self.root=root;self.calls=0
    def request(self,body):
        self.calls+=1
        assert self.calls<=5
        data=json.loads(body['input']);name=body['tools'][0]['name'];refs=data['allowed_evidence_refs']
        assert 'reference_key.json' not in body['input'] and 'reference_basis' not in body['input']
        assert 'uniqueItems' not in json.dumps(body['tools'][0]['parameters'])
        case=next(c for c in suite.load_cases(self.root) if c['question']==data['evidence']['question'] and c['record']==data['evidence']['record'])
        if name=='t12_choice':value={'tool':'arithmetic_check','reason':'Offline fixture','evidence_refs':[refs[0]]}
        elif name=='t12_critic':value={'weakness':'No fabricated change','requested_revision':'Retain correct assessment','evidence_refs':[refs[-1]]}
        else:
            # Test fixture reads the key, never the real model prompt.
            key=suite.load_key(self.root)[case['id']]
            value={'verdict':key['verdict'],'missing_inputs':key['missing_inputs'],'value':suite.reference_calculate(case['numeric_task']),
              'unit':case['numeric_task']['unit'] if case['numeric_task'] else 'not_applicable','rationale':'Offline reference fixture','next_evidence_request':'Acquire applicable outcome records','evidence_refs':key['required_refs']}
        return {'id':'offline','output':[{'type':'function_call','name':name,'arguments':json.dumps(value)}]}


class SuiteTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        shutil.copytree(ROOT/'benchmarks/t12',self.root/'benchmarks/t12')
    def test_six_each_with_no_source_family_overlap(self):
        cases=suite.load_cases(self.root)
        self.assertEqual([sum(c['split']==s for c in cases) for s in ('development','evaluation')],[6,6])
        a={c['source_group'] for c in cases if c['split']=='development'};b={c['source_group'] for c in cases if c['split']=='evaluation'}
        self.assertFalse(a & b);self.assertEqual(len(b),3)
    def test_split_source_family_leakage_rejected(self):
        p=self.root/suite.BASE/'cases.json';d=json.loads(p.read_text());d['cases'][-1]['source_group']=d['cases'][0]['source_group'];p.write_text(json.dumps(d))
        with self.assertRaises(EvidenceError):suite.load_cases(self.root)
    def test_all_reference_rows_have_basis_and_source_mapping(self):
        key=suite.load_key(self.root);self.assertEqual(len(key),12)
        self.assertTrue(all(v['basis'] and v['required_refs'] for v in key.values()))
    def test_independent_calculation_mismatch_blocks_before_client(self):
        suite.freeze(self.root,'unit')
        with patch('mre_engineer.validation_suite.numeric_check',return_value={'passed':False}):
            with self.assertRaisesRegex(EvidenceError,'Independent numeric mismatch'):
                suite.run(self.root,'bad','unit','development',allow_api_call=True,client_factory=lambda *a:self.fail('Must not instantiate client'))
    def test_charge_and_annual_goal_have_separate_numerical_references(self):
        cases=suite.load_cases(self.root)
        for c in cases:
            check=suite.numeric_check(c);self.assertTrue(check['passed'])
        self.assertAlmostEqual(suite.reference_calculate(cases[7]['numeric_task']),1000/8760)
        self.assertIsNone(suite.reference_calculate(None))
    def test_nonfinite_numeric_input_rejected(self):
        p=self.root/suite.BASE/'cases.json';d=json.loads(p.read_text());d['cases'][6]['numeric_task']['current_A']=-1;p.write_text(json.dumps(d))
        with self.assertRaises(EvidenceError):suite.load_cases(self.root)
    def test_freeze_stops_changed_reference_before_paid_call(self):
        suite.freeze(self.root,'unit');p=self.root/suite.BASE/'reference_key.json';p.write_text(p.read_text()+'\n')
        with self.assertRaises(EvidenceError):suite.check_freeze(self.root,'unit')
    def test_no_paid_work_without_explicit_flag(self):
        with self.assertRaises(EvidenceError):suite.run(self.root,'x','none','development',client_factory=FakeClient)
    def test_six_case_pipeline_uses_42_calls_and_does_not_claim_live(self):
        suite.freeze(self.root,'unit')
        with patch('urllib.request.build_opener',side_effect=AssertionError('No network')):
            result=suite.run(self.root,'dev','unit','development',allow_api_call=True,client_factory=FakeClient)
        self.assertEqual(result['status'],'t12-batch-completed');self.assertEqual(result['api_attempts'],42)
        saved=suite.load_report(self.root,'dev');self.assertTrue(saved['current']);self.assertEqual(saved['report']['execution_mode'],'test-double')
        self.assertFalse(suite.gate(self.root,suite.check_freeze(self.root,'unit'))['execution_complete'])
        self.assertEqual(result['summary']['methods']['one_pass']['correct'],6)
    def test_evaluation_numeric_denominator_excludes_non_numeric_tasks(self):
        suite.freeze(self.root,'unit');r=suite.run(self.root,'eval','unit','evaluation',allow_api_call=True,client_factory=FakeClient)
        self.assertEqual(r['summary']['methods']['one_pass']['numeric_total'],2)
        self.assertEqual(r['summary']['methods']['one_pass']['numeric_exact'],2)
        self.assertEqual(r['summary']['methods']['one_pass']['correct'],6)
    def test_failed_first_request_preserves_not_attempted_cases(self):
        class Bad(FakeClient):
            def request(self,body):self.calls+=1;return {'output':[]}
        suite.freeze(self.root,'unit');r=suite.run(self.root,'bad','unit','development',allow_api_call=True,client_factory=Bad)
        self.assertEqual(r['api_attempts'],1);self.assertEqual(r['status'],'t12-incomplete-or-changed')
        rows=suite.load_report(self.root,'bad')['report']['rows'];self.assertEqual(rows[1]['status'],'not-attempted')
        self.assertEqual(r['summary']['methods']['one_pass']['available'],0)
    def test_report_tampering_is_not_displayed_as_verified(self):
        suite.freeze(self.root,'unit');suite.run(self.root,'dev','unit','development','D01',True,FakeClient)
        p=suite.directory(self.root,'dev')/'report.json';d=json.loads(p.read_text());d['api_attempts']=0;p.write_text(json.dumps(d))
        self.assertEqual(suite.load_report(self.root,'dev')['status'],'needs-review')
    def test_unsupported_endorsement_and_contradiction_metrics(self):
        case=suite.load_cases(self.root)[8];key=suite.load_key(self.root)[case['id']];answer=suite.baseline(case);answer['verdict']='supported'
        s=suite.score(answer,case,key);self.assertTrue(s['unsupported_endorsement']);self.assertTrue(s['missed_contradiction']);self.assertFalse(s['passed'])
    def test_wrong_numeric_unit_or_missing_citation_fails(self):
        case=suite.load_cases(self.root)[6];key=suite.load_key(self.root)[case['id']];answer=suite.baseline(case)
        answer['unit']='kg/h';self.assertFalse(suite.score(answer,case,key)['passed'])
        answer=suite.baseline(case);answer['evidence_refs']=['unrelated'];self.assertFalse(suite.score(answer,case,key)['passed'])
    def test_missing_numeric_task_requires_null_and_not_applicable(self):
        case=suite.load_cases(self.root)[8];key=suite.load_key(self.root)[case['id']];answer=suite.baseline(case);answer['value']=0
        self.assertFalse(suite.score(answer,case,key)['passed'])
    def test_ui_construct_and_state_do_not_start_jobs(self):
        with patch('mre_engineer.validation_suite.run',side_effect=AssertionError('No automatic API')):
            actions=Actions(self.root);self.assertEqual(actions.state()['state'],'idle')
    def test_ui_requires_explicit_credit_consent(self):
        with self.assertRaises(EvidenceError):Actions(self.root).start({'action':'run','run_name':'x','freeze_name':'unit','split':'development','consent':False})
    def test_ui_rejects_arbitrary_actions_and_path_traversal(self):
        with self.assertRaises(EvidenceError):Actions(self.root).start({'action':'shell','command':'anything'})
        with self.assertRaises(EvidenceError):Actions(self.root).start({'action':'export','run_name':'../escape'})
    def test_ui_does_not_run_two_jobs_at_once(self):
        actions=Actions(self.root);actions.job={'state':'running'}
        with self.assertRaises(EvidenceError):actions.start({'action':'check'})
    def test_stop_prevents_further_api_calls(self):
        suite.freeze(self.root,'unit');r=suite.run(self.root,'stop','unit','development','D01',True,FakeClient,stop=lambda:True)
        self.assertEqual(r['api_attempts'],0)
    def test_unknown_missing_input_is_not_accepted(self):
        case=suite.load_cases(self.root)[0]
        class Bad(FakeClient):
            def request(self,body):
                value=suite.baseline(case);value['missing_inputs']=['imaginary']
                return {'output':[{'type':'function_call','name':'t12_answer','arguments':json.dumps(value)}]}
        with self.assertRaises(EvidenceError):suite.submit(Bad(self.root,None),case,'t12_answer',suite.ANSWER,{},['dev-record'],lambda *a:None,None)

    def test_record_categories_are_constrained_in_provider_schema(self):
        from mre_engineer.evaluation import provider_output_schema
        wire=provider_output_schema(suite.ANSWER)
        self.assertEqual(wire['properties']['missing_inputs']['items']['enum'],suite.RECORD_CATEGORIES)
        self.assertNotIn('current_A',wire['properties']['missing_inputs']['items']['enum'])

    def test_unsupported_current_unit_is_not_a_missing_record(self):
        case=next(c for c in suite.load_cases(self.root) if c['id']=='D05')
        answer=suite.baseline(case)
        self.assertEqual(answer['verdict'],'reject_input')
        self.assertEqual(answer['missing_inputs'],[])
        self.assertTrue(suite.score(answer,case,suite.load_key(self.root)['D05'])['passed'])

    def test_numeric_field_cannot_pass_the_full_answer_schema(self):
        from mre_engineer.agent_contracts import validate
        case=next(c for c in suite.load_cases(self.root) if c['id']=='D05');answer=suite.baseline(case)
        answer['missing_inputs']=['current_A']
        with self.assertRaises(EvidenceError):validate(answer,suite.ANSWER)
