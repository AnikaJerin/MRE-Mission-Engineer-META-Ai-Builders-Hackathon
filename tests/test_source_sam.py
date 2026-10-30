import base64,struct,unittest
from mre_engineer.sam_assets import validate_capture,read_events
from mre_engineer.evidence import EvidenceError
class SourceSamTests(unittest.TestCase):
 def packet(self):
  raw=b'\x89PNG\r\n\x1a\n'+b'\0\0\0\rIHDR'+struct.pack('>II',100,80)+b'\0'*12
  return dict(image_base64=base64.b64encode(raw).decode(),component_id='vessel',concept='ceramic tube',source_url='https://ntrs.nasa.gov/citations/20250004626',source_locator='Supplement Figure S1',rights_note='Owner reviewed source permission')
 def test_experimental_photo_allows_unknown_publication_metadata(self):
  d=self.packet()
  for k in ('source_url','source_locator','rights_note'):d[k]=''
  self.assertEqual(validate_capture(d)[1:],(100,80))
 def test_render_scene_not_required_or_accepted(self):
  d=self.packet();self.assertEqual(validate_capture(d)[1:],(100,80));d['scene_id']='fabricated'
  with self.assertRaises(EvidenceError):validate_capture(d)
 def test_no_local_path_or_unknown_part(self):
  d=self.packet();d['source_url']='file:///secret'
  with self.assertRaises(EvidenceError):validate_capture(d)
 def test_real_sse_events_preserved(self):
  events=list(read_events([b'data: {"type":"response.completed"}\n',b'\n']))
  self.assertEqual(events,[{'type':'response.completed'}])
if __name__=='__main__':unittest.main()
