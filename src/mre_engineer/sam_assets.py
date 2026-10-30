"""Explicit SAM 3.1 cloud segmentation of a source reference image.

No CUDA dependency, no SAM-3D claim, no execution on import or GET.
The generated visual image is not reactor telemetry or validated geometry.
"""
import base64
import json
import os
import struct
import urllib.request
import urllib.error
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone
from .evidence import EvidenceError, read_json
from .evaluation import safe_name, scrub
from .investigation import digest
from .meta_client import NoRedirect, http_diagnostic
from . import api_budget

MODEL='sam-3.1'
ENDPOINT='https://api.meta.ai/v1/responses'
MAX_IMAGE_BYTES=750_000
MAX_STREAM_BYTES=8_000_000

def folder(root,id):return Path(root)/'outputs/sam-segmentations'/safe_name(id)

COMPONENTS=('vessel','wall','anode','cathode','melt','gas')
def validate_capture(data):
    required={'image_base64','component_id','concept','source_url','source_locator','rights_note'}
    if not isinstance(data,dict) or set(data)!=required:raise EvidenceError('Reference image, component, concept, source URL, locator and rights note required')
    if data['component_id'] not in COMPONENTS:raise EvidenceError('Unknown reactor component')
    for k,limit in [('concept',100),('source_url',1000),('source_locator',300),('rights_note',500)]:
        if not isinstance(data[k],str) or len(data[k])>limit:raise EvidenceError('Invalid or oversized '+k)
    if not data['concept'].strip():raise EvidenceError('Visible object is required')
    from urllib.parse import urlparse
    if data['source_url'].strip():
        url=urlparse(data['source_url'])
        if url.scheme!='https' or not url.netloc or url.username or url.password:raise EvidenceError('Use an HTTPS publication URL when supplied')
    text=data['image_base64']
    if not isinstance(text,str) or len(text)>1_000_000:raise EvidenceError('Reference image is too large')
    try:raw=base64.b64decode(text,validate=True)
    except (ValueError,TypeError):raise EvidenceError('Invalid image encoding') from None
    if len(raw)<33 or len(raw)>MAX_IMAGE_BYTES or raw[:8]!=b'\x89PNG\r\n\x1a\n' or raw[12:16]!=b'IHDR':raise EvidenceError('Use a PNG up to 750 KB')
    w,h=struct.unpack('>II',raw[16:24])
    if not 16<=w<=1200 or not 16<=h<=1200:raise EvidenceError('Reference dimensions must be 16–1200 pixels')
    return raw,w,h

def read_events(stream):
    """Retain the provider's actual SSE events, not manufactured parser events."""
    total=0;parts=[]
    for line in stream:
        total+=len(line)
        if total>MAX_STREAM_BYTES:raise EvidenceError('SAM response exceeded the local bound; no automatic retry')
        line=line.decode('utf-8').rstrip('\r\n')
        if not line:
            if parts:
                value='\n'.join(parts);parts=[]
                if value=='[DONE]':return
                event=json.loads(value)
                if not isinstance(event,dict):raise EvidenceError('Unexpected SAM event')
                yield event
        elif line.startswith('data:'):parts.append(line[5:].lstrip())
    if parts:
        event=json.loads('\n'.join(parts))
        if not isinstance(event,dict):raise EvidenceError('Unexpected SAM event')
        yield event

def run(root,capture,allow_api_call=False,stop=None,progress=None,opener_factory=None):
    if not allow_api_call:raise EvidenceError('Explicit consent required to send this reference image to Meta SAM')
    raw,w,h=validate_capture(capture)
    key=os.environ.get('MODEL_API_KEY','').strip()
    if not key:raise EvidenceError('Set MODEL_API_KEY in the backend terminal')
    id=uuid4().hex;dest=folder(root,id);events=[];error=None;billing=None;reservation=None
    prompt=capture['concept'].strip()
    body={'model':MODEL,'input':[{'type':'message','role':'user','content':[
      {'type':'input_text','text':prompt},{'type':'input_image','image_url':'data:image/png;base64,'+capture['image_base64']}]}],
      'stream':True,'metadata':{'mask_encoding':'one_bit'}}
    with api_budget.lock(root,'investigation'):
        if stop and stop():raise EvidenceError('Owner requested stop before the SAM request')
        dest.mkdir(parents=True,exist_ok=False);(dest/'input.png').write_bytes(raw)
        try:
            reservation=api_budget.reserve(root)
            if progress:progress({'kind':'sam_request_sent','api_attempts':1})
            request=urllib.request.Request(ENDPOINT,data=json.dumps(body,separators=(',',':')).encode(),method='POST',
              headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','Accept':'text/event-stream'})
            opener=opener_factory() if opener_factory else urllib.request.build_opener(NoRedirect())
            with opener.open(request,timeout=120) as response:
                for event in read_events(response):
                    clean=scrub(event)
                    if clean!=event:raise EvidenceError('Credential reflection rejected')
                    events.append(clean)
                    if event.get('type') in ('response.failed','response.incomplete','error'):raise EvidenceError('SAM response did not complete; no automatic retry')
                    if event.get('type')=='response.completed':break
            if not any(e.get('type')=='response.completed' for e in events):raise EvidenceError('SAM stream ended before completion')
            billing=api_budget.settle_sam_image(root,reservation)
        except urllib.error.HTTPError as exc:
            details=http_diagnostic(exc,key);error=f"SAM HTTP {exc.code}: {details.get('message','Provider error')}. No automatic retry."
        except Exception as exc:
            error=str(exc) if isinstance(exc,EvidenceError) else 'SAM transport or response failed. No automatic retry; inspect billing.'
        if error and reservation:billing=api_budget.settle(root,reservation,None)
        value={'id':id,'asset_key':'yu2025-reference-v1', 'source':{k:capture[k] for k in ('source_url','source_locator','rights_note','concept')},
          'created_at':datetime.now(timezone.utc).isoformat(),'status':'completed' if error is None else 'failed','error':error,
          'model':MODEL,'component_id':capture['component_id'],'image_sha256':digest(capture['image_base64']),
          'concept':prompt,'width':w,'height':h,'events':events,'billing':billing,'api_attempts':1 if reservation else 0,
          'scope':'Actual SAM segmentation of an owner-supplied source reference image. Provenance is owner-declared; no automatic source authentication. Not physical diagnosis, SAM 3D reconstruction or validation of reactor geometry.'}
        value['sha256']=digest(value)
        with (dest/'report.json').open('x') as f:json.dump(value,f,indent=2,allow_nan=False)
    return {'status':value['status'],'sam_id':id,'error':error,'api_attempts':value['api_attempts']}

def load(root,id):
    r=read_json(folder(root,id)/'report.json')
    if r.get('sha256')!=digest({k:v for k,v in r.items() if k!='sha256'}):raise EvidenceError('SAM result changed')
    image=base64.b64encode((folder(root,id)/'input.png').read_bytes()).decode()
    if digest(image)!=r['image_sha256']:raise EvidenceError('SAM capture changed')
    return {**r,'image_data_url':'data:image/png;base64,'+image}

def latest(root):
    rows=[]
    for p in (Path(root)/'outputs/sam-segmentations').glob('*/report.json'):
        try:
            r=read_json(p)
            if r.get('asset_key')=='yu2025-reference-v1':rows.append(r)
        except (OSError,ValueError,KeyError,TypeError):continue
    rows.sort(key=lambda r:r['created_at'],reverse=True)
    return {'latest':load(root,rows[0]['id']) if rows else None,'api_calls':0}
