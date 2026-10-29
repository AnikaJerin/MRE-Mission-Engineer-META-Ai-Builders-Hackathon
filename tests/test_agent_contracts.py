import json
import unittest
from mre_engineer.agent_contracts import parse_action, strict_json, structured_result
from mre_engineer.evidence import EvidenceError


class ContractTests(unittest.TestCase):
    def test_arbitrary_code_tool_is_rejected(self):
        with self.assertRaises(EvidenceError):
            parse_action({"output": [{"type": "function_call", "name": "run_shell", "call_id": "a", "arguments": "{}"}]}, {"check_charge_accounting"})

    def test_plain_text_is_not_a_fabricated_tool_execution(self):
        with self.assertRaises(EvidenceError):
            parse_action({"output": [{"type": "message", "content": [{"type": "output_text", "text": "No check needed"}]}]}, {"check_charge_accounting"})

    def test_no_measurement_injection_through_tool_arguments(self):
        with self.assertRaises(EvidenceError):
            parse_action({"output": [{"type": "function_call", "name": "check_charge_accounting", "call_id": "a", "arguments": '{"current_a": 100}'}]}, {"check_charge_accounting"})

    def test_duplicate_and_nonfinite_json_are_rejected(self):
        for text in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}'):
            with self.subTest(text=text), self.assertRaises(EvidenceError): strict_json(text)

    def test_unknown_citation_is_rejected(self):
        challenge = {"weakness": "Unknown calibration", "why_it_matters": "Cannot verify collection",
                     "alternate_explanation": "Collection uncertainty", "evidence_refs": ["invented"],
                     "requested_revision": "Request evidence"}
        response = {"output": [{"type": "function_call", "name": "submit_challenge", "call_id": "a", "arguments": json.dumps(challenge)}]}
        with self.assertRaises(EvidenceError):
            structured_result(response, "submit_challenge", {"tool-real"}, {"tool-real"})
