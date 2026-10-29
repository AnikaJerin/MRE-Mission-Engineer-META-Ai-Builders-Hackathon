import json
import shutil
import tempfile
import unittest
from pathlib import Path

from mre_engineer.day2 import build_report, load_saved_report, save_report
from mre_engineer.evidence import EvidenceError

ROOT = Path(__file__).resolve().parents[1]


class Day2ReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for folder in ("cases", "sources"):
            shutil.copytree(ROOT / folder, self.root / folder)

    def test_historical_check_is_rounding_not_prediction(self):
        result = build_report(self.root)
        self.assertEqual(result["historical_comparison"]["status"], "rounding-compatible")
        self.assertEqual(result["api_calls"], 0)
        self.assertFalse(result["agent_run_ready"])
        self.assertEqual(result["inventory"]["uncertainty"]["status"], "unknown")

    def test_missing_input_does_not_produce_a_result(self):
        path = self.root / "cases/yu2025-1h.json"
        case = json.loads(path.read_text())
        case["evidence"] = [e for e in case["evidence"] if e.get("field") != "current"]
        path.write_text(json.dumps(case))
        with self.assertRaises(EvidenceError):
            build_report(self.root)

    def test_failed_historical_check_is_visible(self):
        path = self.root / "cases/yu2025-1h.json"
        case = json.loads(path.read_text())
        next(e for e in case["evidence"] if e.get("field") == "oxygen_mass")["value"] = 0.1
        path.write_text(json.dumps(case))
        self.assertEqual(build_report(self.root)["historical_comparison"]["status"],
                         "rounding-mismatch-needs-review")

    def test_saved_report_roundtrip_and_no_overwrite(self):
        save_report(self.root, "v1")
        self.assertEqual(load_saved_report(self.root, "v1")["status"], "saved-accounting-available")
        with self.assertRaises(EvidenceError):
            save_report(self.root, "v1")

    def test_changed_inputs_invalidate_replay(self):
        save_report(self.root, "v1")
        path = self.root / "cases/feedstocks/lhs1-yu2025.csv"
        path.write_text(path.read_text() + "\n")
        self.assertEqual(load_saved_report(self.root, "v1")["status"], "stale")

    def test_modified_report_is_rejected(self):
        _, path = save_report(self.root, "v1")
        report = json.loads(path.read_text())
        report["inventory"]["represented_oxygen_g"] = 0
        path.write_text(json.dumps(report))
        self.assertEqual(load_saved_report(self.root, "v1")["status"], "needs-review")

    def test_run_path_traversal_is_rejected(self):
        with self.assertRaises(EvidenceError):
            save_report(self.root, "../../elsewhere")
