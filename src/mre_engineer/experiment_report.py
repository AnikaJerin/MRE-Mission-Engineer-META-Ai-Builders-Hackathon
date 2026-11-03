"""Readable experiment exports;"""
import html
import json
from pathlib import Path
from .evidence import EvidenceError
from .experiment_agent import load


def export_data(root,id):
    value=load(root,id)
    if 'report' not in value:raise EvidenceError('No verified saved assessment to export')
    return {'assessment':value['report'],'researcher_review':value['review'],'trace':value['events'],'trace_integrity':value['trace_integrity'],'current_code_matches':value['current_code_matches']}


def readable(value):
    e=html.escape
    hidden={'id','evidence_id','input_sha256','sha256','kind','exact_values_location'}
    if value is None:return 'Not supplied'
    if isinstance(value,bool):return 'Yes' if value else 'No'
    if isinstance(value,dict):return '<dl>'+''.join('<dt>'+e(str(k).replace('_',' '))+'</dt><dd>'+readable(v)+'</dd>' for k,v in value.items() if k not in hidden)+'</dl>'
    if isinstance(value,list):return '<ul>'+''.join('<li>'+readable(v)+'</li>' for v in value)+'</ul>'
    return e(str(value))


def to_html(value):
    e=lambda v:html.escape(str(v),quote=True)
    r=value['assessment']; calc=r['accounting']; perf=r.get('performance') or {}
    def number(v):
        return format(v,'.5g') if isinstance(v,(float,int)) and not isinstance(v,bool) else str(v)
    def table(headers,rows):
        return '<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+e(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'
    body=['<header><div class="brand">MRE / MISSION ENGINEER</div><h1>Reactor assessment</h1><p class="name">'+e(r['input']['experiment_name'])+'</p><p class="date">'+e(r.get('completed_at',''))+' · '+e(r['status'].replace('_',' '))+'</p></header>']
    final=r.get('final_review') or r.get('original_review') or {}
    if final.get('summary'):body.append('<section class="lead"><h2>Key conclusion</h2><p>'+e(final['summary'])+'</p></section>')
    if r.get('error'):body.append('<section><h2>Assessment incomplete</h2><p>'+e(r['error'])+'</p></section>')
    cards=[]
    for label,key,unit in [('Collected oxygen','reported_collected_o2_g','g'),('Ideal oxygen from charge','ideal_o2_g','g'),('Collected / ideal','apparent_collected_to_charge_ratio','%'),('Electrical energy','electrical_energy_Wh','Wh')]:
        v=calc.get(key)
        if v is not None:cards.append('<div class="stat"><span>'+label+'</span><strong>'+e(number(v*100 if unit=='%' else v))+' <small>'+unit+'</small></strong></div>')
    body.append('<div class="stats">'+''.join(cards)+'</div>')
    chart=[]
    for label,key in [('Ideal oxygen','ideal_o2_g'),('Collected oxygen','reported_collected_o2_g')]:
        if calc.get(key) is not None:chart.append({'category':label,'value':calc[key]})
    if chart:
        body.append('<section><h2>Oxygen comparison</h2><div id="oxygen-chart" role="img" aria-label="Ideal and collected oxygen in grams"></div><p id="chart-state" class="small" role="status">Loading chart…</p>'+table(['Quantity','Mass'],[[e(d['category']),e(number(d['value'])+' g')] for d in chart])+'</section>')
    metrics=[[e(m['label']),e(number(m['value'])),e(m['unit'])] for m in perf.get('metrics',{}).values() if m.get('value') is not None]
    if metrics:body.append('<section><h2>Calculated performance</h2>'+table(['Measurement','Result','Unit'],metrics)+'</section>')
    checks=perf.get('target_checks') or []
    if checks:
        body.append('<section><h2>Target comparison</h2>'+table(['Measurement','Result','Target','Outcome'],[[e(c['metric_id'].replace('_',' ')),e(number(c['actual'])) if c['actual'] is not None else 'Missing measurement',e(number(c['target'])),e({'within_declared_target':'Within target','outside_declared_target':'Outside target','insufficient_evidence':'More evidence needed'}.get(c['status'],c['status']))] for c in checks])+'</section>')
    findings=final.get('assessments') or []
    critics=r.get('critic_evidence') or []
    if findings or critics:
        body.append('<section><h2>Review and challenge</h2><div class="pair"><article><h3>Final review</h3>')
        for f in findings:body.append('<div class="finding"><h4>'+e(f.get('dimension','').replace('_',' '))+'</h4><p>'+e(f.get('finding',''))+'</p>' + ('<p class="small">'+e(f['basis'])+'</p>' if f.get('basis') else '')+'</div>')
        if not findings:
            for f in final.get('findings',[]):body.append('<p>'+e(f.get('text',''))+'</p>')
        body.append('</article><article><h3>Critic</h3>')
        for c in critics:body.append('<div class="finding"><h4>'+e(c.get('dimension','').replace('_',' '))+'</h4><p>'+e(c.get('comment',''))+'</p>'+('<p class="small">'+e(c['basis'])+'</p>' if c.get('basis') else '')+'</div>')
        if not critics and r.get('critique'):body.append('<p>'+e(r['critique'].get('weakness',''))+'</p>')
        body.append('</article></div></section>')
    comparisons=(perf.get('publication_comparisons') or {}).get('comparisons',[])
    used={}
    if comparisons:
        rows=[]
        for c in comparisons:
            if c.get('reported_input') is None:continue
            url=c.get('source_url',''); used.setdefault(url,set()).add(c.get('locator',''))
            rows.append([e({'collected_o2_g':'Collected oxygen','initial_resistance_ohm':'Initial resistance','final_resistance_ohm':'Final resistance','wall_loss_um':'Wall loss'}.get(c['field'],c['field'].replace('_',' '))),e(number(c['reported_input'])),e(number(c.get('published_value'))),e(number(c['difference'])) if c.get('difference') is not None else 'Basis differs',e(c.get('unit',''))])
        if rows:body.append('<section><h2>Published comparison</h2><p class="small">Reported research values provide context; conditions may differ.</p>'+table(['Quantity','Your input','Research value','Difference','Unit'],rows)+'</section>')
    if final.get('hypotheses'):
        body.append('<section><h2>Possible explanations</h2><ol>')
        for h in final['hypotheses']:body.append('<li><p>'+e(h['explanation'])+'</p><p class="small">'+e(h.get('discriminating_observation',''))+'</p></li>')
        body.append('</ol></section>')
    t=final.get('next_test') or {}
    if t:body.append('<section class="next"><h2>Recommended next check</h2>'+''.join('<p>'+e(t[k])+'</p>' for k in ('question','measurement_or_record','reason') if t.get(k))+'</section>')
    refs=set()
    for plan in (r.get('original_review'),r.get('final_review')):
        if plan:
            for f in plan.get('findings',[])+plan.get('assessments',[]):refs.update(f.get('evidence_refs',[]))
    for c in critics:
        for ref in c.get('references',[]):
            source=ref.get('source')
            if source and source.get('url'):used.setdefault(source['url'],set()).add(source.get('locator',''))
    for source in r.get('sources',[]):
        if source.get('id') in refs and source.get('url'):used.setdefault(source['url'],set()).add(source.get('locator',''))
    if used:
        body.append('<section class="sources"><h2>Research used</h2><ol>')
        for url,locators in used.items():
            source=next((s for s in r.get('sources',[]) if s.get('url')==url),{})
            body.append('<li><a href="'+e(url)+'">'+e(source.get('title') or ('Yu et al. 2025' if '20250004626' in url else 'SI defining constants' if 'bipm.org' in url else 'Research reference'))+'</a><span class="small"> · '+e('; '.join(sorted(x for x in locators if x)))+'</span></li>')
        body.append('</ol></section>')
    payload=json.dumps(chart).replace('<','\\u003c')
    library=Path(__file__).parent/'web'/'amcharts'
    vendor=''.join('<script>'+ (library/name).read_text().replace('</script','<\\/script')+'</script>' for name in ('index.js','xy.js','Animated.js')) if chart else ''
    scripts=vendor+"""<script>
    (function(){const state=document.getElementById('chart-state');try{if(!window.am5||!window.am5xy)throw Error();const data=CHARTDATA;const root=am5.Root.new('oxygen-chart');root.setThemes([am5themes_Animated.new(root)]);const chart=root.container.children.push(am5xy.XYChart.new(root,{panX:false,panY:false,paddingLeft:0}));const y=chart.yAxes.push(am5xy.CategoryAxis.new(root,{categoryField:'category',renderer:am5xy.AxisRendererY.new(root,{inversed:true,minGridDistance:25})}));y.data.setAll(data);const x=chart.xAxes.push(am5xy.ValueAxis.new(root,{min:0,renderer:am5xy.AxisRendererX.new(root,{})}));const series=chart.series.push(am5xy.ColumnSeries.new(root,{xAxis:x,yAxis:y,valueXField:'value',categoryYField:'category',fill:am5.color(0x25857c),stroke:am5.color(0x25857c),tooltip:am5.Tooltip.new(root,{labelText:'{categoryY}: {valueX} g'})}));series.columns.template.setAll({cornerRadiusTR:6,cornerRadiusBR:6,height:30});series.data.setAll(data);state.textContent='Mass in grams';window.addEventListener('beforeprint',()=>root.resize());}catch(e){document.getElementById('oxygen-chart').style.display='none';state.textContent='Chart unavailable. Exact values are shown in the table.';}})();</script>""".replace('CHARTDATA',payload) if chart else ''
    css="""*{box-sizing:border-box}body{margin:0;background:#eff4f5;color:#18333b;font:15px/1.55 system-ui,-apple-system,sans-serif}main{max-width:1100px;margin:32px auto;padding:36px;background:white;border-radius:20px}header{border-bottom:3px solid #25857c;padding-bottom:20px}.brand{letter-spacing:3px;font-size:11px;font-weight:800;color:#25857c}h1{font-size:34px;margin:10px 0}h2{font-size:20px;margin:0 0 16px}h3{font-size:16px;color:#25857c}h4{text-transform:capitalize;margin:0 0 6px}.name{font-size:19px;margin:0}.date,.small{font-size:12px;color:#536c73}section{margin-top:28px;padding-top:20px;border-top:1px solid #dce7e8}.lead{border:0;font-size:17px}.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:24px 0}.stat{background:#eaf6f3;border-radius:10px;padding:18px}.stat span{display:block;font-size:12px}.stat strong{display:block;font-size:25px;margin-top:8px}.stat small{font-size:14px}.pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}.pair article{min-width:0;background:#f5f8f9;padding:20px;border-radius:12px}.finding{padding:14px 0;border-bottom:1px solid #dce7e8}.finding p{margin:6px 0}table{width:100%;border-collapse:collapse;font-size:13px}th{text-align:left;background:#eaf2f3}th,td{padding:11px 12px;border-bottom:1px solid #dce7e8;vertical-align:top}td:first-child{width:38%}.table-wrap{width:100%;overflow-x:auto}p,td,li{overflow-wrap:anywhere}#oxygen-chart{width:100%;height:230px}.next{background:#eaf6f3;padding:22px;border-radius:12px}.sources li{margin-bottom:10px}a{color:#196f68}@media(max-width:680px){main{margin:0;padding:20px;border-radius:0}.stats{grid-template-columns:repeat(2,minmax(0,1fr))}.pair{grid-template-columns:1fr}h1{font-size:27px}.stat strong{font-size:21px}th,td{padding:8px;font-size:12px}}@media print{body{background:white}main{margin:0;padding:0;max-width:none}section,.stat,.finding{break-inside:avoid}.pair{gap:14px}a{color:inherit;text-decoration:none}h2{break-after:avoid}}"""
    return "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>MRE reactor assessment</title><style>"+css+'</style></head><body><main>'+''.join(body)+'</main>'+scripts+'</body></html>'
