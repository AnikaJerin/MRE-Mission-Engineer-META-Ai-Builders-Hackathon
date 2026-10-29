"""Mock HTTP diagnostics only; no provider calls."""
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from mre_engineer import api_budget
from mre_engineer.evidence import EvidenceError
from mre_engineer.meta_client import MetaClient, http_diagnostic


class MetaDiagnosticsTests(unittest.TestCase):
    def test_http_error_preserves_status_and_parameter_with_redaction(self):
        error = urllib.error.HTTPError("https://api.meta.ai/v1/responses", 400, "Bad request", {},
            io.BytesIO(json.dumps({"error": {"message": "Invalid test-secret", "param": "text.format", "code": "invalid_schema"}}).encode()))
        value = http_diagnostic(error, "test-secret")
        self.assertEqual(value["http_status"], 400)
        self.assertEqual(value["param"], "text.format")
        self.assertNotIn("test-secret", json.dumps(value))

    def test_non_json_error_body_is_not_logged(self):
        error = urllib.error.HTTPError("https://api.meta.ai/v1/responses", 502, "Gateway", {}, io.BytesIO(b"<html>private proxy content</html>"))
        value = http_diagnostic(error, "")
        self.assertEqual(value["body_status"], "unreadable_or_non_json")
        self.assertNotIn("private", json.dumps(value))

    def test_http_failure_is_recorded_once_and_billing_stays_unresolved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); events = []
            error = urllib.error.HTTPError("https://api.meta.ai/v1/responses", 400, "Bad request", {},
                io.BytesIO(b'{"error":{"message":"Unsupported field","param":"text.format"}}'))
            with patch.dict("os.environ", {"MODEL_API_KEY": "offline-test-key"}), patch("urllib.request.build_opener") as opener:
                opener.return_value.open.side_effect = error
                with self.assertRaisesRegex(EvidenceError, "Meta HTTP 400"):
                    MetaClient(root, lambda kind, data: events.append((kind, data))).request({"input": "offline"})
                self.assertEqual(opener.return_value.open.call_count, 1)
            self.assertEqual(events[-1][0], "api_error")
            self.assertEqual(events[-1][1]["param"], "text.format")
            self.assertEqual(len(api_budget.snapshot(root)["unresolved_requests"]), 1)
