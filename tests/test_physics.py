import csv
import math
import tempfile
import unittest
from pathlib import Path

from mre_engineer.evidence import EvidenceError
from mre_engineer.physics import (FARADAY_C_PER_MOL, charge_oxygen_bound,
                                 load_composition, oxygen_inventory)

ROOT = Path(__file__).resolve().parents[1]


class AccountingPhysicsTests(unittest.TestCase):
    def setUp(self):
        self.rows = load_composition(ROOT / "cases/feedstocks/lhs1-yu2025.csv", {"yu2025-main"})

    def test_no_silent_normalization_of_published_composition(self):
        result = oxygen_inventory(self.rows, 100)
        self.assertAlmostEqual(result["oxide_total_wt_percent"], 99.1)
        self.assertAlmostEqual(result["unrepresented_wt_percent"], 0.9)
        self.assertFalse(result["normalization_applied"])
        self.assertGreater(result["represented_oxygen_g"], 40)
        self.assertLess(result["represented_oxygen_g"], 50)

    def test_inventory_scales_with_reference_mass_not_yield(self):
        small = oxygen_inventory(self.rows, 1)["represented_oxygen_g"]
        large = oxygen_inventory(self.rows, 100)["represented_oxygen_g"]
        self.assertAlmostEqual(large, small * 100)

    def test_four_faradays_correspond_to_one_mole_oxygen(self):
        result = charge_oxygen_bound(FARADAY_C_PER_MOL, 4)
        self.assertAlmostEqual(result["ideal_oxygen_mol"], 1)
        self.assertAlmostEqual(result["ideal_oxygen_g"], 31.998)

    def test_published_one_hour_case_is_near_reported_47_percent(self):
        result = charge_oxygen_bound(0.5, 3600, 0.070)
        self.assertEqual(result["charge_c"], 1800)
        self.assertAlmostEqual(result["ideal_oxygen_g"], 0.14923, delta=0.00002)
        self.assertAlmostEqual(result["apparent_oxygen_to_charge_ratio"], 0.47, delta=0.005)

    def test_impossible_ratio_is_flagged_not_clipped(self):
        result = charge_oxygen_bound(0.5, 3600, 1)
        self.assertTrue(result["ratio_exceeds_one"])
        self.assertGreater(result["apparent_oxygen_to_charge_ratio"], 1)
        self.assertEqual(result["status"], "accounting-inconsistency-needs-review")

    def test_bad_numbers_and_missing_inputs_are_not_invented(self):
        for value in (0, -1, True, math.inf, math.nan):
            with self.subTest(value=value), self.assertRaises(EvidenceError):
                charge_oxygen_bound(value, 3600)
        with self.assertRaises(EvidenceError):
            charge_oxygen_bound(0.5, None)
        with self.assertRaises(EvidenceError):
            oxygen_inventory(self.rows, float("inf"))

    def write_variant(self, change):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / "composition.csv"
        rows = [dict(r, value=str(r["value"])) for r in self.rows]
        change(rows)
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_weight_fraction_cannot_masquerade_as_weight_percent(self):
        path = self.write_variant(lambda rows: rows[0].update(unit="fraction"))
        with self.assertRaises(EvidenceError):
            load_composition(path, {"yu2025-main"})

    def test_analysis_mixing_is_rejected(self):
        path = self.write_variant(lambda rows: rows[0].update(analysis_id="different-batch"))
        with self.assertRaises(EvidenceError):
            load_composition(path, {"yu2025-main"})

    def test_ambiguous_total_iron_is_not_speciated(self):
        path = self.write_variant(lambda rows: rows[1].update(oxide="FeOT"))
        with self.assertRaises(EvidenceError):
            load_composition(path, {"yu2025-main"})

    def test_duplicate_oxide_is_rejected(self):
        path = self.write_variant(lambda rows: rows[1].update(oxide="SiO2"))
        with self.assertRaises(EvidenceError):
            load_composition(path, {"yu2025-main"})

    def test_excess_total_is_rejected_instead_of_rescaled(self):
        path = self.write_variant(lambda rows: rows[0].update(value="60"))
        with self.assertRaises(EvidenceError):
            load_composition(path, {"yu2025-main"})
