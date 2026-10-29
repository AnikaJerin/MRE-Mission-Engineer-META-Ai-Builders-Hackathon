"""Offline workflow/metric tests. Test-double results never establish model quality."""
import copy
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from mre_engineer.engineering_review import (BASE,PLAN,load_cases,load_key,context,freeze,check_freeze,run,load_report,tool,
    numeric_references,production_calculations,independent_checks,validate_plan,score,parse_engineering_submission,choice_schema,request)
from mre_engineer.evidence import EvidenceError

ROOT=Path(__file__).resolve().parents[1]


def fixture_plan(root,case,refs):
    # Exact references are used only inside this OFFLINE test double.
    key=load_key(root)["cases"][case["id"]];values=numeric_references(case)
    return {"claims":[{"claim_id":id,"status":r["status"],"rationale":"Offline reference fixture, not a model inference","evidence_refs":r["required_refs"]} for id,r in key.items()],
        "calculations":[{"calculation_id":c["id"],"value":values[c["id"]],"unit":c["unit"],"evidence_refs":c["source_refs"]} for c in case["calculations"]],
        "hypotheses":[{"explanation":"Unconfirmed possibility A","status":"unconfirmed","distinguishing_evidence":"Applicable measurement","evidence_refs":[refs[0]]},
                      {"explanation":"Unconfirmed possibility B","status":"unconfirmed","distinguishing_evidence":"Applicable calibration","evidence_refs":[refs[0]]}],
        "next_evidence_request":{"question":"Which input gap remains?","measurement_or_record":"Obtain applicable evidence","why_relevant":"Avoid unsupported causal attribution","prerequisites":["Review source and test scope"],"evidence_refs":[refs[0]]},
        "limitations":["Offline test double","No hardware approval"],"decision_status":"draft_for_document_review","ready_for_hardware_operation":False,"evidence_refs":[refs[-1]]}


class OfflineClient:
    def __init__(self,root,record):self.root=root;self.calls=0
    def request(self,body):
        self.calls+=1
        assert self.calls<=5
        data=json.loads(body["input"]);refs=data["allowed_evidence_refs"]
        assert "numeric_absolute_tolerances" not in json.dumps(data)
        assert "reference_key.json" not in json.dumps(data)
        wire_schema=body["tools"][0]["parameters"] if body["tools"] else body["text"]["format"]["schema"]
        assert "uniqueItems" not in json.dumps(wire_schema)
        case=next(c for c in load_cases(self.root) if c["title"]==data["case_evidence"]["title"])
        name=body["tools"][0]["name"] if body["tools"] else body["text"]["format"]["name"]
        if name=="engineering_tool_choice":
            assert "Return only the requested JSON object" not in body["instructions"]
            assert "classifying each" not in body["instructions"]
            value={"tool":wire_schema["properties"]["tool"]["enum"][0],"reason":"Offline bounded check selection","evidence_refs":[refs[0]]}
            return {"id":"offline-"+str(self.calls),"output":[{"type":"function_call","name":name,"call_id":"offline-choice","arguments":json.dumps(value)}]}
        elif name=="engineering_critique":value={"challenged_claim_ids":[],"weakness":"No unsupported change required in this fixture","alternative_explanation":"Unconfirmed alternative","requested_revision":"Retain correct labels","evidence_refs":[refs[-1]]}
        else:value=fixture_plan(self.root,case,refs)
        return {"id":"offline-"+str(self.calls),"output":[{"type":"message","content":[{"type":"output_text","text":json.dumps(value)}]}]}


class EngineeringReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        shutil.copytree(ROOT/"engineering_cases",self.root/"engineering_cases")

    def plan_and_case(self):
        case=load_cases(self.root)[0];returned=tool(case,case["tools"][0]);refs=[s["id"] for s in case["sources"]]+[returned["evidence_id"]]
        return fixture_plan(self.root,case,refs),case,refs

    def parse_choice_blocks(self,*texts):
        response={"output":[{"type":"message","content":[{"type":"output_text","text":t}]} for t in texts]}
        return parse_engineering_submission(response,"engineering_tool_choice",choice_schema(["oxygen_charge"]),["yu-operation"])

    def test_separate_commentary_does_not_corrupt_standalone_submission(self):
        text=json.dumps({"tool":"oxygen_charge","reason":"Check charge accounting","evidence_refs":["yu-operation"]})
        self.assertEqual(self.parse_choice_blocks("Selecting the oxygen-charge check first.",text)["tool"],"oxygen_charge")

    def test_multiple_json_submissions_are_not_arbitrarily_selected(self):
        text=json.dumps({"tool":"oxygen_charge","reason":"Check charge","evidence_refs":["yu-operation"]})
        with self.assertRaises(EvidenceError):self.parse_choice_blocks(text,text)

    def test_malformed_json_beside_valid_json_is_not_discarded(self):
        text=json.dumps({"tool":"oxygen_charge","reason":"Check charge","evidence_refs":["yu-operation"]})
        with self.assertRaises(EvidenceError):self.parse_choice_blocks('{"tool":',text)

    def test_prose_embedded_with_json_is_not_repaired(self):
        text='Here is the result: '+json.dumps({"tool":"oxygen_charge","reason":"Check charge","evidence_refs":["yu-operation"]})
        with self.assertRaises(EvidenceError):self.parse_choice_blocks(text)

    def test_selected_standalone_json_still_needs_full_local_validation(self):
        text=json.dumps({"tool":"arbitrary_code","reason":"Bad selection","evidence_refs":["yu-operation"]})
        with self.assertRaises(EvidenceError):self.parse_choice_blocks("A separate comment.",text)

    def test_credential_in_separate_commentary_is_still_rejected(self):
        text=json.dumps({"tool":"oxygen_charge","reason":"Check charge","evidence_refs":["yu-operation"]})
        with patch.dict(os.environ,{"MODEL_API_KEY":"offline-test-secret-only"}):
            with self.assertRaises(EvidenceError):self.parse_choice_blocks("offline-test-secret-only",text)

    def choice_request(self,response):
        class Capture:
            def request(inner,body):
                self.assertEqual(body["tools"][0]["name"],"engineering_tool_choice")
                self.assertNotIn("text",body)
                self.assertNotIn("return their exact claim_id",body["instructions"])
                return response
        case=load_cases(self.root)[1]
        return request(Capture(),case,"Select one local check.",{},choice_schema(case["tools"]),[s["id"] for s in case["sources"]],lambda *a:None,"engineering_tool_choice")

    def test_selection_uses_real_function_transport_with_narrow_instructions(self):
        value={"tool":"rate_comparison","reason":"Compare reports","evidence_refs":["ksc-2025"]}
        output={"output":[{"type":"function_call","name":"engineering_tool_choice","arguments":json.dumps(value)}]}
        self.assertEqual(self.choice_request(output)["tool"],"rate_comparison")

    def test_plain_text_choice_never_impersonates_function_execution(self):
        value={"tool":"rate_comparison","reason":"Compare reports","evidence_refs":["ksc-2025"]}
        with self.assertRaises(EvidenceError):self.choice_request({"output":[{"type":"message","content":[{"type":"output_text","text":json.dumps(value)}]}]})

    def test_invented_tool_evidence_in_actual_function_arguments_is_rejected(self):
        value={"tool":"rate_comparison","reason":"Compare reports","evidence_refs":["engtool-rate_comparison-placeholder"]}
        with self.assertRaises(EvidenceError):self.choice_request({"output":[{"type":"function_call","name":"engineering_tool_choice","arguments":json.dumps(value)}]})

    def test_two_contexts_twelve_claims_are_not_twelve_trials(self):
        cases=load_cases(self.root)
        self.assertEqual(len(cases),2);self.assertEqual(sum(len(c["review_claims"]) for c in cases),12)
        self.assertEqual(len({c["source_group"] for c in cases}),2)

    def test_all_claims_have_source_bounded_references(self):
        key=load_key(self.root)
        for case in load_cases(self.root):
            self.assertEqual(set(key["cases"][case["id"]]),{c["id"] for c in case["review_claims"]})

    def test_independent_fraction_references_have_manual_rate_answers(self):
        refs=numeric_references(load_cases(self.root)[1])
        self.assertEqual(refs["reported_rate_difference_kg_h"],0.03)
        self.assertEqual(refs["reported_rate_ratio_percent"],70)

    def test_independent_resistance_reference_has_manual_sign(self):
        refs=numeric_references(load_cases(self.root)[0])
        self.assertAlmostEqual(refs["resistance_change_percent"],-46.57534246575342)
        self.assertGreater(refs["ideal_o2_g"],0)

    def test_independent_numeric_checks_detect_production_drift(self):
        case=load_cases(self.root)[0]
        self.assertTrue(independent_checks(case)["passed"])
        wrong=production_calculations(case);wrong["ideal_o2_g"]*=2
        with patch("mre_engineer.engineering_review.production_calculations",return_value=wrong):
            self.assertFalse(independent_checks(case)["passed"])

    def test_bad_numeric_reference_blocks_before_client_instantiation(self):
        freeze(self.root,"unit")
        with patch("mre_engineer.engineering_review.independent_checks",return_value={"passed":False}):
            with self.assertRaisesRegex(EvidenceError,"no paid requests"):
                run(self.root,"unit","unit",allow_api_call=True,client_factory=lambda *a: self.fail("Client must not start"))

    def test_unknown_tools_do_not_execute_arbitrary_code(self):
        with self.assertRaises(EvidenceError):tool(load_cases(self.root)[0],"run_python")

    def test_incomplete_or_string_observation_is_rejected_before_api_work(self):
        p=self.root/BASE/"cases.json";data=json.loads(p.read_text());data["cases"][0]["observations"]["current_A"]="0.5"
        p.write_text(json.dumps(data))
        with self.assertRaises(EvidenceError):load_cases(self.root)

    def test_duplicate_claim_ids_are_rejected(self):
        plan,case,refs=self.plan_and_case();plan["claims"][1]["claim_id"]=plan["claims"][0]["claim_id"]
        with self.assertRaises(EvidenceError):validate_plan(plan,case,refs)

    def test_unknown_nested_citation_is_rejected(self):
        plan,case,refs=self.plan_and_case();plan["hypotheses"][0]["evidence_refs"]=["invented"]
        with self.assertRaises(EvidenceError):validate_plan(plan,case,refs)

    def test_plan_must_cite_an_actual_returned_tool(self):
        plan,case,refs=self.plan_and_case();plan["evidence_refs"]=[refs[0]]
        with self.assertRaises(EvidenceError):validate_plan(plan,case,refs)

    def test_unsupported_endorsement_and_missed_contradiction_are_counted(self):
        plan,case,refs=self.plan_and_case();key=load_key(self.root)
        next(c for c in plan["claims"] if c["claim_id"]=="Y2")["status"]="supported"
        result=score(plan,case,key["cases"][case["id"]],key["numeric_absolute_tolerances"])
        self.assertEqual(result["unsupported_endorsements"],1);self.assertEqual(result["missed_contradictions"],1)
        self.assertFalse(result["all_checks_passed"])
        self.assertEqual(result["release_status"],"blocked_structured_evidence_mismatch")

    def test_incorrect_units_and_numeric_values_fail_separately(self):
        plan,case,refs=self.plan_and_case();key=load_key(self.root)
        plan["calculations"][0]["unit"]="percent";plan["calculations"][1]["value"]=0
        result=score(plan,case,key["cases"][case["id"]],key["numeric_absolute_tolerances"])
        self.assertFalse(result["calculations"][0]["passed"]);self.assertFalse(result["calculations"][1]["passed"])

    def test_reference_selection_is_not_just_any_known_citation(self):
        plan,case,refs=self.plan_and_case();key=load_key(self.root)
        next(c for c in plan["claims"] if c["claim_id"]=="Y3")["evidence_refs"]=["yu-operation"]
        validate_plan(plan,case,refs)
        result=score(plan,case,key["cases"][case["id"]],key["numeric_absolute_tolerances"])
        self.assertFalse(result["all_checks_passed"])

    def test_freeze_refuses_reference_changes(self):
        freeze(self.root,"unit")
        p=self.root/BASE/"reference_key.json";p.write_text(p.read_text()+"\n")
        with self.assertRaises(EvidenceError):check_freeze(self.root,"unit")

    def test_explicit_paid_flag_required(self):
        with self.assertRaises(EvidenceError):run(self.root,"unit","unit",client_factory=OfflineClient)

    def test_two_complete_offline_workflows_are_labelled_test_double(self):
        freeze(self.root,"unit")
        with patch("urllib.request.build_opener",side_effect=AssertionError("No network")):
            result=run(self.root,"unit","unit",allow_api_call=True,client_factory=OfflineClient)
        self.assertEqual(result["status"],"engineering-reviews-completed")
        self.assertEqual(result["api_attempts"],16)
        self.assertEqual(len(result["summary"]["complete_case_ids"]),2)
        self.assertFalse(result["summary"]["general_engineering_advantage_established"])
        saved=load_report(self.root,"unit")
        self.assertEqual(saved["report"]["execution_mode"],"test-double")
        self.assertTrue(all(len(row["tools"])==2 for row in saved["report"]["rows"]))
        self.assertEqual(result["summary"]["paired"]["revision_corrected_cases"],0)

    def test_early_failure_stops_and_leaves_second_case_unattempted(self):
        class Bad(OfflineClient):
            def request(self,body):self.calls+=1;return {"output":[]}
        freeze(self.root,"unit");result=run(self.root,"unit","unit",allow_api_call=True,client_factory=Bad)
        self.assertEqual(result["api_attempts"],1)
        saved=load_report(self.root,"unit")["report"]
        self.assertEqual(saved["rows"][1]["status"],"not-attempted")
        self.assertIsNone(saved["rows"][0]["plans"]["one_pass"])

    def test_report_tampering_is_visible(self):
        freeze(self.root,"unit");run(self.root,"unit","unit",["hollow-anode-review"],True,OfflineClient)
        p=self.root/"outputs/engineering-reviews/unit/report.json";data=json.loads(p.read_text());data["api_attempts"]=0;p.write_text(json.dumps(data))
        self.assertEqual(load_report(self.root,"unit")["status"],"needs-review")

    def test_two_distinct_runs_combine_without_new_api_work(self):
        from mre_engineer.review_collection import combine
        freeze(self.root,"unit")
        run(self.root,"hollow","unit",["hollow-anode-review"],True,OfflineClient)
        run(self.root,"lr1","unit",["lr1-core-review"],True,OfflineClient)
        with patch("urllib.request.build_opener",side_effect=AssertionError("No network")):
            result=combine(self.root,"combined",["hollow","lr1"])
        self.assertEqual(result["api_calls"],0)
        saved=load_report(self.root,"combined")
        self.assertEqual(len(saved["report"]["summary"]["complete_case_ids"]),2)
        self.assertEqual(saved["report"]["api_attempts"],16)
        self.assertEqual(saved["report"]["execution_mode"],"test-double")

    def test_duplicate_case_cannot_be_presented_as_two_contexts(self):
        from mre_engineer.review_collection import combine
        freeze(self.root,"unit")
        run(self.root,"a","unit",["hollow-anode-review"],True,OfflineClient)
        run(self.root,"b","unit",["hollow-anode-review"],True,OfflineClient)
        with self.assertRaises(EvidenceError):combine(self.root,"combined",["a","b"])

    def test_separate_code_versions_require_explicit_historical_collection(self):
        from mre_engineer.review_collection import combine
        from mre_engineer.engineering_review import hashes
        freeze(self.root,"old")
        run(self.root,"hollow","old",["hollow-anode-review"],True,OfflineClient)
        altered=hashes(self.root);altered["code/engineering_review.py"]="1"*64
        with patch("mre_engineer.engineering_review.hashes",return_value=altered):
            freeze(self.root,"new")
            run(self.root,"lr1","new",["lr1-core-review"],True,OfflineClient)
            with self.assertRaises(EvidenceError):combine(self.root,"blocked",["hollow","lr1"])
            result=combine(self.root,"versioned",["hollow","lr1"],accept_versioned_components=True)
            self.assertEqual(result["api_calls"],0)
            saved=load_report(self.root,"versioned")
            self.assertFalse(saved["current_implementation_matches"])
            self.assertFalse(saved["report"]["same_frozen_implementation"])
            self.assertEqual(len({c["freeze_sha256"] for c in saved["report"]["components"]}),2)
