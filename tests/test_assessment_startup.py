"""Regression checks for assessment initialization and useful crash diagnostics."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from mre_engineer.experiment_agent import source_context,candidates,preview
from mre_engineer.experiment_input import validate_input,readiness,CANDIDATES
from mre_engineer.workspace_actions import Actions


def sample():
    raw=json.loads((Path(__file__).parent/'fixtures/full_workflow_synthetic.json').read_text())
    raw.update(configuration='hollow_ysz_pt',feedstock='LHS-1',temperature_C=1600,
               duration_s=3600,current_A=.5,trace=[],voltage_V=3.2,collected_o2_g=.09,
               current_uncertainty_A=.005,duration_uncertainty_s=1,oxygen_uncertainty_g=.002,
               initial_resistance_ohm=None,final_resistance_ohm=None,
               resistance_trace=[{'time_s':0,'resistance_ohm':1.54},{'time_s':1800,'resistance_ohm':1.60},{'time_s':3600,'resistance_ohm':1.70}],
               thermal_exposure_h=3,wall_loss_um=40,wall_loss_uncertainty_um=5,
               endurance_test_h=1,system_operating_h=None,reported_projected_lifetime_h=None,
               projection_model='not_requested',retirement_wall_loss_um=None,
               total_energy_kWh=.12,comparison_profile='none')
    return raw


class AssessmentStartupTests(unittest.TestCase):
    def test_source_and_candidate_definitions_exist_without_network(self):
        data=validate_input(sample())
        with patch('urllib.request.build_opener',side_effect=AssertionError('No network')):
            refs=source_context(data)
            options=candidates(data,readiness(data,None))
        self.assertIn('si-constants',{s['id'] for s in refs})
        self.assertIn('yu-hollow-anode',{s['id'] for s in refs})
        self.assertEqual({c['id'] for c in options},set(CANDIDATES))
        self.assertTrue(all(c['label'] for c in options))

    def test_mixed_synthetic_measurements_reach_source_comparison(self):
        with tempfile.TemporaryDirectory() as root,patch('urllib.request.build_opener',side_effect=AssertionError('No network')):
            result=preview(root,sample())
        self.assertEqual(result['api_calls'],0)
        self.assertAlmostEqual(result['accounting']['charge_C'],1800)
        metrics=result['performance']['metrics']
        self.assertAlmostEqual(metrics['resistance_change_percent']['value'],100*(1.70-1.54)/1.54)
        self.assertAlmostEqual(metrics['wall_loss_rate_um_h']['value'],40/3)
        self.assertAlmostEqual(metrics['reported_specific_energy_kWh_kg']['value'],.12*1000/.09)
        self.assertEqual(result['performance']['publication_comparisons']['status'],'declared_context_matched_not_experimental_equivalence')

    def test_unexpected_failure_saves_locations_without_secret_text(self):
        with tempfile.TemporaryDirectory() as root,patch('mre_engineer.experiment_agent.run',side_effect=RuntimeError('secret-do-not-log')):
            actions=Actions(root)
            actions._work({'action':'assess','input':{}})
            state=actions.state()
            self.assertEqual(state['state'],'failed')
            self.assertIn('RuntimeError',state['error'])
            path=Path(root)/'outputs/workspace-errors'/f"{state['diagnostic_id']}.json"
            diagnostic=path.read_text()
            self.assertNotIn('secret-do-not-log',diagnostic)
            self.assertNotIn('secret-do-not-log',state['error'])
            self.assertTrue(json.loads(diagnostic)['frames'])
