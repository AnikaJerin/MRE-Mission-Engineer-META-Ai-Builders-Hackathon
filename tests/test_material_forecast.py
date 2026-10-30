import tempfile,unittest,copy
from unittest.mock import patch
from mre_engineer.material_forecast import validate,save,latest
from mre_engineer.evidence import EvidenceError
D=dict(component='wall',measured_loss_um=40,loss_bound_um=5,exposure_h=3,horizon_h=3,initial_thickness_um=1000,source='SYNTHETIC example',comparable_conditions=True)
class SavedMaterialForecastTests(unittest.TestCase):
 def test_save_reopen_and_uncertainty_without_modifying_assessment(self):
  original={'sha256':'original-sha'};before=copy.deepcopy(original)
  with tempfile.TemporaryDirectory() as root,patch('mre_engineer.reactor_hypotheses.assessment',return_value=original):
   r=save(root,'case',D);self.assertEqual(r['api_calls'],0);self.assertEqual(r['prediction']['total_loss_um'],80);self.assertEqual(r['prediction']['total_loss_lower_um'],70);self.assertEqual(r['prediction']['total_loss_upper_um'],90);self.assertEqual(latest(root,'case')['latest'],r)
  self.assertEqual(original,before)
 def test_future_conditions_must_be_explicit(self):
  with self.assertRaises(EvidenceError):validate({**D,'comparable_conditions':False})
 def test_nonfinite_inputs_rejected(self):
  with self.assertRaises(EvidenceError):validate({**D,'horizon_h':float('nan')})
 def test_zero_exposure_rejected(self):
  with self.assertRaises(EvidenceError):validate({**D,'exposure_h':0})
