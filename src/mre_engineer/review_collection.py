"""Combine two verified case runs locally, without repeating paid requests."""
import copy
import json
from datetime import datetime, timezone
from .evidence import EvidenceError,read_json,sha256
from .investigation import digest


def combine(root,name,run_names,accept_versioned_components=False):
    from .engineering_review import folder,load_report,summary
    if len(run_names)!=2 or len(set(run_names))!=2 or name in run_names:raise EvidenceError("Choose two distinct source runs and a fresh output name")
    components=[];rows=[];reports=[]
    for run_name in run_names:
        source=folder(root,run_name)/"report.json";raw=read_json(source)
        if raw.get("kind")=="engineering-review-collection":raise EvidenceError("Use original case runs, not nested collections")
        saved=load_report(root,run_name)
        complete=saved.get("report",{}).get("status")=="engineering-reviews-completed"
        if not complete or (not saved.get("current_implementation_matches") and not accept_versioned_components):
            raise EvidenceError("Both source runs must be complete; archived code versions require explicit --accept-versioned-components")
        report=saved["report"];reports.append(report);rows.extend(copy.deepcopy(report["rows"]))
        components.append({"run_name":run_name,"report_sha256":sha256(source),"trace_head":report["trace_head"],"freeze_sha256":report["freeze_sha256"],"implementation_hashes":{k:v for k,v in report["hashes"].items() if k.startswith("code/")}})
    same_freeze=len({r["freeze_sha256"] for r in reports})==1
    if len({r["execution_mode"] for r in reports})!=1:raise EvidenceError("Do not combine live/test-double modes")
    if not same_freeze and not accept_versioned_components:raise EvidenceError("Different freezes require explicit --accept-versioned-components")
    data_hashes=[{k:v for k,v in r["hashes"].items() if not k.startswith("code/")} for r in reports]
    if data_hashes[0]!=data_hashes[1]:raise EvidenceError("Do not collect cases with different source/reference/protocol data")
    if len(rows)!=2 or {r["case_id"] for r in rows}!={"hollow-anode-review","lr1-core-review"}:
        raise EvidenceError("Collection requires both distinct engineering contexts exactly once")
    if any(r["status"]!="completed-engineering-evidence-workflow" or r.get("api_attempts")!=8 or len(r["tools"])!=2 for r in rows):
        raise EvidenceError("Each case must retain all eight recorded requests and two local checks")
    result={"kind":"engineering-review-collection","status":"engineering-reviews-completed","created_at":datetime.now(timezone.utc).isoformat(),
        "execution_mode":reports[0]["execution_mode"],"data_hashes":data_hashes[0],"same_frozen_implementation":same_freeze,
        "versioned_components_accepted":bool(accept_versioned_components),
        "components":components,"rows":rows,"summary":summary(rows),"api_attempts":sum(r["api_attempts"] for r in reports),
        "settled_estimated_cost_usd":sum(r["settled_estimated_cost_usd"] for r in reports),
        "collector_code_sha256":sha256(__file__),"claim_limits":reports[0]["claim_limits"],
        "scope":"Local collection of separately versioned case runs; inspect each component freeze/code before interpretation. Mixed versions are not one fixed-implementation experiment. No synthetic event chain or new API requests."}
    result["sha256"]=digest(result);dest=folder(root,name);dest.mkdir(parents=True,exist_ok=False)
    with (dest/"report.json").open("x") as stream:json.dump(result,stream,indent=2,allow_nan=False)
    return {"status":"engineering-runs-collected-no-new-api","report":str(dest/"report.json"),"summary":result["summary"],"api_calls":0,"network_calls":0}


def load(root,name,result):
    from .engineering_review import folder,load_report
    current=result.get("collector_code_sha256")==sha256(__file__)
    if len(result.get("components",[]))!=2:raise EvidenceError("Invalid engineering collection")
    for item in result["components"]:
        if item["run_name"]==name:raise EvidenceError("Self-referencing collection")
        path=folder(root,item["run_name"])/"report.json"
        if sha256(path)!=item["report_sha256"] or read_json(path).get("kind")=="engineering-review-collection":raise EvidenceError("Collection source changed or nested")
        saved=load_report(root,item["run_name"])
        if "report" not in saved or saved["report"].get("trace_head")!=item["trace_head"]:raise EvidenceError("Collection component trace invalid")
        current=current and saved.get("current_implementation_matches",False)
    return {"status":result["status"] if current else "archived-engineering-reviews","current_implementation_matches":bool(current),
        "run_name":name,"report":result,"trace_integrity":"verified-component-report-and-trace-links"}
