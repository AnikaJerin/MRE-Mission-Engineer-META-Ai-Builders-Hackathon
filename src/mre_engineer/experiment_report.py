"""Readable experiment exports; no API and no retrospective model certification."""
import html
import json
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
    e=html.escape;r=value['assessment'];calc=r['accounting'];body=[]
    body.append('<h1>'+e(r['input']['experiment_name'])+'</h1><p>'+e(r['input']['question'])+'</p><p>'+e(r['status']+' · '+r['effective_review_status'].replace('_',' '))+'</p>')
    body.append('<p>Input-driven ground-test review. New user data has no independently known correct engineering decision. Calculations are independently checked; hypotheses and next-test usefulness remain unvalidated.</p>')
    body.append('<h2>Accounting</h2><table>')
    for label,key,unit in [('Charge','charge_C','C'),('Ideal oxygen','ideal_o2_g','g'),('Reported collected oxygen','reported_collected_o2_g','g'),('Apparent collected / ideal ratio','apparent_collected_to_charge_ratio',''),('Electrical energy','electrical_energy_Wh','Wh')]:
        v=calc[key];body.append('<tr><th>'+label+'</th><td>'+e('Not available' if v is None else format(v,'.8g')+' '+unit)+'</td></tr>')
    body.append('</table><p>'+e(calc['basis'])+'</p>')
    performance=r.get('performance')
    if performance:
        body.append('<h2>Structured performance metrics</h2><table><tr><th>Metric</th><th>Value</th><th>Formula / basis</th></tr>')
        for m in performance['metrics'].values():body.append('<tr><td>'+e(m['label'])+'</td><td>'+e('Not available' if m['value'] is None else format(m['value'],'.8g')+' '+m['unit'])+'</td><td>'+e(m['formula'])+'</td></tr>')
        body.append('</table><h2>Declared targets and selected official requirements</h2>'+readable({'user_targets':performance['target_checks'],'official_profile':performance.get('official_profile_checks',[])})+'')
        body.append('<h2>Decision evidence</h2>')
        for d in r.get('decision_evidence',[]):
            body.append('<h3>'+e(d['dimension'])+' — '+e({'supported_observation':'Recorded observation — not a performance pass','concern_supported':'Evidence supports a concern','insufficient_evidence':'More evidence needed'}.get(d['model_status'],d['model_status']))+'</h3><p>'+e(d['model_finding'])+'</p><p>'+e(d.get('model_basis') or '')+'</p><p>'+e(d['improvement_or_next_evidence'])+'</p><details><summary>Inputs, calculations, references and tool receipts</summary>'+readable(d)+'</details>')
    if performance and performance.get('publication_comparisons'):
        body.append('<h2>Published observation comparisons</h2>'+readable(performance['publication_comparisons'])+'')
    if r.get('reference_registry'):body.append('<p>Reference registry version: '+e(r['reference_registry']['version'])+'</p>')
    if r.get('error'):body.append('<h2>Incomplete workflow</h2><p>'+e(r['error'])+'</p><p>No completed critic/final review is implied. API attempts: '+str(r['api_attempts'])+'</p>')
    body.append('<h2>Evidence still needed</h2><ul>'+''.join('<li>'+e(g['message'])+'</li>' for g in r['readiness']['gaps'])+'</ul>')
    for name,key in [('Original review','original_review'),('Critic','critique'),('Final review','final_review')]:
        data=r[key];body.append('<h2>'+name+'</h2>')
        if not data:body.append('<p>Not completed.</p>');continue
        if key=='critique':
            body.extend('<p>'+e(data[k])+'</p>' for k in ('weakness','rival_explanation','requested_revision'))
            for c in r.get('critic_evidence',[]):
                body.append('<h3>'+e(c['dimension']+' — '+c['position'])+'</h3><p>'+e(c['comment'])+'</p><p>Why: '+e(c['basis'])+'</p>')
                for ref in c['references']:
                    source=ref.get('source')
                    body.append('<p>'+('<a href="'+e(source['url'],quote=True)+'">'+e(source.get('title') or source['id'])+'</a>: '+e(source['locator']) if source else e(ref['id']))+'</p>')
                body.append('<details><summary>Comment evidence</summary>'+readable(c)+'</details>')
            continue
        for f in data.get('findings',[]):body.append('<p>'+e(f['text'])+'</p><p>Why: '+e(f.get('basis') or 'Not recorded in this archived version')+'</p><p>Evidence: '+e(', '.join(f['evidence_refs']))+'</p>')
        for a in data.get('assessments',[]):body.append('<p>'+e(a['dimension']+': '+a['finding'])+'</p><p>Why: '+e(a.get('basis') or 'Not recorded in this archived version')+'</p>')
        body.append('<p>'+e(data['summary'])+'</p><h3>Unconfirmed explanations</h3><ul>')
        for h in data['hypotheses']:body.append('<li>'+e(h['explanation'])+'<br>Evidence to distinguish: '+e(h['discriminating_observation'])+'</li>')
        body.append('</ul><h3>Next evidence request</h3>')
        body.append('<p>Proposed next request: draft starting point, not a validated priority ranking or proven causal discrimination. Recorded observations are not performance passes.</p>')
        t=data['next_test'];body.extend('<p>'+e(t[k])+'</p>' for k in ('question','measurement_or_record','rival_outcomes','prerequisites','reason'))
    body.append('<h2>Sources</h2><ul>')
    for s in r['sources']:body.append('<li><a href="'+e(s['url'],quote=True)+'">'+e(s['id'])+'</a>: '+e(s['locator'])+'</li>')
    body.append('</ul><h2>Researcher review</h2>'+readable(value['researcher_review'])+'')
    body.append('<p>API attempts: '+str(r['api_attempts'])+'; estimated settled cost $'+str(r['settled_estimated_cost_usd'])+'. Saved '+e(r['completed_at'])+'.</p>')
    body.append('<h2>Integration scope</h2><p>Manual entry is the supported researcher workflow. Read-only potentiostat/DAQ, LIMS and approved reactor-historian adapters are future work. No live equipment connection, official-software compatibility or reactor control is demonstrated.</p>')
    body.append('<p>Full machine-readable inputs, calculation receipts and event trace are available in the separate JSON export.</p>')
    return "<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>MRE experiment review</title><style>body{font:16px system-ui;max-width:980px;margin:40px auto;padding:24px;color:#152631}h1,h2{color:#245c60}table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:10px;border-bottom:1px solid #d1dfe0}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}li{margin:12px 0}details{margin-top:32px}@media print{body{margin:0}}</style></head><body>"+''.join(body)+'</body></html>'
