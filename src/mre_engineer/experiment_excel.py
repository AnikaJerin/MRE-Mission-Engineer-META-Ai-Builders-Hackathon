"""Bounded value-only XLSX import with cell provenance. Never executes workbook code."""
import io
import json
import math
import posixpath
import re
import zipfile
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree as ET
from .evidence import EvidenceError,read_json,sha256
from .experiment_input import ALLOWED,ENUMS,NUMERIC_FIELDS,UNITS,validate_input
from .investigation import digest

NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
MAX_BYTES=2_000_000


def xml(z,name):
    raw=z.read(name)
    if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():raise EvidenceError('XML entity definitions are unsupported')
    return ET.fromstring(raw)


def rows(z,path,shared):
    root=xml(z,path);out=[];count=0;seen=set()
    for row in root.findall('.//s:sheetData/s:row',NS):
        cells={}
        for cell in row.findall('s:c',NS):
            count+=1
            if count>15000:raise EvidenceError('Workbook has too many cells')
            address=cell.get('r','')
            if not re.fullmatch(r'[A-Z]{1,3}[1-9][0-9]{0,5}',address):raise EvidenceError('Cell address missing or unsupported')
            if address in seen:raise EvidenceError('Duplicate cell address')
            seen.add(address)
            if cell.find('s:f',NS) is not None:raise EvidenceError(f'{address}: formulas are unsupported; paste measured values only')
            kind=cell.get('t','n');raw=cell.findtext('s:v',default='',namespaces=NS)
            if kind=='inlineStr':value=''.join(cell.find('s:is',NS).itertext()) if cell.find('s:is',NS) is not None else ''
            elif kind=='s':
                try:
                    index=int(raw)
                    if index<0:raise ValueError('Negative string index')
                    value=shared[index]
                except (ValueError,IndexError):raise EvidenceError('Invalid shared string') from None
            elif kind in ('n',''):
                if raw=='':value=None
                else:
                    try:value=float(raw)
                    except ValueError:raise EvidenceError('Invalid numeric cell') from None
                    if not math.isfinite(value):raise EvidenceError('Nonfinite Excel value')
            elif kind=='str':value=raw
            else:raise EvidenceError(f'{address}: unsupported cell type; use plain text or numbers')
            if isinstance(value,str) and len(value)>2000:raise EvidenceError('Excel cell text is too long')
            column=re.match(r'[A-Z]+',address).group()
            if column in cells:raise EvidenceError('Duplicate cell address')
            cells[column]={'value':value,'address':address}
        if any(c['value'] not in (None,'') for c in cells.values()):out.append(cells)
        if len(out)>1100:raise EvidenceError('Too many workbook rows')
    return out


def table(rows_,headers):
    if not rows_:return []
    columns={chr(65+i):name for i,name in enumerate(headers)}
    if any(rows_[0].get(c,{}).get('value')!=name for c,name in columns.items()):raise EvidenceError('Excel headers must match the template exactly: '+', '.join(headers))
    if any(v['value'] not in (None,'') for c,v in rows_[0].items() if c not in columns):raise EvidenceError('Unexpected Excel header')
    result=[]
    for row in rows_[1:]:
        if any(v['value'] not in (None,'') for c,v in row.items() if c not in columns):raise EvidenceError('Unexpected data outside template columns')
        result.append({name:row.get(c,{'value':None,'address':None}) for c,name in columns.items()})
    return result


def parse_xlsx(raw,filename):
    if not isinstance(raw,bytes) or len(raw)>MAX_BYTES:raise EvidenceError('Upload an XLSX file no larger than 2 MB')
    if not isinstance(filename,str) or not filename.lower().endswith('.xlsx'):raise EvidenceError('Use .xlsx; legacy .xls and macro-enabled workbooks are unsupported')
    try:
        z=zipfile.ZipFile(io.BytesIO(raw));names=z.namelist()
        if len(names)!=len(set(names)) or len(names)>1200 or sum(i.file_size for i in z.infolist())>8_000_000:raise EvidenceError('Workbook archive is oversized or ambiguous')
        if any('vba' in n.lower() or 'externallinks/' in n.lower() for n in names):raise EvidenceError('Macros and external workbook links are unsupported')
        rels=xml(z,'xl/_rels/workbook.xml.rels');targets={}
        for rel in rels:
            if rel.get('TargetMode')=='External':raise EvidenceError('External workbook relationships are unsupported')
            target=rel.get('Target','');path=posixpath.normpath(target.lstrip('/') if target.startswith('/') else 'xl/'+target)
            if not path.startswith('xl/'):raise EvidenceError('Invalid workbook relationship')
            targets[rel.get('Id')]=path
        shared=[]
        if 'xl/sharedStrings.xml' in names:shared=[''.join(s.itertext()) for s in xml(z,'xl/sharedStrings.xml').findall('s:si',NS)]
        workbook=xml(z,'xl/workbook.xml');sheets={}
        for s in workbook.findall('s:sheets/s:sheet',NS):
            name=s.get('name');rid=s.get('{'+NS['r']+'}id')
            if name not in ('Experiment','Trace','Composition','Resistance') or name in sheets:raise EvidenceError('Use only Experiment, Trace, Composition and Resistance template sheets')
            if s.get('state','visible')!='visible':raise EvidenceError('Hidden input sheets are unsupported')
            sheets[name]=rows(z,targets[rid],shared)
        if 'Experiment' not in sheets:raise EvidenceError('Experiment worksheet is required')
        data={};locations={}
        for row in table(sheets['Experiment'],('field','value','unit','source')):
            key=row['field']['value'];value=row['value']['value'];unit=row['unit']['value'] or ''
            if not isinstance(key,str) or key not in ALLOWED-{'trace','composition','test_estimates','resistance_trace'}:raise EvidenceError('Unknown Experiment field: '+str(key))
            if key in data:raise EvidenceError('Duplicate Experiment field: '+key)
            if unit!=UNITS.get(key,''):raise EvidenceError(f'{key}: use explicit unit {UNITS.get(key,"(text)")}')
            if value in (None,''):data[key]=None;continue
            if key in NUMERIC_FIELDS and type(value) not in (int,float):raise EvidenceError(f'{key}: enter an Excel number, not a text value')
            data[key]=value;locations[key]={'sheet':'Experiment','cell':row['value']['address'],'declared_source':row['source']['value'] or None}
        # Blank template enum cells mean explicitly unknown, never a measured value.
        for key,allowed in ENUMS.items():
            if data.get(key) is None:data.pop(key,None)
        data['trace']=[];trace_locations=[];composition_locations=[]
        for row in table(sheets.get('Trace',[]),('time_s','current_A','voltage_V','source')):
            data['trace'].append({key:row[key]['value'] for key in ('time_s','current_A','voltage_V','source')})
            trace_locations.append({key:row[key]['address'] for key in row})
        comp=[];ids=set();sources=set()
        for row in table(sheets.get('Composition',[]),('analysis_id','oxide','wt_percent','source')):
            composition_locations.append({key:row[key]['address'] for key in row})
            ids.add(row['analysis_id']['value']);sources.add(row['source']['value']);comp.append({'oxide':row['oxide']['value'],'wt_percent':row['wt_percent']['value']})
        if comp:
            if len(ids)!=1 or len(sources)!=1:raise EvidenceError('Do not combine different composition analyses or sources')
            data['composition']={'analysis_id':next(iter(ids)),'source':next(iter(sources)),'rows':comp}
        data['resistance_trace']=[];resistance_locations=[]
        for row in table(sheets.get('Resistance',[]),('time_s','resistance_ohm','source')):
            data['resistance_trace'].append({key:row[key]['value'] for key in ('time_s','resistance_ohm','source')})
            resistance_locations.append({key:row[key]['address'] for key in row})
        data=validate_input(data)
        return {'input':data,'filename':Path(filename).name[:200],'file_sha256':__import__('hashlib').sha256(raw).hexdigest(),'locations':locations,'trace_locations':trace_locations,'composition_locations':composition_locations,
          'resistance_locations':resistance_locations,'transformation':'Template values parsed; no formulas executed, normalization or implicit unit conversion. Trace/Composition/Resistance preserve worksheet rows.'}
    except EvidenceError:raise
    except (KeyError,ValueError,IndexError,ET.ParseError,zipfile.BadZipFile,RuntimeError,OSError) as exc:raise EvidenceError('Workbook could not be read; use the current XLSX template with plain values') from exc


def save_import(root,receipt):
    id=uuid4().hex;value={**receipt,'id':id};value['sha256']=digest(value)
    dest=Path(root)/'outputs/experiment-imports';dest.mkdir(parents=True,exist_ok=True)
    with (dest/(id+'.json')).open('x') as f:json.dump(value,f,indent=2,allow_nan=False)
    return value


def input_provenance(root,data,import_id=None):
    if not import_id:return {'kind':'manual','source_label':data['source_label'],'status':'User-reported; not independently authenticated'}
    if not isinstance(import_id,str) or not re.fullmatch('[0-9a-f]{32}',import_id):raise EvidenceError('Invalid import receipt ID')
    receipt=read_json(Path(root)/'outputs/experiment-imports'/(import_id+'.json'))
    if receipt.get('sha256')!=digest({k:v for k,v in receipt.items() if k!='sha256'}):raise EvidenceError('Import receipt modified')
    original=receipt['input'];changed=[k for k in set(original)|set(data) if original.get(k)!=data.get(k)]
    return {'kind':'excel' if not changed else 'edited_excel','filename':receipt['filename'],'file_sha256':receipt['file_sha256'],'locations':receipt['locations'],'trace_locations':receipt.get('trace_locations',[]),'composition_locations':receipt.get('composition_locations',[]),'resistance_locations':receipt.get('resistance_locations',[]),'changed_fields':sorted(changed),'import_id':import_id,
      'status':'Imported values with local cell provenance; edited fields are user-reported. A file hash is not calibration or authenticity validation.'}
