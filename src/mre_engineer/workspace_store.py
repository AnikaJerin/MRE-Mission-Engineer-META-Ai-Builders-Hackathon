"""Local SQLite persistence. Reviewed references are versioned; no model answers/keys.
Immutable assessment JSON/events remain the canonical evidence, not this UI store.
GET readers use a read-only connection and never initialize or refresh the database.
"""
import hashlib
import json
import sqlite3
from contextlib import contextmanager,closing
from datetime import datetime,timezone
from importlib.resources import files
from pathlib import Path
from .evidence import EvidenceError
from .performance_contract import SOURCES,load_profile

SCHEMA_VERSION=1
MAX_DRAFT_BYTES=1_000_000

def now():return datetime.now(timezone.utc).isoformat()
def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def checksum(value):return hashlib.sha256(encoded(value).encode()).hexdigest()
def database_path(root):return Path(root)/'data/workspace/mre.sqlite3'
def workspace_id(root):return hashlib.sha256(str(Path(root).resolve()).encode()).hexdigest()[:20]

def packaged_registry():
    observations=json.loads(files('mre_engineer').joinpath('resources','published_mre_cases.json').read_text())
    return {'sources':SOURCES,'official_profile':load_profile(),'published_observations':observations,
            'scope':'Reviewed published references and selected requirements; not true outcomes for unseen reactor hardware.'}

@contextmanager
def writer(root):
    with closing(sqlite3.connect(database_path(root),timeout=10)) as conn:
        with conn:yield conn

def initialize(root):
    path=database_path(root);path.parent.mkdir(parents=True,exist_ok=True)
    registry=packaged_registry();stamp=checksum(registry)
    with writer(root) as conn:
        version=conn.execute('PRAGMA user_version').fetchone()[0]
        if version not in (0,SCHEMA_VERSION):raise EvidenceError('Workspace database schema is newer than this application; keep the database and use the matching application version')
        conn.execute('CREATE TABLE IF NOT EXISTS drafts (id INTEGER PRIMARY KEY CHECK(id=1), revision INTEGER NOT NULL, payload TEXT NOT NULL, sha256 TEXT NOT NULL, updated_at TEXT NOT NULL)')
        conn.execute('CREATE TABLE IF NOT EXISTS evidence_versions (sha256 TEXT PRIMARY KEY, payload TEXT NOT NULL, installed_at TEXT NOT NULL)')
        conn.execute('CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
        conn.execute('INSERT OR IGNORE INTO evidence_versions VALUES (?,?,?)',(stamp,encoded(registry),now()))
        conn.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)',('active_evidence_version',stamp))
        conn.execute('PRAGMA user_version=1')
    return {'database':'data/workspace/mre.sqlite3','schema_version':SCHEMA_VERSION,'evidence_version':stamp,'workspace_id':workspace_id(root)}

@contextmanager
def reader(root):
    path=database_path(root)
    if not path.is_file():raise EvidenceError('Persistent workspace is not initialized. Restart the updated backend once; existing reports are retained')
    with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=10)) as conn:yield conn

def registry(root):
    # CLI/offline tests may have no server-owned database yet. The same packaged
    # reviewed references are used; no request is made and no DB is created.
    if not database_path(root).exists():return {**packaged_registry(),'storage':'packaged-reviewed-reference','version':checksum(packaged_registry())}
    try:
        with reader(root) as conn:
            row=conn.execute("SELECT value FROM metadata WHERE key='active_evidence_version'").fetchone()
            record=conn.execute('SELECT payload FROM evidence_versions WHERE sha256=?',(row[0],)).fetchone() if row else None
        if record is None:raise EvidenceError('Reviewed evidence registry is missing')
        value=json.loads(record[0])
        if checksum(value)!=row[0]:raise EvidenceError('Reviewed evidence registry integrity check failed; no new assessment started')
        return {**value,'storage':'local-sqlite','version':row[0]}
    except (sqlite3.Error,ValueError,TypeError,IndexError) as exc:
        if isinstance(exc,EvidenceError):raise
        raise EvidenceError('Persistent evidence registry could not be read; retain the database and inspect workspace diagnostics') from None

def load_draft(root):
    try:
        with reader(root) as conn:row=conn.execute('SELECT revision,payload,sha256,updated_at FROM drafts WHERE id=1').fetchone()
        if row is None:return {'revision':0,'draft':None,'updated_at':None}
        value=json.loads(row[1]);validate_draft(value)
        if checksum(value)!=row[2]:raise EvidenceError('Saved draft integrity check failed; saved assessments remain separate')
        return {'revision':row[0],'draft':value,'updated_at':row[3]}
    except sqlite3.Error:raise EvidenceError('Saved draft database could not be read; do not delete existing evidence') from None

def validate_draft(value):
    if not isinstance(value,dict) or set(value)-{'form','origin','tab','view','selected_assessment_id'}:raise EvidenceError('Unsupported draft fields')
    if not isinstance(value.get('form'),dict):raise EvidenceError('Draft form must be an object')
    if value.get('tab') not in ('manual','excel','connect') or value.get('view') not in ('input','history','references'):raise EvidenceError('Unsupported draft view')
    selected=value.get('selected_assessment_id')
    if selected is not None and (not isinstance(selected,str) or len(selected)!=32 or any(c not in '0123456789abcdef' for c in selected)):raise EvidenceError('Invalid saved assessment selection')
    from .experiment_input import ALLOWED
    permitted=ALLOWED|{'duration_h','current_trace_text','resistance_text','analysis_id','composition_source','composition_text'}
    if set(value['form'])-permitted:raise EvidenceError('Unsupported form draft fields')
    for key,entry in value['form'].items():
        if key in ('trace','resistance_trace') and (not isinstance(entry,list) or len(entry)>1000):raise EvidenceError('Draft trace must contain at most 1000 rows')
        if key=='test_estimates' and not isinstance(entry,dict):raise EvidenceError('Draft estimates must be an object')
        if key=='reactor_scenario' and entry is not None:
            from .reactor_field import validate_scenario
            validate_scenario(entry)
        if key=='composition' and entry is not None and not isinstance(entry,dict):raise EvidenceError('Draft composition must be an object')
        if key not in ('trace','resistance_trace','test_estimates','composition','reactor_scenario') and entry is not None and type(entry) not in (str,int,float):raise EvidenceError('Draft scalar fields must contain text or numbers')
    origin=value.get('origin')
    if origin is not None and (not isinstance(origin,dict) or set(origin)-{'import_id','example_id','label'}):raise EvidenceError('Unsupported draft provenance')
    try:
        payload=encoded(value)
        if len(payload.encode())>MAX_DRAFT_BYTES:raise EvidenceError('Draft is too large; original imported workbook and assessment files remain separate')
    except (TypeError,ValueError):raise EvidenceError('Draft must contain finite JSON values') from None
    return payload

def save_draft(root,value,revision):
    if type(revision) is not int or revision<0:raise EvidenceError('Draft revision must be a nonnegative integer')
    payload=validate_draft(value);stamp=now()
    if not database_path(root).is_file():raise EvidenceError('Restart the updated backend once to initialize persistence; saved assessments are retained')
    try:
        with writer(root) as conn:
            conn.execute('BEGIN IMMEDIATE')
            row=conn.execute('SELECT revision FROM drafts WHERE id=1').fetchone();actual=row[0] if row else 0
            if actual!=revision:raise EvidenceError('Draft changed in another tab. Your browser backup is retained; reload the saved draft before overwriting it')
            conn.execute('CREATE TABLE IF NOT EXISTS draft_history (revision INTEGER PRIMARY KEY, payload TEXT NOT NULL, sha256 TEXT NOT NULL, updated_at TEXT NOT NULL)')
            conn.execute('INSERT OR IGNORE INTO draft_history SELECT revision,payload,sha256,updated_at FROM drafts WHERE id=1')
            conn.execute('INSERT OR REPLACE INTO drafts VALUES (1,?,?,?,?)',(actual+1,payload,checksum(value),stamp))
        return {'revision':actual+1,'updated_at':stamp,'status':'draft-saved','api_calls':0}
    except sqlite3.Error:raise EvidenceError('Draft could not be saved to SQLite; browser backup and existing assessments are retained') from None

def publication_comparisons(data,evidence):
    published=evidence['published_observations'];app=published['applicability'];missing=[]
    for key in ('configuration','temperature_C','current_A'):
        actual=data.get(key)
        if key=='current_A' and data.get('trace') and all(row['current_A']==app[key] for row in data['trace']):actual=app[key]
        if actual!=app[key]:missing.append(key)
    if (data.get('feedstock') or '').strip().upper()!=app['feedstock'].upper():missing.append('feedstock')
    matches=[r for r in published['cases'] if data['duration_s']==r['duration_h']*3600]
    if not matches:missing.append('matching_published_electrolysis_duration')
    if missing:return {'status':'no_condition_matched_publication','unmatched_context':missing,'comparisons':[],
        'reference_context':app,'reference_cases':published['cases'],'source_url':published['source_url'],
        'scope':published['scope']+' Reference cases are shown for context only. No performance difference or pass/fail is computed across unmatched conditions.'}
    reference=matches[0];rows=[]
    for field in ('collected_o2_g','initial_resistance_ohm','final_resistance_ohm','wall_loss_um'):
        actual=data.get(field);reason=None
        if data.get('resistance_trace') and field in ('initial_resistance_ohm','final_resistance_ohm'):
            actual=data['resistance_trace'][0 if field=='initial_resistance_ohm' else -1]['resistance_ohm']
        if field=='collected_o2_g' and data['time_alignment']!='reported_same_interval':reason='different_or_unknown_oxygen_window'
        if field in ('initial_resistance_ohm','final_resistance_ohm') and (data['resistance_comparability']!='same_conditions' or not data['resistance_reference']):reason='unconfirmed_resistance_measurement_basis'
        if field=='wall_loss_um' and (data['thermal_exposure_h']!=reference['thermal_exposure_h'] or not data['wall_measurement_reference']):reason='different_or_unknown_hot_exposure_or_method'
        rows.append({'field':field,'reported_input':actual,'published_value':reference[field],'difference':actual-reference[field] if actual is not None and reason is None else None,'comparison_basis_gap':reason,'unit':'g' if field=='collected_o2_g' else 'ohm' if 'resistance' in field else 'um','source_id':published['source_id'],'source_url':published['source_url'],'locator':reference['locator']})
    return {'status':'declared_context_matched_not_experimental_equivalence','reference_case_id':reference['id'],'comparisons':rows,'scope':published['scope']+' Differences are descriptive, never healthy/faulty acceptance tests; geometry, full methods and measurement quality still need review.'}
