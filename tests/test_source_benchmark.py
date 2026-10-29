"""Offline source comparison and immutable artifact tests, not model performance."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from mre_engineer.source_benchmark import (BASE,load_tasks,load_key,packet,execute_check,checklist,freeze,check_freeze,run,load_report,score)
from mre_engineer.evidence import EvidenceError

ROOT=Path(__file__).resolve().parents[1]


class OfflineClient:
    def __init__(self,root,record):self.root=root;self.calls=0
    def request(self,body):
        self.calls+=1
        assert self.calls<=5
        data=json.loads(body["input"]);e=data["evidence"]
        assert e["evidence_id"] in data["allowed_evidence_refs"]
        assert "absolute_tolerance" not in json.dumps(data)
        assert "task_id" not in data
        assert "uniqueItems" not in json.dumps(body["text"]["format"]["schema"])
        task=next(t for t in load_tasks(self.root) if t["record"]==e["record"])
        if body["text"]["format"]["name"]=="source_critic":
            value={"weakness":"Check source basis before revising","requested_check":"numerical_check","evidence_refs":[e["evidence_id"]]}
        else:value=checklist(task)
        return {"id":"offline-"+str(self.calls),"output":[{"type":"message","content":[{"type":"output_text","text":json.dumps(value)}]}]}


class SourceBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        shutil.copytree(ROOT/"benchmarks",self.root/"benchmarks")

    def test_real_sources_remain_two_groups_not_four_trials(self):
        tasks=load_tasks(self.root)
        self.assertEqual(len(tasks),4)
        self.assertEqual(len({t["source_group"] for t in tasks}),2)
        self.assertTrue(all("constructed_claim" in t for t in tasks))

    def test_exact_checks_match_predeclared_key(self):
        keys=load_key(self.root)
        for t in load_tasks(self.root):self.assertTrue(score(checklist(t),keys[t["id"]])["all_exact"])

    def test_thermal_duration_not_electrolysis_duration(self):
        task=load_tasks(self.root)[0]
        result=execute_check(task,"numerical_check")["result"]
        self.assertEqual(result["thermal_exposure_h"],14)
        self.assertEqual(result["electrolysis_h"],12)

    def test_resistance_percent_change_sign_and_rounding(self):
        task=load_tasks(self.root)[1]
        self.assertAlmostEqual(execute_check(task,"numerical_check")["result"]["change_percent"],-46.57534246575)

    def test_unknown_tool_and_zero_denominator_rejected(self):
        task=load_tasks(self.root)[1]
        with self.assertRaises(EvidenceError):execute_check(task,"run_python")
        task["record"]["initial_ohm"]=0
        with self.assertRaises(EvidenceError):execute_check(task,"numerical_check")

    def test_numeric_null_and_units_scored_separately(self):
        task=load_tasks(self.root)[0];key=load_key(self.root)[task["id"]];answer=checklist(task)
        answer["reference_value"]=None
        self.assertFalse(score(answer,key)["number_exact"])
        answer=checklist(task);answer["reference_unit"]="percent"
        self.assertFalse(score(answer,key)["unit_exact"])

    def test_freeze_is_immutable_and_key_changes_block(self):
        freeze(self.root,"unit")
        with self.assertRaises(FileExistsError):freeze(self.root,"unit")
        p=self.root/BASE/"answers.json";p.write_text(p.read_text()+"\n")
        with self.assertRaises(EvidenceError):check_freeze(self.root,"unit")

    def test_no_paid_work_without_flag(self):
        with self.assertRaises(EvidenceError):run(self.root,"unit","unit",client_factory=OfflineClient)

    def test_equal_answers_no_superiority_and_five_calls_per_task(self):
        freeze(self.root,"unit")
        with patch("urllib.request.build_opener",side_effect=AssertionError("No network")):
            result=run(self.root,"unit","unit",allow_api_call=True,client_factory=OfflineClient)
        self.assertEqual(result["status"],"source-pilot-completed")
        self.assertEqual(result["api_attempts"],20)
        self.assertEqual(result["summary"]["paired"]["revision_corrections"],0)
        self.assertFalse(result["summary"]["general_engineering_value_proven"])
        saved=load_report(self.root,"unit")
        self.assertEqual(saved["report"]["execution_mode"],"test-double")
        self.assertTrue(saved["events"])

    def test_failure_stops_later_calls_without_fabricating_answers(self):
        class Bad(OfflineClient):
            def request(self,body):self.calls+=1;return {"output":[]}
        freeze(self.root,"unit")
        result=run(self.root,"unit","unit",allow_api_call=True,client_factory=Bad)
        self.assertEqual(result["api_attempts"],1)
        self.assertEqual(result["summary"]["counts"]["one_pass"]["not_attempted"],3)
        self.assertEqual(result["summary"]["counts"]["challenge_revision"]["not_attempted"],4)

    def test_trace_tampering_is_not_a_valid_replay(self):
        freeze(self.root,"unit");run(self.root,"unit","unit",["thermal-clock"],True,OfflineClient)
        path=self.root/"outputs/source-evaluations/unit/events.jsonl"
        lines=path.read_text().splitlines();row=json.loads(lines[-1]);row["kind"]="fabricated";lines[-1]=json.dumps(row);path.write_text("\n".join(lines)+"\n")
        self.assertEqual(load_report(self.root,"unit")["status"],"needs-review")

    def test_prompt_packet_contains_source_receipt_not_answer_key(self):
        data=packet(load_tasks(self.root)[0])
        self.assertNotIn("absolute_tolerance",json.dumps(data))
        self.assertTrue(data["source_receipt"]["url"].startswith("https://ntrs.nasa.gov/"))

    def test_missing_temperature_packet_is_rejected_before_paid_work(self):
        path=self.root/BASE/"tasks.json";data=json.loads(path.read_text());del data["tasks"][0]["record"]["temperature_C"]
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(EvidenceError,"Incomplete source packet"):load_tasks(self.root)

    def test_checklist_does_not_ignore_missing_claim_temperature(self):
        task=load_tasks(self.root)[0];del task["record"]["temperature_C"]
        self.assertEqual(checklist(task)["evidence_status"],"not_established")

    def test_receipt_check_contains_source_context_not_just_a_link(self):
        task=load_tasks(self.root)[0]
        result=execute_check(task,"source_receipt")["result"]
        self.assertEqual(result["transcribed_source_record"]["temperature_C"],1600)
        self.assertEqual(result["transcribed_source_record"]["thermal_exposure_h"],14)

    def test_resistance_packet_identifies_specimen_duration(self):
        task=load_tasks(self.root)[1]
        self.assertEqual(task["record"]["electrolysis_h"],12)
        self.assertEqual(task["record"]["temperature_C"],1600)

    def test_code_change_retains_archived_results_without_current_success_claim(self):
        freeze(self.root,"unit");run(self.root,"unit","unit",["thermal-clock"],True,OfflineClient)
        from mre_engineer.source_benchmark import fingerprints
        changed=fingerprints(self.root);changed["code/source_benchmark.py"]="0"*64
        with patch("mre_engineer.source_benchmark.fingerprints",return_value=changed):saved=load_report(self.root,"unit")
        self.assertEqual(saved["status"],"archived-source-pilot")
        self.assertFalse(saved["current_implementation_matches"])
        self.assertEqual(saved["report"]["summary"]["counts"]["one_pass"]["all_exact"],1)
