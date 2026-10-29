"""Owner-run release audit and script-free evidence export; never calls Meta."""
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from .decision_policy import release_decision
from .evaluation import load_report as load_pilot, safe_name
from .evidence import EvidenceError, read_json, sha256
from .investigation import digest
from .source_benchmark import load_report as load_source
from .engineering_review import load_report as load_engineering
from .validation_suite import overview as suite_overview


def release_audit(root,pilot_run="full-pilot-v4",name="v1"):
    status=load_pilot(root,pilot_run)
    if status.get("status")!="pilot-completed":raise EvidenceError("A current, complete pilot report is required for release audit")
    path=Path(root)/"outputs/evaluations"/safe_name(pilot_run)/"report.json"
    report=read_json(path);rows=[]
    for case in report["cases"]:
        for method,answer in case["decisions"].items():
            if answer is None:continue
            rows.append({"case_id":case["case_id"],"method":method,
                         **release_decision(case["model_packet"]["packet"],answer)})
    hashes={"pilot_report":sha256(path),"decision_policy":sha256(Path(__file__).with_name("decision_policy.py")),"dossier_code":sha256(Path(__file__))}
    result={"status":"release-policy-audited-not-model-improvement","pilot_run":pilot_run,"hashes":hashes,"rows":rows,
            "code_corrected_decisions":sum(r["decision_changed_by_code"] for r in rows),
            "scope":"Raw pilot scores unchanged. This audits release policy for structured pilot decisions, not arbitrary free-text plans or reactor operations."}
    result["sha256"]=digest(result)
    dest=Path(root)/"outputs/release-audits"/safe_name(name);dest.mkdir(parents=True,exist_ok=False)
    with (dest/"report.json").open("x") as stream:json.dump(result,stream,indent=2,allow_nan=False)
    return {"status":result["status"],"report":str(dest/"report.json"),"code_corrected_decisions":result["code_corrected_decisions"]}


def load_release(root,name="v1"):
    path=Path(root)/"outputs/release-audits"/safe_name(name)/"report.json"
    if not path.exists():return {"status":"not-run"}
    try:
        report=read_json(path)
        if report.get("sha256")!=digest({k:v for k,v in report.items() if k!="sha256"}):raise EvidenceError("Release audit modified")
        pilot=Path(root)/"outputs/evaluations"/safe_name(report["pilot_run"])/"report.json"
        hashes={"pilot_report":sha256(pilot),"decision_policy":sha256(Path(__file__).with_name("decision_policy.py")),"dossier_code":sha256(Path(__file__))}
        if report["hashes"].get("pilot_report")!=hashes["pilot_report"] or report["hashes"].get("decision_policy")!=hashes["decision_policy"] or load_pilot(root,report["pilot_run"]).get("status")!="pilot-completed":return {"status":"stale"}
        current=report["hashes"]==hashes
        return {"status":report["status"] if current else "archived-release-policy-audit","report":report,"current_exporter_matches":current,
                "scope":"Policy and original pilot still match; changed exporter version does not rewrite the historical audit"}
    except (OSError,ValueError,KeyError,TypeError):return {"status":"needs-review"}


def bundle(root,pilot_run="full-pilot-v4",source_run="v1",release_run="v1",engineering_run="v1"):
    return {"created_at":datetime.now(timezone.utc).isoformat(),"api_calls":0,"network_calls":0,
            "pilot":load_pilot(root,pilot_run),"source_benchmark":load_source(root,source_run),"release_audit":load_release(root,release_run),
            "engineering_reviews":load_engineering(root,engineering_run),"t12_validation":suite_overview(root),
            "claim_limits":["Public sources and dependent development cases, not blinded reactor validation",
                "Raw model and deterministic policy results are separate",
                "Source grounding and numerical checks do not establish optimal next experiments, failure probabilities, researcher time saved, NASA adoption or hardware clearance",
                "No personal review is needed for exact source-field checks; open-ended practical utility remains unscored"]}


def engineering_html(saved):
    e=html.escape;report=saved.get("report")
    if not report:return "<p>No recorded engineering investigation available.</p>"
    pieces=["<p>Exact structured claim and numeric checks; free-text engineering utility remains unscored.</p>"]
    if report.get("components"):
        pieces.append("<p>"+e(report.get("scope",""))+"</p><ul>")
        for component in report["components"]:
            pieces.append("<li>"+e(component["run_name"]+" — freeze "+component.get("freeze_sha256","see original report"))+"</li>")
        pieces.append("</ul>")
    pieces.append("<table><tr><th>Method</th><th>Claim labels</th><th>Numerical checks</th><th>Unsupported endorsements</th><th>Missed contradictions</th></tr>")
    for method,score in report.get("summary",{}).get("methods",{}).items():
        values=[method,f"{score['claims_correct']}/{score['claims_total']}",f"{score['numeric_correct']}/{score['numeric_total']}",str(score["unsupported_endorsements"]),f"{score['missed_contradictions']}/{score['reference_contradictions']}"]
        pieces.append("<tr>"+"".join("<td>"+e(v)+"</td>" for v in values)+"</tr>")
    pieces.append("</table>")
    for row in report["rows"]:
        pieces.append("<h3>"+e(row["title"])+"</h3><p>"+e(row["evidence"]["configuration"])+"</p>")
        for method,label in (("one_pass","Original request"),("challenge_revision","Revised or retained request"),("resample_control","Equal-call control")):
            plan=row["plans"].get(method)
            if plan:
                next=plan["next_evidence_request"]
                pieces.append("<h4>"+e(label)+"</h4><p><strong>"+e(next["question"])+"</strong></p><p>"+e(next["measurement_or_record"])+"</p><p>"+e(next["why_relevant"])+"</p>")
        pieces.append("<h4>Sources</h4><ul>")
        for source in row["evidence"]["sources"]:
            if source["url"].startswith("https://ntrs.nasa.gov/"):
                pieces.append('<li><a href="'+e(source["url"],quote=True)+'">'+e(source["id"]+" — "+source["locator"])+"</a></li>")
        pieces.append("</ul><details><summary>Raw reviews, references, independent checks and scores</summary><pre>"+e(json.dumps(row,indent=2,allow_nan=False))+"</pre></details>")
    return "".join(pieces)


def suite_html(value):
    e=html.escape
    parts=["<p>"+e(value.get('scope','T12 not configured'))+"</p>"]
    for frozen in value.get('freezes',[]):
        parts.append('<p><strong>'+e(frozen['name'])+'</strong>: '+e(json.dumps(frozen['gate']))+'</p>')
    for saved in value.get('reports',[]):
        report=saved.get('report')
        if not report:continue
        parts.append('<h3>'+e(report['run_name']+' / '+report['split'])+'</h3><p>'+e(saved['status'])+'</p>')
        parts.append('<table><tr><th>Method</th><th>Valid/selected</th><th>Correct verdicts</th><th>Numeric checks</th><th>Unsupported</th><th>Missed contradictions</th></tr>')
        for method,s in report.get('summary',{}).get('methods',{}).items():
            row=[method,f"{s['available']}/{s['selected']}",f"{s['correct']}/{s['available']}",f"{s['numeric_exact']}/{s['numeric_total']}",str(s['unsupported_endorsements']),f"{s['missed_contradictions']}/{s['reference_contradictions']}"]
            parts.append('<tr>'+''.join('<td>'+e(cell)+'</td>' for cell in row)+'</tr>')
        parts.append('</table>')
        for row in report['rows']:
            parts.append('<h4>'+e(row['case_id']+' / '+row['title'])+'</h4><p>'+e(row['evidence']['question'])+'</p>')
            revised=row['answers'].get('challenge_revision')
            if revised:parts.append('<p>Revised verdict: <strong>'+e(revised['verdict'])+'</strong></p><p>'+e(revised['rationale'])+'</p><p>Next evidence request (usefulness unscored): '+e(revised['next_evidence_request'])+'</p>')
    parts.append('<details><summary>Exact reference audit, source register, attempts and protocol</summary><pre>'+e(json.dumps(value,indent=2,allow_nan=False))+'</pre></details>')
    return ''.join(parts)


def to_html(data):
    escape=html.escape
    blocks=[]
    for title,key in (("Original six-case pilot","pilot"),("Source-grounded comparison","source_benchmark"),("Deterministic release audit","release_audit"),("Two engineering evidence investigations","engineering_reviews"),("T12 split validation and ground truth","t12_validation")):
        value=data.get(key,{"status":"not-run"})
        content=engineering_html(value) if key=="engineering_reviews" else suite_html(value) if key=="t12_validation" else "<details><summary>Inspect saved evidence and exact results</summary><pre>"+escape(json.dumps(value,indent=2,allow_nan=False))+"</pre></details>"
        blocks.append(f"<section><h2>{escape(title)}</h2><p>{escape(value.get('status','unknown'))}</p>{content}</section>")
    limits="".join("<li>"+escape(t)+"</li>" for t in data["claim_limits"])
    return "<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>MRE evidence dossier</title><style>body{font:16px system-ui;background:#09131b;color:#e2ecef;max-width:1100px;margin:40px auto;padding:24px}h1,h2{color:#93dfcf}table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:10px;border-bottom:1px solid #42505c;text-align:left;vertical-align:top}a{color:#93dfcf}details{margin:16px 0}section{border-top:1px solid #42505c;margin-top:24px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}li{margin:8px 0}@media print{body{background:white;color:black}h1,h2{color:#125447}pre{font-size:10px}}</style><h1>MRE Mission Engineer</h1><p>Evidence dossier · "+escape(data["created_at"])+"</p><ul>"+limits+"</ul>"+"".join(blocks)+"</html>"


def export(root,name="v1",pilot_run="full-pilot-v4",source_run="v1",release_run="v1",engineering_run="v1"):
    data=bundle(root,pilot_run,source_run,release_run,engineering_run)
    dest=Path(root)/"outputs/dossiers"/safe_name(name);dest.mkdir(parents=True,exist_ok=False)
    with (dest/"evidence.json").open("x") as stream:json.dump(data,stream,indent=2,allow_nan=False)
    (dest/"evidence.html").write_text(to_html(data),encoding="utf-8")
    return {"status":"evidence-exported-not-scientific-certification","json":str(dest/"evidence.json"),"html":str(dest/"evidence.html")}
