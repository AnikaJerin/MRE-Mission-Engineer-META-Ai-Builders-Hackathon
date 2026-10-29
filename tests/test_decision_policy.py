import copy
import unittest
from pathlib import Path
from mre_engineer.evaluation import load_cases,checked_packet,checklist
from mre_engineer.decision_policy import release_decision
from mre_engineer.dossier import to_html

ROOT=Path(__file__).resolve().parents[1]


class ReleasePolicyTests(unittest.TestCase):
    def test_unsupported_unit_cannot_be_released_and_raw_is_retained(self):
        case=next(c for c in load_cases(ROOT) if c["case_id"]=="constructed-unsupported-unit")
        answer=checklist(checked_packet(case));answer["decision"]="proceed_conditional_review";original=copy.deepcopy(answer)
        result=release_decision(case["packet"],answer)
        self.assertEqual(result["effective_decision"]["decision"],"reject_input")
        self.assertEqual(result["raw_decision"],original);self.assertEqual(answer,original)

    def test_scope_and_missing_record_gates_remain_deterministic(self):
        cases={c["case_id"]:c for c in load_cases(ROOT)}
        for id,wanted in (("constructed-out-of-scope","reject_scope"),("constructed-missing-calibration","request_evidence")):
            case=cases[id];answer=checklist(checked_packet(case));answer["decision"]="proceed_conditional_review"
            self.assertEqual(release_decision(case["packet"],answer)["effective_decision"]["decision"],wanted)

    def test_valid_inputs_do_not_fabricate_hardware_approval(self):
        case=next(c for c in load_cases(ROOT) if c["case_id"]=="constructed-complete")
        answer=checklist(checked_packet(case));result=release_decision(case["packet"],answer)
        self.assertFalse(result["gate_applied"]);self.assertFalse(result["effective_decision"]["ready_for_hardware_operation"])

    def test_dossier_html_escapes_untrusted_prose(self):
        data={"created_at":"now","claim_limits":["<script>alert(1)</script>"],"pilot":{"status":"ok","text":"<img src=x onerror=alert(1)>"}}
        rendered=to_html(data)
        self.assertNotIn("<script>",rendered);self.assertNotIn("<img",rendered)
        self.assertIn("&lt;script&gt;",rendered)
