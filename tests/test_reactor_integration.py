"""Owner-run targeted integration checks; no network or paid API."""
import unittest
from mre_engineer.experiment_input import validate_input
from mre_engineer.reactor_field import simulate
from mre_engineer.investigation import digest
from mre_engineer.evidence import EvidenceError

class ReactorIntegrationTests(unittest.TestCase):
    def test_scenario_is_explicit_and_receipt_tracks_input(self):
        value={'experiment_name':'Synthetic radial test','duration_s':3600,'current_A':.5,
          'reactor_scenario':dict(inner_radius_mm=3,outer_radius_mm=12,height_mm=25,
            conductivity_S_m=10,thermal_conductivity_W_mK=2,current_A=.5,
            inner_temperature_C=1600,outer_temperature_C=1500)}
        a=validate_input(value);receipt={'result':simulate(a['reactor_scenario']),'evidence_id':digest(a['reactor_scenario'])}
        self.assertEqual(receipt['result']['input'],a['reactor_scenario'])
        value['reactor_scenario']['current_A']=1
        b={'result':simulate(validate_input(value)['reactor_scenario']),'evidence_id':digest(value['reactor_scenario'])}
        self.assertNotEqual(receipt['evidence_id'],b['evidence_id'])
        self.assertAlmostEqual(b['result']['joule_power_W'],4*receipt['result']['joule_power_W'])
    def test_simulation_never_invents_missing_scenario(self):
        a=validate_input({'experiment_name':'No scenario','duration_s':3600,'current_A':.5})
        with self.assertRaises(EvidenceError):simulate(a.get('reactor_scenario'))
    def test_scenario_draft_survives_workspace_validation(self):
        from mre_engineer.workspace_store import validate_draft
        s=dict(inner_radius_mm=3,outer_radius_mm=12,height_mm=25,conductivity_S_m=10,
               thermal_conductivity_W_mK=2,current_A=.5,inner_temperature_C=1600,outer_temperature_C=1500)
        encoded=validate_draft({'form':{'reactor_scenario':s},'tab':'manual','view':'input'})
        self.assertIn('reactor_scenario',encoded)
    def test_scenario_endpoint_is_local_and_does_not_dispatch_api(self):
        import io,json
        from types import SimpleNamespace
        from unittest.mock import Mock
        from mre_engineer.dashboard import Handler
        s=dict(inner_radius_mm=3,outer_radius_mm=12,height_mm=25,conductivity_S_m=10,
               thermal_conductivity_W_mK=2,current_A=.5,inner_temperature_C=1600,outer_temperature_C=1500)
        raw=json.dumps(s).encode();h=object.__new__(Handler)
        h.server=SimpleNamespace(server_port=8769,csrf='test-token',actions=Mock())
        h.path='/api/reactor-scenario';h.headers={'Host':'127.0.0.1:8769','Origin':'http://127.0.0.1:8769',
          'X-MRE-Token':'test-token','Content-Type':'application/json','Content-Length':str(len(raw))}
        h.rfile=io.BytesIO(raw);h._respond=Mock();h.do_POST()
        self.assertEqual(h._respond.call_args.args[0],200)
        h.server.actions.start.assert_not_called()
