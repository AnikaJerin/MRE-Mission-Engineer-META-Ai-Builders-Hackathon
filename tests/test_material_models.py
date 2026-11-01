import unittest
from mre_engineer.evidence import EvidenceError
from mre_engineer.material_models import calculate, properties
from mre_engineer.reactor_degradation import lifetime_prediction, thermal_stress

class MaterialModelRegressionTests(unittest.TestCase):
    def test_parabolic_life_preserves_existing_age(self):
        v=lifetime_prediction(40,3,2000,1000,model='parabolic',uncertainty_percent=0)
        self.assertEqual(v['predicted_remaining_h'],1872)
        self.assertEqual(v['lower_bound_h'],1872)
        self.assertEqual(v['upper_bound_h'],1872)

    def test_uncertainty_domain(self):
        for value in (100,101,True):
            with self.assertRaises(EvidenceError):
                lifetime_prediction(40,3,10,1000,uncertainty_percent=value)

    def test_every_model_can_be_evaluated(self):
        cases={
            'linear':dict(rate_um_h=10,horizon_h=2,initial_thickness_um=100),
            'parabolic':dict(k_parabolic=10,horizon_h=4,initial_thickness_um=100),
            'arrhenius':dict(A_pre=100,Q_J_per_mol=10000,temperature_K=1000),
            'thermal_cycles':dict(delta_T_C=100,C_constant=1000000,m_exponent=2),
            'thermal_stress':dict(E_Pa=200e9,alpha_per_K=1e-5,delta_T_C=100),
            'lifetime':dict(measured_loss_um=20,exposure_h=2,horizon_h=10,initial_thickness_um=100,uncertainty_percent=20),
        }
        for name,parameters in cases.items():
            with self.subTest(name=name):
                v=calculate(dict(model=name,parameters=parameters))
                self.assertEqual(v['api_calls'],0)
                self.assertTrue(v['result'])
        self.assertEqual(calculate(dict(model='linear',parameters=cases['linear']))['result']['total_loss_um'],20)

    def test_thermal_restraint_is_explicit(self):
        v=thermal_stress(200e9,1e-5,100)
        self.assertEqual(v['stress_MPa'],200)
        self.assertIn('Free thermal expansion',v['note'])

    def test_properties_are_dynamic_and_not_melt(self):
        lo,hi=properties({'temperature_C':1200}),properties({'temperature_C':1600})
        self.assertGreater(hi['ysz_conductivity_S_m'],lo['ysz_conductivity_S_m'])
        self.assertIn('not molten',hi['scope'])

    def test_invalid_model_rejected(self):
        with self.assertRaises(EvidenceError):calculate({'model':'unknown','parameters':{}})
