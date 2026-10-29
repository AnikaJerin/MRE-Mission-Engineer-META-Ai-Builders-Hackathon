"""Offline evaluation plumbing tests, not model performance measurements."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mre_engineer.evaluation import (check_freeze, checked_packet, checklist, freeze,
    load_cases, load_report, parse_submission, run, score, summarize, submit, response_record, provider_output_schema, SubmissionError, DECISION, CRITIQUE)
from mre_engineer.evidence import EvidenceError

ROOT = Path(__file__).resolve().parents[1]


class OfflineClient:
    def __init__(self, root, record): self.calls = 0
    def request(self, body):
        self.calls += 1
        assert self.calls <= 5
        encoded = json.dumps(body)
        assert 'answer_key' not in encoded
        assert 'expected_decision' not in encoded
        assert 'constructed-missing-calibration' not in encoded
        packet = json.loads(body["input"])["evidence"]
        assert body["tools"] == []
        assert body["text"]["format"]["strict"] is True
        assert body["text"]["format"]["type"] == "json_schema"
        assert "uniqueItems" not in json.dumps(body["text"]["format"]["schema"])
        assert "local_output_contract" in json.loads(body["input"])
        name = body["text"]["format"]["name"]
        if name == "submit_pilot_critique":
            value = {"weakness": "No demonstrated correction needed", "counterevidence": "Use supplied metadata only",
                     "requested_change": "Retain correct contract decision", "evidence_refs": packet["citation_refs"]}
        else: value = checklist(packet)
        return {"id": f"offline-{self.calls}", "output": [{"type": "message", "content": [
                  {"type": "output_text", "text": json.dumps(value)}]}]}


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "evaluation", self.root / "evaluation")

    def test_historical_and_constructed_cases_are_not_independent_reactors(self):
        cases = load_cases(self.root)
        historical = [c for c in cases if c["packet"]["case_type"] == "historical-summary"]
        self.assertEqual(len(historical), 2)
        self.assertEqual(len({c["packet"]["source_group"] for c in historical}), 1)
        self.assertEqual(len(cases) - len(historical), 4)

    def test_complete_control_prevents_blanket_abstention(self):
        case = next(c for c in load_cases(self.root) if c["case_id"] == "constructed-complete")
        self.assertEqual(checklist(checked_packet(case))["decision"], "proceed_conditional_review")

    def test_scope_and_unit_gates_do_not_invent_conversions(self):
        cases = {c["case_id"]: c for c in load_cases(self.root)}
        self.assertEqual(checklist(checked_packet(cases["constructed-out-of-scope"]))["decision"], "reject_scope")
        self.assertEqual(checklist(checked_packet(cases["constructed-unsupported-unit"]))["decision"], "reject_input")

    def test_descriptive_case_id_not_exposed_to_model(self):
        case = next(c for c in load_cases(self.root) if c["case_id"] == "constructed-missing-calibration")
        self.assertNotIn(case["case_id"], json.dumps(checked_packet(case)))

    def test_unknown_citation_fails_instead_of_getting_credit(self):
        case = load_cases(self.root)[0]; packet = checked_packet(case)
        result = checklist(packet); result["evidence_refs"] = ["fabricated"]
        response = {"output": [{"type": "function_call", "name": "submit_pilot_decision", "arguments": json.dumps(result)}]}
        with self.assertRaises(EvidenceError): parse_submission(response, "submit_pilot_decision", DECISION, packet["citation_refs"])

    def test_protocol_change_invalidates_freeze(self):
        freeze(self.root, "unit-v1")
        path = self.root / "evaluation/PROTOCOL.md"; path.write_text(path.read_text() + "\nchanged\n")
        with self.assertRaises(EvidenceError): check_freeze(self.root, "unit-v1")

    def test_no_paid_work_without_flag(self):
        with self.assertRaises(EvidenceError): run(self.root, client_factory=OfflineClient)

    def test_equal_outputs_do_not_become_a_superiority_claim(self):
        freeze(self.root, "unit-v1")
        with patch("urllib.request.build_opener", side_effect=AssertionError("No network")):
            result = run(self.root, "offline-pilot", "unit-v1", ["historical-3h", "constructed-complete"], True, OfflineClient)
        self.assertEqual(result["status"], "pilot-completed")
        self.assertEqual(result["summary"]["paired"]["revision_corrected_decision"], 0)
        self.assertFalse(result["summary"]["general_superiority_claim_supported"])
        self.assertEqual(result["summary"]["counts"]["one_pass"]["decision_exact"], 2)
        loaded = load_report(self.root, "offline-pilot")
        self.assertEqual(loaded["execution_mode"], "test-double")
        template = json.loads((self.root / "outputs/evaluations/offline-pilot/review_template.json").read_text())
        self.assertTrue(all(r["diagnostic_relevance"] is None for r in template))

    def test_regression_counts_against_revision_and_failures_remain_visible(self):
        key = {"x": {"decision": "request_evidence", "missing_inputs": []}}
        good = {"decision": "request_evidence", "missing_inputs": []}
        wrong = {"decision": "proceed_conditional_review", "missing_inputs": []}
        row = {"case_id": "x", "case_type": "constructed-contract-case", "source_group": "control", "status": "failed",
               "decisions": {"checklist": good, "one_pass": good, "challenge_revision": wrong, "resample_control": None}}
        report = summarize([row], key)
        self.assertEqual(report["paired"]["revision_regressed_decision"], 1)
        self.assertFalse(report["comparison_complete"])
        self.assertEqual(report["counts"]["resample_control"]["selected_cases"], 1)
        self.assertEqual(report["counts"]["resample_control"]["valid_outputs"], 0)

    def test_missing_input_extras_are_not_rewarded(self):
        expected = {"decision": "request_evidence", "missing_inputs": ["gas_calibration"]}
        result = {"decision": "request_evidence", "missing_inputs": ["gas_calibration", "current_record"]}
        self.assertTrue(score(result, expected)["decision_exact"])
        self.assertFalse(score(result, expected)["missing_set_exact"])

    def test_structured_response_submission(self):
        packet = checked_packet(load_cases(self.root)[0])
        client = OfflineClient(self.root, None)
        self.assertEqual(submit(client, packet, "Review", {})["decision"], checklist(packet)["decision"])
        self.assertEqual(client.calls, 1)

    def test_schema_failure_records_field_without_retry(self):
        packet = checked_packet(load_cases(self.root)[0]); events = []
        class BadClient:
            calls = 0
            def request(self, body):
                self.calls += 1
                value = checklist(packet); value["hypotheses"] = [{"unexpected": "object"}]
                return {"output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(value)}]}]}
        client = BadClient()
        with self.assertRaises(SubmissionError) as caught:
            submit(client, packet, "Review", {}, record=lambda kind, data: events.append((kind, data)))
        self.assertEqual(client.calls, 1)
        self.assertEqual(caught.exception.diagnostics[0]["path"], "/hypotheses/0")
        self.assertEqual([e[0] for e in events], ["model_submission", "submission_rejected"])

    def test_failed_first_submission_leaves_other_methods_unattempted(self):
        class BadClient:
            def __init__(self, root, record): self.calls = 0; self.record = record
            def request(self, body):
                self.calls += 1
                self.record("api_reserved", {"test_double": True})
                return {"output": [{"type": "message", "content": [{"type": "output_text", "text": "{}"}]}]}
        freeze(self.root, "unit-v1")
        with patch("urllib.request.build_opener", side_effect=AssertionError("No network")):
            result = run(self.root, "failed-pilot", "unit-v1", ["historical-3h"], True, BadClient)
        self.assertEqual(result["api_attempts"], 1)
        counts = result["summary"]["counts"]
        self.assertEqual(counts["one_pass"]["failed_outputs"], 1)
        self.assertEqual(counts["challenge_revision"]["not_attempted"], 1)
        self.assertEqual(counts["resample_control"]["not_attempted"], 1)

    def test_credential_reflection_is_redacted_and_rejected(self):
        response = {"output": [{"type": "message", "content": [{"type": "output_text", "text": "test-secret"}]}]}
        with patch.dict("os.environ", {"MODEL_API_KEY": "test-secret"}):
            self.assertNotIn("test-secret", json.dumps(response_record(response, "decision")))
            with self.assertRaises(SubmissionError): parse_submission(response, "decision", DECISION, [])

    def test_provider_schema_contains_only_structural_subset_without_mutation(self):
        for schema in (DECISION, CRITIQUE):
            original = json.dumps(schema, sort_keys=True)
            wire = provider_output_schema(schema)
            def check(node):
                self.assertLessEqual(set(node), {"type", "enum", "required", "additionalProperties", "properties", "items"})
                self.assertIn("type", node)
                for child in node.get("properties", {}).values(): check(child)
                if "items" in node: check(node["items"])
            check(wire)
            self.assertEqual(json.dumps(schema, sort_keys=True), original)

    def test_duplicate_items_still_fail_full_local_contract(self):
        packet = checked_packet(load_cases(self.root)[0]); value = checklist(packet)
        value["evidence_refs"] = [packet["citation_refs"][0]] * 2
        response = {"output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(value)}]}]}
        with self.assertRaises(SubmissionError) as caught:
            parse_submission(response, "submit_pilot_decision", DECISION, packet["citation_refs"])
        self.assertTrue(any(error["rule"] == "uniqueItems" for error in caught.exception.diagnostics))
