"""Local evidence and explicit owner-authorized Meta investigations."""

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from .evidence import EvidenceError, read_json, sha256, validate_case, validate_manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(),
                        help="Repository root; default is current directory")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Local interpreter and package inventory")
    sub.add_parser("sources", help="Validate and list the resource manifest")
    check = sub.add_parser("validate-case", help="Validate a historical case and provenance links")
    check.add_argument("--case", type=Path, default=Path("cases/yu2025-1h.json"))
    sub.add_parser("data-status", help="Check locally registered source files")
    register = sub.add_parser("register-file", help="Record an owner-downloaded local source file")
    register.add_argument("--source", required=True)
    register.add_argument("--path", required=True, type=Path)
    web = sub.add_parser("serve", help="Local lunar dashboard; paid jobs require explicit UI authorization")
    web.add_argument("--port", type=int, default=8766)
    web.add_argument("--accounting-run", default="v1", help="Saved Day 2 run to display; no calculations on refresh")
    web.add_argument("--investigation-run", default="v1", help="Recorded investigation to replay; no API calls")
    web.add_argument("--pilot-run", default="full-pilot-v4")
    web.add_argument("--source-run", default="v2")
    web.add_argument("--release-run", default="v1")
    web.add_argument("--engineering-run", default="v1")
    sub.add_parser('t12-preview',help='Inspect split and independent references without API')
    tf=sub.add_parser('t12-freeze');tf.add_argument('--name',default='t12-v1')
    tr=sub.add_parser('t12-run');tr.add_argument('--run-name',required=True);tr.add_argument('--freeze-name',default='t12-v1');tr.add_argument('--split',choices=['development','evaluation'],required=True);tr.add_argument('--case-id');tr.add_argument('--allow-api-call',action='store_true')
    tp=sub.add_parser('t12-report');tp.add_argument('--run-name',required=True)
    sub.add_parser("api-budget", help="Inspect local MRE usage estimates, not provider balance")
    pre = sub.add_parser("investigation-preview", help="Inspect context/tool contracts locally; no API calls")
    pre.add_argument("--accounting-run", default="v1")
    agent = sub.add_parser("investigate", help="Explicit paid Meta investigation: maximum 5 requests / $1.25 local reservation")
    agent.add_argument("--run-name", default="v1")
    agent.add_argument("--accounting-run", default="v1")
    agent.add_argument("--allow-api-call", action="store_true")
    rec = sub.add_parser("reconcile-request", help="Resolve a billing uncertainty only after provider review")
    rec.add_argument("--request-id", required=True)
    rec.add_argument("--actual-usd", required=True, type=float)
    rec.add_argument("--confirm-provider-review", action="store_true")
    ack = sub.add_parser("acknowledge-unknown-cost", help="Retain full reservation and explicitly permit continuation with unknown actual billing")
    ack.add_argument("--request-id", required=True)
    ack.add_argument("--accept-unknown-cost", action="store_true")
    evpre = sub.add_parser("eval-preview", help="Inspect the predeclared pilot scope and cost envelope; no API calls")
    evpre.add_argument("--case-id", action="append")
    evfreeze = sub.add_parser("eval-freeze", help="Freeze protocol, cases, labels and evaluation code before paid comparison")
    evfreeze.add_argument("--name", default="pilot-v1")
    evrun = sub.add_parser("eval-run", help="Explicit paid paired comparison: up to 5 requests / $1.25 reservation per selected case")
    evrun.add_argument("--run-name", default="pilot-v1")
    evrun.add_argument("--freeze-name", default="pilot-v1")
    evrun.add_argument("--case-id", action="append")
    evrun.add_argument("--allow-api-call", action="store_true")
    evreport = sub.add_parser("eval-report", help="Read a saved pilot report; no API calls")
    evreport.add_argument("--run-name", default="pilot-v1")
    sub.add_parser("source-preview", help="Read source-task scope and cost envelope; no API")
    sf=sub.add_parser("source-freeze", help="Freeze source-based tasks, references and code")
    sf.add_argument("--name", default="sources-v2")
    sr=sub.add_parser("source-run", help="Explicit paid source-grounding comparison, up to 5 requests per task")
    sr.add_argument("--run-name", default="v2")
    sr.add_argument("--freeze-name", default="sources-v2")
    sr.add_argument("--task-id", action="append")
    sr.add_argument("--allow-api-call", action="store_true")
    sp=sub.add_parser("source-report", help="Read source comparison; no API")
    sp.add_argument("--run-name", default="v2")
    ra=sub.add_parser("release-audit", help="Local deterministic policy audit; raw model scores unchanged")
    ra.add_argument("--pilot-run", default="full-pilot-v4")
    ra.add_argument("--run-name", default="v1")
    dos=sub.add_parser("dossier", help="Export saved comparison and release evidence as JSON/HTML; no API")
    dos.add_argument("--run-name", default="v1")
    dos.add_argument("--pilot-run", default="full-pilot-v4")
    dos.add_argument("--source-run", default="v2")
    dos.add_argument("--release-run", default="v1")
    dos.add_argument("--engineering-run", default="v1")
    sub.add_parser("engineering-preview",help="Inspect two engineering evidence investigations and scope; no API")
    ef=sub.add_parser("engineering-freeze",help="Freeze engineering cases, reference key and code")
    ef.add_argument("--name",default="engineering-v1")
    er=sub.add_parser("engineering-run",help="Two full bounded engineering review workflows; 8 unique API requests per case")
    er.add_argument("--run-name",default="v1")
    er.add_argument("--freeze-name",default="engineering-v1")
    er.add_argument("--case-id",action="append")
    er.add_argument("--allow-api-call",action="store_true")
    ep=sub.add_parser("engineering-report",help="Read claim errors, contradiction recall and independent checks; no API")
    ep.add_argument("--run-name",default="v1")
    ec=sub.add_parser("engineering-combine",help="Collect two verified original engineering case runs locally; no API")
    ec.add_argument("--run-name",default="v1")
    ec.add_argument("--from-run",action="append",required=True)
    ec.add_argument("--accept-versioned-components",action="store_true",help="Retain complete historical code versions as separately versioned evidence, not one fixed-implementation experiment")
    accounting = sub.add_parser("accounting", help="Compute and save bounded local Day 2 accounting")
    accounting.add_argument("--run-name", default="v1")
    accounting.add_argument("--reference-mass-g", type=float, default=100.0,
                            help="Illustrative inventory reference mass, not observed batch mass")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    report = {"created_at": datetime.now(timezone.utc).isoformat(),
              "network_calls": 0, "api_calls": 0}
    try:
        if args.command == "serve":
            from .dashboard import serve
            if not 0 <= args.port <= 65535:
                raise EvidenceError("Port must be between 0 and 65535")
            serve(root, args.port, args.accounting_run, args.investigation_run,args.pilot_run,args.source_run,args.release_run,args.engineering_run)
            return 0
        elif args.command == 't12-preview':
            from .validation_suite import overview
            report.update(status='t12-preview-not-executed',suite=overview(root))
        elif args.command == 't12-freeze':
            from .validation_suite import freeze
            report.update(freeze(root,args.name))
        elif args.command == 't12-run':
            from .validation_suite import run
            result=run(root,args.run_name,args.freeze_name,args.split,args.case_id,args.allow_api_call)
            report.update(result);report['api_calls']=result['api_attempts'];report['network_calls']=result['api_attempts']
        elif args.command == 't12-report':
            from .validation_suite import load_report
            report.update(load_report(root,args.run_name))
        elif args.command == "engineering-preview":
            from .engineering_review import load_cases,independent_checks
            cases=load_cases(root)
            report.update(status="engineering-preview-not-executed",cases=[{"id":c["id"],"title":c["title"],"claims":len(c["review_claims"]),"source_group":c["source_group"],"independent_numeric_checks":independent_checks(c)} for c in cases],
                          max_api_requests=16,max_local_reservation_usd=4.0,scope="Two public-source development investigations, not two prospective reactor trials")
        elif args.command == "engineering-freeze":
            from .engineering_review import freeze
            report.update(freeze(root,args.name))
        elif args.command == "engineering-run":
            from .engineering_review import run
            result=run(root,args.run_name,args.freeze_name,args.case_id,args.allow_api_call)
            report.update(result);report["api_calls"]=result["api_attempts"];report["network_calls"]=result["api_attempts"]
        elif args.command == "engineering-report":
            from .engineering_review import load_report
            result=load_report(root,args.run_name)
            report.update(status=result["status"],summary=result.get("report",{}).get("summary"),api_attempts=result.get("report",{}).get("api_attempts",0),current_implementation_matches=result.get("current_implementation_matches"))
        elif args.command == "engineering-combine":
            from .review_collection import combine
            report.update(combine(root,args.run_name,args.from_run,args.accept_versioned_components))
        elif args.command == "source-preview":
            from .source_benchmark import load_tasks
            tasks=load_tasks(root)
            report.update(status="source-preview-not-executed",tasks=[{"id":t["id"],"source_group":t["source_group"],"question":t["question"]} for t in tasks],max_api_requests=len(tasks)*5,max_local_reservation_usd=len(tasks)*1.25,
                          scope="Published source checks; constructed claims; not independent fault diagnoses")
        elif args.command == "source-freeze":
            from .source_benchmark import freeze
            report.update(freeze(root,args.name))
        elif args.command == "source-run":
            from .source_benchmark import run
            result=run(root,args.run_name,args.freeze_name,args.task_id,args.allow_api_call)
            report.update(result);report["api_calls"]=result["api_attempts"];report["network_calls"]=result["api_attempts"]
        elif args.command == "source-report":
            from .source_benchmark import load_report
            result=load_report(root,args.run_name)
            report.update(status=result["status"],summary=result.get("report",{}).get("summary"),api_attempts=result.get("report",{}).get("api_attempts",0),
                          annotations=result.get("annotations",[]),current_implementation_matches=result.get("current_implementation_matches"))
        elif args.command == "release-audit":
            from .dossier import release_audit
            report.update(release_audit(root,args.pilot_run,args.run_name))
        elif args.command == "dossier":
            from .dossier import export
            report.update(export(root,args.run_name,args.pilot_run,args.source_run,args.release_run,args.engineering_run))
        elif args.command == "eval-preview":
            from .evaluation import load_cases
            cases = load_cases(root)
            if args.case_id:
                if not set(args.case_id) <= {c["case_id"] for c in cases}: raise EvidenceError("Unknown pilot case ID")
                cases = [c for c in cases if c["case_id"] in set(args.case_id)]
            report.update(status="pilot-preview-not-executed", selected_cases=[{"case_id": c["case_id"], "type": c["packet"]["case_type"], "source_group": c["packet"]["source_group"]} for c in cases],
                          max_unique_api_requests=len(cases)*5, max_local_reservation_usd=len(cases)*1.25,
                          scope="Record-presence/input/scope development pilot. Next-test usefulness requires qualified review.")
        elif args.command == "eval-freeze":
            from .evaluation import freeze
            report.update(freeze(root, args.name))
        elif args.command == "eval-run":
            from .evaluation import run
            result = run(root, args.run_name, args.freeze_name, args.case_id, args.allow_api_call)
            report.update(result)
            report["api_calls"] = result["api_attempts"]
            report["network_calls"] = result["api_attempts"]
        elif args.command == "eval-report":
            from .evaluation import load_report
            report.update(load_report(root, args.run_name))
        elif args.command == "api-budget":
            from .api_budget import snapshot
            report.update(status="local-mre-budget", **snapshot(root))
        elif args.command == "reconcile-request":
            from .api_budget import reconcile
            report.update(status="owner-reconciled-estimate", request=reconcile(root, args.request_id, args.actual_usd, args.confirm_provider_review))
        elif args.command == "acknowledge-unknown-cost":
            from .api_budget import acknowledge_unknown_cost
            report.update(status="unknown-cost-acknowledged-not-settled", request=acknowledge_unknown_cost(root, args.request_id, args.accept_unknown_cost))
        elif args.command == "investigation-preview":
            from .investigation import preview
            report.update(preview(root, args.accounting_run))
        elif args.command == "investigate":
            from .investigation import investigate
            result = investigate(root, args.run_name, args.accounting_run, args.allow_api_call)
            # Count paid attempts explicitly; unknown billing remains reserved in ledger.
            report.update(result)
            report["api_calls"] = result["api_requests"]
            report["network_calls"] = result["api_requests"]
        elif args.command == "accounting":
            from .day2 import save_report
            result, path = save_report(root, args.run_name, args.reference_mass_g)
            report.update(status=result["status"], report=str(path),
                          report_sha256=result["report_sha256"],
                          oxide_total_wt_percent=result["inventory"]["oxide_total_wt_percent"],
                          reference_mass_g=result["reference_mass_g"],
                          represented_oxygen_g=result["inventory"]["represented_oxygen_g"],
                          ideal_charge_oxygen_g=result["charge"]["ideal_oxygen_g"],
                          apparent_oxygen_to_charge_ratio=result["charge"]["apparent_oxygen_to_charge_ratio"],
                          historical_comparison=result["historical_comparison"]["status"],
                          note="Conditional accounting only. No gas calibration, prediction or Meta investigation.")
        elif args.command == "register-file":
            from .acquisition import register_file
            report.update(status="local-file-registered", receipt=register_file(root, args.source, args.path))
        elif args.command == "doctor":
            packages = {}
            for name in ("mre-mission-engineer", "jsonschema"):
                try:
                    packages[name] = version(name)
                except PackageNotFoundError:
                    packages[name] = None
            report.update(status="local-inventory-only", python=platform.python_version(),
                          executable=sys.executable, architecture=platform.machine(),
                          root=str(root), packages=packages,
                          note="Inventory does not establish scientific validity or API access.")
        else:
            manifest_path = root / "sources/manifest.json"
            manifest = read_json(manifest_path)
            source_map = validate_manifest(manifest)
            report["manifest_sha256"] = sha256(manifest_path)
            if args.command == "data-status":
                from .acquisition import acquisition_status
                report.update(status="local-acquisition-inventory", sources={
                    id: acquisition_status(root, id) for id in source_map})
            elif args.command == "sources":
                report.update(status="source-metadata-valid-not-files-downloaded",
                              sources=[{"id": s["id"], "role": s["role"],
                                        "acquisition": s["acquisition"], "url": s["url"]}
                                       for s in source_map.values()])
            else:
                path = args.case if args.case.is_absolute() else root / args.case
                case = validate_case(read_json(path), manifest)
                report.update(status="case-structure-and-provenance-valid",
                              case_id=case["case_id"], case_sha256=sha256(path),
                              evidence_count=len(case["evidence"]),
                              provenance_class=case["provenance_class"],
                              missing_inputs=case["missing_inputs"],
                              agent_run_ready=False,
                              note="No physics, scientific inference, file download or Meta call was executed.")
        print(json.dumps(report, indent=2, allow_nan=False))
        return 2 if report.get("status") in {"failed", "stopped", "pilot-incomplete-or-changed", "source-pilot-incomplete-or-changed", "engineering-reviews-incomplete-or-changed", "t12-incomplete-or-changed", "needs-review", "stale"} else 0
    except (EvidenceError, OSError, ValueError) as exc:
        print(f"MRE: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
