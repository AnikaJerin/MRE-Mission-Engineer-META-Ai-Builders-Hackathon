"""Read-only refresh and explicit-input dispatch checks; no sockets or real requests."""
import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
from mre_engineer.dashboard import Handler,read_action_body
from mre_engineer.workspace_actions import Actions
from mre_engineer.evidence import EvidenceError


class ResearcherActionsTests(unittest.TestCase):
    def test_assessment_needs_explicit_credit_consent(self):
        with self.assertRaises(EvidenceError):Actions('.').start({'action':'assess','input':{}})
    def test_bad_input_fails_before_thread_and_api(self):
        with patch('threading.Thread') as thread:
            with self.assertRaises(EvidenceError):Actions('.').start({'action':'assess','consent':True,'input':{'experiment_name':'Missing current and duration'}})
            thread.assert_not_called()
    def test_duplicate_and_nonfinite_action_values_are_rejected(self):
        for raw in (b'{"action":"stop","action":"assess"}',b'{"value":NaN}',b'{"value":1e999}'):
            with self.assertRaises(EvidenceError):read_action_body(raw)
    def test_large_import_is_not_rejected_by_model_text_limit(self):
        value={'action':'import_excel','filename':'control.xlsx','file_base64':'A'*25000};self.assertEqual(read_action_body(json.dumps(value).encode()),value)
    def handler(self,path):
        h=object.__new__(Handler);h.path=path;h.root='.';h.server=SimpleNamespace(server_port=8769,csrf='test',actions=Mock(),persistence={'schema_version':1});h.headers={'Host':'127.0.0.1:8769'};h._respond=Mock();return h
    def test_researcher_refresh_does_not_dispatch_assessment(self):
        h=self.handler('/api/experiment-workspace');h.server.actions.state.return_value={'state':'idle'}
        with patch('mre_engineer.dashboard.list_reports',return_value=[]),patch('mre_engineer.dashboard.api_budget.snapshot',return_value={}),patch('mre_engineer.dashboard.workspace_store.load_draft',return_value={'revision':0,'draft':None}):h.do_GET()
        self.assertEqual(h._respond.call_args.args[0],200);h.server.actions.start.assert_not_called()
    def test_example_load_does_not_dispatch_assessment(self):
        h=self.handler('/api/experiment-example');h.do_GET();self.assertEqual(h._respond.call_args.args[0],200);h.server.actions.start.assert_not_called()
    def test_report_export_escapes_user_text_and_makes_no_api_calls(self):
        from mre_engineer.experiment_report import to_html
        # A minimal constructed export, not a model or reactor ground truth.
        report={'input':{'experiment_name':'<script>alert(1)</script>','question':'Review'},'status':'failed','effective_review_status':'incomplete',
          'accounting':{'charge_C':1,'ideal_o2_g':0.1,'reported_collected_o2_g':None,'apparent_collected_to_charge_ratio':None,'electrical_energy_Wh':None,'basis':'Constructed'},
          'readiness':{'gaps':[]},'original_review':None,'critique':None,'final_review':None,'sources':[],'api_attempts':0,'settled_estimated_cost_usd':0,'completed_at':'test'}
        with patch('urllib.request.build_opener',side_effect=AssertionError('No network')):text=to_html({'assessment':report,'researcher_review':{'state':'awaiting_review'}})
        self.assertNotIn('<script>alert',text);self.assertIn('&lt;script&gt;',text)

    def test_draft_save_is_protected_and_does_not_dispatch_paid_work(self):
        h=self.handler('/api/workspace-draft')
        body=json.dumps({'draft':{'form':{}},'revision':0}).encode()
        h.headers.update({'Origin':'http://127.0.0.1:8769','X-MRE-Token':'test','Content-Type':'application/json','Content-Length':str(len(body))});h.rfile=io.BytesIO(body)
        with patch('mre_engineer.dashboard.workspace_store.save_draft',return_value={'revision':1,'api_calls':0}) as save:
            h.do_POST();save.assert_called_once()
        self.assertEqual(h._respond.call_args.args[0],200);h.server.actions.start.assert_not_called()
    def test_foreign_origin_cannot_modify_saved_draft(self):
        h=self.handler('/api/workspace-draft');h.headers.update({'Origin':'https://untrusted.example','X-MRE-Token':'test'})
        with patch('mre_engineer.dashboard.workspace_store.save_draft') as save:h.do_POST();save.assert_not_called()
        self.assertEqual(h._respond.call_args.args[0],403)
    def test_library_read_does_not_dispatch_paid_work(self):
        h=self.handler('/api/evidence-library')
        with patch('mre_engineer.dashboard.workspace_store.registry',return_value={'version':'constructed'}):h.do_GET()
        self.assertEqual(h._respond.call_args.args[0],200);h.server.actions.start.assert_not_called()

    def test_unreadable_billing_blocks_paid_work_without_hiding_saved_reviews(self):
        from mre_engineer.dashboard import researcher_workspace
        server=SimpleNamespace(csrf='test',actions=Mock(),persistence={'schema_version':1})
        with patch('mre_engineer.dashboard.api_budget.snapshot',side_effect=EvidenceError('Corrupt ledger')),patch('mre_engineer.dashboard.workspace_store.load_draft',return_value={'revision':0,'draft':None}),patch('mre_engineer.dashboard.list_reports',return_value=[{'id':'constructed'}]):
            value=researcher_workspace('.',server)
        self.assertEqual(len(value['assessments']),1);self.assertEqual(value['budget']['blocking_unresolved_requests'],['ledger-unreadable']);server.actions.start.assert_not_called()
