"""Saved conditional material forecasts. No model/API call and no old review edits."""
import json,math
from pathlib import Path
from uuid import uuid4
from datetime import datetime,timezone
from .evidence import EvidenceError,read_json
from .investigation import digest
from .evaluation import safe_name
from .hypothesis_tests import recession

def validate(d):
 keys={'component','measured_loss_um','loss_bound_um','exposure_h','horizon_h','initial_thickness_um','source','comparable_conditions'}
 if not isinstance(d,dict) or set(d)!=keys:raise EvidenceError('Complete the material forecast fields')
 if d['component'] not in ('wall','anode','cathode') or d['comparable_conditions'] is not True:raise EvidenceError('Choose a component and explicitly assume comparable future conditions')
 if not isinstance(d['source'],str) or not d['source'].strip() or len(d['source'])>500:raise EvidenceError('Measurement/scenario source required')
 out=dict(d)
 for k,lo in [('measured_loss_um',0),('exposure_h',1e-6),('horizon_h',0),('initial_thickness_um',1e-6)]:
  v=d[k]
  if type(v) not in (int,float) or not math.isfinite(v) or not lo<=v<=1e6:raise EvidenceError('Invalid '+k)
 if d['measured_loss_um']>d['initial_thickness_um']:raise EvidenceError('Measured loss exceeds initial thickness')
 v=d['loss_bound_um']
 if v is not None and (type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=d['measured_loss_um']):raise EvidenceError('Invalid absolute loss bound')
 return out

def save(root,assessment_id,raw):
 from .reactor_hypotheses import assessment
 original=assessment(root,safe_name(assessment_id));d=validate(raw);result=recession(d);id=uuid4().hex
 value={'id':id,'assessment_id':assessment_id,'assessment_sha256':original['sha256'],'created_at':datetime.now(timezone.utc).isoformat(),'input':d,'prediction':result,'domain_exhausted':result['remaining_thickness_um']<=0,'api_calls':0,'scope':'Constant measured-rate extrapolation under unchanged conditions; no crack growth, corrosion kinetics, spatial damage map or validated lifetime prediction.'}
 value['sha256']=digest(value);folder=Path(root)/'outputs/material-forecasts'/id;folder.mkdir(parents=True,exist_ok=False);(folder/'report.json').write_text(json.dumps(value,indent=2,allow_nan=False));return value

def latest(root,assessment_id):
 safe_name(assessment_id);rows=[]
 for p in (Path(root)/'outputs/material-forecasts').glob('*/report.json'):
  d=read_json(p)
  if d.get('assessment_id')==assessment_id:
   if d.get('sha256')!=digest({k:v for k,v in d.items() if k!='sha256'}):raise EvidenceError('Material forecast changed')
   rows.append(d)
 rows.sort(key=lambda d:d['created_at'],reverse=True);return {'latest':rows[0] if rows else None,'api_calls':0}
