import tempfile,threading,unittest
from pathlib import Path
from mre_engineer.api_budget import lock
from mre_engineer.evidence import EvidenceError
class BillingLockContentionTests(unittest.TestCase):
 def test_short_dashboard_read_does_not_abort_billing_write(self):
  with tempfile.TemporaryDirectory() as root:
   ready=threading.Event();release=threading.Event();acquired=threading.Event();errors=[]
   def reader():
    with lock(root,'billing'):ready.set();release.wait(1)
   def writer():
    try:
     with lock(root,'billing'):acquired.set()
    except Exception as e:errors.append(e)
   a=threading.Thread(target=reader);a.start();self.assertTrue(ready.wait(1));b=threading.Thread(target=writer);b.start();release.set();a.join(2);b.join(3)
   self.assertFalse(a.is_alive());self.assertFalse(b.is_alive());self.assertEqual(errors,[]);self.assertTrue(acquired.is_set())
 def test_paid_investigations_are_still_exclusive(self):
  with tempfile.TemporaryDirectory() as root:
   with lock(root,'investigation'):
    with self.assertRaises(EvidenceError):
     with lock(root,'investigation'):pass
