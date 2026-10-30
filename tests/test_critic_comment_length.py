import unittest
from mre_engineer.experiment_agent import CRITIC_COMMENT
from mre_engineer.agent_contracts import validate
from mre_engineer.evidence import EvidenceError
class CriticCommentLengthTests(unittest.TestCase):
 def comment(self,text):
  return dict(dimension='cross_dimension',position='challenge',comment=text,basis='Publication comparisons are descriptive, not experimental equivalence.',metric_ids=[],input_fields=['configuration'],evidence_refs=['input-record'])
 def test_complete_comment_over_writing_target_is_not_truncated_or_rejected(self):
  text='Challenge wording that published configuration/methods are simply unmatched: revise to condition/context-matched but not experimental equivalence, and name actual remaining method/geometry differences rather than asserting unmatched configuration.'
  self.assertGreater(len(text),240);value=self.comment(text);validate(value,CRITIC_COMMENT);self.assertEqual(value['comment'],text)
 def test_hard_resource_bound_still_rejects_oversize(self):
  with self.assertRaises(EvidenceError):validate(self.comment('x'*1001),CRITIC_COMMENT)
 def test_citation_contract_is_not_removed(self):
  value=self.comment('Short comment');value['evidence_refs']=[]
  with self.assertRaises(EvidenceError):validate(value,CRITIC_COMMENT)
