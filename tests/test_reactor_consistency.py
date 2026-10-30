import unittest
from mre_engineer.reactor_consistency import inspect
class MeasurementBasisTests(unittest.TestCase):
 def test_different_measurement_bases_are_reported_without_rewriting(self):
  d={'trace':[{'time_s':0,'current_A':.5,'voltage_V':3.2}], 'resistance_trace':[{'time_s':0,'resistance_ohm':1.54}]}
  result=inspect(d);self.assertEqual(result['electrical_pairs'][0]['dc_apparent_V_over_I_ohm'],6.4);self.assertEqual(d['resistance_trace'][0]['resistance_ohm'],1.54)
 def test_unmatched_times_are_not_paired(self):
  self.assertEqual(inspect({'trace':[{'time_s':0,'current_A':.5,'voltage_V':3.2}],'resistance_trace':[{'time_s':1,'resistance_ohm':1.54}]})['electrical_pairs'],[])
 def test_zero_current_is_not_divided(self):
  self.assertEqual(inspect({'trace':[{'time_s':0,'current_A':0,'voltage_V':3.2}],'resistance_trace':[{'time_s':0,'resistance_ohm':1.54}]})['electrical_pairs'],[])
