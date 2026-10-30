import unittest
from mre_engineer.reactor_field import simulate, validate_scenario
from mre_engineer.evidence import EvidenceError

class ReactorFieldTests(unittest.TestCase):
    def scenario(self):
        return dict(inner_radius_mm=3,outer_radius_mm=12,height_mm=25,conductivity_S_m=10,
                    thermal_conductivity_W_mK=2,current_A=.5,inner_temperature_C=1600,outer_temperature_C=1500)
    def test_analytic_solution_and_energy_balance(self):
        r=simulate(self.scenario());v=r['verification']
        self.assertLess(v['energy_balance_error_W'],1e-7)
        self.assertLess(v['analytic_max_error_C'],v['coarse_analytic_error_C'])
        self.assertLess(v['analytic_max_error_C'],.01)
    def test_zero_current_equal_boundaries_is_isothermal(self):
        s=self.scenario();s.update(current_A=0,outer_temperature_C=1600)
        r=simulate(s)
        self.assertAlmostEqual(r['joule_power_W'],0)
        for row in r['samples']:self.assertAlmostEqual(row['temperature_C'],1600,places=7)
    def test_current_scaling_is_not_a_fixed_field(self):
        s=self.scenario();a=simulate(s);s['current_A']*=2;b=simulate(s)
        self.assertAlmostEqual(b['joule_power_W'],4*a['joule_power_W'])
        self.assertAlmostEqual(b['bulk_voltage_V'],2*a['bulk_voltage_V'])
    def test_missing_invalid_or_unphysical_geometry_rejected(self):
        for change in ({'inner_radius_mm':12},{'current_A':float('nan')},{'current_A':True}):
            s=self.scenario();s.update(change)
            with self.assertRaises(EvidenceError):validate_scenario(s)
        with self.assertRaises(EvidenceError):validate_scenario({})
