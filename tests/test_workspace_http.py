"""Protected local actions without opening a socket or starting any server."""
import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
from mre_engineer.dashboard import Handler


class WorkspaceHTTPTests(unittest.TestCase):
    def make_handler(self,body=None):
        h=object.__new__(Handler)
        h.server=SimpleNamespace(server_port=8768,csrf='offline-token',actions=Mock())
        h.headers={'Host':'127.0.0.1:8768','Origin':'http://127.0.0.1:8768','X-MRE-Token':'offline-token','Content-Type':'application/json'}
        encoded=json.dumps(body or {'action':'stop'}).encode();h.headers['Content-Length']=str(len(encoded));h.rfile=io.BytesIO(encoded);h.path='/api/actions';h._respond=Mock();return h
    def test_foreign_origin_cannot_start_paid_job(self):
        h=self.make_handler();h.headers['Origin']='https://other.example';h.do_POST()
        self.assertEqual(h._respond.call_args.args[0],403);h.server.actions.start.assert_not_called()
    def test_missing_token_cannot_start_job(self):
        h=self.make_handler();del h.headers['X-MRE-Token'];h.do_POST()
        self.assertEqual(h._respond.call_args.args[0],403);h.server.actions.start.assert_not_called()
    def test_non_ascii_wrong_token_is_rejected_without_handler_crash(self):
        h=self.make_handler();h.headers['X-MRE-Token']='ভুল';h.do_POST()
        self.assertEqual(h._respond.call_args.args[0],403)
    def test_owner_stop_action_is_dispatched_once(self):
        h=self.make_handler();h.server.actions.start.return_value={'status':'stop-requested'};h.do_POST()
        self.assertEqual(h._respond.call_args.args[0],202);h.server.actions.start.assert_called_once_with({'action':'stop'})
    def test_oversized_body_is_rejected_before_dispatch(self):
        h=self.make_handler();h.headers['Content-Length']='16001';h.do_POST()
        self.assertEqual(h._respond.call_args.args[0],400);h.server.actions.start.assert_not_called()
    def test_duplicate_action_keys_are_rejected(self):
        h=self.make_handler();body=b'{"action":"stop","action":"run"}';h.rfile=io.BytesIO(body);h.headers['Content-Length']=str(len(body));h.do_POST()
        self.assertEqual(h._respond.call_args.args[0],400);h.server.actions.start.assert_not_called()
    def test_workspace_refresh_never_dispatches_a_job(self):
        h=self.make_handler();h.path='/api/workspace';h.root='.'
        for field in ('accounting_run','investigation_run','pilot_run','source_run','release_run','engineering_run'):setattr(h,field,'v1')
        h.server.actions.state.return_value={'state':'idle'}
        with patch('mre_engineer.dashboard.snapshot',return_value={}),patch('mre_engineer.dashboard.overview',return_value={}),patch('mre_engineer.dashboard.api_budget.snapshot',return_value={}):h.do_GET()
        self.assertEqual(h._respond.call_args.args[0],200);h.server.actions.start.assert_not_called()
    def test_export_path_traversal_is_rejected(self):
        h=self.make_handler();h.root='.';h.path='/api/export?name=..%2Fescape&format=html';h.do_GET()
        self.assertEqual(h._respond.call_args.args[0],422)
