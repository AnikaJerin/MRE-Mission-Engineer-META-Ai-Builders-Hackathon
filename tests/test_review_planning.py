import unittest
from mre_engineer.experiment_agent import planning_context,PROMPT
class ReviewPlanningTests(unittest.TestCase):
    def test_cracks_and_electrical_evidence_remain_rivals_to_gas_accounting(self):
        context=planning_context({'crack_observation':'detected','wall_loss_um':40,'resistance_trace':[{'time_s':0,'resistance_ohm':1}]})
        self.assertEqual({c['candidate'] for c in context['rival_requests_to_consider']},{'material_characterization_review','current_record_review'})
        self.assertIn('priority remains unranked',context['priority_rule'])
    def test_no_inputs_do_not_invent_concerns(self):
        self.assertEqual(planning_context({})['rival_requests_to_consider'],[])
    def test_gas_discrimination_and_observation_limits_are_explicit(self):
        self.assertIn('Independent recovery',planning_context({})['gas_discrimination_limit'])
        self.assertIn('cannot separate collection losses',PROMPT)
        self.assertIn('not good performance',PROMPT)
