"""Tests for reactor_degradation.py — corrosion, crack, and lifetime models.

All tests use only stdlib / the package under test; no paid API calls.
"""
import math
import unittest

from mre_engineer.evidence import EvidenceError
from mre_engineer.reactor_degradation import (
    arrhenius_rate,
    coffin_manson_cycles,
    lifetime_prediction,
    linear_degradation,
    model_catalog,
    parabolic_degradation,
    thermal_stress,
)


class TestLinearDegradation(unittest.TestCase):
    """linear_degradation() correctness."""

    def test_known_input_output(self):
        """rate=0.25 µm/h over 100 h from 200 µm → loss=25, remaining=175."""
        r = linear_degradation(0.25, 100, 200)
        self.assertAlmostEqual(r['total_loss_um'], 25.0)
        self.assertAlmostEqual(r['remaining_um'], 175.0)
        self.assertFalse(r['domain_exhausted'])

    def test_model_label(self):
        r = linear_degradation(0.1, 10, 100)
        self.assertEqual(r['model'], 'linear')

    def test_domain_exhausted_when_loss_exceeds_thickness(self):
        r = linear_degradation(10.0, 100, 50)   # loss=1000 > 50
        self.assertTrue(r['domain_exhausted'])
        self.assertEqual(r['remaining_um'], 0.0)

    def test_zero_remaining_clamped_to_zero(self):
        r = linear_degradation(1.0, 50, 50)      # exactly depleted
        self.assertEqual(r['remaining_um'], 0.0)

    def test_scope_and_limitations_present(self):
        r = linear_degradation(0.1, 10, 100)
        self.assertIn('scope', r)
        self.assertIn('limitations', r)

    def test_negative_rate_raises(self):
        with self.assertRaises(EvidenceError):
            linear_degradation(-1.0, 10, 100)

    def test_zero_rate_raises(self):
        with self.assertRaises(EvidenceError):
            linear_degradation(0.0, 10, 100)

    def test_nonfinite_horizon_raises(self):
        with self.assertRaises(EvidenceError):
            linear_degradation(0.1, float('inf'), 100)


class TestParabolicDegradation(unittest.TestCase):
    """parabolic_degradation() correctness."""

    def test_sqrt_scaling(self):
        """loss = k·√t, so loss at t=4 should be 2× loss at t=1."""
        r1 = parabolic_degradation(1.0, 1.0, 1000)
        r4 = parabolic_degradation(1.0, 4.0, 1000)
        self.assertAlmostEqual(r4['total_loss_um'], 2 * r1['total_loss_um'], places=6)

    def test_positive_loss_at_nonzero_time(self):
        r = parabolic_degradation(0.5, 9.0, 100)
        # k=0.5, t=9 → loss = 0.5*3 = 1.5
        self.assertAlmostEqual(r['total_loss_um'], 1.5, places=4)

    def test_model_label(self):
        r = parabolic_degradation(1.0, 1.0, 1000)
        self.assertEqual(r['model'], 'parabolic')

    def test_domain_exhausted(self):
        r = parabolic_degradation(100.0, 100.0, 50)   # loss >> thickness
        self.assertTrue(r['domain_exhausted'])

    def test_zero_k_raises(self):
        with self.assertRaises(EvidenceError):
            parabolic_degradation(0.0, 10, 100)

    def test_negative_horizon_raises(self):
        with self.assertRaises(EvidenceError):
            parabolic_degradation(1.0, -1.0, 100)

    def test_scope_present(self):
        r = parabolic_degradation(0.1, 10, 100)
        self.assertIn('scope', r)


class TestArrheniusRate(unittest.TestCase):
    """arrhenius_rate() correctness."""

    def test_positive_output(self):
        rate = arrhenius_rate(1e6, 100_000, 1873)   # 1600 °C
        self.assertGreater(rate, 0)
        self.assertTrue(math.isfinite(rate))

    def test_doubles_with_temperature_increase(self):
        """Rule of thumb: rate roughly doubles every 10 °C near Arrhenius."""
        Q = 100_000   # J/mol
        T1 = 1873.0   # K
        T2 = 1883.0   # K  (+10 K)
        r1 = arrhenius_rate(1.0, Q, T1)
        r2 = arrhenius_rate(1.0, Q, T2)
        # r2 > r1 (higher T → higher rate)
        self.assertGreater(r2, r1)

    def test_higher_Q_means_lower_rate(self):
        """Higher activation energy → exponentially slower rate at same T."""
        r_low_Q = arrhenius_rate(1.0, 50_000, 1873)
        r_high_Q = arrhenius_rate(1.0, 200_000, 1873)
        self.assertGreater(r_low_Q, r_high_Q)

    def test_zero_A_raises(self):
        with self.assertRaises(EvidenceError):
            arrhenius_rate(0.0, 100_000, 1873)

    def test_nonpositive_temperature_raises(self):
        with self.assertRaises(EvidenceError):
            arrhenius_rate(1.0, 100_000, 0.0)

    def test_negative_Q_raises(self):
        with self.assertRaises(EvidenceError):
            arrhenius_rate(1.0, -50_000, 1873)


class TestCoffinMansonCycles(unittest.TestCase):
    """coffin_manson_cycles() correctness."""

    def test_cycles_positive(self):
        r = coffin_manson_cycles(100, 1e6, 2.0)
        self.assertGreater(r['cycles_to_initiation'], 0)
        self.assertTrue(math.isfinite(r['cycles_to_initiation']))

    def test_known_value(self):
        """Nf = 1e6 * 100^(-2) = 100."""
        r = coffin_manson_cycles(100, 1e6, 2.0)
        self.assertAlmostEqual(r['cycles_to_initiation'], 100.0, places=1)

    def test_larger_delta_T_fewer_cycles(self):
        r1 = coffin_manson_cycles(100, 1e6, 2.0)
        r2 = coffin_manson_cycles(200, 1e6, 2.0)
        self.assertGreater(r1['cycles_to_initiation'], r2['cycles_to_initiation'])

    def test_zero_delta_T_raises(self):
        with self.assertRaises(EvidenceError):
            coffin_manson_cycles(0, 1e6, 2.0)

    def test_negative_delta_T_raises(self):
        with self.assertRaises(EvidenceError):
            coffin_manson_cycles(-50, 1e6, 2.0)

    def test_scope_present(self):
        r = coffin_manson_cycles(100, 1e6, 2.0)
        self.assertIn('scope', r)


class TestThermalStress(unittest.TestCase):
    """thermal_stress() correctness."""

    def test_known_value(self):
        """σ = 200e9 * 10.5e-6 * 100 = 210 MPa."""
        r = thermal_stress(200e9, 10.5e-6, 100)
        self.assertAlmostEqual(r['stress_MPa'], 210.0, places=2)

    def test_positive_output(self):
        r = thermal_stress(200e9, 10e-6, 50)
        self.assertGreater(r['stress_MPa'], 0)

    def test_negative_E_raises(self):
        with self.assertRaises(EvidenceError):
            thermal_stress(-200e9, 10e-6, 100)

    def test_zero_alpha_raises(self):
        with self.assertRaises(EvidenceError):
            thermal_stress(200e9, 0.0, 100)

    def test_scope_present(self):
        r = thermal_stress(200e9, 10e-6, 100)
        self.assertIn('scope', r)


class TestLifetimePrediction(unittest.TestCase):
    """lifetime_prediction() correctness and edge cases."""

    def test_linear_model_basic(self):
        """10 µm loss over 10 h, 100 µm thick → rate=1 µm/h, remaining=90 µm → 90 h remaining."""
        r = lifetime_prediction(10, 10, 1000, 100, model='linear')
        self.assertAlmostEqual(r['predicted_remaining_h'], 90.0, delta=5)
        self.assertFalse(r['domain_exhausted'])

    def test_parabolic_model_basic(self):
        """k = loss/√t; check result structure and positivity."""
        r = lifetime_prediction(5, 25, 1000, 200, model='parabolic')
        self.assertGreater(r['predicted_remaining_h'], 0)
        self.assertIn('model_used', r)
        self.assertEqual(r['model_used'], 'parabolic')

    def test_arrhenius_model_requires_temperature(self):
        with self.assertRaises(EvidenceError):
            lifetime_prediction(10, 10, 1000, 100, model='arrhenius')

    def test_arrhenius_model_with_temperature(self):
        r = lifetime_prediction(10, 10, 1000, 100, model='arrhenius', temperature_C=1600)
        self.assertGreater(r['predicted_remaining_h'], 0)
        self.assertEqual(r['model_used'], 'arrhenius')

    def test_domain_exhausted_when_already_worn_through(self):
        """If measured loss ≥ initial thickness, remaining = 0."""
        r = lifetime_prediction(200, 10, 1000, 100, model='linear')
        self.assertTrue(r['domain_exhausted'])
        self.assertEqual(r['predicted_remaining_h'], 0.0)

    def test_bounds_straddle_central_estimate(self):
        r = lifetime_prediction(10, 10, 1000, 100, model='linear', uncertainty_percent=20)
        lo = r['lower_bound_h']
        mid = r['predicted_remaining_h']
        hi = r['upper_bound_h']
        self.assertLessEqual(lo, mid)
        self.assertLessEqual(mid, hi)

    def test_unknown_model_raises(self):
        with self.assertRaises(EvidenceError):
            lifetime_prediction(10, 10, 1000, 100, model='magic')

    def test_negative_loss_raises(self):
        with self.assertRaises(EvidenceError):
            lifetime_prediction(-5, 10, 1000, 100)

    def test_zero_exposure_raises(self):
        with self.assertRaises(EvidenceError):
            lifetime_prediction(5, 0, 1000, 100)

    def test_nonfinite_thickness_raises(self):
        with self.assertRaises(EvidenceError):
            lifetime_prediction(5, 10, 1000, float('nan'))

    def test_scope_and_limitations_present(self):
        r = lifetime_prediction(10, 10, 1000, 100)
        self.assertIn('scope', r)
        self.assertIn('limitations', r)


class TestModelCatalog(unittest.TestCase):
    """model_catalog() output structure."""

    def test_returns_dict(self):
        cat = model_catalog()
        self.assertIsInstance(cat, dict)

    def test_all_expected_models_present(self):
        cat = model_catalog()
        for m in ('linear', 'parabolic', 'arrhenius', 'coffin_manson', 'thermoelastic', 'lifetime'):
            self.assertIn(m, cat['models'])

    def test_disclaimer_present(self):
        cat = model_catalog()
        self.assertIn('important_disclaimer', cat)

    def test_scope_and_limitations(self):
        cat = model_catalog()
        self.assertIn('scope', cat)
        self.assertIn('limitations', cat)


if __name__ == '__main__':
    unittest.main()

