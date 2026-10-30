import tempfile,unittest
from unittest.mock import patch
from mre_engineer.api_budget import snapshot
class BudgetStatusClassificationTests(unittest.TestCase):
 def test_reserved_request_is_not_unknown_cost_recovery(self):
  row=dict(id='active',state='reserved',reservation_microusd=250000,accounted_microusd=250000)
  with tempfile.TemporaryDirectory() as root,patch('mre_engineer.api_budget._read',return_value={'requests':[row]}):
   r=snapshot(root)
  self.assertEqual(r['active_reserved_requests'],['active']);self.assertEqual(r['recoverable_unknown_cost_requests'],[]);self.assertEqual(r['blocking_unresolved_requests'],['active'])
 def test_only_unknown_equal_reservation_is_acknowledgeable(self):
  rows=[dict(id='unknown',state='unresolved',reservation_microusd=250000,accounted_microusd=250000),dict(id='exceeded',state='unresolved',reservation_microusd=250000,accounted_microusd=300000)]
  with tempfile.TemporaryDirectory() as root,patch('mre_engineer.api_budget._read',return_value={'requests':rows}):r=snapshot(root)
  self.assertEqual(r['recoverable_unknown_cost_requests'],['unknown']);self.assertEqual(r['active_reserved_requests'],[])
