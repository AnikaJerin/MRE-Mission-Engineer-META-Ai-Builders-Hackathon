"""Explicit local UI actions. One background job; never starts work on GET/refresh."""
import threading
import base64
import json
import traceback
from uuid import uuid4
from pathlib import Path
from .evidence import EvidenceError
from .evaluation import safe_name
from . import validation_suite as suite


class Actions:
    def __init__(self,root):
        self.root=Path(root);self.lock=threading.Lock();self.stop_event=threading.Event()
        self.job={'state':'idle'}

    def state(self):
        with self.lock:return dict(self.job)

    def start(self,data):
        if not isinstance(data,dict) or set(data)-{'action','run_name','freeze_name','split','case_id','consent','input','import_id','example_id','filename','file_base64','assessment_id','review_state','reviewer','comment','preview_sha256','previous_scene_id','capture','scene_id','assumptions','request_id','comparison','forecast_id'}:raise EvidenceError('Unknown action fields')
        action=data.get('action')
        if action not in ('check','freeze','run','export','stop','preview_assessment','assess','import_excel','review_assessment','reactor_hypotheses','sam_segment','sam_compare','hypothesis_tests','acknowledge_unknown_cost','explain_forecast'):raise EvidenceError('Unsupported UI action')
        if action=='stop':
            self.stop_event.set();return {'status':'stop-requested','note':'An in-flight request may finish; stop applies before the next request.'}
        for field in ('run_name','freeze_name'):
            if field in data:safe_name(data[field])
        if action=='run':
            if data.get('consent') is not True:raise EvidenceError('Explicit credit consent required')
            if data.get('split') not in ('development','evaluation'):raise EvidenceError('Choose a split')
            if not data.get('run_name') or not data.get('freeze_name'):raise EvidenceError('Run and freeze names required')
            if data.get('case_id') and data['case_id'] not in {c['id'] for c in suite.load_cases(self.root) if c['split']==data['split']}:raise EvidenceError('Case does not belong to split')
            suite.check_freeze(self.root,data['freeze_name'])
            if suite.directory(self.root,data['run_name']).exists():raise EvidenceError('Run name already exists; use a new name, never overwrite')
        if action=='assess':
            if data.get('consent') is not True:raise EvidenceError('Confirm Meta credit use before assessment')
            from .experiment_input import validate_input
            validated=validate_input(data.get('input'))
            if data.get('preview_sha256') is not None:
                from .experiment_agent import digest
                if data['preview_sha256']!=digest(validated):raise EvidenceError('Inputs changed after local preview. Preview the current values again before spending credits.')
        if action=='import_excel':
            if not isinstance(data.get('file_base64'),str) or len(data['file_base64'])>2_700_000:raise EvidenceError('Excel upload is too large')
        if action=='reactor_hypotheses':
            if data.get('consent') is not True:raise EvidenceError('Confirm Meta credit use for the hypothesis layer')
            from .reactor_hypotheses import assessment
            assessment(self.root,safe_name(data.get('assessment_id')))
            if data.get('previous_scene_id'):safe_name(data['previous_scene_id'])
        if action=='sam_compare':
            if data.get('consent') is not True:raise EvidenceError('Confirm image review credit use')
            from .sam_comparison import validate_input
            from .reactor_hypotheses import assessment
            validate_input(data.get('comparison'));assessment(self.root,safe_name(data.get('assessment_id')))
        if action=='sam_segment':
            if data.get('consent') is not True:raise EvidenceError('Confirm reference-image sharing with Meta SAM')
            from .sam_assets import validate_capture
            validate_capture(data.get('capture'))
        if action=='hypothesis_tests':
            if data.get('consent') is not True:raise EvidenceError('Confirm two-request hypothesis test credit use')
            from .hypothesis_tests import validate_assumptions
            from .reactor_hypotheses import load
            validate_assumptions(data.get('assumptions'))
            scene=load(self.root,safe_name(data.get('scene_id')))
            if scene['status']!='completed':raise EvidenceError('A completed hypothesis set is required')
        if action=='explain_forecast':
            if data.get('consent') is not True:raise EvidenceError('Confirm Meta credit use for the explanation')
            from .material_forecast_review import load_forecast
            load_forecast(self.root,safe_name(data.get('forecast_id')))
        if action=='acknowledge_unknown_cost':
            if data.get('consent') is not True:raise EvidenceError('Explicit acceptance of unknown cost is required')
            safe_name(data.get('request_id'))
        if action=='review_assessment':safe_name(data.get('assessment_id'))
        with self.lock:
            if self.job['state']=='running':raise EvidenceError('A workspace job is already running')
            self.stop_event.clear();self.job={'state':'running','action':action,'run_name':data.get('run_name'),'progress':{'kind':'queued'}}
        thread=threading.Thread(target=self._work,args=(dict(data),),daemon=False);thread.start()
        return {'status':'job-started','action':action}

    def _work(self,data):
        def progress(event):
            with self.lock:self.job['progress']=event
        try:
            action=data['action']
            if action=='preview_assessment':
                from .experiment_agent import preview
                result=preview(self.root,data['input'])
            elif action=='assess':
                from .experiment_agent import run
                result=run(self.root,data['input'],True,data.get('import_id'),data.get('example_id'),stop=self.stop_event.is_set,progress=progress)
            elif action=='reactor_hypotheses':
                from .reactor_hypotheses import run
                result=run(self.root,data['assessment_id'],True,data.get('previous_scene_id'),stop=self.stop_event.is_set,progress=progress)
            elif action=='explain_forecast':
                from .material_forecast_review import run
                result=run(self.root,data['forecast_id'],True,stop=self.stop_event.is_set,progress=progress)
            elif action=='hypothesis_tests':
                from .hypothesis_tests import run
                result=run(self.root,data['scene_id'],data['assumptions'],True,stop=self.stop_event.is_set,progress=progress)
            elif action=='acknowledge_unknown_cost':
                from .api_budget import acknowledge_unknown_cost
                row=acknowledge_unknown_cost(self.root,data['request_id'],True)
                result={'status':'unknown-cost-acknowledged-not-settled','request_id':row['id'],'api_calls':0}
            elif action=='sam_compare':
                from .sam_comparison import run
                result=run(self.root,data['assessment_id'],data['comparison'],True,stop=self.stop_event.is_set,progress=progress)
            elif action=='sam_segment':
                from .sam_assets import run
                result=run(self.root,data['capture'],True,stop=self.stop_event.is_set,progress=progress)
            elif action=='import_excel':
                from .experiment_excel import parse_xlsx,save_import
                try:raw=base64.b64decode(data['file_base64'],validate=True)
                except (ValueError,TypeError):raise EvidenceError('Invalid XLSX upload encoding') from None
                receipt=save_import(self.root,parse_xlsx(raw,data.get('filename','')))
                result={'status':'excel-imported','import_id':receipt['id'],'input':receipt['input'],'filename':receipt['filename'],'locations':receipt['locations'],'file_sha256':receipt['file_sha256']}
            elif action=='review_assessment':
                from .experiment_agent import save_review
                result=save_review(self.root,data['assessment_id'],data.get('review_state'),data.get('reviewer'),data.get('comment'))
            elif action=='check':
                cases=suite.load_cases(self.root);checks={c['id']:suite.numeric_check(c) for c in cases};suite.load_key(self.root)
                result={'status':'local-reference-checks-completed','checks':checks,'passed':all(c['passed'] for c in checks.values()),'api_calls':0}
            elif action=='freeze':result=suite.freeze(self.root,data.get('freeze_name','t12-v1'))
            elif action=='run':result=suite.run(self.root,data['run_name'],data['freeze_name'],data['split'],data.get('case_id') or None,True,stop=self.stop_event.is_set,progress=progress)
            else:
                from .dossier import export
                result=export(self.root,data.get('run_name','workspace-export'),source_run='v2',engineering_run='versioned-v3')
            with self.lock:self.job.update(state='completed',result=result)
        except Exception as exc:
            if isinstance(exc,(EvidenceError,FileExistsError)):
                reason=str(exc);diagnostic_id=None
            else:
                diagnostic_id=uuid4().hex
                # Keep only frame locations: never persist exception text, locals,
                # input values, source lines or credentials in a crash diagnostic.
                frames=[{'file':Path(f.filename).name,'line':f.lineno,'function':f.name}
                        for f in traceback.extract_tb(exc.__traceback__)]
                diagnostic={'id':diagnostic_id,'action':data.get('action'),
                            'exception_type':type(exc).__name__,'frames':frames,
                            'scope':'Internal failure locations only; billing state is not inferred.'}
                try:
                    target=self.root/'outputs/workspace-errors'/f'{diagnostic_id}.json'
                    target.parent.mkdir(parents=True,exist_ok=True)
                    with target.open('x') as f:json.dump(diagnostic,f,indent=2,allow_nan=False)
                    reason=f'Backend error ({type(exc).__name__}). Diagnostic: outputs/workspace-errors/{diagnostic_id}.json. No automatic retry.'
                except OSError:
                    reason=f'Backend error ({type(exc).__name__}); diagnostic could not be saved. No automatic retry.'
            with self.lock:self.job.update(state='failed',error=reason,diagnostic_id=diagnostic_id)
