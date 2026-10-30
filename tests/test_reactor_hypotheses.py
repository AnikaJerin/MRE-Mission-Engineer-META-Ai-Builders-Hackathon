"""Owner-run bounded checks. No live Meta request or GPU reconstruction."""
import copy
import json
import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch
from mre_engineer.reactor_hypotheses import verify, run, load, index
from mre_engineer.evidence import EvidenceError


def assessment():
    return {'id':'a'*32,'sha256':'assessment-hash','status':'completed',
      'input':{'experiment_name':'Synthetic test','wall_loss_um':40,'duration_s':3600},
      'performance':{'metrics':{'wall_loss':{'value':40,'unit':'um'}}},
      'final_review':{'summary':'Unconfirmed material concern'},'critique':{'weakness':'Check measurement basis'},
      'sources':[{'id':'paper','url':'https://ntrs.nasa.gov/citations/20250004626'}],
      'tools':[{'tool':'performance_assessment','evidence_id':'experiment-tool-test'}]}

def result():
    h={'explanation':'Unconfirmed wall recession interpretation','components':['wall'],
       'basis':'Reported wall loss requires measurement and exposure review.',
       'metric_ids':['wall_loss'],'input_fields':['wall_loss_um'],
       'evidence_refs':['input-record','experiment-tool-test'],'research_refs':['paper'],
       'applicability':'Configuration and methods require review.','test_to_distinguish':'Compare calibrated before/after wall measurements.'}
    return {'hypotheses':[h,{**copy.deepcopy(h),'explanation':'A measurement basis difference remains a rival','components':['records']}],
       'changes':[],'summary':'Two unconfirmed alternatives','scope':'unconfirmed_result_linked_hypotheses'}

class FakeClient:
    def __init__(self,root,record):self.calls=0
    def request(self,body):
        self.calls+=1
        return {'output':[{'type':'function_call','name':'submit_component_hypotheses','arguments':json.dumps(result())}]}

class HypothesisLayerTests(unittest.TestCase):
    def test_unknown_components_or_sources_fail(self):
        for key,value in [('components',['invented_part']),('research_refs',['invented_source']),('input_fields',['invented_input']),('metric_ids',['invented_metric'])]:
            v=result();v['hypotheses'][0][key]=value
            with self.assertRaises(EvidenceError):verify(v,assessment())
    def test_calculation_must_be_available_and_cite_executed_tool(self):
        r=assessment();r['performance']['metrics']['wall_loss']['value']=None
        with self.assertRaises(EvidenceError):verify(result(),r)
        v=result();v['hypotheses'][0]['evidence_refs']=['input-record']
        with self.assertRaises(EvidenceError):verify(v,assessment())
    def test_every_previous_hypothesis_is_reconsidered_once(self):
        prior={'result':result()};v=result()
        with self.assertRaises(EvidenceError):verify(v,assessment(),prior)
        v['changes']=[{'previous_number':i,'outcome':'retained','reason':'Current result does not distinguish it.','evidence_refs':['input-record']} for i in (1,2)]
        verify(v,assessment(),prior)
        v['changes'][1]['previous_number']=1
        with self.assertRaises(EvidenceError):verify(v,assessment(),prior)
    def test_generation_is_additive_and_refresh_is_read_only(self):
        r=assessment()
        with tempfile.TemporaryDirectory() as root:
            old=Path(root)/'old-review.txt';old.write_text('immutable review')
            with patch('mre_engineer.reactor_hypotheses.assessment',return_value=r),patch('mre_engineer.reactor_hypotheses.api_budget.snapshot',return_value={'blocking_unresolved_requests':[],'accounted_or_reserved_usd':0,'local_limit_usd':100}),patch('mre_engineer.reactor_hypotheses.api_budget.lock',return_value=nullcontext()):
                saved=run(root,r['id'],True,client_factory=FakeClient)
                self.assertEqual(saved['status'],'completed');self.assertEqual(saved['api_attempts'],1)
                self.assertEqual(load(root,saved['scene_id'])['assessment_sha256'],r['sha256'])
                self.assertEqual(index(root,r['id'])['latest']['id'],saved['scene_id'])
                self.assertEqual(old.read_text(),'immutable review')
                self.assertFalse((Path(root)/'outputs/assessments').exists())
    def test_no_paid_work_without_explicit_flag(self):
        with self.assertRaises(EvidenceError):run('.', 'a'*32)
