import tempfile,unittest
from unittest.mock import patch
from mre_engineer.workspace_actions import Actions
from mre_engineer.evidence import EvidenceError
class UIBillingRecoveryTests(unittest.TestCase):
 def test_acceptance_required_before_dispatch(self):
  with tempfile.TemporaryDirectory() as root:
   with self.assertRaises(EvidenceError):Actions(root).start({'action':'acknowledge_unknown_cost','request_id':'abc'})
 def test_recovery_action_only_calls_local_acknowledgement(self):
  with tempfile.TemporaryDirectory() as root,patch('mre_engineer.api_budget.acknowledge_unknown_cost',return_value={'id':'abc'}) as ack:
   actions=Actions(root);actions._work({'action':'acknowledge_unknown_cost','request_id':'abc','consent':True})
   ack.assert_called_once_with(actions.root,'abc',True);self.assertEqual(actions.state()['result']['api_calls'],0)
