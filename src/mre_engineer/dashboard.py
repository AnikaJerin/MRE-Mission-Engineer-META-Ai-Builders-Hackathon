"""Loopback evidence workspace; GET is read-only, explicit protected POST starts work."""

import json
import os
import secrets
import hmac
import mimetypes
import re
import hashlib
import base64
import traceback
from urllib.parse import urlparse,parse_qs
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path

from .acquisition import acquisition_status
from .evidence import EvidenceError, read_json, sha256, validate_case, validate_manifest
from .day2 import load_saved_report, run_directory
from .investigation import load_investigation, folder as investigation_folder
from .dossier import bundle
from .agent_contracts import strict_json
from .evaluation import safe_name
from .workspace_actions import Actions
from . import api_budget
from .validation_suite import overview
from .experiment_agent import list_reports,load as load_assessment,example as experiment_example
from .experiment_report import export_data,to_html as assessment_html
from .performance_contract import contract as performance_contract
from . import workspace_store
from uuid import uuid4
from datetime import datetime,timezone


def read_action_body(raw):
    # XLSX uses bounded base64 JSON, so the model-output 24 KB parser is not appropriate.
    def unique_pairs(items):
        value={}
        for k,v in items:
            if k in value:raise EvidenceError('Duplicate action field')
            value[k]=v
        return value
    def invalid(_):raise EvidenceError('Nonfinite action number')
    def finite(text):
        import math
        value=float(text)
        if not math.isfinite(value):raise EvidenceError('Action number exceeds finite range')
        return value
    return json.loads(raw.decode('utf-8'),object_pairs_hook=unique_pairs,parse_constant=invalid,parse_float=finite)


def snapshot(root, accounting_run="v1", investigation_run="v1",pilot_run="full-pilot-v4",source_run="v1",release_run="v1",engineering_run="v1"):
    root = Path(root)
    manifest_path = root / "sources/manifest.json"
    case_path = root / "cases/yu2025-1h.json"
    manifest = read_json(manifest_path)
    sources = validate_manifest(manifest)
    case = validate_case(read_json(case_path), manifest)
    return {
        "status": "local-evidence-only", "case": case,
        "sources": [{**s, "local_acquisition": acquisition_status(root, id)}
                    for id, s in sources.items()],
        "manifest_sha256": sha256(manifest_path), "case_sha256": sha256(case_path),
        "api_calls": 0, "external_network_calls": 0, "agent_run_ready": False,
        "scope": "Historical development case; displays saved accounting when available. No calculations or Meta calls on refresh.",
        "day2": load_saved_report(root, accounting_run),
        "investigation": load_investigation(root, investigation_run),
        "validation":bundle(root,pilot_run,source_run,release_run,engineering_run),
    }


def researcher_workspace(root,server):
    warnings=[]
    try:budget=api_budget.snapshot(root)
    except EvidenceError:
        budget={'accounted_or_reserved_usd':None,'local_limit_usd':None,'blocking_unresolved_requests':['ledger-unreadable'],'scope':'Billing ledger needs review; paid work remains blocked.'}
        warnings.append('The billing ledger cannot be read. Saved evidence is still available; new paid work is blocked.')
    try:draft=workspace_store.load_draft(root);persistence_error=False
    except EvidenceError as exc:
        draft={'revision':0,'draft':None};persistence_error=True;warnings.append(str(exc))
    return {'job':server.actions.state(),'csrf':server.csrf,'api_key_present':bool(os.environ.get('MODEL_API_KEY','').strip()),'budget':budget,'assessments':list_reports(root),
            'workspace_id':workspace_store.workspace_id(root),'persistence':server.persistence,'draft':draft,'persistence_error':persistence_error,'warnings':warnings}


def allowed_request(host, origin=None):
    public = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '').strip().lower()
    if public:
        return host == public and (origin is None or origin == 'https://' + public)
    port = os.environ.get('MRE_LISTEN_PORT')
    hosts = {f'127.0.0.1:{port}', f'localhost:{port}'}
    return host in hosts and (origin is None or origin == 'http://' + host)


class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, root, accounting_run="v1", investigation_run="v1",pilot_run="full-pilot-v4",source_run="v1",release_run="v1",engineering_run="v1", **kwargs):
        self.root = root
        self.accounting_run = accounting_run
        self.investigation_run = investigation_run
        self.pilot_run,self.source_run,self.release_run=pilot_run,source_run,release_run
        self.engineering_run=engineering_run
        super().__init__(*args, **kwargs)

    def _respond(self, status, body, content_type, exported_style=False):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        style_hashes=''.join(" 'sha256-"+base64.b64encode(hashlib.sha256(style).digest()).decode()+"'" for style in re.findall(b'<style>(.*?)</style>',body,flags=re.S)) if exported_style else ''
        script_hashes=''.join(" 'sha256-"+base64.b64encode(hashlib.sha256(script).digest()).decode()+"'" for script in re.findall(b'<script>(.*?)</script>',body,flags=re.S)) if exported_style else ''
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'"+script_hashes+"; style-src 'self'"+style_hashes+"; img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        port = self.server.server_port
        if not allowed_request(self.headers.get("Host", "")):
            self._respond(403, b"Local host required", "text/plain")
            return
        routes = {"/": ("react-start.html", "text/html; charset=utf-8"),
                  "/validation": ("index.html", "text/html; charset=utf-8"),
                  "/validation/app.js": ("app.js", "text/javascript; charset=utf-8"),
                  "/validation/style.css": ("style.css", "text/css; charset=utf-8"),
                  "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                  "/style.css": ("style.css", "text/css; charset=utf-8")}
        try:
            dist=Path(self.root)/'frontend/dist'
            if self.path=='/' and (dist/'index.html').is_file():
                self._respond(200,(dist/'index.html').read_bytes(),'text/html; charset=utf-8')
            elif self.path in ('/demo/before-plate-cropped-synthetic.png', '/demo/after-plate-cropped-synthetic.png'):
                self._respond(200,(dist/self.path.lstrip('/')).read_bytes(),'image/png')
            elif self.path.startswith('/assets/'):
                name=self.path[len('/assets/'):]
                if not re.fullmatch(r'[A-Za-z0-9_.-]+\.(js|css|svg|png|woff2)',name):raise EvidenceError('Unknown asset')
                self._respond(200,(dist/'assets'/name).read_bytes(),mimetypes.guess_type(name)[0] or 'application/octet-stream')
            elif self.path == '/api/performance-contract':
                self._respond(200,json.dumps(performance_contract(),allow_nan=False).encode(),'application/json')
            elif self.path == '/api/experiment-workspace':
                value=researcher_workspace(self.root,self.server)
                self._respond(200,json.dumps(value,allow_nan=False).encode(),'application/json')
            elif self.path == '/api/evidence-library':
                self._respond(200,json.dumps(workspace_store.registry(self.root),allow_nan=False).encode(),'application/json')
            elif self.path == '/api/experiment-example':
                self._respond(200,json.dumps({'input':experiment_example(),'example_id':'yu2025-one-hour'},allow_nan=False).encode(),'application/json')
            elif self.path.startswith('/api/material-forecast-review?'):
                from .material_forecast_review import latest
                query=parse_qs(urlparse(self.path).query)
                self._respond(200,json.dumps(latest(self.root,query.get('forecast_id',[''])[0]),allow_nan=False).encode(),'application/json')
            elif self.path.startswith('/api/material-forecast?'):
                from .material_forecast import latest
                query=parse_qs(urlparse(self.path).query)
                self._respond(200,json.dumps(latest(self.root,query.get('assessment_id',[''])[0]),allow_nan=False).encode(),'application/json')
            elif self.path.startswith('/api/hypothesis-tests?'):
                from .hypothesis_tests import latest
                query=parse_qs(urlparse(self.path).query)
                self._respond(200,json.dumps(latest(self.root,query.get('scene_id',[''])[0]),allow_nan=False).encode(),'application/json')
            elif self.path == '/api/reactor-diagnostics':
                from .reactor_diagnostics import latest
                self._respond(200,json.dumps(latest(self.root),allow_nan=False).encode(),'application/json')
            elif self.path == '/api/sam-library':
                from . import sam_assets
                items=[]
                for p in (Path(self.root)/'outputs/sam-segmentations').glob('*/report.json'):
                    d=read_json(p)
                    if d.get('status')=='completed':items.append({k:d[k] for k in ('id','created_at','component_id','concept')})
                items.sort(key=lambda d:d['created_at'],reverse=True)
                self._respond(200,json.dumps({'items':items}).encode(),'application/json')
            elif self.path.startswith('/api/sam-capture?'):
                from .sam_comparison import mask_metrics
                query=parse_qs(urlparse(self.path).query)
                image,masks=mask_metrics(self.root,safe_name(query.get('id',[''])[0]))
                self._respond(200,json.dumps({**image,'masks':masks},allow_nan=False).encode(),'application/json')
            elif self.path.startswith('/api/sam-comparison?'):
                from .sam_comparison import latest
                query=parse_qs(urlparse(self.path).query)
                self._respond(200,json.dumps(latest(self.root,query.get('assessment_id',[''])[0]),allow_nan=False).encode(),'application/json')
            elif self.path.startswith('/api/sam-comparison-record?'):
                from .sam_comparison import load
                query=parse_qs(urlparse(self.path).query)
                self._respond(200,json.dumps(load(self.root,safe_name(query.get('id',[''])[0])),allow_nan=False).encode(),'application/json')
            elif self.path == '/api/sam-segmentation':
                from .sam_assets import latest
                self._respond(200,json.dumps(latest(self.root),allow_nan=False).encode(),'application/json')
            elif self.path.startswith('/api/reactor-hypotheses?'):
                from .reactor_hypotheses import index
                query=parse_qs(urlparse(self.path).query)
                value=index(self.root,safe_name(query.get('assessment_id',[''])[0]))
                self._respond(200,json.dumps(value,allow_nan=False).encode(),'application/json')
            elif self.path.startswith('/api/reactor-hypothesis?'):
                from .reactor_hypotheses import load
                query=parse_qs(urlparse(self.path).query)
                value=load(self.root,safe_name(query.get('id',[''])[0]))
                self._respond(200,json.dumps(value,allow_nan=False).encode(),'application/json')
            elif self.path.startswith('/api/assessment?'):
                query=parse_qs(urlparse(self.path).query);id=safe_name(query.get('id',[''])[0]);value=load_assessment(self.root,id)
                self._respond(200,json.dumps(value,allow_nan=False).encode(),'application/json')
            elif self.path.startswith('/api/assessment-export?'):
                query=parse_qs(urlparse(self.path).query);id=safe_name(query.get('id',[''])[0]);fmt=query.get('format',[''])[0]
                if fmt not in ('json','html'):raise EvidenceError('Unknown assessment export format')
                value=export_data(self.root,id);body=assessment_html(value) if fmt=='html' else json.dumps(value,indent=2,allow_nan=False)
                self._respond(200,body.encode(),'text/html; charset=utf-8' if fmt=='html' else 'application/json',exported_style=fmt=='html')
            elif self.path == '/api/experiment-template':
                self._respond(200,files('mre_engineer').joinpath('web','experiment-template.xlsx').read_bytes(),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            elif self.path == "/api/workspace":
                value=snapshot(self.root, self.accounting_run, self.investigation_run,self.pilot_run,self.source_run,self.release_run,self.engineering_run)
                value['workbench']={'suite':overview(self.root),'job':self.server.actions.state(),'csrf':self.server.csrf,'api_key_present':bool(os.environ.get('MODEL_API_KEY','').strip()),'budget':api_budget.snapshot(self.root)}
                body = json.dumps(value, allow_nan=False).encode()
                self._respond(200, body, "application/json; charset=utf-8")
            elif self.path.startswith('/api/export?'):
                query=parse_qs(urlparse(self.path).query)
                name=safe_name(query.get('name',[''])[0]);fmt=query.get('format',[''])[0]
                if fmt not in ('html','json'):raise EvidenceError('Unknown export format')
                export_path=Path(self.root)/'outputs/dossiers'/name/('evidence.'+fmt)
                if export_path.stat().st_size>10_000_000:raise EvidenceError('Export too large')
                self._respond(200,export_path.read_bytes(),'text/html; charset=utf-8' if fmt=='html' else 'application/json')
            elif self.path in routes:
                name, mime = routes[self.path]
                asset=files("mre_engineer").joinpath("web", name).read_bytes()
                if self.path=='/validation':asset=asset.replace(b'href="/style.css"',b'href="/validation/style.css"').replace(b'src="/app.js"',b'src="/validation/app.js"')
                self._respond(200,asset,mime)
            elif self.path.startswith('/api/material-model?'):
                from .material_models import latest
                query=parse_qs(urlparse(self.path).query)
                self._respond(200,json.dumps(latest(self.root,query.get('assessment_id',[''])[0]),allow_nan=False).encode(),'application/json')
            elif self.path == '/api/reactor-geometry':
                from importlib.resources import files as _resfiles
                import json as _json2
                _gdata = _json2.loads(_resfiles('mre_engineer').joinpath('resources', 'reactor_geometry.json').read_text(encoding='utf-8'))
                self._respond(200, _json2.dumps(_gdata, allow_nan=False).encode(), 'application/json')
            elif self.path == '/api/reactor-calibration-profile':
                from .reactor_calibration import calibration_profile as _cal_profile
                import json as _json3
                self._respond(200, _json3.dumps(_cal_profile(), allow_nan=False).encode(), 'application/json')
            elif self.path == '/api/reactor-degradation-models':
                from .reactor_degradation import model_catalog as _deg_catalog
                import json as _json4
                self._respond(200, _json4.dumps(_deg_catalog(), allow_nan=False).encode(), 'application/json')
            else:
                self._respond(404, b"Not found", "text/plain")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            incident=uuid4().hex[:12]
            # Do not log input, credentials, file contents, or exception arguments.
            record={'incident':incident,'route':urlparse(self.path).path,'exception_type':type(exc).__name__,'created_at':datetime.now(timezone.utc).isoformat(),'errno':getattr(exc,'errno',None),'frames':[{'file':Path(f.filename).name,'line':f.lineno,'function':f.name} for f in traceback.extract_tb(exc.__traceback__)[-6:]]}
            try:
                directory=Path(self.root)/'outputs/diagnostics';directory.mkdir(parents=True,exist_ok=True)
                (directory/(incident+'.json')).write_text(json.dumps(record,indent=2))
            except OSError:pass
            specific=str(exc) if isinstance(exc,EvidenceError) else 'This saved workspace resource could not be read. Your existing assessments have not been deleted. Use Saved reviews or reload the workspace; do not repeat a paid assessment.'
            self._respond(422,json.dumps({'error':specific,'incident_id':incident,'route':record['route'],'api_calls':0}).encode(),'application/json')

    def do_POST(self):
        port=self.server.server_port
        allowed={f'127.0.0.1:{port}',f'localhost:{port}'}
        host=self.headers.get('Host','')
        origin=self.headers.get('Origin','')
        if not allowed_request(host, origin) or not hmac.compare_digest(self.headers.get('X-MRE-Token','').encode('utf-8'),self.server.csrf.encode('utf-8')):
            self._respond(403,b'{"error":"Local same-origin token required"}','application/json');return
        if self.path not in ('/api/actions','/api/workspace-draft','/api/reactor-scenario','/api/material-forecast','/api/material-model','/api/material-properties') or self.headers.get('Content-Type','').split(';')[0]!='application/json':
            self._respond(400,b'{"error":"Unsupported local action route or content type"}','application/json');return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=3_000_000:raise ValueError('Invalid action length')
            raw=self.rfile.read(size)
            if len(raw)!=size:raise EvidenceError('Incomplete action body')
            data=read_action_body(raw)
            if self.path in ('/api/material-model','/api/material-properties'):
                from .material_models import save, properties
                if size>4000:raise EvidenceError('Material model input is too large')
                result=save(self.root,data) if self.path=='/api/material-model' else properties(data)
                self._respond(200,json.dumps(result,allow_nan=False).encode(),'application/json');return
            if self.path=='/api/material-forecast':
                from .material_forecast import save
                if size>4000 or not isinstance(data,dict) or set(data)!={'assessment_id','forecast'}:raise EvidenceError('Invalid material forecast request')
                self._respond(200,json.dumps(save(self.root,data['assessment_id'],data['forecast']),allow_nan=False).encode(),'application/json');return
            if self.path=='/api/reactor-scenario':
                from .reactor_field import simulate
                if size>4000:raise EvidenceError('Scenario input is too large')
                self._respond(200,json.dumps(simulate(data),allow_nan=False).encode(),'application/json');return
            if self.path=='/api/workspace-draft':
                if not isinstance(data,dict) or set(data)!={'draft','revision'}:raise EvidenceError('Draft and revision are required')
                result=workspace_store.save_draft(self.root,data['draft'],data['revision'])
                self._respond(200,json.dumps(result,allow_nan=False).encode(),'application/json');return
            limit=3_000_000 if isinstance(data,dict) and data.get('action')=='import_excel' else 1_000_000 if isinstance(data,dict) and data.get('action') in ('assess','preview_assessment','sam_segment') else 16000
            if size>limit:raise EvidenceError('Action body exceeds allowed size')
            result=self.server.actions.start(data)
            self._respond(202,json.dumps(result,allow_nan=False).encode(),'application/json')
        except (OSError,ValueError,TypeError,KeyError) as exc:
            message=str(exc) if isinstance(exc,(EvidenceError,FileExistsError)) else 'Invalid local action'
            self._respond(400,json.dumps({'error':message}).encode(),'application/json')

    def log_message(self, fmt, *args):
        # Keep terminal output concise; never print file contents or keys.
        pass


def serve(root, port=8766, accounting_run="v1", investigation_run="v1",pilot_run="full-pilot-v4",source_run="v1",release_run="v1",engineering_run="v1"):
    run_directory(root, accounting_run)  # validate name before binding any socket
    investigation_folder(root, investigation_run)
    for name in (pilot_run,source_run,release_run,engineering_run):safe_name(name)
    public = bool(os.environ.get('RENDER_EXTERNAL_HOSTNAME', '').strip())
    if public:
        port = int(os.environ.get('PORT', port))
    os.environ['MRE_LISTEN_PORT'] = str(port)
    server = ThreadingHTTPServer(("0.0.0.0" if public else "127.0.0.1", port), partial(Handler, root=Path(root), accounting_run=accounting_run, investigation_run=investigation_run,pilot_run=pilot_run,source_run=source_run,release_run=release_run,engineering_run=engineering_run))
    os.environ['MRE_LISTEN_PORT'] = str(server.server_port)
    try:server.persistence=workspace_store.initialize(root)
    except Exception:
        server.server_close();raise
    server.actions=Actions(root)
    server.csrf=secrets.token_urlsafe(32)
    print(f"MRE lunar workspace: http://127.0.0.1:{server.server_port}")
    print("Local workspace. Refresh uses no Meta credits; paid work needs an explicit Run and credit consent. Ctrl+C stops.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.actions.stop_event.set()
        server.server_close()
