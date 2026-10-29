"""Owner-run Excel contract tests. Fixtures contain constructed software inputs."""
import io
import zipfile
import tempfile
import unittest
from pathlib import Path
from xml.sax.saxutils import escape
from mre_engineer.evidence import EvidenceError
from mre_engineer.experiment_excel import parse_xlsx,save_import,input_provenance


def workbook(fields=None,trace=None,composition=None,formula=False,extra=None,resistance=None):
    fields=fields if fields is not None else [('experiment_name','Constructed control','','Notebook control'),('current_A',0.5,'A','Declared control'),('duration_s',3600,'s','Declared control')]
    sheets={'Experiment':[['field','value','unit','source'],*fields]}
    if trace is not None:sheets['Trace']=[['time_s','current_A','voltage_V','source'],*trace]
    if composition is not None:sheets['Composition']=[['analysis_id','oxide','wt_percent','source'],*composition]
    if resistance is not None:sheets['Resistance']=[['time_s','resistance_ohm','source'],*resistance]
    out=io.BytesIO();ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    with zipfile.ZipFile(out,'w') as z:
        names=[];rels=[]
        for i,(name,rows) in enumerate(sheets.items(),1):
            names.append(f'<sheet name="{name}" sheetId="{i}" r:id="rId{i}"/>');rels.append(f'<Relationship Id="rId{i}" Target="worksheets/sheet{i}.xml"/>')
            content=[]
            for n,row in enumerate(rows,1):
                cells=[]
                for j,v in enumerate(row):
                    if v is None:continue
                    a=f'{chr(65+j)}{n}'
                    if type(v) in (int,float):cells.append(f'<c r="{a}"><v>{v}</v></c>')
                    else:cells.append(f'<c r="{a}" t="inlineStr"><is><t>{escape(str(v))}</t></is></c>')
                content.append(f'<row r="{n}">'+''.join(cells)+'</row>')
            text=f'<worksheet xmlns="{ns}"><sheetData>'+''.join(content)+'</sheetData></worksheet>'
            if formula:text=text.replace('<v>0.5</v>','<f>1/2</f><v>0.5</v>')
            z.writestr(f'xl/worksheets/sheet{i}.xml',text)
        z.writestr('xl/workbook.xml',f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'+''.join(names)+'</sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships>'+''.join(rels)+'</Relationships>')
        if extra:
            for name,value in extra.items():z.writestr(name,value)
    return out.getvalue()


class ExcelTests(unittest.TestCase):
    def test_plain_values_and_cell_provenance_are_preserved(self):
        value=parse_xlsx(workbook(),'test.xlsx');self.assertEqual(value['input']['current_A'],0.5);self.assertEqual(value['locations']['current_A']['cell'],'B3');self.assertEqual(len(value['file_sha256']),64)
    def test_missing_required_value_is_not_invented(self):
        with self.assertRaises(EvidenceError):parse_xlsx(workbook([('experiment_name','Control','','')]),'test.xlsx')
    def test_cached_formula_is_rejected_without_execution(self):
        with self.assertRaises(EvidenceError):parse_xlsx(workbook(formula=True),'test.xlsx')
    def test_wrong_unit_is_rejected(self):
        fields=[('experiment_name','Control','',''),('current_A',500,'mA',''),('duration_s',3600,'s','')]
        with self.assertRaises(EvidenceError):parse_xlsx(workbook(fields),'test.xlsx')
    def test_duplicate_field_is_rejected(self):
        fields=[('experiment_name','Control','',''),('current_A',0.5,'A',''),('current_A',1,'A',''),('duration_s',3600,'s','')]
        with self.assertRaises(EvidenceError):parse_xlsx(workbook(fields),'test.xlsx')
    def test_unknown_field_is_rejected(self):
        with self.assertRaises(EvidenceError):parse_xlsx(workbook([('healthy_reactor',1,'','')]),'test.xlsx')
    def test_nonfinite_number_is_rejected(self):
        fields=[('experiment_name','Control','',''),('current_A',float('inf'),'A',''),('duration_s',3600,'s','')]
        with self.assertRaises(EvidenceError):parse_xlsx(workbook(fields),'test.xlsx')
    def test_legacy_and_macro_formats_are_rejected(self):
        for name in ('test.xls','test.xlsm'):
            with self.assertRaises(EvidenceError):parse_xlsx(workbook(),name)
        with self.assertRaises(EvidenceError):parse_xlsx(workbook(extra={'xl/vbaProject.bin':b'not executed'}),'test.xlsx')
    def test_external_workbook_link_is_rejected(self):
        with self.assertRaises(EvidenceError):parse_xlsx(workbook(extra={'xl/externalLinks/externalLink1.xml':'<x/>'}),'test.xlsx')
    def test_trace_rows_are_not_merged_with_scalar_current(self):
        with self.assertRaises(EvidenceError):parse_xlsx(workbook(trace=[[0,0.5,None,'control'],[3600,0.5,None,'control']]),'test.xlsx')
    def test_trace_requires_exact_window_and_retains_cells(self):
        fields=[('experiment_name','Control','',''),('duration_s',3600,'s','')]
        good=parse_xlsx(workbook(fields,trace=[[0,0.5,None,'control'],[3600,0.5,None,'control']]),'test.xlsx')
        self.assertEqual(len(good['input']['trace']),2);self.assertEqual(good['trace_locations'][1]['time_s'],'A3')
        with self.assertRaises(EvidenceError):parse_xlsx(workbook(fields,trace=[[0,0.5,None,'control'],[1800,0.5,None,'control']]),'test.xlsx')
    def test_different_composition_analyses_cannot_be_pooled(self):
        rows=[['assay-A','SiO2',50,'source'],['assay-B','FeO',10,'source']]
        with self.assertRaises(EvidenceError):parse_xlsx(workbook(composition=rows),'test.xlsx')
    def test_edit_after_import_is_labelled_and_original_receipt_retained(self):
        receipt=parse_xlsx(workbook(),'test.xlsx')
        with tempfile.TemporaryDirectory() as tmp:
            saved=save_import(Path(tmp),receipt);data=dict(saved['input']);data['current_A']=1
            result=input_provenance(tmp,data,saved['id']);self.assertEqual(result['kind'],'edited_excel');self.assertEqual(result['changed_fields'],['current_A']);self.assertEqual(saved['input']['current_A'],0.5)
    def test_delivered_template_has_no_formulas_and_needs_measurements(self):
        asset=Path(__file__).parents[1]/'src/mre_engineer/web/experiment-template.xlsx'
        with zipfile.ZipFile(asset) as z:
            for name in z.namelist():
                if name.startswith('xl/worksheets/') and name.endswith('.xml'):self.assertNotIn(b'<f>',z.read(name))
        with self.assertRaises(EvidenceError):parse_xlsx(asset.read_bytes(),asset.name)


class PerformanceExcelTests(unittest.TestCase):
    def test_resistance_sheet_and_exposure_unit_preserve_provenance(self):
        fields=[('experiment_name','Constructed control','',''),('current_A',0.5,'A',''),('duration_s',3600,'s',''),('thermal_exposure_h',2,'h','Control notebook')]
        value=parse_xlsx(workbook(fields,resistance=[[0,2,'Constructed meter'],[3600,1,'Constructed meter']]),'test.xlsx')
        self.assertEqual(value['input']['thermal_exposure_h'],2)
        self.assertEqual(value['input']['resistance_trace'][1]['resistance_ohm'],1)
        self.assertEqual(value['resistance_locations'][1]['time_s'],'A3')
    def test_performance_unit_mismatch_is_rejected(self):
        fields=[('experiment_name','Control','',''),('current_A',0.5,'A',''),('duration_s',3600,'s',''),('wall_loss_um',5,'mm','Control')]
        with self.assertRaises(EvidenceError):parse_xlsx(workbook(fields),'test.xlsx')
