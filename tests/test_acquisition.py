import shutil
import tempfile
import unittest
from pathlib import Path

from mre_engineer.acquisition import acquisition_status, register_file
from mre_engineer.dashboard import snapshot
from mre_engineer.evidence import EvidenceError

ROOT = Path(__file__).resolve().parents[1]


class AcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "sources", self.root / "sources")
        shutil.copytree(ROOT / "cases", self.root / "cases")

    def test_missing_files_do_not_impersonate_downloads(self):
        self.assertEqual(acquisition_status(self.root, "yu2025-main")["status"], "not-registered")

    def test_html_download_is_rejected_as_pdf(self):
        path = self.root / "bad.pdf"
        path.write_text("<html>Unavailable</html>")
        with self.assertRaises(EvidenceError):
            register_file(self.root, "yu2025-main", path)

    def test_local_hash_does_not_certify_scientific_content(self):
        path = self.root / "fixture.pdf"
        # Intentionally not a real paper: registration claims only integrity.
        path.write_bytes(b"%PDF-1.7\nplaceholder for receipt test\n")
        register_file(self.root, "yu2025-main", path)
        status = acquisition_status(self.root, "yu2025-main")
        self.assertEqual(status["status"], "local-hash-matches")
        self.assertNotIn("path", status)
        path.write_bytes(b"%PDF-1.7\nchanged content\n")
        self.assertEqual(acquisition_status(self.root, "yu2025-main")["status"], "registered-file-changed")

    def test_snapshot_does_not_claim_an_agent_run(self):
        data = snapshot(self.root)
        self.assertFalse(data["agent_run_ready"])
        self.assertEqual(data["api_calls"], 0)
        self.assertEqual(len(data["sources"]), 8)
        self.assertTrue(all(s["local_acquisition"]["status"] == "not-registered" for s in data["sources"]))
