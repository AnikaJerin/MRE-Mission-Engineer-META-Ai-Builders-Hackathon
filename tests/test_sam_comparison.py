import unittest
from mre_engineer.sam_comparison import calculate,validate_input
from mre_engineer.evidence import EvidenceError
class SamComparisonTests(unittest.TestCase):
 def form(self):
  return dict(before_id='before',after_id='after',before_mask=0,after_mask=0,before_mm_per_px=.1,after_mm_per_px=.2,before_scale_bound=0,after_scale_bound=0,aligned=True,masks_confirmed=True,same_component=True,notes='scale target')
 def test_different_scales_same_physical_area(self):
  b=dict(area_px=400,area_one_pixel_low=350,area_one_pixel_high=450,max_width_px=20,median_row_width_px=20)
  a=dict(area_px=100,area_one_pixel_low=75,area_one_pixel_high=125,max_width_px=10,median_row_width_px=10)
  r=calculate(b,a,self.form())
  self.assertAlmostEqual(r['change']['projected_area_percent'],0)
  self.assertAlmostEqual(r['change']['max_width_mm'],0)
  self.assertLess(r['change']['area_change_low_mm2'],0)
  self.assertGreater(r['change']['area_change_high_mm2'],0)
 def test_missing_alignment_rejected(self):
  f=self.form();f['aligned']=False
  with self.assertRaises(EvidenceError):validate_input(f)
 def test_identical_capture_rejected(self):
  f=self.form();f['after_id']=f['before_id']
  with self.assertRaises(EvidenceError):validate_input(f)
 def test_nonfinite_scale_rejected(self):
  f=self.form();f['before_mm_per_px']=float('nan')
  with self.assertRaises(EvidenceError):validate_input(f)
 def test_bound_larger_than_scale_rejected(self):
  f=self.form();f['before_scale_bound']=.2
  with self.assertRaises(EvidenceError):validate_input(f)
 def test_scale_and_mask_bounds_propagate(self):
  f=self.form();f['before_scale_bound']=.01;f['after_scale_bound']=.02
  b=dict(area_px=400,area_one_pixel_low=350,area_one_pixel_high=450,max_width_px=20,median_row_width_px=20)
  a=dict(area_px=100,area_one_pixel_low=75,area_one_pixel_high=125,max_width_px=10,median_row_width_px=10)
  r=calculate(b,a,f)
  self.assertAlmostEqual(r['before']['area_low_mm2'],350*.09**2)
  self.assertAlmostEqual(r['after']['area_high_mm2'],125*.22**2)
 def test_reviewer_critic_additive_and_persisted(self):
  import json,tempfile
  from pathlib import Path
  from unittest.mock import patch
  from mre_engineer.sam_comparison import run
  class Client:
   def __init__(self,root,record):self.calls=0
   def request(self,body):
    self.calls+=1
    v=dict(summary='Evidence-dependent test response',comments=[dict(finding='Projected change alone is not corrosion depth',basis='Computed silhouette and declared scale',next_check='Inspect calibrated same-view photos',evidence_refs=['image-comparison','input-record'])])
    return {'output':[{'type':'function_call','name':'submit_image_review','arguments':json.dumps(v)}]}
  r=dict(sha256='original',input={'wall_loss_um':20},sources=[],performance={},final_review={'original':'preserved'})
  image=dict(status='completed',component_id='wall',sha256='imagehash')
  mask=dict(area_px=400,area_one_pixel_low=350,area_one_pixel_high=450,max_width_px=20,median_row_width_px=20,touches_edge=False)
  with tempfile.TemporaryDirectory() as root,patch('mre_engineer.sam_comparison.assessment',return_value=r),patch('mre_engineer.sam_comparison.mask_metrics',return_value=(image,[mask])):
   result=run(root,'assessment',self.form(),True,client_factory=Client)
   saved=json.loads((Path(root)/'outputs/sam-comparisons'/result['comparison_id']/'report.json').read_text())
   self.assertEqual(result['api_attempts'],2)
   self.assertIsNotNone(saved['reviewer']);self.assertIsNotNone(saved['critic'])
   self.assertEqual(r['final_review'],{'original':'preserved'})
 def test_no_paid_work_without_consent(self):
  from mre_engineer.sam_comparison import run
  with self.assertRaises(EvidenceError):run('.', 'assessment',self.form(),False)
