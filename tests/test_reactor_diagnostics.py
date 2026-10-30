import unittest
from mre_engineer.reactor_diagnostics import SCENARIOS,baseline,run
from mre_engineer.evidence import EvidenceError
class DiagnosticsTests(unittest.TestCase):
 def test_constructed_reference_rules_agree(self):
  for c in SCENARIOS:self.assertEqual(baseline(c['observations']),(c['expected'],c['test']))
 def test_unmatched_balance_cannot_locate_fault(self):
  self.assertEqual(baseline({'trap_O2_g':.1,'same_window':False,'calibration_verified':True})[0],'unresolved')
 def test_no_paid_run_without_flag(self):
  with self.assertRaises(EvidenceError):run('/unused','v1','v1')
