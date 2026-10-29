import tempfile
import unittest
from pathlib import Path
from mre_engineer import api_budget
from mre_engineer.evidence import EvidenceError


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_reservation_stops_parallel_or_uncertain_spending(self):
        id = api_budget.reserve(self.root)
        self.assertEqual(api_budget.snapshot(self.root)["accounted_or_reserved_usd"], 0.25)
        with self.assertRaises(EvidenceError): api_budget.reserve(self.root)
        api_budget.settle(self.root, id, None)
        with self.assertRaises(EvidenceError): api_budget.reserve(self.root)

    def test_usage_is_accounted_at_uncached_wonder_rates(self):
        id = api_budget.reserve(self.root)
        api_budget.settle(self.root, id, {"input_tokens": 1000, "output_tokens": 1000})
        self.assertAlmostEqual(api_budget.snapshot(self.root)["accounted_or_reserved_usd"], 0.024)
        self.assertFalse(api_budget.snapshot(self.root)["unresolved_requests"])

    def test_usage_over_reservation_blocks_further_calls(self):
        id = api_budget.reserve(self.root)
        api_budget.settle(self.root, id, {"input_tokens": 100000, "output_tokens": 10000})
        self.assertGreater(api_budget.snapshot(self.root)["accounted_or_reserved_usd"], 0.25)
        with self.assertRaises(EvidenceError): api_budget.reserve(self.root)

    def test_corrupt_ledger_fails_closed(self):
        path = self.root / "outputs/api-ledger.json"; path.parent.mkdir()
        path.write_text('{"version":1,"requests":[{"id":"bad","state":"settled","accounted_microusd":-1}]}')
        with self.assertRaises(EvidenceError): api_budget.snapshot(self.root)

    def test_reconciliation_requires_explicit_provider_review(self):
        id = api_budget.reserve(self.root)
        with self.assertRaises(EvidenceError): api_budget.reconcile(self.root, id, 0, False)
        api_budget.reconcile(self.root, id, 0.01, True)
        self.assertFalse(api_budget.snapshot(self.root)["unresolved_requests"])
        with self.assertRaises(EvidenceError): api_budget.reconcile(self.root, id, 0, True)

    def test_acknowledgement_retains_unknown_cost_and_reservation(self):
        id = api_budget.reserve(self.root); api_budget.settle(self.root, id, None)
        with self.assertRaises(EvidenceError): api_budget.acknowledge_unknown_cost(self.root, id, False)
        api_budget.acknowledge_unknown_cost(self.root, id, True)
        status = api_budget.snapshot(self.root)
        self.assertEqual(status["unresolved_requests"], [id])
        self.assertFalse(status["blocking_unresolved_requests"])
        self.assertEqual(status["accounted_or_reserved_usd"], 0.25)
        second = api_budget.reserve(self.root)
        self.assertEqual(api_budget.snapshot(self.root)["accounted_or_reserved_usd"], 0.5)
        self.assertEqual(api_budget.snapshot(self.root)["blocking_unresolved_requests"], [second])
        api_budget.settle(self.root, second, {"input_tokens": 1, "output_tokens": 1})
        api_budget.reconcile(self.root, id, 0.01, True)
        self.assertFalse(api_budget.snapshot(self.root)["unresolved_requests"])

    def test_acknowledgement_cannot_override_active_or_exceeded_reservation(self):
        id = api_budget.reserve(self.root)
        with self.assertRaises(EvidenceError): api_budget.acknowledge_unknown_cost(self.root, id, True)
        api_budget.settle(self.root, id, {"input_tokens": 100000, "output_tokens": 10000})
        with self.assertRaises(EvidenceError): api_budget.acknowledge_unknown_cost(self.root, id, True)
        with self.assertRaises(EvidenceError): api_budget.reserve(self.root)

    def test_acknowledged_cost_still_counts_toward_local_limit(self):
        from unittest.mock import patch
        id = api_budget.reserve(self.root); api_budget.settle(self.root, id, None)
        api_budget.acknowledge_unknown_cost(self.root, id, True)
        with patch.object(api_budget, "PROJECT_LIMIT_MICROUSD", 250000):
            with self.assertRaises(EvidenceError): api_budget.reserve(self.root)
