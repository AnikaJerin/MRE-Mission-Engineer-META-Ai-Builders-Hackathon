import copy
import tempfile
import unittest
from pathlib import Path

from mre_engineer.evidence import EvidenceError, read_json, validate_case

ROOT = Path(__file__).resolve().parents[1]


class EvidenceContractTests(unittest.TestCase):
    def setUp(self):
        self.manifest = read_json(ROOT / "sources/manifest.json")
        self.case = read_json(ROOT / "cases/yu2025-1h.json")

    def test_historical_case_retains_limitations(self):
        result = validate_case(self.case, self.manifest)
        self.assertEqual(result["provenance_class"], "published_summary")
        self.assertEqual(result["evaluation_role"], "development_only")
        self.assertTrue(result["missing_inputs"])

    def test_percent_masquerading_as_fraction_is_rejected(self):
        item = next(x for x in self.case["evidence"] if x.get("field") == "faradaic_efficiency")
        item["value"] = 47
        with self.assertRaises(EvidenceError):
            validate_case(self.case, self.manifest)

    def test_wrong_unit_is_rejected(self):
        item = next(x for x in self.case["evidence"] if x.get("field") == "current")
        item["unit"] = "mA"
        with self.assertRaises(EvidenceError):
            validate_case(self.case, self.manifest)

    def test_missing_citation_cannot_pass(self):
        del self.case["evidence"][0]["locator"]
        with self.assertRaises(EvidenceError):
            validate_case(self.case, self.manifest)

    def test_unknown_source_is_rejected(self):
        self.case["evidence"][0]["source_id"] = "fabricated-source"
        with self.assertRaises(EvidenceError):
            validate_case(self.case, self.manifest)

    def test_duplicate_evidence_id_is_rejected(self):
        self.case["evidence"].append(copy.deepcopy(self.case["evidence"][0]))
        with self.assertRaises(EvidenceError):
            validate_case(self.case, self.manifest)

    def test_unknown_uncertainty_requires_null_value(self):
        self.case["evidence"][0]["uncertainty"] = {"status": "unknown", "value": 0}
        with self.assertRaises(EvidenceError):
            validate_case(self.case, self.manifest)

    def test_nonfinite_json_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            path.write_text('{"value": NaN}')
            with self.assertRaises(EvidenceError):
                read_json(path)

    def test_overflowing_json_number_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            path.write_text('{"value": 1e999}')
            with self.assertRaises(EvidenceError):
                read_json(path)


if __name__ == "__main__":
    unittest.main()
