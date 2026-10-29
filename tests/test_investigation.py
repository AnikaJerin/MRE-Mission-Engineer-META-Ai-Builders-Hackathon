"""Offline test doubles. Never contact Meta or assert real API performance."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mre_engineer.day2 import save_report
from mre_engineer.evidence import EvidenceError
from mre_engineer.investigation import investigate, load_investigation, preview
from mre_engineer.meta_client import MetaClient
from mre_engineer import api_budget

ROOT = Path(__file__).resolve().parents[1]


def plan(ref, revised=False):
    return {"hypotheses": [
        {"label": "H1", "explanation": "Possible collection-accounting limitation", "evidence_refs": [ref], "discriminating_observation": "Calibrated collection record"},
        {"label": "H2", "explanation": "Possible material-related process difference", "evidence_refs": [ref], "discriminating_observation": "Relevant post-test evidence"}],
        "next_test": {"category": "gas-accounting-review" if revised else "current-trace-review",
            "question": "What evidence is missing?", "measurement": "Review calibration" if revised else "Review current trace",
            "why_discriminates": "Clarify what can be inferred from oxygen recovery", "evidence_refs": [ref],
            "prerequisites": ["Qualified engineer review"]},
        "decision_status": "draft_requires_engineer_review", "limitations": ["No diagnosis", "Historical test double"]}


class FakeClient:
    def __init__(self, root, record): self.calls = 0

    def request(self, body):
        self.calls += 1
        n = self.calls
        if n in (1, 3):
            name = "check_charge_accounting" if n == 1 else "check_measurement_readiness"
            args = {}
        elif n in (2, 4):
            ref = json.loads(body["input"][0]["output"])["evidence_id"]
            if n == 2: name, args = "submit_plan", plan(ref)
            else:
                self.second_ref = ref
                name, args = "submit_challenge", {"weakness": "Gas calibration is absent", "why_it_matters": "Cannot independently verify collection",
                    "alternate_explanation": "Measurement limitation", "evidence_refs": [ref], "requested_revision": "Review gas accounting"}
        else: name, args = "submit_plan", plan(self.second_ref, True)
        return {"id": f"fake-{n}", "output": [{"type": "function_call", "name": name, "call_id": f"call-{n}", "arguments": json.dumps(args)}]}


class InvestigationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for d in ("cases", "sources"): shutil.copytree(ROOT / d, self.root / d)
        save_report(self.root, "v1")

    def test_preview_does_not_make_api_requests(self):
        with patch("urllib.request.build_opener", side_effect=AssertionError("No network allowed")):
            data = preview(self.root)
        self.assertEqual(data["api_calls"], 0)
        self.assertEqual(data["max_api_requests"], 5)

    def test_paid_call_needs_explicit_flag(self):
        with self.assertRaises(EvidenceError): investigate(self.root, client_factory=FakeClient)

    def test_offline_loop_preserves_tools_challenge_and_revision(self):
        with patch("urllib.request.build_opener", side_effect=AssertionError("No network allowed")):
            result = investigate(self.root, allow_api_call=True, client_factory=FakeClient)
        self.assertEqual(result["status"], "completed-draft-investigation")
        self.assertEqual(result["api_requests"], 5)
        self.assertEqual(result["local_tool_calls"], 2)
        run = load_investigation(self.root)
        self.assertTrue(run["result"]["test_card_changed"])
        self.assertEqual(run["events"][0]["data"]["execution_mode"], "test-double")

    def test_no_tool_selected_is_a_failed_run_not_fabricated_success(self):
        class NoTool(FakeClient):
            def request(self, body):
                self.calls += 1
                return {"id": "none", "output": []}
        result = investigate(self.root, allow_api_call=True, client_factory=NoTool)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["local_tool_calls"], 0)

    def test_new_citation_alone_does_not_fabricate_a_test_change(self):
        class Retain(FakeClient):
            def request(self, body):
                result = super().request(body)
                if self.calls == 5:
                    result["output"][0]["arguments"] = json.dumps(plan(self.second_ref, False))
                return result
        result = investigate(self.root, allow_api_call=True, client_factory=Retain)
        self.assertEqual(result["status"], "completed-draft-investigation")
        self.assertFalse(load_investigation(self.root)["result"]["test_card_changed"])

    def test_trace_tampering_is_visible(self):
        investigate(self.root, allow_api_call=True, client_factory=FakeClient)
        path = self.root / "outputs/day3/v1/events.jsonl"
        lines = path.read_text().splitlines()
        data = json.loads(lines[-1]); data["data"]["test_card_changed"] = False
        lines[-1] = json.dumps(data); path.write_text("\n".join(lines) + "\n")
        self.assertEqual(load_investigation(self.root)["status"], "needs-review")

    def test_changed_case_marks_replay_stale(self):
        investigate(self.root, allow_api_call=True, client_factory=FakeClient)
        path = self.root / "cases/yu2025-1h.json"
        path.write_text(path.read_text() + "\n")
        self.assertEqual(load_investigation(self.root)["status"], "stale")

    def test_transport_failure_stops_spending_without_retry(self):
        with patch.dict("os.environ", {"MODEL_API_KEY": "offline-test-key"}), patch("urllib.request.build_opener") as opener:
            opener.return_value.open.side_effect = TimeoutError("offline timeout")
            client = MetaClient(self.root, lambda *args: None)
            with self.assertRaises(EvidenceError): client.request({"input": "offline"})
            self.assertEqual(opener.return_value.open.call_count, 1)
        self.assertTrue(api_budget.snapshot(self.root)["unresolved_requests"])

    def test_historical_code_change_is_explicit_archived_replay_not_current_success(self):
        from mre_engineer.evidence import sha256
        investigate(self.root, allow_api_call=True, client_factory=FakeClient)
        with patch("mre_engineer.investigation.sha256",side_effect=lambda p: "0"*64 if Path(p).name=="meta_client.py" else sha256(p)):
            saved=load_investigation(self.root)
        self.assertEqual(saved["status"],"archived-draft-investigation")
        self.assertFalse(saved["current_code_matches"])
        self.assertIsNotNone(saved["result"])
