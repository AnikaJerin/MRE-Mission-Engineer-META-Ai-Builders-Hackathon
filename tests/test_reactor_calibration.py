"""Tests for reactor_calibration.py — temperature-dependent material properties.

All tests use only stdlib / the package under test; no paid API calls.
"""
import math
import unittest

from mre_engineer.evidence import EvidenceError
from mre_engineer.reactor_calibration import (
    calibration_profile,
    calibrated_scenario,
    ysz_conductivity,
    mo_resistivity,
)


class TestYszConductivity(unittest.TestCase):
    """YSZ Arrhenius conductivity model."""

    def test_positive_at_operating_temperature(self):
        """Conductivity must be positive at MRE operating temperature."""
        sigma = ysz_conductivity(1600)
        self.assertGreater(sigma, 0)
        self.assertTrue(math.isfinite(sigma))

    def test_increases_with_temperature(self):
        """Ionic conductors: σ increases as temperature rises."""
        self.assertLess(ysz_conductivity(1000), ysz_conductivity(1200))
        self.assertLess(ysz_conductivity(1200), ysz_conductivity(1400))
        self.assertLess(ysz_conductivity(1400), ysz_conductivity(1600))

    def test_reference_range_at_1600C(self):
        """Bulk 8YSZ typically 1–10 S/m at 1600 °C (Badwal 1992, Ivers-Tiffee 2001)."""
        sigma = ysz_conductivity(1600)
        self.assertGreater(sigma, 0.1)
        self.assertLess(sigma, 20.0)

    def test_below_minimum_temperature_raises(self):
        with self.assertRaises(EvidenceError):
            ysz_conductivity(800)

    def test_above_maximum_temperature_raises(self):
        with self.assertRaises(EvidenceError):
            ysz_conductivity(1900)

    def test_nonfinite_raises(self):
        with self.assertRaises(EvidenceError):
            ysz_conductivity(float('inf'))

    def test_nan_raises(self):
        with self.assertRaises(EvidenceError):
            ysz_conductivity(float('nan'))


class TestMoResistivity(unittest.TestCase):
    """Mo linear resistivity model."""

    def test_positive_at_operating_temperature(self):
        rho = mo_resistivity(1600)
        self.assertGreater(rho, 0)
        self.assertTrue(math.isfinite(rho))

    def test_increases_with_temperature(self):
        """Metallic conductors: ρ increases as temperature rises."""
        self.assertLess(mo_resistivity(20), mo_resistivity(500))
        self.assertLess(mo_resistivity(500), mo_resistivity(1000))
        self.assertLess(mo_resistivity(1000), mo_resistivity(1600))

    def test_reference_value_at_room_temperature(self):
        """Mo ρ at 20 °C: published ~5.2×10⁻⁸ Ω·m."""
        rho = mo_resistivity(20)
        self.assertAlmostEqual(rho, 5.2e-8, delta=1e-9)

    def test_nonfinite_raises(self):
        with self.assertRaises(EvidenceError):
            mo_resistivity(float('nan'))


class TestCalibrationProfile(unittest.TestCase):
    """calibration_profile() output structure."""

    def setUp(self):
        self.profile = calibration_profile()

    def test_returns_dict(self):
        self.assertIsInstance(self.profile, dict)

    def test_expected_keys_present(self):
        for key in ('temperatures_C', 'ysz_conductivity_S_m', 'mo_resistivity_ohm_m',
                    'scope', 'limitations', 'reference_values'):
            self.assertIn(key, self.profile)

    def test_temperatures_cover_mre_range(self):
        temps = self.profile['temperatures_C']
        self.assertIn(1600, temps)
        self.assertGreaterEqual(min(temps), 1000)
        self.assertLessEqual(max(temps), 1750)

    def test_lists_same_length(self):
        n = len(self.profile['temperatures_C'])
        self.assertEqual(len(self.profile['ysz_conductivity_S_m']), n)
        self.assertEqual(len(self.profile['mo_resistivity_ohm_m']), n)

    def test_all_ysz_values_positive(self):
        for v in self.profile['ysz_conductivity_S_m']:
            self.assertGreater(v, 0)

    def test_all_mo_values_positive(self):
        for v in self.profile['mo_resistivity_ohm_m']:
            self.assertGreater(v, 0)

    def test_scope_and_limitations_present(self):
        self.assertIsInstance(self.profile['scope'], str)
        self.assertIsInstance(self.profile['limitations'], list)
        self.assertGreater(len(self.profile['limitations']), 0)


class TestCalibratedScenario(unittest.TestCase):
    """calibrated_scenario() output structure and physics."""

    _BASE_SCENARIO = {
        'inner_radius_mm': 3.0,
        'outer_radius_mm': 5.0,
        'height_mm': 25.0,
        'conductivity_S_m': 10.0,        # deliberately different from YSZ Arrhenius value
        'thermal_conductivity_W_mK': 2.0,
        'current_A': 0.5,
        'inner_temperature_C': 1550.0,
        'outer_temperature_C': 1650.0,
    }

    def test_returns_dict_with_required_keys(self):
        result = calibrated_scenario(dict(self._BASE_SCENARIO))
        for key in ('samples', 'bulk_resistance_ohm', 'bulk_voltage_V',
                    'joule_power_W', 'peak_temperature_C', 'calibration'):
            self.assertIn(key, result)

    def test_calibration_block_present(self):
        result = calibrated_scenario(dict(self._BASE_SCENARIO))
        cal = result['calibration']
        self.assertIn('method', cal)
        self.assertEqual(cal['method'], 'ysz_arrhenius_bulk')
        self.assertIn('overridden_conductivity_S_m', cal)
        self.assertIn('scope', cal)
        self.assertIn('limitations', cal)

    def test_overridden_conductivity_differs_from_user_input(self):
        """The returned conductivity should be the YSZ Arrhenius value, not user's 10.0."""
        result = calibrated_scenario(dict(self._BASE_SCENARIO))
        cal = result['calibration']
        self.assertNotAlmostEqual(cal['overridden_conductivity_S_m'], 10.0, places=1)

    def test_midpoint_temperature_is_average(self):
        result = calibrated_scenario(dict(self._BASE_SCENARIO))
        cal = result['calibration']
        self.assertAlmostEqual(cal['midpoint_temperature_C'], 1600.0, places=5)

    def test_all_sample_temperatures_finite(self):
        result = calibrated_scenario(dict(self._BASE_SCENARIO))
        for s in result['samples']:
            self.assertTrue(math.isfinite(s['temperature_C']))

    def test_invalid_scenario_raises_evidence_error(self):
        bad = dict(self._BASE_SCENARIO)
        del bad['inner_radius_mm']
        with self.assertRaises(EvidenceError):
            calibrated_scenario(bad)

    def test_temperature_out_of_range_raises_evidence_error(self):
        """Mid temperature below YSZ model floor (900 C) must raise."""
        cold = dict(self._BASE_SCENARIO)
        cold['inner_temperature_C'] = 400.0
        cold['outer_temperature_C'] = 500.0
        with self.assertRaises(EvidenceError):
            calibrated_scenario(cold)


if __name__ == '__main__':
    unittest.main()
